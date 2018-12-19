import os
from ManualRules import CandidateEvents
from nltk.corpus import framenet as fn
import numpy as np

class Loader():

    def __init__(self, directory):
        self.dir=directory
        self.trainF=['03', '04', '05', '02', '20', '18', '11', '16', '17', '10', '19', '21', '07', '09', '08', '06', '15', '12', '13', '14']
        self.devF=['22']
        self.testF=['23']
        self.embeddings= self.setEmbeddings() ##Default size 50
        self.fnEmbeddings= self.setFNEmbedding() ##Defualt size fn.size(), 1-hot vectors
        # self.vocabulary={}


    def getY(self, file, folder):
        f=open(self.dir+'/'+folder+'/'+file)
        text= f.read()
        lines= text.split('\n')
        f.close()
        #relations= {'Temporal':{}, 'Comparison':{}, 'Contingency':{}, 'Expansion':{}}
        Y={'arg1':{}, 'arg2':{}, 'rel':{}}
        allSenses = ['Temporal', 'Comparison', 'Contingency', 'Expansion']
        for line in lines:
            if len(line)>1:
                items= line.split('|')
                relType= items[0]
                if relType=='Implicit':
                    span= [items[6], items[6]]
                    #text= items[9]
                    senses= [items[11].split('.')[0], items[12].split('.')[0], items[13].split('.')[0], items[14].split('.')[0]]
                    y=[0., 0., 0., 0.]
                    for i in senses:
                        index= allSenses.index(i)
                        y[index]= 1.
                    arg1= items[22].split('..')
                    arg2= items[32].split('..')
                    Y['arg1'].update({arg1:y})
                    Y['arg2'].update({arg2: y})
                    # relations[sense][span]= [relType, text, arg1, arg2]

                elif relType== 'Explicit':
                    span= items[3].split('..')
                    #text= items[5]
                    senses = [items[11].split('.')[0], items[12].split('.')[0]]
                    y = [0., 0., 0., 0.]
                    for i in senses:
                        index = allSenses.index(i)
                        y[index] = 1.
                    arg1 = items[22].split('..')
                    arg2 = items[32].split('..')
                    Y['arg1'].update({arg1: y})
                    Y['arg2'].update({arg2: y})
                    Y['rel'].update({span: y})
                    # relations[sense][span] = [relType, text, arg1, arg2]
                    ###Add direction here!!!
                    #By analyzing the children classes, write subroutine ---Minor issue
                    #Classes should then become -1, 0, 1. Where -1 means opposite direction
        return Y

    def getData(self, mode):
        data={}
        folders=self.trainF
        if mode=='dev':
            folders= self.devF
        elif mode== 'test':
            folders= self.testF
        data_X = []
        data_Y = []
        for folder in folders:
            files=os.listdir(self.dir+'/data/'+folder)
            for file in files:
                ########
                Y= self.getY(folder, file)
                # data_X=[]
                # data_Y=[]
                eventReader= CandidateEvents(file, self.dir, 'none')
                numSentences = eventReader.dataSize()
                for index in range(numSentences):
                    events2, events, entities = eventReader.classifyNominals(index)
                    events2, events = eventReader.getVerbEvents(index, events2, events, entities)
                    #sentence= eventReader.getSentence(index)
                    tokens=eventReader.getTokens(index)
                    for token in tokens:
                        wordVector= self.getEmbeddings(token['token'])
                        event_entityVector=[0., 0.]
                        span= (token['start'], token['end'])
                        frame=[]
                        if span in events:
                            frame+= events[span]['FrameNetFr'] #Check if FrameNetFrame is a list or a string: not sure if I have converted it at some point....
                            event_entityVector[0]=1.
                        elif span in entities:
                            frame+= entities[span]['FrameNetFr']
                            event_entityVector[1] = 1.
                        ##Currently does not include any information on whether it is part of events' Agent/Patient
                        #Maybe include it in the future???
                        fnVector= self.getFNEmbeddings(frame)
                        xVector= wordVector+fnVector+event_entityVector
                        data_X.append(xVector)
                        #Y= [Temporal, Comparison, Contingency, Expansion, Arg1/Arg2/Rel]
                        #Arg1= 1, Arg2=2, Rel=0
                        yVector= [0.] *15
                        if span in Y:
                            if span in Y['rel']:
                                yVector[:4]= Y['rel'][span]
                                yVector[4]= 1.
                            if span in Y['arg1']:
                                yVector[5:9] = Y['arg1'][span]
                                yVector[9] = 1.
                            if span in Y['arg2']:
                                yVector[10:14] = Y['arg2'][span]
                                yVector[14] = 1.
                        data_Y.append(yVector)
                    #data.append({'events': events, 'entities': entities, 'sentence': sentence})
                    ##Maybe change the data to reflect all combinations of events?
                    #Combinations of events within the sentence and intra-sentential from
                    #the sentence before. All pairs would be considered, ofc many should end up with null relations
                    #NONONONO wrong!!! We do not want to map the events, as we cannot provide supervision for that
                    #Supervision can be offered only to the type of relation involved. So what we can do is simply provide ALL EVENTS in the sentence
                #############
                # data[file]= [data_X, data_Y]
        return data_X, data_Y

    def setEmbeddings(self, embFile= 'embeddings.txt'):
        f=open(os.path.dirname(self.dir)+ embFile)
        text= f.read()
        f.close()
        embeddings={}
        terms= text.split('\n')
        for term in terms:
            vector= term.split(' ')
            word= vector[0]
            vector= vector[1:]
            vector = [float(i) for i in vector]
            embeddings[word]= vector
        return embeddings

    def getEmbeddings(self, word):
        if word in self.embeddings:
            return self.embeddings[word]
        v = np.zeros(50)
        return v

    def setFNEmbedding(self):
        embedding={}
        frames= fn.frames()
        vector=[0.]*len(frames)
        for i in range(len(frames)):
            name= frames[i].name
            vector_i= vector[:]
            vector_i[i]=1.0
            embedding[name]= vector_i
        return embedding

    def getFNEmbeddings(self, fnList):
        v = np.zeros(len(self.fnEmbeddings['Annoyance']))
        if len(fnList)==0:
            return v
        for frame in fnList:
            v_i= self.fnEmbeddings[frame]
            v+= v_i
        return v

    def getLabels(self):
        labels=[]
        return labels










