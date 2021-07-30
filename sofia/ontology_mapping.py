import json
import string
import os
import nltk
from nltk.corpus import stopwords
import yaml

class Ontology:

    # def __init__(self, ontology):
    #     self.dir= os.getcwd()
    #     file_name = '/data/Ontology_{}.json'.format(ontology)
    #     #file_name = '/data/Ontology_wm.json'
    #     self.external_ontology=False
    #     if ontology == 'causex':
    #         self.external_ontology = True
    #         file_name = '/data/CauseX_Ontology.json'
    #     file_path= os.path.dirname(os.path.abspath(file_name)) + file_name
    #     with open(file_path) as f:
    #         text = f.read()
    #         self.ontology= json.loads(text)
    #     indicator_path = os.path.dirname(os.path.abspath(file_name)) + '/data/Indicators_WorldBank_Full.txt'
    #     self.indicators_WorldBank= self.get_indicators(indicator_path)

    def __init__(self, ontology_name):
        self.dir= os.getcwd()
        file_name = f'/data/Ontology_{ontology_name}.json'
        #file_name = '/data/Ontology_wm.json'
        self.external_ontology=False
        if ontology_name == 'causex':
            self.external_ontology = True
            file_name = './data/CauseX_Ontology.json'
        file = os.path.dirname(os.path.abspath(__file__)) + file_name
        if not os.path.exists(file):
            self.format_ontology(ontology_name, file)
        with open(file) as f:
            text = f.read()
            self.ontology= json.loads(text)
        indicator_path = os.path.dirname(os.path.abspath(__file__)) + '/data/Indicators_WorldBank_Full.txt'
        self.indicators_WorldBank= self.get_indicators(indicator_path)


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
        events1, events2, entities= self.ontology['event'], self.ontology['property'], self.ontology['entity']
        for type in events1.keys():
            if lemma in events1[type]:
                return 'event/'+type, 'event'
        for type in events2.keys():
            if lemma in events2[type]:
                return 'property/'+type, 'property'
        for type in entities.keys():
            if lemma in entities[type]:
                return type, 'entity'
        return "", ""

    def format_ontology(self, ontology_name, save_file):
        file_name = f'/data/{ontology_name}.yml'
        #file_path = os.path.dirname(os.path.abspath(file_name))+file_name
        file = os.path.dirname(os.path.abspath(__file__)) + file_name
        with open(file) as f:
            data= yaml.full_load(f)
        data = data[0]['wm']
        path= 'base_path'
        output = {'entity': {}, 'event': {}, 'property': {}}
        output = recurse(data, path, output)
        with open(save_file, 'w') as f:
            json.dump(output, f)
        return output


def recurse(data, path, output):
    for i in range(len(data)):
        if 'OntologyNode' in data[i].keys():
            semantic_type = data[i]['semantic type']
            path_new = "{}/{}".format(path, data[i]['name'])
            output[semantic_type][path_new] = data[i]['examples']
            #return output
        else:
            k = list(data[i].keys())[0]
            data_new = data[i][k]
            path_new = "{}/{}".format(path, k)
            output_new= recurse(data_new, path_new, output)
            for j in output_new: output[j].update(output_new[j])
    return output