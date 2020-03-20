from sofia.event_extraction import CandidateEvents
from sofia.causal_extraction import CausalLinks
from sofia.ontology_mapping import Ontology
from sofia.query_search import QueryFinder
from sofia.corenlp_parse import DataExtractor
import os
import json
import pdb
import corenlp
import pandas as pd


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
       results = sofia.getOutputOnline(sentence) 
       sofia.results2excel('output.xlsx',results)
       sofia.getQueryBasedOutput(document_path, output_name, queryList)
       :keyword
       sofia.getOutputFromFiles(document_path, output_name, docs= None)
       ```
       
       In this example, results is an array of JSON objects (one per sentence submitted to SOFIA).
       The final line writes this output to an Excel file at the user specified path.
    """

    def __init__(self, CoreNLP='/Users/evangeliaspiliopoulou/Desktop/stanfordCoreNLP'):
        self.causal_headers = ["Source_File", 'Query', "Score",  "Span", "Relation Index", "Relation", "Relation_Type",
                               "Indicator", "Cause Index", "Cause", "Effect Index", "Effect", "Sentence"]
        self.event_headers = ["Source_File", 'Query', "Score", "Event Index", "Span", "Relation", "Event_Type",
                              "FrameNet_Frame", "Indicator", "Location", "Time", 'Agent Index', "Agent",
                              'Patient Index', "Patient", "Sentence"]
        self.entity_headers = ["Source_File", 'Query', "Score", "Entity Index", "Span", "Entity", "Entity_Type",
                               "FrameNet_Frame", "Indicator", "Qualifier", "Sentence"]
        self.variable_headers = ["Source_File", 'Sentence', 'Indicator', 'Scoring', 'Index']
        self.entity_index = 0
        self.event_index = 0
        self.variable_index = 0
        self.causal_index = 0
        os.environ['CORENLP_HOME'] = CoreNLP
        self.CoreNLPclient = corenlp.CoreNLPClient(annotators=['tokenize', 
                                                               'ssplit', 
                                                               'pos', 
                                                               'parse', 
                                                               'lemma', 
                                                               'ner', 
                                                               'depparse'])

    def get_output(self, data_extractor, file, scoring = False):
        output = []
        eventReader = CandidateEvents(data_extractor)
        num_sentences = data_extractor.get_data_size()
        all_events, all_entities = eventReader.get_semantic_units()
        self.eventReader = eventReader
        for s_index in range(num_sentences):
            events= all_events[s_index]
            entities= all_entities[s_index]
            sentence_output = self.sentence_output(file, data_extractor, s_index, events, entities, 'None', 'None',
                                                   scoring = scoring)
            output.append(sentence_output)
        return output

    def sentence_output(self, file, data_extractor, s_index, events, entities, query, query_finder, scoring = False):
        output = {}
        sentence= data_extractor.sentences[s_index]
        ontology = Ontology()
        self.variable_index += 1
        variable_index = 'V{}'.format(self.variable_index)
        scores=''
        if scoring:
            scores = ontology.string_matching(sentence, 'WorldBank')
        output['Variables'] = dict(zip(self.variable_headers, [str(file), sentence, query, str(scores), variable_index]))
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
            entity_info = [str(file), query, str(score), entity_index, span, entity["trigger"].lower(), entity["frame"],
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
            if 'event2' in event['frame']:
                event2Spans.append(span)
                self.event_index -= 1
                continue
            patient = span_to_index(entity_local_index, event['patient'][0])
            agent = span_to_index(entity_local_index, event['agent'][0])
            score = 0.0
            if query_finder != 'None':
                score = query_finder.rank_node(event, 'event', sentence)
            event_scores[event_index] = score

            event_info = [str(file), query, str(score), event_index, span, event["trigger"], event["frame"],
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
            causal_info = [str(file), query, str(score), sentence_span, causal_index, relation["trigger"], relation_type,
                           str(scores), cause[0], cause[1], effect[0], effect[1], sentence]
            output['Causal'].append(dict(zip(self.causal_headers,causal_info)))
        return output

    def get_online_output(self, text, scoring = False):
        annotations = self.annotate(text)
        data_extractor = DataExtractor(annotations)
        output = self.get_output(data_extractor, file= 'userinput', scoring = scoring)
        return output
    
    def annotate(self, text):
        annotations = self.CoreNLPclient.annotate(text, output_format='json')
        #annotations = self.CoreNLPclient.annotate(text)
        self.entityIndex = 0
        self.eventIndex = 0
        self.variableIndex = 0
        self.causalIndex = 0
        return annotations

    def load_annotations(self, doc):
        f=open('sofia/data/annotations/'+doc+'.json')
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
                eventReader = CandidateEvents(data_extractor)
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


    def get_file_output(self, document_path, output_name, docs= None):
        if docs== None: docs=os.listdir(document_path)
        output=[]
        data={}
        i=0
        for doc in docs:
            i+=1
            print('Processing doc '+str(doc) + ',' + str(i))
            #try:
            if True:
                data_extractor = DataExtractor(self.load_annotations(doc))
                doc_results=self.get_output(data_extractor, doc, scoring = False)
                output+= doc_results
                data[doc]= {'entities':self.flatten([i['Entities'] for i in doc_results]),
                            'events':self.flatten([i['Events'] for i in doc_results]),
                            'causal': self.flatten([i['Causal'] for i in doc_results])}
            #except:
            #    print("Issue with file....")
        print('Parsing done')
        self.results2excel('sofia/data/'+output_name+'.xlsx', output)
        return data


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

