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
            time = ""
            loc = ""
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
                tokens.append({"start": start, "end": end, "token":token, 'lemma': lemma})
                ner= sentTokens[index]["ner"]
                if str(ner)== 'DATE':
                    time+= " " + token
                elif str(ner)== "LOCATION":
                    loc+= " "+ token
                lemmas.append(lemma)
                #ner= str(sentTokens[index]['ner'])
                #mapping.append({"start": start, "end": end, "pos": pos, "lemma": lemma, "index": ind, "token": token})
            nounPhrases= self.processParse(parse, tokens)
            sentData = {"tokens": tokens, "lemmas": lemmas, "pos": pos, "location": loc, "temporal": time, "NPs": nounPhrases, "deps": dep, "sentence": sentence}
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
                end= mapping[endIndex]['end']
                lemma= mapping[endIndex]['lemma']
                qualifier= ""
                eventuality=""
                for item in mapping[startIndex:endIndex+1]:
                    if item['pos']== verbTags:
                        eventuality= item['token']
                    elif item['pos']== 'JJ':
                        qualifier= item['token']
                nPhrases.append({'start': start, 'end': end, 'token': phrase, 'headLemma': lemma, 'eventuality': eventuality, 'qualifier': qualifier})
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


def proc(parse):
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
            nPhrases.append(phrase)
    return nPhrases
