from OdinElements import OdinRead
from ManualRules import CandidateEvents
from Utils import Quantifiers, ExcelWriter
import os
from openpyxl import Workbook

project= 'South_Sudan_Famine'

def writeOutput(files):
    path = os.getcwd()
    dir = os.path.dirname(path) + '/' + project
    writer= ExcelWriter(['Causal', 'Events', 'Entities'])
    causalHeaders= ["Source_File", "Relation_Number", "Relation", "Relation_Type", "Location", "Time", "Cause", "Effect", "Polarity to Cause", "Polarity to Effect", "Sentence"]
    eventHeaders= ["Source_File", "Event_Number", "Relation", "Event_Type", "Location", "Time", "Agent", "Patient", "Sentence"]
    entityHeaders= ["Source_File", "Entity_Number", "Entity", "Entity_Type", "Location", "Sentence"]
    writer.writeRow("Causal", causalHeaders)
    writer.writeRow("Events", eventHeaders)
    writer.writeRow("Entities", entityHeaders)
    for file in files:
        data= odinData(file)
        eventReader= CandidateEvents(file, dir)
        numSentences = eventReader.dataSize()
        for index in range(numSentences):
            sentEntities = data[index]['entities']

            sentence = eventReader.getSentence(index)
            loc_time = eventReader.getLocAndTime(index)
            ####
            entities, nominalEvents = eventReader.nominalEvents(sentence, sentEntities)
            ####
            relations = data[index]['CauseRelations']
            quants = Quantifiers(data[index]['quantifiers'], data[index]['entities'], sentence)

            events= eventReader.getEventsWithDependencies(index, sentEntities)
            for event in events:
                evIndex = writer.getIndex("Events")
                eventInfo= [str(file), 'E'+str(evIndex-1), event["trigger"], event["frame"], event['location'], event['time'], event['agent'],
                             event['patient'], sentence]
                writer.writeRow("Events", eventInfo)

            for relation in relations:
                relIndex = writer.getIndex("Causal")
                causalInfo= [str(file), 'R'+str(relIndex-1), relation["trigger"], "CausalRelation", loc_time['location'], loc_time['time'], relation['cause'],
                             relation['effect'], quants.getQuantifier(relation['cause']), quants.getQuantifier(relation['effect']), sentence]
                writer.writeRow("Causal", causalInfo)
    writer.saveExcelFile(dir, 'output/Para6'+'v5.xlsx' )



def odinData(file):
    currPath= os.getcwd()
    dir= os.path.dirname(currPath)+'/'+ project+'/data/'
    filePath= dir+file
    reader= OdinRead(filePath)
    #output= reader.annotateDocument()
    output= reader.getAnnotations()
    print "Analyzing", str(file)
    return output

file= ['Paragraphs_SSudan']
files= ['FFP Fact Sheet_South Sudan_2018.01.17 BG', 'i8533en', 'FEWS NET South Sudan Famine Risk Alert_20170117 BG', 'FAOGIEWSSouthSudanCountryBriefSept2017 BG', '130035 excerpt BG', 'CLiMIS_FAO_UNICEF_WFP_SouthSudanIPC_29June_FINAL BG', 'FEWSNET South Sudan Outlook January 2018 BG', 'EA_Seasonal Monitor_2017_08_11 BG']

writeOutput(file)
