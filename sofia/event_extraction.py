from sofia.frames_FN_mapping import FrameNetFrames
from sofia.ontology_mapping import Ontology




targetN= ['sudan', 'famine', 'food', 'hunger', 'drought', 'nutrition']
targetV= ['affect', 'cause', 'focus', 'need', 'suffer', 'occur']
aux= ['be', 'can', 'could', 'dare', 'do', 'have', 'may', 'might', 'must', 'ought', 'shall', 'should', 'will', 'would']
#Don't include "NEED", it serves BOTH as modal verb AND normal verb: eg "I need food.". What about "get"?

verbTags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"] #VBN and VBG maybe?
nounTags= ["NN", "NNS", "NNP", "NNPS", "JJ"]

class CandidateEvents:

    def __init__(self, data_extractor, refiner= None):
        self.data_extractor = data_extractor
        self.sentences= self.data_extractor.sentences
        if refiner != None:
            self.ontology = Ontology(refiner)
        else:
            self.ontology = None
        self.frameNet= FrameNetFrames()


    def overlap(self, span, keys):
        s1, t1= span
        for s2, t2 in keys:
            if s1>= s2 and t2> s1:
                return True, (s2, t2)
            elif s2<=t1 and t2>s1:
                return True, (s2, t2)
        return False, (0, 0)

    def get_verb_events(self, s_index, events2, events, entities, refine=True):
        data= self.data_extractor.get_sentence_data(s_index)
        pos= data["pos"]
        lemmas= data["lemmas"]
        tokens= data["tokens"]
        sentence= data["sentence"]
        spans = data["spans"]
        s_events = events
        s_events2= events2
        for i in range(len(lemmas)):
            span = spans[i]
            overlap1=self.overlap(span, events.keys())
            overlap2=self.overlap(span, events2.keys())
            if overlap1[0]:
                span= overlap1[1]
                s_events[span] = events[span]
                s_events[span].update({"index": i})
            elif overlap2[0]:
                span= overlap2[1]
                s_events2[span] = events2[span]
                s_events2[span].update({"index": i})
            elif pos[i] in verbTags and lemmas[i] not in aux:
                lemma_type_FN= "event"
                frame= ""
                if refine:
                    frame_FN, lemma_type_FN= self.frameNet.refine_word(sentence, lemmas[i], pos[i])
                    if self.ontology!=None:
                        frame, lemma_type = self.ontology.refine_word(sentence, lemmas[i], pos[i])
                    else:
                        frame= frame_FN
                        lemma_type= lemma_type_FN
                if lemma_type_FN=="event" or lemma_type[:-1]== "event":
                    token= tokens[i]
                    if lemma_type=='event2':
                        s_events2[span] = {"trigger": token["token"], "lemma": lemmas[i], "index": i,
                                                "frame": frame, 'frame_FN': frame_FN, "temporal": data["temporal"],
                                                "location": data["location"]}
                    else:
                        srl_output= self.get_dependencies(s_index, i+1, entities)
                        s_events[span] ={"trigger": token["token"], "lemma": lemmas[i], "index": i, "frame": frame,
                                         'frame_FN': frame_FN, "temporal": data["temporal"], "location": data["location"]}
                        s_events[span].update(srl_output)
        for span in s_events2.keys():
            e_index=s_events2[span]['index']
            mapped=dict(entities)
            mapped.update(s_events)
            srl_output = self.get_dependencies(s_index, e_index + 1, mapped)
            s_events2[span].update(srl_output)
        return s_events2, s_events

    def get_semantic_units(self):
        #events2=[]
        events=[]
        entities=[]
        for s_index in range(self.data_extractor.get_data_size()):
            s_events2, s_events, s_entities = self.classify_nominals(s_index)
            s_events2, s_events= self.get_verb_events(s_index, s_events2, s_events, s_entities)
            s_events.update(s_events2)
            events.append(s_events)
            entities.append(s_entities)
        return events, entities

    #TODO: fix here for the quantitative? Figure it out after quant nominals are taken care???
    def get_dependencies(self, s_index, e_index, entities):
        s_dependencies= self.data_extractor.get_dependencies(s_index)
        agent= []
        patient= []
        event_dependencies={}
        for dependency in s_dependencies:
            governor = int(dependency['governor'])
            dependency_type = dependency['dep']
            dependent = str(dependency['dependentGloss'])
            if governor == e_index:
                prev=[]
                if dependency_type in event_dependencies.keys():
                    prev= event_dependencies[dependency_type]
                event_dependencies[dependency_type] = prev+ [dependent]
        passive= False
        if "nsubj" in event_dependencies.keys():
            agent= event_dependencies["nsubj"]
        if "nsubjpass" in event_dependencies.keys():
            patient=  event_dependencies["nsubjpass"]
            passive= True
        elif "dobj" in event_dependencies.keys():
            patient = event_dependencies["dobj"]
        if patient== [] or passive:
            for relation in event_dependencies.keys():
                if "nmod" in relation:
                    if agent == [] and passive:
                        agent= event_dependencies[relation]
                    elif patient== []:
                        patient= event_dependencies[relation]
        srl_output={'agent':(0, ""), 'patient':(0, "")}
        if agent!= []:
            srl_output['agent']= self.map_to_entity(agent, entities)
        if patient!= []:
            srl_output['patient']= self.map_to_entity(patient, entities)
        return srl_output

    def map_to_entity(self, terms, noun_phrases):
        normalized=""
        mySpan=[]
        for span in noun_phrases.keys():
            noun_phrase= noun_phrases[span]
            entity= noun_phrase["trigger"]
            norm= ""
            for term in terms:
                if term in entity:
                    norm= entity
                    mySpan.append(span)
            if norm!="":
                normalized+= norm+', '
        normalized = normalized.strip(', ')
        return mySpan, normalized

    def classify_nominals(self, s_index):
        events = {}
        entities={}
        events2={}
        data = self.data_extractor.get_sentence_data(s_index)
        sentence = data["sentence"]
        nominals = data["NPs"]
        for noun_phrase in nominals:
            span= (noun_phrase['start'], noun_phrase['end'])
            head_lemma = noun_phrase['head_lemma']
            frames_head_FN, head_type_FN = self.frameNet.refine_word(sentence, head_lemma, 'NN')
            if self.ontology!=None:
                frames_head, head_type = self.ontology.refine_word(sentence, head_lemma, 'NN')
            else:
                frames_head= frames_head_FN
                head_type = head_type_FN
            #The NP is part of an eventuality, thus NP is entity
            if len(noun_phrase['eventuality'])>0:
                entities[span]= {'text':noun_phrase['text'], 'trigger': noun_phrase['token'], 'frame': frames_head,
                                 'frame_FN': frames_head_FN, 'qualifier': noun_phrase['qualifier']}
                event = noun_phrase['eventuality']
                lemma= event['lemma']
                frame_lemma_FN, lemma_type_FN = self.frameNet.refine_word(sentence, lemma, 'VBG')
                if self.ontology!=None:
                    frame_lemma, lemma_type = self.ontology.refine_word(sentence, lemma, 'VBG')
                else:
                    frame_lemma= frame_lemma_FN
                    lemma_type= lemma_type_FN
                if lemma_type_FN=="event" or lemma_type[:-1]=="event":
                    event_span= (event['start'], event['end'])
                    if lemma_type== 'event2':
                        events2[event_span]= {'trigger': event['token'], 'location': data['location'],
                                        'temporal': data['temporal'], 'frame': frame_lemma, 'frame_FN': frame_lemma_FN}
                    else:
                        events[event_span]= {'trigger': event['token'], 'location': data['location'],
                                            'temporal': data['temporal'], 'patient': ([span], noun_phrase['token']),
                                             'agent':(0, ""), 'frame': frame_lemma, 'frame_FN': frame_lemma_FN}
            elif head_type_FN=="event" or head_type[:-1]=="event":
                if head_type== 'event2':
                    events2[span] = {'trigger': noun_phrase['text'], 'frame': frames_head, 'frame_FN': frames_head_FN,
                                     'location': data['location'], 'temporal': data['temporal']}
                else:
                    events[span] = {'trigger': noun_phrase['text'], 'frame': frames_head, 'frame_FN': frames_head_FN,
                                    'location': data['location'], 'temporal': data['temporal'],
                                    'patient': (0, ""), 'agent':(0, "")}
            else:
                entities[span] = {'text':noun_phrase['text'],'trigger': noun_phrase['token'], 'frame': frames_head,
                                  'frame_FN': frames_head_FN, 'qualifier': noun_phrase['qualifier']}
        return events2, events, entities
