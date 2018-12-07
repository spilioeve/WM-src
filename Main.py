from OdinElements import OdinRead
from ManualRules import CandidateEvents
from CausalityDetection import RSTModel
from Utils import Quantifiers, ExcelWriter
from OntologyMapping import Ontology
from IndicatorSearch import IndicatorSearch
import os
import string
from openpyxl import Workbook
import pdb
import corenlp

class SOFIA:
    """SOFIA class. Can be invoked with:
       
       ```
       sofia = SOFIA(dataDir='data_path', ProjectName='/path_to_project', CoreNLP='/path_to_CoreNLP')
       sentence="The intense rain caused flooding in the area."
       sofia.getOutputOnline(sentence)
       ```
    """

    def __init__(self, dataDir, ProjectName, CoreNLP):
        self.dataDir = dataDir
        self.projectName = ProjectName
        self.path = os.getcwd()
        self.project = os.path.dirname(self.path) + self.projectName
        self.corenlp = CoreNLP
        self.causalHeaders = ["Source_File", 'Query', "Score", "Relation Index", "Relation", "Relation_Type", "Indicator", "Cause Index", "Cause", "Effect Index", "Effect", "Sentence"]
        self.eventHeaders = ["Source_File", 'Query', "Score", "Event Index", "Relation", "Event_Type", "FrameNet_Frame", "Indicator", "Location", "Time", 'Agent Index', "Agent", 'Patient Index', "Patient", "Sentence"]
        self.entityHeaders = ["Source_File", 'Query', "Score", "Entity Index", "Entity", "Entity_Type", "FrameNet_Frame", "Indicator", "Qualifier", "Sentence"]
        self.variableHeaders = ["Source_File", 'Sentence', 'Indicator', 'Index']        
        os.environ['CORENLP_HOME'] = self.corenlp
        self.CoreNLPclient = corenlp.CoreNLPClient(annotators=['tokenize', 
                                       'ssplit', 
                                       'pos', 
                                       'parse', 
                                       'lemma', 
                                       'ner', 
                                       'depparse'])

    def writeOutput(self, annotations):
        writer= ExcelWriter(['Causal', 'Events', 'Entities', 'Variables'])
        output = []
        file = 'userinput'
        eventReader = CandidateEvents(annotations)
        numSentences = eventReader.dataSize()
        data = eventReader.getEvents_Entities()
        self.eventReader = eventReader
        for index in range(numSentences):
            sentence_output = self.writeSentence(file, index, writer, eventReader, data, 'None', 'None', scoring= False)
            output.append(sentence_output)
        return output

    def writeQueryBasedOutput(self, text, queryList):
        writer = ExcelWriter(['Causal', 'Events', 'Entities', 'Variables'])
        output = []
        file = 'userinput'
        annotations = self.annotate(text)
        eventReader = CandidateEvents(annotations)
        for query in queryList:
            query_finder= IndicatorSearch(annotations, query)
            data = eventReader.getEvents_Entities()
            query_sentences= query_finder.findQuery()
            for index in query_sentences:
                sentence_output = self.writeSentence(file, index, writer, eventReader, data, query, query_finder, False)
                output.append(sentence_output)
        return output

    def writeSentence(self, file, index, writer, eventReader, data, query, query_finder, scoring= False):
        #allEvents2, allEvents, allEntities = data
        output = {}
        allEvents, allEntities = data
        sentence = eventReader.getSentence(index)
        ontologyMapper = Ontology(self.project)
        scores=''
        if scoring:
            scores = ontologyMapper.stringMatching(sentence, 'WorldBank')
            output['Variables'] = dict(zip(self.variableHeaders, [str(file), query, sentence, str(scores)]))
        lemmas = eventReader.getSentenceLemmas(index)
        pos = eventReader.getSentencePOSTags(index)
        entLocalIndex = {}
        entities = allEntities[index]
        events = allEvents[index]

        output['Entities'] = []
        for span in list(entities.keys()):
            entity = entities[span]
            entIndex = writer.getIndex('Entities')
            entLocalIndex[span] = 'N' + str(entIndex - 1)
            #scores = ontologyMapper.stringMatching(entity["trigger"], 'WorldBank')
            score=0.0
            if query_finder!= 'None':
                score= query_finder.rankNode(entity, 'entity', sentence)
            entInfo = [str(file), query, str(score), 'N' + str(entIndex - 1), entity["trigger"].lower(), entity["frame"],
                       str(entity["FrameNetFr"]), str(scores), entity['qualifier'].lower(), sentence]
            output['Entities'].append(dict(zip(self.entityHeaders,entInfo)))
        eventLocalIndex = {}
        eventScores={}
        event2Spans=[]
        output['Events'] = []
        for span in list(events.keys()):
            event = events[span]
            if 'event2' in event['frame']:
                event2Spans.append(span)
                continue
            evIndex = writer.getIndex("Events")
            eventLocalIndex[span] = 'E' + str(evIndex - 1)
            patient = writer.getIndexFromSpan(entLocalIndex, event['patient'][0])
            agent = writer.getIndexFromSpan(entLocalIndex, event['agent'][0])
            score = 0.0
            if query_finder != 'None':
                score = query_finder.rankNode(event, 'event', sentence)
            eventScores['E' + str(evIndex - 1)] = score

            eventInfo = [str(file), query, str(score), 'E' + str(evIndex - 1), event["trigger"], event["frame"], str(event["FrameNetFr"]), str(scores), event['location'],
                             event['temporal'], agent, event['agent'][1], patient, event['patient'][1], sentence]
            output['Events'].append(dict(zip(self.eventHeaders,eventInfo)))
            ##Model RST currently based only on Events. Being able to bring Entities in front???
            ###Or maybe include this portion as the merged Deep Learning Architecture?
            ###Merged with Coreference & Temporal Seq???
        for span in event2Spans:
            event = events[span]
            evIndex = writer.getIndex("Events")
            eventLocalIndex[span] = 'E' + str(evIndex - 1)
            try:
                patient = writer.getIndexFromSpan(eventLocalIndex, event['patient'][0])
            except:
                try:
                    patient= writer.getIndexFromSpan(entLocalIndex, event['patient'][0])
                except:
                    patient=''
            try:
                agent = writer.getIndexFromSpan(eventLocalIndex, event['agent'][0])
            except:
                try:
                    agent= writer.getIndexFromSpan(entLocalIndex, event['agent'][0])
                except:
                    agent=''
            score = 0.0
            if query_finder != 'None':
                score = query_finder.rankNode(event, 'event', sentence)
            eventScores['E' + str(evIndex - 1)] = score
            eventInfo = [str(file), query, str(score), 'E' + str(evIndex - 1), event["trigger"], event["frame"], str(event["FrameNetFr"]), str(scores), event['location'],
                             event['temporal'], agent, event['agent'][1], patient, event['patient'][1], sentence]
            output['Events'].append(dict(zip(self.eventHeaders,eventInfo)))
        #TODO: Fix the Causality Model
        #It currently chooses ALL the events. This is wrong, it should choose the ones that do not contain others as arguments

        rst = RSTModel(events, eventLocalIndex, entities, entLocalIndex, sentence, lemmas, pos)
        causalRel = rst.getCausalNodes()  ### OR TRUE
        output['Causal'] = []
        for relation in causalRel:
            relIndex = writer.getIndex("Causal")
            cause = relation["cause"]
            effect = relation["effect"]
            relType = relation['type']
            score = 0.0
            if query_finder != 'None':
                score = query_finder.rankNode((eventScores, cause[0], effect[0]), 'relation', sentence)
            causalInfo = [str(file), query, str(score), 'R' + str(relIndex - 1), relation["trigger"], relType, str(scores),
                          cause[0], cause[1], effect[0], effect[1], sentence]
            output['Causal'].append(dict(zip(self.causalHeaders,causalInfo)))
        return output

    def getOutputOnline(self, text):
        annotations = self.annotate(text)
        output = self.writeOutput(annotations)
        return output
    
    def annotate(self, text):
        annotations = self.CoreNLPclient.annotate(text, output_format='json')
        return annotations

    def odinData(self, file):
        currPath= os.getcwd()
        dir= os.path.dirname(currPath)+'/'+ project+'/data/'
        filePath= dir+file
        reader= OdinRead(filePath)
        #output= reader.annotateDocument()
        output= reader.getAnnotations()
        print("Analyzing", str(file))
        return output

    def runSOFIA(self, query):
        #files= ['proposal_doc']
        files= os.listdir(project+ '/data/'+dataDir)
        ##files= ['FFP Fact Sheet_South Sudan_2018.01.17 BG', 'i8533en', 'FEWS NET South Sudan Famine Risk Alert_20170117 BG', 'FAOGIEWSSouthSudanCountryBriefSept2017 BG', '130035 excerpt BG', 'CLiMIS_FAO_UNICEF_WFP_SouthSudanIPC_29June_FINAL BG', 'FEWSNET South Sudan Outlook January 2018 BG', 'EA_Seasonal Monitor_2017_08_11 BG']
        if '.DS_Store' in files:
            files= files[:files.index('.DS_Store')]+ files[files.index('.DS_Store')+1:]
        #writeOutput(files)
        #files+= ['IPC_Annex_Indicators', 'Food_security' ]
        #files=['MONTHLY_PRICE_WATCH_AND_ANNEX_AUGUST2014_1', 'Global Weather Hazard-150305']
        writeQueryBasedOutput(files, query)