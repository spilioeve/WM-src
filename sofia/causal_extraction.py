
verb_tags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"]

class CausalLinks:

    def __init__(self, events, event_local_index, events2, entities, entity_local_index, sentence, lemmas, pos,
                 event_scores, entity_scores):
        self.sentence= sentence
        self.tokens= self.sentence.split(' ')
        self.events = events
        self.events2 = {}
        #Fix that? Delete events[e] where e is in events2?
        for span in events2:
            event = events[span]
            del self.events[span]
            self.events2[span] = event
        self.triggers= self.detect_causal_triggers(lemmas, pos)
        self.bounds= self.set_bounds()
        self.event_index= event_local_index
        self.entities= entities
        self.entity_index= entity_local_index
        self.report_frames = ['Communication', 'Text_creation', 'Statement', 'Warning', 'Indicating', 'Cogitation']
        self.event_scores= event_scores
        self.entity_scores= entity_scores


    def format(self, keys):
        event_index=""
        event_text=""
        bestScore = -1.0
        for span in self.event_index.keys():
            if span in keys:
                index= self.event_index[span]
                if self.event_scores[index] > bestScore:
                    bestScore = self.event_scores[index]
                    event_index = index
                    event_text = self.events[span]['trigger']
        return event_index, event_text

    def detect_causal_triggers(self, lemmas, pos):
        triggers=[]
        if len(self.events)<2:
            return []
        # Hard Triggers
        causal={'CauseEffect':['impact', 'affect', 'drive', 'lead', 'result'], 'EffectCause':['because', 'due']}
        ##Add constraint that preventive triggers must also be verbs???
        # What about correlation triggers?
        ## Soft triggers
        preventive = ['prevent', 'limit', 'restrict', 'constrain', 'block', 'bind', 'regulate']
        # Hard or soft?
        correlation = ['relate', 'influence', 'correlate']
        for index in range(len(lemmas)):
            lemma= lemmas[index]
            if lemma in causal['CauseEffect']:
                if 'by' in lemmas[index+1:]:
                    triggers.append((index, "right", 'CausalRelation'))
                else:
                    triggers.append((index, "left", 'CausalRelation'))
            elif lemma in causal['EffectCause']:
                triggers.append((index, 'right', 'CausalRelation'))
            elif lemma in preventive:
                if pos[index] in verb_tags:
                    if 'by' in lemmas[index + 1:]:
                        triggers.append((index, "right", 'PreventRelation'))
                    else:
                        triggers.append((index, "left", 'PreventRelation'))
            elif lemma in correlation:
                triggers.append((index, "left", 'CorrelateRelation'))
        for span in self.events2:
            index=self.events2[span]['index']
            triggers.append((index, "left", "Catalyst/Mitigator/Precondition"))
        return triggers

    def set_bounds(self):
        bounds={}
        bound_index = [0, len(self.tokens)]
        for trigger in self.triggers:
            index= trigger[0]
            bound_index.append(index)
            bounds[index]= {"trigger": trigger}
        bound_index.sort()
        for i in range(1, len(bound_index)-1):
            bound= bound_index[i]
            prev= bound_index[i-1]
            next= bound_index[i+1]
            bounds[bound].update({'curr': bound, "prev": prev, "next": next})
        return bounds

    def get_causal_nodes(self, entity_replacement=False):
        ##Use also Entities as potential nodes, in case that we cannot locate an Event as cause/effect
        causal_links=[]
        for b in self.bounds.keys():
            bound= self.bounds[b]
            trigger, direction, causal_type= bound['trigger']
            cause, effect= self.locate_events(bound, direction) ##Left is default: cause, relation, effect
            cause_index, cause_text = self.format(cause)
            effect_index, effect_text= self.format(effect)
            if entity_replacement:
                if len(effect_index)== 0:
                    cause, effect = self.locate_events(bound, direction)
                    effect_index, effect_text = self.format(effect)
                elif len(cause_index)==0:
                    cause, effect = self.locate_events(bound, direction)
                    cause_index, cause_text = self.format(cause)
            if cause_index!= '' and effect_index!= '':
                trigger_text= self.tokens[trigger]
                causal_links.append({'trigger': trigger_text, 'cause': (cause_index, cause_text),
                                  'effect': (effect_index, effect_text), 'type': causal_type})
        return causal_links

    def locate_events(self, bound, direction):
        keys = self.events.keys()
        left_events=[]
        right_events=[]
        for span in keys:
            event = self.events[span]
            #index = self.sentence.index(event['trigger'])
            event_text= event['trigger'].split(' ')[0]
            index= self.tokens.index(event_text)
            if len(set(event['frame_FN']).intersection(set(self.report_frames))) >0:
                continue
            if index>bound['prev'] and index<bound['next']:
                if index<bound['curr']:
                    left_events.append(span)
                elif index>bound['curr']:
                    right_events.append(span)
        if direction=='left':
            return left_events, right_events
        return right_events, left_events