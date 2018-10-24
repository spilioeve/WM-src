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
        eventReader = CandidateEvents(file, project)
        numSentences = eventReader.dataSize()
        data = eventReader.getEvents_Entities()
        for index in range(numSentences):
            writer= writeSentence(file, index, writer, eventReader, data, 'None', 'None', scoring= True)
    writer.saveExcelFile(project, 'output/'+ dataDir + 'v10.xlsx')
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
        eventReader = CandidateEvents(file, project)
        for query in queryList:
            query_finder= IndicatorSearch(file, project, query)
            data = eventReader.getEvents_Entities()
            query_sentences= query_finder.findQuery()
            for index in query_sentences:
                writer= writeSentence(file, index, writer, eventReader, data, query, query_finder, True)
    writer.saveExcelFile(project, 'output/' + 'Query_search.v4.xlsx')

def writeSentence(file, index, writer, eventReader, data, query, query_finder, scoring= False):
    allEvents2, allEvents, allEntities = data
    sentence = eventReader.getSentence(index)
    ontologyMapper = Ontology(project)
    scores=''
    if scoring:
        scores = ontologyMapper.stringMatching(sentence, 'WorldBank')
        writer.writeRow('Variables', [str(file), query, sentence, str(scores)])
    lemmas = eventReader.getSentenceLemmas(index)
    pos = eventReader.getSentencePOSTags(index)
    entLocalIndex = {}
    entities = allEntities[index]
    events = allEvents[index]
    for span in entities.keys():
        entity = entities[span]
        entIndex = writer.getIndex('Entities')
        entLocalIndex[span] = 'N' + str(entIndex - 1)
        #scores = ontologyMapper.stringMatching(entity["trigger"], 'WorldBank')
        score= query_finder.rankNode(entity, 'entity')
        entInfo = [str(file), query, str(score), 'N' + str(entIndex - 1), string.lower(entity["trigger"]), entity["frame"],
                   str(entity["FrameNetFr"]), str(scores), string.lower(entity['qualifier']), sentence]
        writer.writeRow('Entities', entInfo)
    eventLocalIndex = {}
    eventScores={}
    for span in events.keys():
        event = events[span]
        evIndex = writer.getIndex("Events")
        eventLocalIndex[span] = 'E' + str(evIndex - 1)
        patient = writer.getIndexFromSpan(entLocalIndex, event['patient'][0])
        agent = writer.getIndexFromSpan(entLocalIndex, event['agent'][0])
        score = query_finder.rankNode(event, 'event')
        eventScores['E' + str(evIndex - 1)] = score

        eventInfo = [str(file), query, str(score), 'E' + str(evIndex - 1), event["trigger"], event["frame"], str(event["FrameNetFr"]), str(scores), event['location'],
                         event['temporal'], agent, event['agent'][1], patient, event['patient'][1], sentence]
        writer.writeRow('Events', eventInfo)
        ##Model RST currently based only on Events. Being able to bring Entities in front???
        ###Or maybe include this portion as the merged Deep Learning Architecture?
        ###Merged with Coreference & Temporal Seq???
    rst = RSTModel(events, eventLocalIndex, entities, entLocalIndex, sentence, lemmas, pos)
    causalRel = rst.getCausalNodes()  ### OR TRUE
    for relation in causalRel:
        relIndex = writer.getIndex("Causal")
        cause = relation["cause"]
        effect = relation["effect"]
        relType = relation['type']
        score = query_finder.rankNode((eventScores, cause[0], effect[0]), 'relation')
        #score= 1.0
        causalInfo = [str(file), query, str(score), 'R' + str(relIndex - 1), relation["trigger"], relType, str(scores),
                      cause[0], cause[1], effect[0], effect[1], sentence]
        writer.writeRow("Causal", causalInfo)
    return writer

def getOutputOnline(sentence):
    os.chdir('/Users/evangeliaspiliopoulou/Desktop/stanfordCoreNLP')
    inputF= open('userInput', 'w')
    inputF.write(sentence)
    inputF.close()
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



dataDir='MITRE_June18'
#dataDir='proposal_doc'
projectName= '/South_Sudan_Famine'
path = os.getcwd()
project = os.path.dirname(path) + projectName


def runSOFIA(query):
    #files= ['proposal_doc']
    files= os.listdir(project+ '/data/'+dataDir)
    ##files= ['FFP Fact Sheet_South Sudan_2018.01.17 BG', 'i8533en', 'FEWS NET South Sudan Famine Risk Alert_20170117 BG', 'FAOGIEWSSouthSudanCountryBriefSept2017 BG', '130035 excerpt BG', 'CLiMIS_FAO_UNICEF_WFP_SouthSudanIPC_29June_FINAL BG', 'FEWSNET South Sudan Outlook January 2018 BG', 'EA_Seasonal Monitor_2017_08_11 BG']
    if '.DS_Store' in files:
        files= files[:files.index('.DS_Store')]+ files[files.index('.DS_Store')+1:]
    #writeOutput(files)
    files+= ['IPC_Annex_Indicators', 'Food_security' ]
    writeQueryBasedOutput(files, query)



sentence="The intense rain caused flooding in the area."
#getOutputOnline(sentence)
query= ['food security', 'malnutrition', 'starvation', 'famine', 'mortality', 'die', 'conflict', 'IPC phase']
runSOFIA(query)
