

class RSTModel:

    def __init__(self, events, eventLocalIndex, sentence, typeRel='None'):
        self.sentence= sentence
        self.relType= typeRel
        self.events= events
        self.localIndex=eventLocalIndex
        #self.events= self.format(events, eventLocalIndex)

    def format(self, event):
        # newEvents={}
        # for index in self.localIndex.keys():
        #     span= self.localIndex[index]
        #     if span in events:
        #         newEvents[index]= events[span]
        # return newEvents
        for index in self.localIndex.keys():
            span = self.localIndex[index]
            if span in event:
                return index, event['trigger']


    def distanceHeuristic(self, triggerRST, causalClause, effectClause):
        rIndex= self.sentence.index(triggerRST)
        cIndex= self.sentence.index(causalClause)
        eIndex = self.sentence.index(effectClause)
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


    def locateEvents(self, bound, direction):
        keys= self.events.keys()
        if direction == 'right':
            keys.sort()
        else:
            keys.sort(reverse=True)
        event= self.events[keys[0]]
        index=0
        for k in keys:
            event= self.events[k]
            index= self.sentence.index(event['trigger'])
            if (direction=='right' and index>bound):
                return event, index
            elif (direction=='left' and index<bound):
                return event, index
        return event, index


    def determineRST(self, sentence):
        return 'Causality'



