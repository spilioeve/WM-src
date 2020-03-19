

verb_tags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"]

class DataExtractor:
    def __init__(self, annotations):
        self.annotations = annotations
        self.structuredData, self.sentences= self.structure_data()

    def structure_data(self):
        sentences=[]
        structured_data=[]
        data = self.annotations
        for i in range(len(data['sentences'])):
            dep = data['sentences'][i]['enhancedPlusPlusDependencies']
            sentTokens= data['sentences'][i]['tokens']
            parse= data['sentences'][i]['parse']
            sentence= ""
            pos=[]
            tokens=[]
            lemmas=[]
            spans=[]
            time = ""
            loc = ""
            prev=0
            for index in range(len(sentTokens)):
                lemma= sentTokens[index]['lemma']
                lemma= lemma.lower()
                token= sentTokens[index]['originalText']
                try:
                    sentence+=  str(token)+ ' '
                except:
                    pass
                pos.append(str(sentTokens[index]["pos"]))
                start= int(sentTokens[index]["characterOffsetBegin"])
                end= int(sentTokens[index]["characterOffsetEnd"])
                tokens.append({"start": start, "end": end, "token":token, "lemma": lemma, 'pos': str(sentTokens[index]["pos"])})
                ner= sentTokens[index]["ner"]
                if str(ner)== "DATE":
                    time+= token +', '
                elif str(ner)== "LOCATION":
                    if index -prev>1:
                        loc+= ','
                    loc+= ' '+ token
                    prev=index
                lemmas.append(lemma)
                spans.append((start, end))
            time=time.strip(', ')
            loc= loc.strip(', ')
            noun_phrases= self.process_parse(parse, tokens)
            sentence_data = {"tokens": tokens, "lemmas": lemmas, "pos": pos, "location": loc, "temporal": time,
                             "NPs": noun_phrases, "deps": dep, "sentence": sentence, "spans": spans}
            sentences.append(sentence)
            structured_data.append(sentence_data)
        return structured_data, sentences

    def process_parse(self, parse, mapping):
        noun_phrases={}
        for line in parse.split('\n'):
            s= line.split('(')
            head= str(s[1]).strip(' ')
            if head== 'NP' and ')' in line:
                if len(s) < 4 and 'DT' in line:
                    continue
                phrase=""
                for item in s[2:]:
                    w = item.strip(') ').split(' ')[1]
                    phrase+= w+' '
                phrase=phrase.strip(' ')
                start_index, end_index= self.find_nominal_term(mapping, phrase.split(' '), 'token')
                start= mapping[start_index]['start']
                end= mapping[end_index-1]['end'] ##Changed to endIndex-1 from endIndex???
                lemma= mapping[end_index-1]['lemma']
                nounP=""
                qualifier= ""
                text=""
                eventuality={}
                for item in mapping[start_index:end_index]:
                    text+= item['token']+ ' '
                    if item['pos']== verb_tags:
                        eventuality= {'token': item['token'], 'start': item['start'], 'end':item['end'], 'lemma': item['lemma']}
                    # TODO: Keep only qualifier wrt quantity. Find a way to filter those from the Adjectives?
                    elif item['pos']== 'JJ' or item['pos']=='JJS':
                        qualifier+= item['token'] +' '
                    elif item['pos']== 'CD':
                        qualifier += item['token'] + ' '
                    else:
                        nounP+= item['token']+ ' '
                nounP= nounP.strip(' ')
                text=text.strip(' ')
                noun_phrases[start]= {'text': text, 'start': start, 'end': end, 'token': nounP, 'head_lemma': lemma,
                                 'eventuality': eventuality, 'qualifier': qualifier.strip()}
        merged_noun_phrases= self.merge_neighbour_phrases(noun_phrases)
        return merged_noun_phrases

    def merge_neighbour_phrases(self, phrases):
        if len(phrases)==0:
            return []
        merged_phrases=[]
        indices= list(phrases.keys())
        indices.sort()
        start_prev= indices[0]
        end_prev= phrases[start_prev]['end']
        phrase_prev= phrases[start_prev]
        for start in indices[1:]:
            phrase_curr= phrases[start]
            if start- end_prev<3:
                for i in (phrase_curr.keys()- {'start', 'end', 'eventuality'}):
                    phrase_prev[i] = str.join(' ', [phrase_prev[i], phrase_curr[i]]).strip()
                phrase_prev['end']= phrase_curr['end']
                if 'eventuality' in phrase_prev:
                    phrase_prev['eventuality'].update(phrase_curr['eventuality'])
            elif phrase_prev['token']!= '':
                merged_phrases.append(phrase_prev)
                phrase_prev=phrase_curr
        if phrase_prev not in merged_phrases and phrase_prev['token']!= '':
            merged_phrases.append(phrase_prev)
        return merged_phrases

    def find_nominal_term(self, my_list, phrase, key):
        index = 0
        while index < len(my_list):
            phraseIndex = 0
            while my_list[index][key] == phrase[phraseIndex]:
                index += 1
                phraseIndex += 1
                if phraseIndex == len(phrase):
                    return index - phraseIndex, index
            if phraseIndex < len(phrase):
                index -= phraseIndex - 1
        return 0, 0

    def get_sentence_data(self, index):
        return self.structuredData[index]

    def get_data_size(self):
        return len(self.structuredData)

    def get_dependencies(self, index):
        return self.structuredData[index]["deps"]

    def get_lemmas(self, index):
        return self.structuredData[index]["lemmas"]

    def get_pos_tags(self, index):
        return self.structuredData[index]["pos"]

    def get_tokens(self, index):
        return self.structuredData[index]["tokens"]

    def get_sentence_span(self, index):
        data= self.structuredData[index]
        spans= data['spans']
        return (spans[0][0], spans[-1][1])
