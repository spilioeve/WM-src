import json
from nltk.wsd import lesk
from nltk.corpus import wordnet
from nltk.corpus import wordnet_ic

verbTags=["VB", "VBP", "VBD", "VBZ", "VBN"] #VBN and VBG maybe?
nounTags= ["NN", "NNS", "NNP", "NNPS", "JJ"]
project= '/Users/evangeliaspiliopoulou/Desktop/WorldModelers/AIDA'
semcor= wordnet_ic.ic('ic-semcor.dat')

def extractNgrams(file):
    print file
    jsonfile = open(project+ '/outputStanford/'+ file+ '.json', 'r')
    jsonstr = jsonfile.read()
    data = json.loads(jsonstr)
    jsonfile.close()
    nomBigrams=[]
    verbs=[]
    nouns=[]
    vSynsets=[]
    nSynsets=[]
    for i in range(len(data['sentences'])):
        tokens= []
        sentTokens= data['sentences'][i]['tokens']
        for index in range(len(sentTokens)):
            token = sentTokens[index]['word']
            if all(ord(c) < 128 for c in token):
                tokens.append(str(token))
        prevLemma= ""
        prevPos= ""
        for index in range(len(sentTokens)):
            lemma= sentTokens[index]['lemma']
            lemma= lemma.lower()
            pos=  str(sentTokens[index]['pos'])
            if all(ord(c) < 128 for c in lemma):
                if pos in nounTags:
                    if prevPos in nounTags:
                        nomBigrams.append((prevLemma, lemma))
                        prevLemma= lemma
                    else:
                        prevLemma = lemma
                        prevPos = pos
                else:
                    prevLemma=""
                    prevPos= ""
                if pos in verbTags:
                    synset= lesk(tokens, lemma, 'v')
                    vSynsets.append(synset)
                    verbs.append(lemma)
                elif pos in nounTags[:-1]:
                    synset = lesk(tokens, lemma, 'n')
                    nSynsets.append(synset)
                    nouns.append(lemma)
    return nomBigrams, verbs, nouns, vSynsets, nSynsets

def relatedVerbList(file):
    jsonfile = open(project+ '/outputStanford/'+ file+ '.json', 'r')
    jsonstr = jsonfile.read()
    data = json.loads(jsonstr)
    jsonfile.close()
    relVerbs={}
    nFile= open(project+'/OntologyFiles/NounCount.txt', 'r')
    nLines= nFile.readlines()
    nFile.close()
    for line in nLines:
        noun, count= line.split('\t')
        count= int(count.strip('\n'))
        if count> 6:
            relVerbs[noun]= {}
    for i in range(len(data['sentences'])):
        tokens= []
        targetFound= False
        targetN=[]
        sentTokens= data['sentences'][i]['tokens']
        for index in range(len(sentTokens)):
            token = sentTokens[index]['word']
            lemma = sentTokens[index]['lemma']
            lemma = lemma.lower()
            if lemma in relVerbs.keys():
                targetFound= True
                targetN.append(lemma)
            if all(ord(c) < 128 for c in token):
                tokens.append(str(token))
        if targetFound:
            for index in range(len(sentTokens)):
                lemma= sentTokens[index]['lemma']
                lemma= lemma.lower()
                pos=  str(sentTokens[index]['pos'])
                if all(ord(c) < 128 for c in lemma):
                    if pos in verbTags:
                        synset= lesk(tokens, lemma, 'v')
                        if synset is None:
                            pass
                        else:
                            for noun in targetN:
                                dic= relVerbs[noun]
                                if synset in dic.keys():
                                    dic[synset]+= 1
                                else:
                                    dic[synset]= 1
    dictFile= open(project+'/OntologyFiles/NounsToVerbs.txt', 'w')
    for key in relVerbs.keys():
        dictFile.write(str(key))
        for verb in relVerbs[key].keys():
            dictFile.write('\t'+str(verb.name()) + '\t'+str(relVerbs[key][verb]))
        dictFile.write('\n')
    dictFile.close()
    return relVerbs



def orderList(list, fileName, synset= False):
    dic={}
    for item in list:
        if item is None:
            pass
        elif item in dic.keys():
            dic[item]+= 1
        else:
            dic[item]=1
    file = open(project+'/OntologyFiles/'+fileName, 'w')
    if not synset:
        for key, value in sorted(dic.iteritems(), key=lambda (k, v): (v, k), reverse=True):
            file.write(str(key) + '\t' + str(value))
            file.write('\n')
    else:
        for key, value in sorted(dic.iteritems(), key=lambda (k, v): (v, k), reverse=True):
            definition= str(key.definition())
            lemma= str(key.name())
            file.write(lemma + '\t' + str(value)+'\t'+ definition)
            file.write('\n')

    file.close()
    print "Done writing "+ fileName

def cleanText(text):
    ###Use BeautifulSoup to refine html. Re-write the code, see documentation to decide
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    fText=""
    for letter in text:
        if ord(letter)<129:
            fText+= str(letter)
    return fText

def getAllSynonyms(synset):
    synonyms=[]
    w1 = wordnet.synset(synset)
    for w2 in wordnet.all_synsets():
        try:
            sim = w1.jcn_similarity(w2, semcor)
        except:
            sim= 0.0
        if sim>0.2:
            synonyms.append(w2)
    return synonyms

def writeNGramLists(fileList):
    bigrams=[]
    vList=[]
    nList=[]
    vSynList=[]
    nSynList=[]
    for file in fileList:
        b, v, n, vS, nS= extractNgrams(file)
        bigrams+= b
        vList+= v
        nList+= n
        vSynList+= vS
        nSynList+= nS
    orderList(bigrams, "BigramCount.txt")
    orderList(vList, "VerbCount.txt")
    orderList(nList, "NounCount.txt")
    orderList(vSynList, "vSynsets.txt", synset= True)
    orderList(nSynList, "nSynsets.txt", synset= True)

#fileList=['2017_South_Sudan_famine', 'Stunted_growth', 'Paragraphs_SSudan', 'History_Sudan_Aid', 'Monitoring_Humanitarian_Aid', 'Thesis_Sudan', 'Food_security']
fileList=['bellingcat_report']
#writeNGramLists(fileList)
relatedVerbList(fileList[0])
