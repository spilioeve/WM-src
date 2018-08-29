import os
from ManualRules import CandidateEvents

class Loader():

    def __init__(self, directory):
        self.dir=directory
        self.trainF=['03', '04', '05', '02', '20', '18', '11', '16', '17', '10', '19', '21', '07', '09', '08', '06', '15', '12', '13', '14']
        self.devF=['22']
        self.testF=['23']


    def getTrainY(self):
        data={}
        for folder in self.trainF:
            files=os.listdir(self.dir+'/data/'+folder)
            for file in files:
                f=open(self.dir+'/'+folder+'/'+file)
                text= f.read()
                lines= text.split('\n')
                f.close()
                relations= {'Temporal':{}, 'Comparison':{}, 'Contingency':{}, 'Expansion':{}}
                for line in lines:
                    if len(line)>1:
                        items= line.split('|')
                        relType= items[0]
                        if relType=='Implicit':
                            span= [items[6], items[6]]
                            text= items[9]
                            sense= items[11].split('.')[0]
                            arg1= items[22].split('..')
                            arg2= items[32].split('..')
                            relations[sense][span]= [relType, text, arg1, arg2]
                        elif relType== 'Explicit':
                            span= items[3].split('..')
                            text= items[5]
                            sense = items[11].split('.')[0]
                            arg1 = items[22].split('..')
                            arg2 = items[32].split('..')
                            relations[sense][span] = [relType, text, arg1, arg2]
                data[file]= relations
            return data

    def getTrainX(self):
        trainX={}
        for folder in self.trainF:
            files=os.listdir(self.dir+'/'+folder)
            for file in files:
                ########
                data=[]
                eventReader= CandidateEvents(file, self.dir, 'none')
                numSentences = eventReader.dataSize()
                for index in range(numSentences):
                    events2, events, entities = eventReader.classifyNominals(index)
                    events2, events = eventReader.getVerbEvents(index, events2, events, entities)
                    sentence= eventReader.getSentence(index)
                    data.append({'events': events, 'entities': entities, 'sentence': sentence})
                    ##Maybe change the data to reflect all combinations of events?
                    #Combinations of events within the sentence and intra-sentential from
                    #the sentence before. All pairs would be considered, ofc many should end up with null relations
                    #NONONONO wrong!!! We do not want to map the events, as we cannot provide supervision for that
                    #Supervision can be offered only to the type of relation involved. So what we can do is simply provide ALL EVENTS in the sentence
                #############
                trainX[file]= data
        return trainX











