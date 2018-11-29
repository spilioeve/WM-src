from StanfordInfo import DataExtractor
# from ManualRules import CandidateEvents
# from OntologyMapping import Ontology
# from CausalityDetection import RSTModel
import wikipedia

class IndicatorSearch:

    def __init__(self, file, dir, query):
        self.file= file
        self.dir= dir
        self.query= query
        self.reportFrames=['Communication', 'Text_creation', 'Statement', 'Warning' , 'Indicating', 'Cogitation']
        # self.Ontology= Ontology(dir)
        # self.indicators= self.Ontology.indicatorsWorldBank
        #self.indicators= indicators

    def findQuery(self):
        targets=[]
        #i_extractor= CandidateEvents(file, self.dir)
        i_extractor= DataExtractor(self.file, self.dir)
        sentences= i_extractor.sentences
        if self.query=='':
            return sentences
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

    def rankNode(self, node, type, sentence):
        score=0.0
        l= len(sentence.split(' '))
        if l < 10:
            score+= 20
        elif l<15:
            score+= 15
        elif l< 20:
            score +=10
        if type== 'entity' or type== 'event':
            ##Too slow so had to delete that!!!
            # try:
            #     wiki = wikipedia.search(node['trigger'])
            # except:
            #     wiki=[]
            if node['FrameNetFr']=='':
                pass
            elif len(set(node['FrameNetFr']).intersection(set(self.reportFrames)))>0:
                score+= 5
            else:
                score+= 15
            if node['frame']!= '':
                score+= 25
            if node['trigger'] == self.query:
                score+= 40
            elif self.query in node['trigger']:
                score+= 40
            else:
                score+= 10
            # if len(wiki)>0:
            #     score+= 20
            return score/100.0
        eventScores, causes, effects= node
        cScore= 0.
        eScore=0.
        causes= causes.split(', ')
        effects = effects.split(', ')
        for i in causes:
            if eventScores[i]>cScore:
                cScore= eventScores[i]
        for i in effects:
            if eventScores[i]>eScore:
                eScore= eventScores[i]
        return eScore * cScore




