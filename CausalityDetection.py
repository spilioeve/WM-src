import pdb

class RSTModel:

    def __init__(self, events, eventLocalIndex, sentence, typeRel='None'):
        self.sentence= sentence
        self.relType= typeRel
        self.events= events
        self.localIndex= eventLocalIndex
        #self.events= self.format(events, eventLocalIndex)

    def format(self, key):
        # newEvents={}
        # for index in self.localIndex.keys():
        #     span= self.localIndex[index]
        #     if span in events:
        #         newEvents[index]= events[span]
        # return newEvents
        for index in self.localIndex.keys():
            #span = self.localIndex[index]
            if index==key:
                return self.localIndex[index], self.events[key]['trigger']
        return "", ""

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


    def locateEvents(self, bound, direction):
        keys= self.events.keys()
        if direction == 'right':
            keys.sort()
        else:
            keys.sort(reverse=True)
        event= self.events[keys[0]]
        #pdb.set_trace()
        index=0
        for k in keys:
            event= self.events[k]
            index = self.sentence.index(event['trigger'])
            if (direction=='right' and index>bound):
                #event = event.update({'key': k})
                return k, index
            elif (direction=='left' and index<bound):
                #event = event.update({'key': k})
                return k, index
        return (0, 0), index


    def determineRST(self, sentence):
        return 'Causality'



