class TemporalModel:

    def __init__(self, events, eventLocalIndex, entities, entityLocalIndex, sentence, lemmas):
        self.sentence= sentence
        self.triggers= self.detectTempTriggers(lemmas)
        self.bounds= self.setBounds()
        self.events= events
        self.localIndex= eventLocalIndex
        self.entities= entities
        self.entityIndex= entityLocalIndex
        #self.events= self.format(events, eventLocalIndex)


    def detectTempTriggers(self, lemmas):
        return []

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

