from StanfordInfo import DataExtractor
# from ManualRules import CandidateEvents
# from OntologyMapping import Ontology
# from CausalityDetection import RSTModel

class IndicatorSearch:

    def __init__(self, file, dir, query):
        self.file= file
        self.dir= dir
        self.query= query
        # self.Ontology= Ontology(dir)
        # self.indicators= self.Ontology.indicatorsWorldBank
        #self.indicators= indicators

    def findQuery(self):
        targets=[]
        #i_extractor= CandidateEvents(file, self.dir)
        i_extractor= DataExtractor(self.file, self.dir)
        sentences= i_extractor.sentences
        for s in range(len(sentences)):
            #sentence= i_extractor.getSentence(s)
            sentence= sentences[s]
            if self.query in sentence:
                # events2, events, entities = i_extractor.classifyNominals(s)
                # events2, events = i_extractor.getVerbEvents(s, events2, events, entities)
                # entLocalIndex = {}
                # entIndex=1
                # for span in entities.keys():
                #     entLocalIndex[span] = 'N' + str(entIndex - 1)
                #     entIndex+=1
                # rst = RSTModel(events, eventLocalIndex, entities, entLocalIndex, sentence, lemmas, pos)
                # causalRel = rst.getCausalNodes()  ### OR TRUE
                #sentences_index.append(s)
                targets.append(s)
        return targets
