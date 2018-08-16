import pdb
verbTags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"]

class RSTModel:

    def __init__(self, events, eventLocalIndex, entities, entityLocalIndex, sentence, lemmas, pos):
        self.sentence= sentence
        # self.lemmas= lemmas
        # self.pos= pos
        self.triggers= self.detectCausalTriggers(lemmas, pos)
        self.bounds= self.setBounds()
        self.events= events
        self.localIndex= eventLocalIndex
        self.entities= entities
        self.entityIndex= entityLocalIndex
        #self.events= self.format(events, eventLocalIndex)

    def format(self, keys, entities=False):
        if entities:
            localIndex= self.entityIndex
            localEvents= self.entities
        else:
            localIndex = self.localIndex
            localEvents = self.events
        eventsIndex=""
        eventsSpan=""
        for index in localIndex.keys():
            if index in keys:
                eventsIndex+= localIndex[index]+ ', '
                eventsSpan+= localEvents[index]['trigger']+', '
        eventsIndex= eventsIndex.strip(', ')
        eventsSpan= eventsSpan.strip(', ')
        return eventsIndex, eventsSpan

##Outcome, result
###Correlation: relate to, influence, correlate
##Prevent, limit, worsen, restrict, constrain
## Increase/Decrease

## Grounding via word-to-vec or glove to the Ontology

    def detectCausalTriggers(self, lemmas, pos):
        triggers=[]
        tokens= self.sentence.split(' ')
        causal={'CauseEffect':['impact', 'affect', 'drive', 'lead', 'result'], 'EffectCause':['because', 'due']} #Hard Triggers
        ##Add constraint that preventive triggers must also be verbs???
        #WHat about correlation triggers?
        preventive = ['prevent', 'limit', 'restrict', 'constrain', 'block', 'bind', 'regulate'] ## Soft triggers
        correlation = ['relate', 'influence', 'correlate'] #Hard or soft? Think about it
        for index in range(len(lemmas)):
            lemma= lemmas[index]
            if lemma== 'cause':
                if lemmas[index+1]== 'by':
                    triggers.append((tokens[index], "right", 'CausalRelation'))
                else:
                    triggers.append((tokens[index], "left", 'CausalRelation'))
            if lemma in causal['CauseEffect']:
                triggers.append((tokens[index], "left", 'CausalRelation'))
            elif lemma in causal['EffectCause']:
                triggers.append((tokens[index], 'right', 'CausalRelation'))
            elif lemma in preventive:
                if pos[index] in verbTags:
                    triggers.append((tokens[index], "left", 'PreventRelation'))
            elif lemma in correlation:
                triggers.append((tokens[index], "left", 'CorrelateRelation'))
        return triggers

    #### Implement to include second order events
    ### Those are taken and ranked by the Extractor
    ### Here it is left only a very simple alignment (similar to CausalNodes) to cause/effect (income outcome nodes)
    ###To-do to fix these issues of mapping

    # def set2OrderEvents(self, eventCandidates):
    #     triggers=[]
    #     for k in eventCandidates.keys():
    #         event= eventCandidates[k]
    #         triggers.append((event['trigger'], 'left'))
            


    # def detectTrendTriggers(self, lemmas):
    #     triggers=[]
    #     tokens= self.sentence.split(' ')
    #     causal={'CauseEffect':['impact', 'affect', 'drive', 'lead'], 'EffectCause':['because', 'due']}
    #     for index in range(len(lemmas)):
    #         lemma= lemmas[index]
    #         if lemma== 'cause':
    #             if lemmas[index+1]== 'by':
    #                 triggers.append((tokens[index], "right"))
    #             else:
    #                 triggers.append((tokens[index], "left"))
    #         if lemma in causal['CauseEffect']:
    #             triggers.append((tokens[index], "left"))
    #         elif lemma in causal['EffectCause']:
    #             triggers.append((tokens[index], 'right'))
    #     return triggers

    def setBounds(self):
        bounds={}
        boundVal = [-1, len(self.sentence) + 1]
        for trigger in self.triggers:
            b=self.sentence.index(trigger[0])
            while b in boundVal:
                b= self.sentence.find(trigger[0], b+1)
            boundVal.append(b)
            bounds[b] = {'curr': b, "trigger": trigger}
        boundVal.sort()
        for index in range(1, len(boundVal)-1):
            b=boundVal[index]
            bounds[b].update({'prev': boundVal[index-1], 'next': boundVal[index+1]})
        return bounds

    # def insertBound(self, newTriggers):
    #     bounds= self.bounds
    #     boundVal= bounds.keys()
    #     boundVal+= [-1, len(self.sentence) + 1]


    ##If Effect/Cause are empty, return no relation
    ##Fix model by searching more Events from previous module, given that there is a hard Relations (Aka hard Causal Trigger)
    def getCausalNodes(self, entityReplacement=False):
        ##Use also Entities as potential nodes, in case that we cannot locate an Event as cause/effect
        causality=[]
        for b in self.bounds.keys():
            bound= self.bounds[b]
            trigger, direction, relType= bound['trigger']
            cause, effect= self.locateEvents2(bound, direction) ##Left is default: cause, relation, effect
            fCause = self.format(cause)
            fEffect= self.format(effect)
            if entityReplacement:
                if len(fEffect[0])== 0:
                    cause, effect = self.locateEvents2(bound, direction)
                    fEffect = self.format(effect, True)
                elif len(fCause[0])==0:
                    cause, effect = self.locateEvents2(bound, direction)
                    fCause = self.format(cause, True)
            if fCause[0]!= '' and fEffect[0]!= '':
                causality.append({'trigger': trigger, 'cause': fCause, 'effect': fEffect, 'type': relType})
        return causality

    def distanceHeuristic(self, triggerRST, causalClause, effectClause):
        rIndex= self.sentence.index(triggerRST)
        cIndex= self.sentence.index(causalClause)
        eIndex = self.sentence.index(effectClause)
        # cause= causalClause
        # effect= effectClause
        #  If not mapped to any event, then try to map it to some entity Ni. Then we must bring Ni in the event space
        # This means that Ni was wrongly labeled as entity: instead it is a nominal event that we failed to detect
        # this brings to light how RST interact back-and-forth with Event Detection
        ####
        #As an example use the first sentence of Par6. "Food insecurity levels" is not an easy-to-detect event
        if cIndex> eIndex:
            if rIndex< eIndex: #r<e<c
                effect, i= self.locateEvents(rIndex, 'right')
                cause, j= self.locateEvents(i, 'right')
            elif rIndex< cIndex: #e<r<c

                effect, i= self.locateEvents(rIndex, 'left')
                cause, j= self.locateEvents(rIndex, 'right')
            else: #e<c<r
                cause, j = self.locateEvents(rIndex, 'left')
                effect, i = self.locateEvents(j, 'left')
        else:
            if rIndex < cIndex: #r<c<e
                cause, j = self.locateEvents(rIndex, 'right')
                effect, i = self.locateEvents(j, 'right')
            elif rIndex < eIndex: #c<r<e
                effect, i = self.locateEvents(rIndex, 'right')
                cause, j = self.locateEvents(rIndex, 'left')
            else:  # c<e<r
                effect, i = self.locateEvents(rIndex, 'left')
                cause, j = self.locateEvents(i, 'left')
        fEffect= self.format(effect)
        fCause= self.format(cause)
        return fCause, fEffect

    def locateEvents2(self, bound, direction):
        keys = self.events.keys()
        list1=[]
        list2=[]
        for k in keys:
            event = self.events[k]
            index = self.sentence.index(event['trigger'])
            if index>bound['prev'] and index<bound['next']:
                if index<bound['curr']:
                    list1.append(k)
                elif index>bound['curr']:
                    list2.append(k)
        if len(list1)==0:
            for k in self.entities.keys():
                entity = self.entities[k]
                index = self.sentence.index(entity['text'])
                if index > bound['prev'] and index < bound['next']:
                    if index < bound['curr']:
                        list1.append(k)
        if len(list2)==0:
            for k in self.entities.keys():
                entity = self.entities[k]
                index = self.sentence.index(entity['text'])
                if index > bound['prev'] and index < bound['next']:
                    if index > bound['curr']:
                        list2.append(k)
        if direction=='left':
            return list1, list2
        return list2, list1


    def locateEvents(self, bound, direction):
        triggerIndex= self.triggers.index(bound)
        keys= self.events.keys()
        if direction == 'right':
            keys.sort()
        else:
            keys.sort(reverse=True)
        event= self.events[keys[0]]

        # #pdb.set_trace()
        index=0
        # for k in keys:
        #     event= self.events[k]
        #     index = self.sentence.index(event['trigger'])
        #     if (direction=='right' and index>bound):
        #         #event = event.update({'key': k})
        #         return k, index
        #     elif (direction=='left' and index<bound):
        #         #event = event.update({'key': k})
        #         return k, index
        return (0, 0), index


    def determineRST(self, sentence):
        return 'Causality'



