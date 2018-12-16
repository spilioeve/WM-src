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
from collections import OrderedDict


def writeOutput(files):
    # path = os.getcwd()
    # dir = os.path.dirname(path) + '/' + project
    writer= ExcelWriter(['Causal', 'Events', 'Entities', 'Variables'])
    causalHeaders= ["Source_File", 'Query', "Score", "Relation Index", "Relation", "Relation_Type", "Indicator", "Cause Index", "Cause", "Effect Index", "Effect", "Sentence"]
    eventHeaders= ["Source_File", 'Query', "Score", "Event Index", "Relation", "Event_Type", "FrameNet_Frame", "Indicator", "Location", "Time", 'Agent Index', "Agent", 'Patient Index', "Patient", "Sentence"]
    entityHeaders= ["Source_File", 'Query', "Score", "Entity Index", "Entity", "Entity_Type", "FrameNet_Frame", "Indicator", "Qualifier", "Sentence"]
    variableHeaders=["Source_File", 'Sentence', 'Indicator', 'Index']
    writer.writeRow("Causal", causalHeaders)
    writer.writeRow("Events", eventHeaders)
    writer.writeRow("Entities", entityHeaders)
    writer.writeRow('Variables', variableHeaders)
    for file in files:
        #data = odinData(file)
        print "Analyzing File"
        print file
        print files.index(file)
        eventReader = CandidateEvents(file, project)
        numSentences = eventReader.dataSize()
        data = eventReader.getEvents_Entities()
        for index in range(numSentences):
            writer= writeSentence(file, index, writer, eventReader, data, 'None', 'None', scoring= False)
    writer.saveExcelFile(project, 'output/'+ dataDir + '_v2.xlsx')
    # for file in files:
    #     data= odinData(file)
    #     eventReader= CandidateEvents(file, dir)
    #     numSentences = eventReader.dataSize()
    #     for index in range(numSentences):
    #         sentEntities = data[index]['entities']
    #         sentence = eventReader.getSentence(index)
    #         loc_time = eventReader.getLocAndTime(index)
    #         ####
    #         entities, nominalEvents = eventReader.nominalEvents(sentence, sentEntities)
    #         ####
    #         relations = data[index]['CauseRelations']
    #         quants = Quantifiers(data[index]['quantifiers'], data[index]['entities'], sentence)
    #
    #         events= eventReader.getEventsWithDependencies(index, sentEntities)

    #         for event in events:
    #             evIndex = writer.getIndex("Events")
    #             eventInfo= [str(file), 'E'+str(evIndex-1), event["trigger"], event["frame"], event['location'], event['time'], event['agent'],
    #                          event['patient'], sentence]
    #             writer.writeRow("Events", eventInfo)
    #
    #         for relation in relations:
    #             relIndex = writer.getIndex("Causal")
    #             causalInfo= [str(file), 'R'+str(relIndex-1), relation["trigger"], "CausalRelation", loc_time['location'], loc_time['time'], relation['cause'],
    #                          relation['effect'], quants.getQuantifier(relation['cause']), quants.getQuantifier(relation['effect']), sentence]
    #             writer.writeRow("Causal", causalInfo)
    # writer.saveExcelFile(dir, 'output/Para6'+'v5.xlsx' )

def writeQueryBasedOutput(files, queryList):
    writer = ExcelWriter(['Causal', 'Events', 'Entities', 'Variables'])
    causalHeaders = ["Source_File", 'Query', "Score", "Relation Index", "Relation", "Relation_Type", "Indicator", "Cause Index", "Cause",
                     "Effect Index", "Effect", "Sentence"]
    eventHeaders = ["Source_File", 'Query', "Score", "Event Index", "Relation", "Event_Type", "FrameNet_Frame", "Indicator", "Location", "Time",
                    'Agent Index', "Agent", 'Patient Index', "Patient", "Sentence"]
    entityHeaders = ["Source_File", 'Query', "Score", "Entity Index", "Entity", "Entity_Type", "FrameNet_Frame", "Indicator", "Qualifier", "Sentence"]
    variableHeaders = ["Source_File", 'Query', 'Sentence', 'Indicator', 'Index']
    writer.writeRow("Causal", causalHeaders)
    writer.writeRow("Events", eventHeaders)
    writer.writeRow("Entities", entityHeaders)
    writer.writeRow('Variables', variableHeaders)
    for file in files:
        print "Analyzing File"
        print file
        print files.index(file)
        eventReader = CandidateEvents(file, project)
        for query in queryList:
            query_finder= IndicatorSearch(file, project, query)
            data = eventReader.getEvents_Entities()
            query_sentences= query_finder.findQuery()
            for index in query_sentences:
                writer= writeSentence(file, index, writer, eventReader, data, query, query_finder, False)
    writer.saveExcelFile(project, 'output/' + dataDir+ '_Query_search.v8.xlsx')

def writeSentence(file, index, writer, eventReader, data, query, query_finder, scoring= False):
    #allEvents2, allEvents, allEntities = data
    allEvents, allEntities = data
    sentence = eventReader.getSentence(index)
    ontologyMapper = Ontology(project)
    scores=''
    if scoring:
        scores = ontologyMapper.stringMatching(sentence, 'WorldBank')
        writer.writeRow('Variables', [str(file), query, sentence, str(scores)])
    lemmas = eventReader.getSentenceLemmas(index)
    pos = eventReader.getSentencePOSTags(index)
    entLocalIndex = OrderedDict()
    entities = allEntities[index]
    events = allEvents[index]
    entityScores= OrderedDict()
    entities_keys = entities.keys()
    entities_keys.sort()
    for span in entities_keys:
        entity = entities[span]
        entIndex = writer.getIndex('Entities')
        entLocalIndex[span] = 'N' + str(entIndex - 1)
        #scores = ontologyMapper.stringMatching(entity["trigger"], 'WorldBank')
        score=0.0
        if query_finder!= 'None':
            score= query_finder.rankNode(entity, 'entity', sentence)
        entityScores['N' + str(entIndex - 1)] = score
        entInfo = [str(file), query, str(score), 'N' + str(entIndex - 1), string.lower(entity["trigger"]), entity["frame"],
                   str(entity["FrameNetFr"]), str(scores), string.lower(entity['qualifier']), sentence]
        writer.writeRow('Entities', entInfo)
    eventLocalIndex = OrderedDict()
    eventScores=OrderedDict()
    event2Spans=[]
    events_keys = events.keys()
    events_keys.sort()
    for span in events_keys:
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
        writer.writeRow('Events', eventInfo)
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
        writer.writeRow('Events', eventInfo)
    #TODO: Fix the Causality Model
    #It currently chooses ALL the events. This is wrong, it should choose the ones that do not contain others as arguments
    rst = RSTModel(events, eventLocalIndex, entities, entLocalIndex, sentence, lemmas, pos, eventScores, entityScores)
    causalRel = rst.getCausalNodes()  ### OR TRUE
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
        writer.writeRow("Causal", causalInfo)
    return writer

def getOutputOnline(sentence):
    os.chdir('/Users/evangeliaspiliopoulou/Desktop/stanfordCoreNLP')
    inputF= open('userInput', 'w')
    inputF.write(sentence)
    inputF.close()
    ##For stanford CoreNLP it is '-filelist ...' NOT '-fileList ..'
    command= 'java -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,parse,lemma,ner,depparse -file userInput'+ ' -outputDirectory '+ project+ '/outputStanford' + ' -outputFormat \'json\''
    os.system(command)
    os.chdir(path)
    writeOutput(['userInput'])
    print "Process Complete"



def odinData(file):
    currPath= os.getcwd()
    dir= os.path.dirname(currPath)+'/'+ project+'/data/'
    filePath= dir+file
    reader= OdinRead(filePath)
    #output= reader.annotateDocument()
    output= reader.getAnnotations()
    print "Analyzing", str(file)
    return output



dataDir='MITRE_AnnualEval'
dataDir='sentence_input'
projectName= '/South_Sudan_Famine'
path = os.getcwd()
project = os.path.dirname(path) + projectName


def runSOFIA(query):
    files= ['userInput']
    #files= os.listdir(project+ '/data/'+dataDir)
    ##files= ['FFP Fact Sheet_South Sudan_2018.01.17 BG', 'i8533en', 'FEWS NET South Sudan Famine Risk Alert_20170117 BG', 'FAOGIEWSSouthSudanCountryBriefSept2017 BG', '130035 excerpt BG', 'CLiMIS_FAO_UNICEF_WFP_SouthSudanIPC_29June_FINAL BG', 'FEWSNET South Sudan Outlook January 2018 BG', 'EA_Seasonal Monitor_2017_08_11 BG']
    if '.DS_Store' in files:
        files= files[:files.index('.DS_Store')]+ files[files.index('.DS_Store')+1:]
    writeOutput(files)
    #files+= ['IPC_Annex_Indicators', 'Food_security' ]
    #files=['MONTHLY_PRICE_WATCH_AND_ANNEX_AUGUST2014_1', 'Global Weather Hazard-150305']
    #writeQueryBasedOutput(files, query)



# sentence="The intense rain caused flooding in the area."
sentence='The intense rain causes flooding in the area and in the capital.'
k=  'This was terrible news for the people of Pandonia. Conflict in the region is on the rise due to the floods. The floods are a direct result of rain and inadequate drainage.'
getOutputOnline(k)

#runSOFIA('')

query1= ['food security', 'malnutrition', 'starvation', 'famine', 'mortality', 'die', 'conflict', 'IPC phase']
query2=['health', 'malnutrition', 'food security', 'drought', 'rainfall', 'food']
#query= ['health', 'malnutrition', 'rainfall' ,'food production', 'food availability', 'food security', 'food imports', 'food aid', 'crop yield', 'drought', 'poverty', 'famine']
query= ['malnutrition', 'famine' ,'food production', 'food availability', 'food security', 'food imports', 'food aid', 'crop yield', 'poverty']
query=['conflict', 'drought', 'flood', 'livestock', 'rainfall', 'conflict', 'displacement', 'crop harvest', 'food production', 'food availability', 'food security', 'community', 'economy', 'currency value', 'crop yield', 'market function', 'poverty', 'political instability']
#runSOFIA(query)
# #runSOFIA(query)
