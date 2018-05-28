from FrameNetRefine import FrameNetRefiner
import os
import ast
import string
from Utils import FileReader


class FrameNetMapper:

    def __init__(self, words, file):
        self.words= words
        self.refiner= FrameNetRefiner()
        self.file= file
        self.fReader= FileReader()
        self.verbTags = ["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"]
        self.nounTags = ["NN", "NNS", "NNP", "NNPS"]
        self.unmatched={}


    def getFrames(self):
        frameClusters={}
        f= open(self.file)
        text= f.read()
        f.close()
        boundC = '============================================'
        clusterBlocks= text.split(boundC)[:-1]
        curr=0
        for details in clusterBlocks:
            w= details.split('\n')[-2]
            wordList= ast.literal_eval(w)
            print "Processing Cluster " + str(curr)
            frameClusters[curr]= self.framesPerCluster(curr, wordList)
            curr+=1
        return frameClusters, clusterBlocks

    def framesPerCluster(self, curr, clusterWords):
        self.unmatched[curr]=[]
        refinedWords=[]
        frames = {}
        for word in clusterWords:
            found= False
            verbal= False
            if word in self.words:
                wordPos = self.words[word]
                for pos in wordPos.keys():
                    # for i in range(wordPos[pos]):
                    if pos in self.nounTags: #or pos in self.verbTags:
                        found= True
                        lemma = self.refiner.getLemma(word, pos)
                        wordFrames = self.refiner.getFrames(lemma, pos)
                        for fr in wordFrames:
                            frName = fr.name
                            if frName in frames.keys():
                                frames[frName] += wordPos[pos]
                            else:
                                frames[frName] = wordPos[pos]
                    elif pos in self.verbTags:
                        verbal= True
            else:
                print "Word not found"
                print word
            if found:
                refinedWords.append(word)
            elif verbal:
                self.unmatched[curr].append(word)
        bestFrames= self.fReader.sortDict(frames)[:5]
        bestFr={}
        for (k, v) in bestFrames:
            bestFr[k]= v
        if len(bestFr)==0:
            self.unmatched[curr]+= refinedWords
            return {}, []
        return bestFr, refinedWords

    def splitCluster(self, clusterWords, fr1, fr2):
        cluster1=[]
        cluster2=[]
        middleCluster=[]
        for word in clusterWords:
            if word in self.words:
                wordPos = self.words[word]
                for pos in wordPos.keys():
                    # for i in range(wordPos[pos]):
                    if pos in self.nounTags or pos in self.verbTags:
                        lemma = self.refiner.getLemma(word, pos)
                        wordFrames = self.refiner.getFrames(lemma, pos)
                        frames=[]
                        for fr in wordFrames:
                            frames.append(fr.name)
                        if fr1 in frames:
                            if fr2 in frames:
                                middleCluster.append(word)
                            else:
                                cluster1.append(word)
                        elif fr2 in frames:
                            cluster2.append(word)
        return cluster1, cluster2, middleCluster

def main(project, numClusters):
    clusterBound='============================================'
    itemBound= '-------------------------------------------'
    if project== 'Sudan':
        path= os.path.dirname(os.getcwd())+'/South_Sudan_Famine/OntologyFiles'
        print "Running Sudan Project"
    else:
        print "Running Bellingcat Project"
        path = os.path.dirname(os.getcwd()) + '/AIDA/OntologyFiles'

    f = open(path + '/terms.txt')
    textW = f.read()
    f.close()
    words = ast.literal_eval(textW)
    #Change file to run different clustering output
    mapper = FrameNetMapper(words, path + '/clusters'+str(numClusters)+'.txt')
    frames, clusters = mapper.getFrames()


    f= open(path+'/Clusters_'+ str(numClusters)+'_'+ project+ '.txt', 'w')
    for index in frames.keys():
        cluster= clusters[index].split(itemBound)
        dic, termList= frames[index]
        if len(termList)>10:
            f.write(string.join(cluster[:2], itemBound) + itemBound + '\nFrameNet Frames : ')
            for key, value in sorted(dic.iteritems(), key=lambda (k, v): (v, k), reverse=True):
                f.write(key+':' +str(value)+',')
            f.write('\n'+itemBound+ '\n'+ str(termList)+ '\n'+clusterBound)
        else:
            mapper.unmatched[index]+= termList
    f.close()
    print "Unmatched words"
    print mapper.unmatched

main('Sudan', 250)
