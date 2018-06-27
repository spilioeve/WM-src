import math
import os
import string
from FrameNetRefine import FrameNetRefiner
from OntologyMapping import Ontology
from StanfordInfo import DataExtractor
from nltk.stem.wordnet import WordNetLemmatizer
import pdb



targetN= ['sudan', 'famine', 'food', 'hunger', 'drought', 'nutrition']
targetV= ['affect', 'cause', 'focus', 'need', 'suffer', 'occur']
# causalVerbs= ['affect', 'impact', 'bear_upon', 'bear_on', 'touch_on', 'touch', 'involve', 'regard', 'feign', 'sham', 'pretend', 'dissemble', 'impress', 'strike', 'cause', 'do', 'make', 'induce', 'stimulate', 'mean', 'intend', 'entail', 'imply', 'signify', 'stand_for', 'think', 'think_of', 'have_in_mind', 'result', 'ensue', 'leave', 'lead', 'take', 'direct', 'conduct', 'guide', 'head', 'run', 'go', 'pass', 'extend', 'top', 'contribute', 'conduce', 'precede', 'moderate', 'chair']
aux= ['be', 'can', 'could', 'dare', 'do', 'have', 'may', 'might', 'must', 'ought', 'shall', 'should', 'will', 'would']
#Don't include "NEED", it serves BOTH as modal verb AND normal verb: eg "I need food.". What about "get"?

# anaphoricVerbs=['reveal','compare', 'equate','state', 'say', 'tell', 'allege', 'aver', 'suppose', 'read', 'order', 'enjoin', 'pronounce', 'articulate', 'enounce', 'sound_out', 'enunciate', 'talk', 'speak', 'utter', 'mouth', 'verbalize', 'verbalise', 'address', 'report', 'describe', 'account', 'cover', 'show', 'demo', 'exhibit', 'present', 'demonstrate', 'prove', 'establish', 'shew', 'testify', 'bear_witness', 'evidence', 'picture', 'depict', 'render', 'express', 'evince', 'indicate', 'point', 'designate', 'show_up', 'register', 'record', 'usher', 'narrate', 'recount', 'recite', 'assure', 'distinguish', 'separate', 'differentiate', 'secern', 'secernate', 'severalize', 'severalise', 'tell_apart', 'spill', 'spill_the_beans', 'let_the_cat_out_of_the_bag', 'tattle', 'blab', 'peach', 'babble', 'sing', 'babble_out', 'blab_out', 'lecture', 'bespeak', 'betoken', 'signal', 'argue', 'suggest']
# estVerbs = ['estimate', 'expect']
verbTags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"] #VBN and VBG maybe?
nounTags= ["NN", "NNS", "NNP", "NNPS", "JJ"]

class CandidateEvents:

    def __init__(self, file, dir, refiner='Ontology'):
        self.file= file
        self.dir = dir
        self.stanfordLoader= DataExtractor(file, dir)
        if refiner== 'FrameNet':
            self.refiner= FrameNetRefiner()
        else:
            self.refiner = Ontology(dir)
        self.lmtzr = WordNetLemmatizer()

    def getVerbEvents(self, sentenceIndex, events2, events, entities, refine=True):
        data= self.stanfordLoader.getDataPerSentence(sentenceIndex)
        #sentence, tokens, mapping, loc, time, depCurr = self.data[sentenceIndex]
        pos= data["pos"]
        lemmas= data["lemmas"]
        tokens= data["tokens"]
        sentence= data["sentence"]
        spans = data['spans']
        sentenceEvents = {}
        sentenceEvents2= {}
        # sentenceEvents = events
        # sentenceEvents2= events2
        for index in range(len(lemmas)):
        #for item in lemmas:
            span = spans[index]
            if span in events:
                sentenceEvents[span] = events[span]
                sentenceEvents[span].update({"index": index})
            elif span in events2:
                sentenceEvents2[span] = events2[span]
                sentenceEvents2[span].update({"index": index})
            elif pos[index] in verbTags and lemmas[index] not in aux:
            #if item["pos"] in verbTags and (item["lemma"] not in aux):
                flag= True
                frame= ""
                # if self.ontology.ontologyTerm(lemmas[index]):
                #     t, frame= self.ontology.getOntologyType(lemmas[index])
                #     if t in ["events1", "events2"]:
                #         flag= True
                #     else:
                #         flag= False
                if refine:
                    flag, frame, category= self.refiner.refineWord(sentence, lemmas[index], pos[index])
                if flag:
                    token= tokens[index]
                    ####srlOut, nomBool= self.recognizeNomEventuality(token, data['NPs'])
                    if category=='event2':
                        sentenceEvents2[span] = {"trigger": token["token"], "lemma": lemmas[index], "index": index,
                                                "frame": frame, "temporal": data["temporal"],
                                                "location": data["location"]}
                    else:
                        srlOut= self.getDependencies(sentenceIndex, index+1, entities)
                        sentenceEvents[span] ={"trigger": token["token"], "lemma": lemmas[index], "index": index,
                                  "frame": frame, "temporal": data["temporal"], "location": data["location"]}
                        sentenceEvents[span].update(srlOut)
        for span in sentenceEvents2.keys():
            #pdb.set_trace()
            index=sentenceEvents2[span]['index']
            srlOut = self.getDependencies(sentenceIndex, index + 1, sentenceEvents)
            sentenceEvents2[span].update(srlOut)
        print sentenceEvents2

        return sentenceEvents2, sentenceEvents

    def getLocAndTime(self, sentenceIndex):
        sentence, tokens, mapping, loc, time, depCurr= self.data[sentenceIndex]
        return {'location': loc, 'time': time}

    def dataSize(self):
        return self.stanfordLoader.getDataSize()

    def getSentence(self, sentenceIndex):
        data= self.stanfordLoader.getDataPerSentence(sentenceIndex)
        sentence= data['sentence']
        return sentence

    def getSentenceLemmas(self, sentenceIndex):
        data= self.stanfordLoader.getDataPerSentence(sentenceIndex)
        lemmas= data['lemmas']
        return lemmas

    def getEvents_Entities(self):
        allEvents2=[]
        allEvents=[]
        allEntities=[]
        for index in range(self.stanfordLoader.getDataSize()):
            events2, events, entities = self.classifyNominals(index)
            events2, events= self.getVerbEvents(index, events2, events, entities)
            allEvents2.append(events2)
            allEvents.append(events)
            allEntities.append(entities)
        return allEvents2, allEvents, allEntities

    def getDependencies(self, sentenceIndex, index, entities):
        deps= self.stanfordLoader.getDependencies(sentenceIndex)
        agent= []
        patient= []
        #otherDeps={}
        allDeps={}
        for dependency in deps:
            governor = int(dependency['governor'])
            depType = dependency['dep']
            dependent = str(dependency['dependentGloss'])
            depIndex = int(dependency['dependent'])
            if governor == index:
                if depType in allDeps.keys():
                    prev= allDeps[depType]
                    allDeps[depType] = prev+ [dependent]
                else:
                    allDeps[depType]= [dependent]
        passive= False
        if "nsubj" in allDeps.keys():
            agent= allDeps["nsubj"]
        if "nsubjpass" in allDeps.keys():
            patient=  allDeps["nsubjpass"]
            passive= True
        elif "dobj" in allDeps.keys():
            patient = allDeps["dobj"]
        if patient== [] or passive:
            for rel in allDeps.keys():
                if "nmod" in rel:
                    if agent == [] and passive:
                        agent= allDeps[rel]
                    elif patient== []:
                        patient= allDeps[rel]
        out={'agent':(0, ""), 'patient':(0, "")}
        if agent!= []:
            out['agent']= self.mapToEntity(agent, entities)
        if patient!= []:
            out['patient']= self.mapToEntity(patient, entities)
        return out

    def mapToEntity(self, terms, NPs):
        normalized=""
        mySpan=[]
        for span in NPs.keys():
            np= NPs[span]
            entity= np["trigger"] ##token?
            norm= ""
            for term in terms:
                if term in entity:
                    norm= entity
                    mySpan.append(span)
            if norm!="":
                normalized+= norm+', '
        normalized = normalized.strip(', ')
        return mySpan, normalized

    def writeEvents(self, sentIndex, currIndex, ws1, entities):
        events= self.getEventsWithDependencies(sentIndex)
        sentence= self.getSentence(sentIndex)
        for event in events:
            ws1["A" + str(currIndex)] = str(self.file)
            ws1["B" + str(currIndex)] = 'E'+str(currIndex-1)
            ws1["C" + str(currIndex)] = event['trigger']
            ws1["D" + str(currIndex)] = event['frame']
            if 'location' in event:
                ws1["E" + str(currIndex)] = event['location']
            if 'time' in event:
                ws1["F" + str(currIndex)] = event['time']
            if 'agent' in event:
                agent=  self.mapToEntity(event['agent'], entities)
                ws1["G" + str(currIndex)] = agent
            if 'patient' in event:
                patient = self.mapToEntity(event['patient'], entities)
                ws1["H" + str(currIndex)] = patient
            ws1["I" + str(currIndex)] = sentence
            currIndex+=1
        return currIndex

    def classifyNominals(self, sentenceIndex):
        events = {}
        entities={}
        events2={}
        data = self.stanfordLoader.getDataPerSentence(sentenceIndex)
        sentence = data["sentence"]
        nominals = data["NPs"]
        for item in nominals:
            span= (item['start'], item['end'])
            lemmaH = item['headLemma']
            booleanH, frameH, category = self.refiner.refineWord(sentence, lemmaH, 'n')
            if len(item['eventuality'])>0:
                entities[span]= {'text':item['text'], 'trigger': item['token'], 'frame': frameH, 'qualifier': item['qualifier']}
                event = item['eventuality']
                lemma= event['lemma']
                boolean, frame, category = self.refiner.refineWord(sentence, lemma, 'v')
                if boolean:
                    eventSpan= (event['start'], event['end'])
                    if category== 'event2':
                        events2[eventSpan]= {'trigger': event['token'], 'location': data['location'], 'temporal': data['temporal'], 'frame': frame}
                    else:
                        events[eventSpan]= {'trigger': event['token'], 'location': data['location'], 'temporal': data['temporal'], 'agent':(0, ""), 'patient': ([span], item['token']), 'frame': frame}

            elif booleanH:
                if category== 'event2':
                    events2[span] = {'trigger': item['text'], 'frame': frameH, 'location': data['location'],
                                    'temporal': data['temporal']}
                else:
                    events[span] = {'trigger': item['text'], 'frame': frameH, 'location': data['location'], 'temporal': data['temporal'], 'patient': (0, ""), 'agent':(0, "")}
            else:
                entities[span] = {'text':item['text'],'trigger': item['token'], 'frame': frameH, 'qualifier': item['qualifier']}
        return events2, events, entities

    def nominalEvents(self, sentence, candidateEvents):
        events=[]
        entities=[]
        for phrase in candidateEvents:
            eventFlag=False
            for word in phrase.split(' '):
                lemma= self.lmtzr.lemmatize(word, 'n')
                boolean, frames= self.refiner.refineWord(sentence, lemma, 'n')
                eventFlag+= boolean
            if eventFlag>0:
                events.append(phrase)
            else:
                entities.append(phrase)
        return entities, events
