class Ontology:

    def __init__(self, file, dir):
        self.file= file
        self.dir= dir
        data1= self.getOntologyManualData()
        data2= self.getOntologyAutoData()


    def getOntologyManualData(self):
        return {}

    def getOntologyAutoData(self):
        return {}

    def getClass(self, lemma, pos):
        return 'None'
