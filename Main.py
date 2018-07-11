from OdinElements import OdinRead
from ManualRules import CandidateEvents
from CausalityDetection import RSTModel
from Utils import Quantifiers, ExcelWriter
import os
import string
from openpyxl import Workbook
import pdb

def writeOutput(files):
    # path = os.getcwd()
    # dir = os.path.dirname(path) + '/' + project
    writer= ExcelWriter(['Causal', 'Events', 'Entities'])
    causalHeaders= ["Source_File", "Relation Index", "Relation", "Relation_Type", "Cause Index", "Cause", "Effect Index", "Effect", "Sentence"]
    eventHeaders= ["Source_File", "Event Index", "Relation", "Event_Type", "Location", "Time", 'Agent Index', "Agent", 'Patient Index', "Patient", "Sentence"]
    entityHeaders= ["Source_File", "Entity Index", "Entity", "Entity_Type", "Qualifier", "Sentence"]
    writer.writeRow("Causal", causalHeaders)
    writer.writeRow("Events", eventHeaders)
    writer.writeRow("Entities", entityHeaders)
    for file in files:
        #data = odinData(file)
        print "Analyzing File"
        print file
        eventReader = CandidateEvents(file, project)
        numSentences = eventReader.dataSize()
        allEvents2, allEvents, allEntities = eventReader.getEvents_Entities()
        for index in range(numSentences):
            #sentEntities = data[index]['entities']
            #relations = data[index]['CauseRelations']
            sentence = eventReader.getSentence(index)
            lemmas= eventReader.getSentenceLemmas(index)
            entLocalIndex={}
            entities= allEntities[index]
            events= allEvents[index]
            for span in entities.keys():
                entity= entities[span]
                entIndex= writer.getIndex('Entities')
                entLocalIndex[span]= 'N' + str(entIndex - 1)
                entInfo= [str(file), 'N' + str(entIndex - 1), string.lower(entity["trigger"]), entity["frame"], string.lower(entity['qualifier']), sentence]
                writer.writeRow('Entities', entInfo)

            eventLocalIndex={}
            for span in events.keys():
                event= events[span]
                evIndex = writer.getIndex("Events")
                eventLocalIndex[span]= 'E' + str(evIndex - 1)
                patient= writer.getIndexFromSpan(entLocalIndex, event['patient'][0])
                agent = writer.getIndexFromSpan(entLocalIndex, event['agent'][0])
                eventInfo = [str(file), 'E' + str(evIndex - 1), event["trigger"], event["frame"], event['location'],
                             event['temporal'], agent, event['agent'][1], patient, event['patient'][1], sentence]
                writer.writeRow('Events', eventInfo)
           ##Model RST currently based only on Events. Being able to bring Entities in front???
                ###Or maybe include this portion as the merged Deep Learning Architecture?
                ###Merged with Coreference & Temporal Seq???
            rst = RSTModel(events, eventLocalIndex, entities, entLocalIndex, sentence, lemmas)
            causalRel= rst.getCausalNodes()### OR TRUE
            for relation in causalRel:
                relIndex = writer.getIndex("Causal")
                cause= relation["cause"]
                effect= relation["effect"]
                relType= relation['type']
                causalInfo = [str(file), 'R' + str(relIndex - 1), relation["trigger"], relType,
                                         cause[0], cause[1], effect[0], effect[1], sentence]
                writer.writeRow("Causal", causalInfo)

            # for relation in allEvents2:
            #     relIndex = writer.getIndex("Causal")
            #     #cause, effect = rst.locateEvents2(bound, 'left')
            #
            #     cause = relation["cause"]
            #     effect = relation["effect"]
            #     causalInfo = [str(file), 'R' + str(relIndex - 1), relation["trigger"], "IncreaseRelation",
            #                   cause[0], cause[1], effect[0], effect[1], sentence]
            #     writer.writeRow("Causal", causalInfo)

            # for relation in relations:
            #     print "relation"
            #     print relation
            #     try:
            #         relIndex = writer.getIndex("Causal")
            #         cause, effect= rst.distanceHeuristic(relation["trigger"], relation['cause'], relation['effect'])
            #         print relation['cause'], cause
            #         print relation['effect'], effect
            #         causalInfo = [str(file), 'R' + str(relIndex - 1), relation["trigger"], "CausalRelation",
            #                      cause[0], cause[1], effect[0], effect[1], sentence]
            #         writer.writeRow("Causal", causalInfo)
            #     except:
            #         print "Relation Not found"
    writer.saveExcelFile(project, 'output/'+ dataDir + 'v2.xlsx')
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



def odinData(file):
    currPath= os.getcwd()
    dir= os.path.dirname(currPath)+'/'+ project+'/data/'
    filePath= dir+file
    reader= OdinRead(filePath)
    #output= reader.annotateDocument()
    output= reader.getAnnotations()
    print "Analyzing", str(file)
    return output


#dataDir='MITRE_June18'
dataDir='Para6v9.1'
projectName= '/South_Sudan_Famine'
path = os.getcwd()
project = os.path.dirname(path) + projectName

files= ['Paragraphs_SSudan']
#files= os.listdir(project+ '/data/'+dataDir)
##files= ['FFP Fact Sheet_South Sudan_2018.01.17 BG', 'i8533en', 'FEWS NET South Sudan Famine Risk Alert_20170117 BG', 'FAOGIEWSSouthSudanCountryBriefSept2017 BG', '130035 excerpt BG', 'CLiMIS_FAO_UNICEF_WFP_SouthSudanIPC_29June_FINAL BG', 'FEWSNET South Sudan Outlook January 2018 BG', 'EA_Seasonal Monitor_2017_08_11 BG']
if '.DS_Store' in files:
    files= files[:files.index('.DS_Store')]+ files[files.index('.DS_Store')+1:]
# files= os.listdir(project+ '/data/'+dataDir)
# ##files= ['FFP Fact Sheet_South Sudan_2018.01.17 BG', 'i8533en', 'FEWS NET South Sudan Famine Risk Alert_20170117 BG', 'FAOGIEWSSouthSudanCountryBriefSept2017 BG', '130035 excerpt BG', 'CLiMIS_FAO_UNICEF_WFP_SouthSudanIPC_29June_FINAL BG', 'FEWSNET South Sudan Outlook January 2018 BG', 'EA_Seasonal Monitor_2017_08_11 BG']
# if '.DS_Store' in files:
#     files= files[:files.index('.DS_Store')]+ files[files.index('.DS_Store')+1:]
writeOutput(files)
