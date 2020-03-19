from sofia.corenlp_parse import DataExtractor

class QueryFinder:

    def __init__(self, annotations, query):
        self.annotations = annotations
        self.query= query
        self.report_frames=['Communication', 'Text_creation', 'Statement', 'Warning' , 'Indicating', 'Cogitation']

    def find_query(self):
        targets=[]
        data_extractor= DataExtractor(self.annotations)
        sentences= data_extractor.sentences
        if self.query=='':
            return sentences
        for s_index in range(len(sentences)):
            sentence= sentences[s_index]
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
                targets.append(s_index)
        return targets

    def rank_node(self, node, type, sentence):
        node_score=0.0
        l= len(sentence.split(' '))
        if l < 10:
            node_score+= 20
        elif l<15:
            node_score+= 15
        elif l< 20:
            node_score +=10
        if type== 'entity' or type== 'event':
            if node['frame_FN']=='':
                pass
            elif len(set(node['frame_FN']).intersection(set(self.report_frames)))>0:
                node_score+= 5
            else:
                node_score+= 15
            if node['frame']!= '':
                node_score+= 25
            if node['trigger'] == self.query:
                node_score+= 40
            elif self.query in node['trigger']:
                node_score+= 40
            else:
                node_score+= 10
            return node_score/100.0
        event_scores, cause, effect= node
        cause_score= 0.
        effect_score=0.
        cause= cause.split(', ')
        effect = effect.split(', ')
        for i in cause:
            if event_scores[i]>cause_score:
                cause_score= event_scores[i]
        for i in effect:
            if event_scores[i]>effect_score:
                effect_score= event_scores[i]
        return effect_score * cause_score




