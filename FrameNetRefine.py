from nltk.corpus import framenet as fn
from nltk.corpus import wordnet as wn
from nltk.wsd import lesk
from nltk.stem import WordNetLemmatizer
import os
import string
import ast

class FrameNetRefiner:
    def __init__(self):
        #word has to be Lemma
        #Pos has to be V or N
        self.dir = os.path.dirname(os.getcwd())
        self.dir= os.getcwd()
        self.verbTags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"] #VBN and VBG maybe?
        self.nounTags= ["NN", "NNS", "NNP", "NNPS"]
        self.adjTags= ['JJ', 'JJR', 'JJS']
        self.lmtzer = WordNetLemmatizer()
        self.frames= self.getTaxonomy()
        self.frameLUs= self.getFrameNetLUs()
        self.wordToFrame= self.getWordFrameNet()
        self.Causal=['Causation']

    def getTaxonomy(self):
        f= open(self.dir+'/event_frames.txt')
        text= f.read()
        frameLines= text.strip('\n').split('\n')
        f.close()
        frames=[]
        for line in frameLines:
            fr= line.split('\t')[0]
            frames.append(fr)
        return frames

    def getFrameNetLUs(self):
        f = open(self.dir+ '/FrameNetLUs.txt')
        text = f.read()
        data = ast.literal_eval(text)
        f.close()
        return data


    def getWordFrameNet(self):
        f = open(self.dir+'/WordFrameNet.txt')
        text= f.read()
        f.close()
        text= text.strip('\n')
        frames= text.split('\n\n\n')
        frameDic={}
        for frame in frames:
            details = frame.split('\n')
            name= details[0].split(': ')[1]
            for item in details[1:]:
                offset= item.split(' ')[2]
                pos= item.split(' ')[1]
                if offset.isdigit():
                    offset = int(offset)
                    try:
                        synset = wn.synset_from_pos_and_offset(pos, offset)
                        if synset in frameDic:
                            frameDic[synset]+= [name]
                        else:
                            frameDic[synset] = [name]
                    except:
                        pass
        return frameDic

    #This is the main function you want to call
    #Lemma should be the lemma form of word of interest (not the token)
    #pos is the PosTag of the word of interest
    #eg: frames= getWordFrames("I went to college", "go", "v")
    #
    def getWordFrames(self, sentence, lemma, pos):
        pos = self.getPos(pos)
        punc= string.punctuation
        i= sentence.split(' ')
        tokens= []
        for j in i:
            tokens.append(j.strip(punc))
        synset = lesk(tokens, lemma, pos)
        if synset in self.wordToFrame:
            frames= self.wordToFrame[synset]
            return frames
        return []

    def getFrames(self, word, pos):
        #Search within the Taxonomy to find LU
        posTag= self.getPos(pos)
        term= word+'.'+posTag
        if term not in self.frameLUs:
            return "" ##Change this from empty string. Modify also ManualRules accordingly
        return self.frameLUs[term]
        # lus= fn.lus()
        # frames=[]
        # for lu in lus:
        #     name= lu.name
        #     if name == term:
        #         frames.append(lu.frame)
        #return frames

    def getPhraseFrames(self, phrase):
        words = filter(lambda a: a != '', phrase.split(' '))
        frames=[]
        for w in words:
            w=w.lower()
            nFrames= self.getFrames(w, 'NN')
            vFrames = self.getFrames(w, 'VB')
            if len(nFrames)>0:
                for f in nFrames:
                    if f not in frames:
                        frames.append(f)
            if len(vFrames) > 0:
                for f in vFrames:
                    if f not in frames:
                        frames.append(f)
        return frames



    #This is to refine Events
    # def refineWord(self, sentence, word, pos, wordNet= False):
    #     if wordNet:
    #         frames= self.getWordFrames(sentence, word, pos)
    #         for frame in frames:
    #             if frame in self.frames:
    #                 return True, frame
    #     else:
    #         frames= self.getFrames(word, pos)
    #         for frame in frames:
    #             if frame.name in self.frames and (frame.name not in self.Causal):
    #                 return True, frame.name
    #     return False, ""

    def refineWord(self, sentence, word, pos):
        frames= self.getFrames(word, pos)
        eventFrames=[]
        for frame in frames:
            if (frame in self.frames) and (frame not in self.Causal):
                eventFrames.append(frame)
        if len(eventFrames)>0:
            return True, eventFrames, "event1"
        return False, "", ""

    def getPos(self, posTag):
        if posTag in self.nounTags:
            return 'n'
        elif posTag in self.verbTags:
            return 'v'
        elif posTag in self.adjTags:
            return 'a'
        return 'None'

    # def getLemma(self, word, posTag):
    #     pos= self.getWnPos(posTag)
    #     if pos== 'None':
    #         return word
    #     lemma= self.lmtzer.lemmatize(word, pos)
    #     return str(lemma)

