import ast
import string
import os

class Ontology:

    def __init__(self):
        #self.dir= os.path.dirname(os.getcwd())
        self.dir= os.getcwd()
        self.file = '/sofia/Ontology_v2.txt'
        self.ontology= self.getOntologyManualData()
        self.indicatorsWorldBank= self.getIndexes('/sofia/Indicators_WorldBank_Full.txt')
        #data2= self.getOntologyAutoData()


    def getOntologyManualData(self):
        f= open(self.dir+self.file)
        text= f.read()
        data=ast.literal_eval(text)
        f.close()
        return data
        #    data['events1'], data['events2'], data['entities']

    def getOntologyAutoData(self):
        return {}

    def getClass(self, lemma, pos):
        return 'None'

    def getIndexes(self, path):
        f= open(self.dir+ path)
        text= f.read().split('\n\n')
        f.close()
        indicators={}
        for type in text:
            terms= type.split('\n')
            indicators[terms[0]]= terms[1:]
        return indicators

    def stringMatching(self, phrase, resource):
        #if resource== 'WorldBank':
        ontology= self.indicatorsWorldBank
        scorer={}
        for key in ontology.keys():
            terms= ontology[key]
            for term in terms:
                score= self.score(phrase, term)
                if score>0.1:
                    scorer[term]= score
        return scorer

    def score(self, phrase, term):
        punc= string.punctuation
        stopWords= ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now']
        phrase= str(phrase.strip(' '))
        if phrase == term:
            return 1.0
        elif phrase in term:
            return len(phrase.split(' '))/ len(term.split(' '))
        else:
            score=0.0
            words= []
            p= phrase.split(' ')
            for i in p:
                if i not in punc and i not in stopWords:
                    words.append(i)
            tWords= term.split(' ')
            for i in words:
                if i in tWords:
                    score+=1
            return 2*score / (len(tWords)+ len(words))

    # def writeOntology(self, data, headers):
    #     f= open(self.ontology, 'w')
    #
    #     return 0

    # def ontologyTerm(self, lemma):
    #     if lemma in self.ontology:
    #         return True
    #     return False

    def refineWord(self, sentence, lemma, pos):
        events1, events2, entities= self.ontology['events1'], self.ontology['events2'], self.ontology['entities']
        for type in events1.keys():
            if lemma in events1[type]:
                return True, 'event1/'+type, 'event1'
        for type in events2.keys():
            if lemma in events2[type]:
                return True, 'event2/'+type, 'event2'
        for type in entities.keys():
            if lemma in entities[type]:
                return False, type, 'entity'
        return False, "", ""
