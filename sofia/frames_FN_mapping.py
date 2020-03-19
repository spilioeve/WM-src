from nltk.corpus import framenet as fn
from nltk.corpus import wordnet as wn
from nltk.wsd import lesk
from nltk.stem import WordNetLemmatizer
import os
import string
import ast
import json

class FrameNetFrames:
    def __init__(self, external=False):
        self.dir = os.path.dirname(os.getcwd())
        self.dir= os.getcwd()
        self.verb_tags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"] #VBN and VBG maybe?
        self.noun_tags= ["NN", "NNS", "NNP", "NNPS"]
        self.adj_tags= ['JJ', 'JJR', 'JJS']
        self.lmtzer = WordNetLemmatizer()
        self.frames= self.get_FN_frames()
        self.frame_LUs= self.get_FN_LUs()
        self.wn2Frame= self.wn_to_FN()
        self.external_frames= self.external_frames(external)
        self.Causal=['Causation']

    def get_FN_frames(self):
        event_path = os.path.dirname(os.path.abspath(__file__)) + '/data/event_frames.txt'
        f= open(event_path)
        text= f.read()
        lines= text.strip('\n').split('\n')
        f.close()
        frames=[]
        for line in lines:
            frame= line.split('\t')[0]
            frames.append(frame)
        return frames

    def get_FN_LUs(self):
        path = os.path.dirname(os.path.abspath(__file__)) + '/data/FrameNetLUs.txt'
        f = open(path)
        text = f.read()
        FN_LUs = ast.literal_eval(text)
        f.close()
        return FN_LUs


    def wn_to_FN(self):
        path = os.path.dirname(os.path.abspath(__file__)) + '/data/WordFrameNet.txt'
        f = open(path)
        text= f.read()
        f.close()
        text= text.strip('\n')
        frames= text.split('\n\n\n')
        wn_frames={}
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
                        if synset in wn_frames:
                            wn_frames[synset]+= [name]
                        else:
                            wn_frames[synset] = [name]
                    except:
                        pass
        return wn_frames

    def external_frames(self, external):
        if not external:
            return None
        CausexOntology = os.path.dirname(os.path.abspath(__file__)) + '/data/CauseX_Ontology.json'
        f= open(CausexOntology)
        text= f.read()
        data=json.loads(text)
        f.close()
        return data

    def get_word_wn_frames(self, sentence, lemma, pos):
        pos = self.get_pos(pos)
        punc= string.punctuation
        sentence_words= sentence.split(' ')
        tokens= []
        for word in sentence_words:
            tokens.append(word.strip(punc))
        synset = lesk(tokens, lemma, pos)
        if synset in self.wn2Frame:
            frames= self.wn2Frame[synset]
            return frames
        return []

    def get_word_frames(self, word, pos):
        pos= self.get_pos(pos)
        term= word+'.'+pos
        if term not in self.frame_LUs:
            return ""
        return self.frame_LUs[term]


    def get_phrase_frames(self, phrase):
        words = filter(lambda a: a != '', phrase.split(' '))
        frames=[]
        for word in words:
            word= word.lower()
            noun_frames= self.get_word_frames(word, 'NN')
            verb_frames = self.get_word_frames(word, 'VB')
            if len(noun_frames)>0:
                for frame in noun_frames:
                    if frame not in frames:
                        frames.append(frame)
            if len(verb_frames) > 0:
                for frame in verb_frames:
                    if frame not in frames:
                        frames.append(frame)
        return frames

    def refine_word(self, sentence, word, pos):
        all_frames = {'root': self.frames}
        if self.external_frames!= None:
            all_frames= self.external_frames
        frames= self.get_word_frames(word, pos)
        event_frames= set()
        event_types= set()
        for frame in frames:
            if frame not in self.Causal:
                for event_type in all_frames:
                    if frame in all_frames[event_type]:
                        event_types.add(event_type)
                        event_frames.add(frame)
        if len(event_frames)>0:
            if self.external_frames!=None:
                return list(event_types), "event"
            return list(event_frames), "event"
        return frames, "entity"

    def get_pos(self, pos):
        if pos in self.noun_tags:
            return 'n'
        elif pos in self.verb_tags:
            return 'v'
        elif pos in self.adj_tags:
            return 'a'
        return 'None'
