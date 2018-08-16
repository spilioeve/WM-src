class EventModel:

    def __init__(self, events, eventLocalIndex, entities, entityLocalIndex, sentence, lemmas):
        self.sentence= sentence
        self.events= events
        self.localIndex= eventLocalIndex
        self.entities= entities
        self.entityIndex= entityLocalIndex

    def pruneEvent(self, currEvent):
        for i in range(len(self.localIndex)):
            if self.localIndex[i]== currEvent:
                self.localIndex=self.localIndex[:i]+ self.localIndex[i+1:]
                self.events= self.events[:i]+self.events[i+1:]



