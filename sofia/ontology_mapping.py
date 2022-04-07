import json
import os
import string
from os.path import isabs
from pathlib import Path

import yaml
from nltk.corpus import stopwords


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
        self.dir = os.getcwd()

        formatted_ontology_file = None
        if ontology_name == 'causex':
            self.external_ontology = True
            formatted_ontology_file = './data/CauseX_Ontology.json'
        if isabs(ontology_name):
            self.external_ontology = True
            formatted_ontology_file = f'/opt/app/tmp/{Path(ontology_name).with_suffix(".json").name}'
        else:
            formatted_ontology_file = os.path.dirname(
                os.path.abspath(__file__)) + f'/data/Ontology_{ontology_name}.json'
            self.external_ontology = False

        print(f'using ontology {formatted_ontology_file}')
        if not os.path.exists(formatted_ontology_file):
            print('formatting ontology...')
            self.format_ontology(ontology_name, formatted_ontology_file)
            print('ontology formatted...')
        with open(formatted_ontology_file) as f:
            text = f.read()
            self.ontology = json.loads(text)
        indicator_path = os.path.dirname(os.path.abspath(__file__)) + '/data/Indicators_WorldBank_Full.txt'
        self.indicators_WorldBank = self.get_indicators(indicator_path)

    def get_indicators(self, path):
        f = open(path)
        text = f.read().split('\n\n')
        f.close()
        indicators = {}
        for type in text:
            terms = type.split('\n')
            indicators[terms[0]] = terms[1:]
        return indicators

    def string_matching(self, phrase, resource):
        term_scores = {}
        for key in self.indicators_WorldBank:
            terms = self.indicators_WorldBank[key]
            for term in terms:
                score = self.score(phrase, term)
                if score > 0.1:
                    term_scores[term] = score
        return term_scores

    def score(self, phrase, key_term):
        punc = string.punctuation
        stop_words = stopwords.words('english')
        phrase = str(phrase.strip(' '))
        if phrase == key_term:
            return 1.0
        elif phrase in key_term:
            return len(phrase.split(' ')) / len(key_term.split(' '))
        else:
            score = 0.0
            phrase_words = []
            for i in phrase.split(' '):
                if i not in punc and i not in stop_words:
                    phrase_words.append(i)
            for word in phrase_words:
                if word in key_term.split(' '):
                    score += 1
            return 2 * score / (len(key_term.split(' ')) + len(phrase_words))

    def refine_word(self, sentence, lemma, pos):
        # if self.externalOntology: return self.refineWord_external(sentence, lemma, pos, fnFrames)
        events1, events2, entities = self.ontology['event'], self.ontology['property'], self.ontology['entity']
        for type in events1.keys():
            if lemma in events1[type]:
                return 'event/' + type, 'event'
        for type in events2.keys():
            if lemma in events2[type]:
                return 'property/' + type, 'property'
        for type in entities.keys():
            if lemma in entities[type]:
                return type, 'entity'
        return "", ""

    def format_ontology(self, ontology_name, save_file):
        print(f'formatting ontology {ontology_name} to {save_file}')
        if isabs(ontology_name):
            file = ontology_name
        else:
            file_name = f'/data/{ontology_name}.yml'
            file = os.path.dirname(os.path.abspath(__file__)) + file_name

        with open(file) as f:
            data = yaml.full_load(f)
        data = data[0]['wm']
        path = ''
        output = {'entity': {}, 'event': {}, 'property': {}}
        output = recurse(data, path, output)
        with open(save_file, 'w') as f:
            json.dump(output, f)

        print(f'finished formatting ontology {ontology_name} to {save_file}')
        return output


def recurse(data, path, output):
    for i in range(len(data)):
        if 'OntologyNode' in data[i].keys():
            semantic_type = data[i]['semantic type']
            path_new = f"{path}/{data[i]['name']}"
            path_new = path_new.strip('/')
            output[semantic_type][path_new] = data[i]['examples']
            # return output
        else:
            k = list(data[i].keys())[0]
            data_new = data[i][k]
            path_new = f"{path}/{k}"
            path_new = path_new.strip('/')
            output_new = recurse(data_new, path_new, output)
            for j in output_new: output[j].update(output_new[j])
    return output
