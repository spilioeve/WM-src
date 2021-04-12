import json
import string
import os
import nltk
from nltk.corpus import stopwords

class Ontology:

    def __init__(self, ontology):
        self.dir= os.getcwd()
        file_name = '/data/Ontology_{}.json'.format(ontology)
        #file_name = '/data/Ontology_wm.json'
        self.external_ontology=False
        if ontology == 'causex':
            self.external_ontology = True
            file_name = './data/CauseX_Ontology.json'
        self.file = os.path.dirname(os.path.abspath(__file__)) + file_name
        self.ontology= self.get_ontology_data()
        indicator_path = os.path.dirname(os.path.abspath(__file__)) + '/data/Indicators_WorldBank_Full.txt'
        self.indicators_WorldBank= self.get_indicators(indicator_path)

    def get_ontology_data(self):
        f= open(self.file)
        text= f.read()
        data=json.loads(text)
        f.close()
        return data

    def get_indicators(self, path):
        f= open(path)
        text= f.read().split('\n\n')
        f.close()
        indicators={}
        for type in text:
            terms= type.split('\n')
            indicators[terms[0]]= terms[1:]
        return indicators

    def string_matching(self, phrase, resource):
        term_scores={}
        for key in self.indicators_WorldBank:
            terms= self.indicators_WorldBank[key]
            for term in terms:
                score= self.score(phrase, term)
                if score>0.1:
                    term_scores[term]= score
        return term_scores

    def score(self, phrase, key_term):
        punc= string.punctuation
        stop_words= stopwords.words('english')
        phrase= str(phrase.strip(' '))
        if phrase == key_term:
            return 1.0
        elif phrase in key_term:
            return len(phrase.split(' '))/ len(key_term.split(' '))
        else:
            score=0.0
            phrase_words= []
            for i in phrase.split(' '):
                if i not in punc and i not in stop_words:
                    phrase_words.append(i)
            for word in phrase_words:
                if word in key_term.split(' '):
                    score+=1
            return 2*score / (len(key_term.split(' '))+ len(phrase_words))


    def refine_word(self, sentence, lemma, pos):
        #if self.externalOntology: return self.refineWord_external(sentence, lemma, pos, fnFrames)
        events1, events2, entities= self.ontology['events1'], self.ontology['events2'], self.ontology['entities']
        for type in events1.keys():
            if lemma in events1[type]:
                return 'event1/'+type, 'event1'
        for type in events2.keys():
            if lemma in events2[type]:
                return 'event2/'+type, 'event2'
        for type in entities.keys():
            if lemma in entities[type]:
                return type, 'entity'
        return "", ""
