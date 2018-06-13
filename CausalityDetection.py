import pdb

class RSTModel:

    def __init__(self, events, eventLocalIndex, sentence, lemmas):
        self.sentence= sentence
        self.triggers= self.detectCausalTriggers(lemmas)
        self.bounds= self.setBounds()
        self.events= events
        self.localIndex= eventLocalIndex
        #self.events= self.format(events, eventLocalIndex)

    def format(self, keys):
        eventsIndex=""
        eventsSpan=""
        for index in self.localIndex.keys():
            #span = self.localIndex[index]
            if index in keys:
                eventsIndex+= self.localIndex[index]+ ', '
                eventsSpan+= self.events[index]['trigger']+', '
                #events.append((self.localIndex[index], self.events[index]['trigger']))
                #return self.localIndex[index], self.events[key]['trigger']
        eventsIndex= eventsIndex.strip(', ')
        eventsSpan= eventsSpan.strip(', ')
        return eventsIndex, eventsSpan

    def detectCausalTriggers(self, lemmas):
        triggers=[]
        tokens= self.sentence.split(' ')
        causal={'CauseEffect':['cause','impact', 'affect', 'drive', 'lead'], 'EffectCause':['because', 'due']}
        for index in range(len(lemmas)):
            lemma= lemmas[index]
            if lemma in causal['CauseEffect']:
                triggers.append((tokens[index], "left"))
            elif lemma in causal['EffectCause']:
                triggers.append((tokens[index], 'right'))
        return triggers

    def setBounds(self):
        bounds={}
        boundVal = [-1, len(self.sentence) + 1]
        for trigger in self.triggers:
            b=self.sentence.index(trigger[0])###
            while b in boundVal:
                b= self.sentence.find(trigger[0], b+1)
            boundVal.append(b)

            #bounds[trigger[0]]={'curr': b}
            bounds[b] = {'curr': b, "trigger": trigger}
        boundVal.sort()
        for index in range(1, len(boundVal)-1):
            b=boundVal[index]
            bounds[b].update({'prev': boundVal[index-1], 'next': boundVal[index+1]})
        # bounds={}
        # boundVal=[-1, len(self.sentence)+1]
        # for trigger in self.triggers:
        #     b=self.sentence.index(trigger[0])
        #     boundVal.append(b)
        #     bounds[trigger[0]]={'curr': b}
        # boundVal.sort()
        # for trigger in self.triggers:
        #     b= bounds[trigger[0]]['curr']
        #     bounds[trigger[0]].update({'prev': boundVal[boundVal.index(b)-1], 'next':boundVal[boundVal.index(b)+1]})
        return bounds

    def getCausalNodes(self):
        causality=[]
        for b in self.bounds.keys():
        #for trigger, direction in self.triggers:
            bound= self.bounds[b]
            trigger, direction= bound['trigger']
            cause, effect= self.locateEvents2(bound, direction) ##Left is default: cause, relation, effect
            fCause = self.format(cause)
            fEffect= self.format(effect)
            causality.append({'trigger': trigger, 'cause': fCause, 'effect': fEffect})
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
        print "Cause, effect"
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



