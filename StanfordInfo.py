import json
import string

verbTags=["VB", "VBP", "VBD", "VBZ", "VBN", "VBG"]

class DataExtractor:
    def __init__(self, file, dir):
        self.file = file
        self.dir = dir
        self.structuredData=[]
        self.getInfoStanford()

    def getInfoStanford(self):
        jsonfile = open(self.dir + '/outputStanford/'+ self.file+ '.json', 'r')
        jsonstr = jsonfile.read()
        data = json.loads(jsonstr)
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
                pos.append(str(sentTokens[index]['pos']))
                #ind= int(sentTokens[index]['index'])
                start= int(sentTokens[index]["characterOffsetBegin"])
                end= int(sentTokens[index]["characterOffsetEnd"])
                tokens.append({"start": start, "end": end, "token":token, 'lemma': lemma, 'pos': str(sentTokens[index]['pos'])})
                ner= sentTokens[index]["ner"]
                if str(ner)== 'DATE':
                    time+= token +', '
                elif str(ner)== "LOCATION":
                    if index -prev>1:
                        loc+= ','
                    loc+= ' '+ token
                    prev=index
                lemmas.append(lemma)
                spans.append((start, end))
                #ner= str(sentTokens[index]['ner'])
                #mapping.append({"start": start, "end": end, "pos": pos, "lemma": lemma, "index": ind, "token": token})
            time=time.strip(', ')
            loc= loc.strip(', ')
            nounPhrases= self.processParse(parse, tokens)
            sentData = {"tokens": tokens, "lemmas": lemmas, "pos": pos, "location": loc, "temporal": time, "NPs": nounPhrases, "deps": dep, "sentence": sentence, 'spans': spans}
            #sentData.setNER(ner)
            self.structuredData.append(sentData)

    def getDataPerSentence(self, index):
        return self.structuredData[index]


    def getDataSize(self):
        return len(self.structuredData)

    def getDependencies(self, index):
        return self.structuredData[index]["deps"]

    def processParse(self, parse, mapping):
        nPhrases=[]
        for line in parse.split('\n'):
            s= line.split('(')
            head= str(s[1]).strip(' ')
            if head== 'NP' and ')' in line:
                phrase=""
                for item in s[2:]:
                    w = item.strip(') ').split(' ')[1]
                    phrase+= w+' '
                phrase=phrase.strip(' ')
                #nPhrases.append(phrase)
                startIndex, endIndex= self.findTerm(mapping, phrase.split(' '), 'token')
                start= mapping[startIndex]['start']
                end= mapping[endIndex-1]['end'] ##Changed to endIndex-1 from endIndex???
                lemma= mapping[endIndex-1]['lemma']
                nounP=""
                qualifier= ""
                text=""
                eventuality={}
                for item in mapping[startIndex:endIndex]:
                    text+= item['token']+ ' '
                    if item['pos']== verbTags:
                        eventuality= {'token': item['token'], 'start': item['start'], 'end':item['end'], 'lemma': item['lemma']}
                    elif item['pos']== 'JJ' or item['pos']=='JJS':
                        qualifier= item['token']
                    else:
                        nounP+= item['token']+ ' '
                nounP= nounP.strip(' ')
                text=text.strip(' ')
                nPhrases.append({'text': text, 'start': start, 'end': end, 'token': nounP, 'headLemma': lemma, 'eventuality': eventuality, 'qualifier': qualifier})
        return nPhrases


    def findTerm(self, myList, phrase, key):
        index = 0
        while index < len(myList):
            phraseIndex = 0
            while myList[index][key] == phrase[phraseIndex]:
                index += 1
                phraseIndex += 1
                if phraseIndex == len(phrase):
                    return index - phraseIndex, index
            if phraseIndex < len(phrase):
                index -= phraseIndex - 1
        return 0, 0


# def proc(parse):
#     nPhrases=[]
#     for line in parse.split('\n'):
#         s= line.split('(')
#         head= str(s[1]).strip(' ')
#         if head== 'NP' and ')' in line:
#             phrase=""
#             for item in s[2:]:
#                 w = item.strip(') ').split(' ')[1]
#                 phrase+= w+' '
#             phrase=phrase.strip(' ')
#             nPhrases.append(phrase)
#     return nPhrases
