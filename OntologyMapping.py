import ast

class Ontology:

    def __init__(self, dir):
        self.dir= dir
        self.file = '/OntologyFiles/Ontology_v2.txt'
        self.ontology= self.getOntologyManualData()
        #data2= self.getOntologyAutoData()


    def getOntologyManualData(self):
        f= open(self.dir+'/'+self.file)
        text= f.read()
        data=ast.literal_eval(text)
        f.close()
        return data
        #    data['events1'], data['events2'], data['entities']

    def getOntologyAutoData(self):
        return {}

    def getClass(self, lemma, pos):
        return 'None'


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
                return True, type
        for type in events2.keys():
            if lemma in events2[type]:
                return True, type
        for type in entities.keys():
            if lemma in entities[type]:
                return False, type
        return False, ""
