import json
import os
from os import makedirs
from os.path import exists

import corenlp
import pandas as pd
import pdb

from sofia.causal_extraction import CausalLinks
from sofia.corenlp_parse import DataExtractor
from sofia.event_extraction import CandidateEvents
from sofia.ontology_mapping import Ontology
from sofia.query_search import QueryFinder


def span_to_index(local_index, span_list):
    if span_list==0:
        return ""
    index=""
    for span in span_list:
        i= local_index[span]
        if i!= "":
            index+= i+ ', '
    index= index.strip(', ')
    return index

class SOFIA:
    """SOFIA class. Can be invoked with:
       
       ```
       sofia = SOFIA(CoreNLP='path_to_CoreNLP')
       sentence="The intense rain caused flooding in the area. This has harmed the local populace."
       results = sofia.get_online_output(sentence)
       sofia.results2excel('output.xlsx',results)
       sofia.getQueryBasedOutput(document_path, output_name, queryList)
       :keyword
       sofia.getOutputFromFiles(document_path, output_name, docs= None)
       ```
       
       In this example, results is an array of JSON objects (one per sentence submitted to SOFIA).
       The final line writes this output to an Excel file at the user specified path.
    """

    def __init__(self, ontology_name):
        self.causal_headers = ["Source_File", 'Query', "Score",  "Span", "Relation Index", "Relation", "Relation_Type",
                               "Indicator", "Cause Index", "Cause", "Effect Index", "Effect", "Sentence"]
        self.event_headers = ["Source_File", 'Query', "Score", "Event Index", "Span", "Sentence Span","Relation", "Event_Type",
                              "FrameNet_Frame", "Indicator", "Location", "Time", 'Agent Index', "Agent",
                              'Patient Index', "Patient", "Sentence"]
        self.entity_headers = ["Source_File", 'Query', "Score", "Entity Index", "Span", "Sentence Span", "Entity", "Entity_Type",
                               "FrameNet_Frame", "Indicator", "Qualifier", "Sentence"]
        self.variable_headers = ["Source_File", 'Sentence', 'Indicator', 'Scoring', 'Index']
        self.entity_index = 0
        self.event_index = 0
        self.variable_index = 0
        self.causal_index = 0
        self.ontology_name = ontology_name

        if os.getenv('CORENLP_HOME') is not None and os.getenv('CORENLP_HOME') != '':
            print(f'using Stanford CoreNLP Server @ {os.getenv("CORENLP_HOME")}')
            self.CoreNLPclient = corenlp.CoreNLPClient( start_server=True,
                                                        be_quiet=True,
                                                        timeout=100000,
                                                        annotators=['tokenize',
                                                                   'ssplit',
                                                                   'pos',
                                                                   'parse',
                                                                   'lemma',
                                                                   'ner',
                                                                   'depparse'])
            self.CoreNLPclient.annotate("hello world") # warmup the CoreNLP client and start the java server
        else:
            raise ValueError('the "CORENLP_HOME" environment variable is not set, cannot run Stanford CoreNLP Server')

    def get_output(self, data_extractor, doc_id, scoring = False):
        output = []
        eventReader = CandidateEvents(data_extractor, self.ontology_name)
        num_sentences = data_extractor.get_data_size()
        all_events, all_entities = eventReader.get_semantic_units()
        self.eventReader = eventReader
        for s_index in range(num_sentences):
            events= all_events[s_index]
            entities= all_entities[s_index]
            sentence_output = self.sentence_output(doc_id, data_extractor, s_index, events, entities, 'None', 'None',
                                                   scoring = scoring)
            output.append(sentence_output)
        return output

    def sentence_output(self, doc_id, data_extractor, s_index, events, entities, query, query_finder, scoring = False):
        output = {}
        sentence= data_extractor.sentences[s_index]
        ontology = Ontology(self.ontology_name)
        self.variable_index += 1
        variable_index = 'V{}'.format(self.variable_index)
        scores=''
        if scoring:
            scores = ontology.string_matching(sentence, 'WorldBank')
        output['Variables'] = dict(zip(self.variable_headers, [doc_id, sentence, query, str(scores), variable_index]))
        lemmas= data_extractor.get_lemmas(s_index)
        pos= data_extractor.get_pos_tags(s_index)
        sentence_span= data_extractor.get_sentence_span(s_index)
        entity_local_index = {}
        entity_scores={}
        output['Entities'] = []
        for span in list(entities.keys()):
            self.entity_index += 1
            entity_index = 'N{}'.format(self.entity_index)
            entity = entities[span]
            entity_local_index[span] = entity_index
            #scores = ontologyMapper.stringMatching(entity["trigger"], 'WorldBank')
            score=0.0
            if query_finder!= 'None':
                score= query_finder.rank_node(entity, 'entity', sentence)
                entity_scores[entity_index] = score
            entity_info = [doc_id, query, str(score), entity_index, span, (int(span[0])-sentence_span[0], int(span[1])-sentence_span[0]),
                           entity["trigger"].lower(), entity["frame"],
                       str(entity["frame_FN"]), str(scores), entity['qualifier'].lower(), sentence]
            output['Entities'].append(dict(zip(self.entity_headers,entity_info)))

        event_local_index = {}
        event_scores={}
        event2Spans=[]
        output['Events'] = []
        for span in list(events.keys()):
            event = events[span]
            self.event_index += 1
            event_index = 'E{}'.format(self.event_index)
            event_local_index[span] = event_index
            if 'property' in event['frame']:
                event2Spans.append(span)
                self.event_index -= 1
                continue
            patient = span_to_index(entity_local_index, event['patient'][0])
            agent = span_to_index(entity_local_index, event['agent'][0])
            score = 0.0
            if query_finder != 'None':
                score = query_finder.rank_node(event, 'event', sentence)
            event_scores[event_index] = score

            event_info = [doc_id, query, str(score), event_index, span, (int(span[0])-sentence_span[0], int(span[1])-sentence_span[0]),
                          event["trigger"], event["frame"],
                         str(event["frame_FN"]), str(scores), event['location'],
                             event['temporal'], agent, event['agent'][1], patient, event['patient'][1], sentence]
            output['Events'].append(dict(zip(self.event_headers,event_info)))
        ###############
        #Does this do anything???
        for span in event2Spans:
            event = events[span]
            self.event_index += 1
            event_index = 'E{}'.format(self.event_index)
            event_local_index[span] = event_index
        #TODO: Fix the Causality Model
        #######
        #It currently chooses ALL the events. This is wrong, it should choose the ones that do not contain others as arguments
        causal_detector = CausalLinks(events, event_local_index, event2Spans, entities, entity_local_index, sentence, lemmas, pos,
                       event_scores, entity_scores)
        causal_relations = causal_detector.get_causal_nodes()  ### OR TRUE
        output['Causal'] = []
        for relation in causal_relations:
            self.causal_index += 1
            causal_index = 'R{}'.format(self.causal_index)
            cause = relation["cause"]
            effect = relation["effect"]
            relation_type = relation['type']
            score = 0.0
            if query_finder != 'None':
                score = query_finder.rank_node((event_scores, cause[0], effect[0]), 'relation', sentence)
            causal_info = [doc_id, query, str(score), sentence_span, causal_index, relation["trigger"], relation_type,
                           str(scores), cause[0], cause[1], effect[0], effect[1], sentence]
            output['Causal'].append(dict(zip(self.causal_headers,causal_info)))
        return output

    def get_online_output(self, text, doc_id, experiment='generic', save= True, scoring = False):
        print(f'sofia processing started for {doc_id}')
        #if text!= None:
        if not exists(f'sofia/data/{experiment}_output'):
            makedirs(f'sofia/data/{experiment}_output')
        try:
            #Change if new files might come in!
            #if os.path.exists(f'sofia/data/{experiment}/annotations/{doc_id}.json'):
            if os.path.exists(f'sofia/data/{experiment}/annotations'):
                annotations = self.load_annotations(experiment, doc_id)
            else:
                annotations = self.annotate(text, experiment, save= save, doc_id= doc_id)
            data_extractor = DataExtractor(annotations)
            output = self.get_output(data_extractor, doc_id, scoring=scoring)
            #print("output!")
            data= {'entities': self.flatten([i['Entities'] for i in output]),
                         'events': self.flatten([i['Events'] for i in output]),
                         'causal': self.flatten([i['Causal'] for i in output])}

            output_file = open(f'sofia/data/{experiment}_output/{doc_id}.json', 'w')
            json.dump(data, output_file)
            output_file.close()
            return output_file.name
        except Exception as e:
            print(e)
            return None


    def annotate(self, text, experiment, save= 'True', doc_id= 'user_input'):
        annotations = self.CoreNLPclient.annotate(text, output_format='json')
        self.entityIndex = 0
        self.eventIndex = 0
        self.variableIndex = 0
        self.causalIndex = 0
        if save:
            json.dump(annotations, open(f'sofia/data/{experiment}/annotations/{doc_id}.json', 'w'))
        return annotations

    def load_annotations(self, experiment, doc_id):
        if '.json' in doc_id:
            f=open(f'sofia/data/{experiment}/annotations/{doc_id}')
        else:
            f = open(f'sofia/data/{experiment}/annotations/{doc_id}.json')
        ann=json.loads(f.read())
        f.close()
        return ann

    def get_file_query_output(self, document_path, output_name, queryList, docs=None):
        if docs == None: docs = os.listdir(document_path)
        output = []
        for doc in docs:
            print('Processing doc '+str(doc))
            try:
                annotations = self.load_annotations(doc)
                data_extractor = DataExtractor(annotations)
                eventReader = CandidateEvents(data_extractor, self.ontology_name)
                for query in queryList:
                    query_finder= QueryFinder(annotations, query)
                    data = eventReader.get_semantic_units()
                    query_sentences= query_finder.find_query()
                    for index in query_sentences:
                        sentence_output = self.sentence_output(doc, index, eventReader, data, query, query_finder, False)
                        output.append(sentence_output)
            except:
                print("Issue with file....")
        self.results2excel('sofia/data/' + output_name + '.xlsx', output)


    # def get_file_output(self, ann_path, experiment='generic', file_name='user_input', scoring= False):
    #     if docs== None: docs=os.listdir('sofia/data/{}'.format(ann_path))
    #     data={}
    #     j=0
    #     if not os.path.isdir('sofia/data/{}_output{}'.format(ann_path, version)):
    #         os.system('mkdir '+'sofia/data/{}_output{}'.format(ann_path, version))
    #     for doc in docs:
    #         file_name= doc.split('.')[0]
    #         j+=1
    #         output = []
    #         print('Processing doc '+str(doc) + ',' + str(j))
    #         try:
    #             data_extractor = DataExtractor(self.load_annotations(doc, ann_path))
    #             doc_results=self.get_output(data_extractor, doc, scoring = False)
    #             output+= doc_results
    #             data[doc]= {'entities':self.flatten([i['Entities'] for i in doc_results]),
    #                         'events':self.flatten([i['Events'] for i in doc_results]),
    #                         'causal': self.flatten([i['Causal'] for i in doc_results])}
    #             json.dump(data[doc], open('sofia/data/{}_output{}/{}{}.json'.format(ann_path, version, file_name, version), 'w'))
    #         except:
    #             print("Issue with file....")
    #     print('Parsing done')
    #     #self.results2excel('sofia/data/'+output_name+'.xlsx', output)
    #     return data


    def flatten(self, l):
        return [item for sublist in l for item in sublist]

    def results2excel(self, output_path, results):
        variables = [i['Variables'] for i in results]
        entities = self.flatten([i['Entities'] for i in results])
        events = self.flatten([i['Events'] for i in results])
        causal = self.flatten([i['Causal'] for i in results])

        variables_df = pd.DataFrame(variables)[self.variable_headers]
        entities_df = pd.DataFrame(entities)[self.entity_headers]
        events_df = pd.DataFrame(events)[self.event_headers]
        causal_df = pd.DataFrame(causal)[self.causal_headers]

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(output_path)

        # Write each dataframe to a different worksheet.
        variables_df.to_excel(writer, sheet_name='Variables', index=False)
        entities_df.to_excel(writer, sheet_name='Entities', index=False)
        events_df.to_excel(writer, sheet_name='Events', index=False)
        causal_df.to_excel(writer, sheet_name='Causal', index=False)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()





# parser = argparse.ArgumentParser(description='Run Sofia Reader')
# parser.add_argument('--dataset', type=str, default='dec2020')
# parser.add_argument('--query_based', type=int, default= 0)
# parser.add_argument('--ontology', type=str, default='wm', help= 'Options are: causex, sofia, wm')
# parser.add_argument('--version', type=str, default= 'v2')
# args = parser.parse_args()

# from sofia import *
# sofia = SOFIA('wm')
# experiment = 'aug2021'
# data = sofia.get_online_output("", doc_id, experiment)

#java -cp "*" -Xmx48g edu.stanford.nlp.pipeline.StanfordCoreNLP --threads 8 -annotators tokenize,ssplit,pos,lemma,parse,ner,depparse -filelist ../june2020_rem/filelist_aug1.txt -outputFormat json -outputDirectory ../june2020_rem/corenlp_aug1