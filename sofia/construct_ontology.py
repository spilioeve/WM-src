import json
from nltk.wsd import lesk
from nltk.corpus import wordnet
from nltk.corpus import wordnet_ic
from nltk.corpus import framenet as fn
import os
from sklearn.cluster import KMeans
import numpy as np
from sofia.frames_FN_mapping import FrameNetFrames

verb_tags=["VB", "VBP", "VBD", "VBZ", "VBN"] #VBN and VBG maybe?
noun_tags= ["NN", "NNS", "NNP", "NNPS", "JJ"]
project= '/Users/evangeliaspiliopoulou/Desktop/WorldModelers/South_Sudan_Famine'


def extract_Ngrams(file_name):
    print(file_name)
    jsonfile = open(project+ '/outputStanford/'+ file_name, 'r')
    jsonstr = jsonfile.read()
    data = json.loads(jsonstr)
    jsonfile.close()
    nominal_bigrams=[]
    verbs=[]
    nouns=[]
    verb_synsets=[]
    noun_synsets=[]
    for i in range(len(data['sentences'])):
        words= []
        sentence_tokens= data['sentences'][i]['tokens']
        for index in range(len(sentence_tokens)):
            word = sentence_tokens[index]['word']
            if all(ord(c) < 128 for c in word):
                words.append(str(word))
        lemma_prev= ""
        pos_prev= ""
        for index in range(len(sentence_tokens)):
            lemma= sentence_tokens[index]['lemma']
            lemma= lemma.lower()
            pos=  str(sentence_tokens[index]['pos'])
            if all(ord(c) < 128 for c in lemma):
                if pos in noun_tags:
                    if pos_prev in noun_tags:
                        nominal_bigrams.append((lemma_prev, lemma))
                        lemma_prev= lemma
                    else:
                        lemma_prev = lemma
                        pos_prev = pos
                else:
                    lemma_prev=""
                    pos_prev= ""
                if pos in verb_tags:
                    synset= lesk(words, lemma, 'v')
                    verb_synsets.append(synset)
                    verbs.append(lemma)
                elif pos in noun_tags[:-1]:
                    synset = lesk(words, lemma, 'n')
                    noun_synsets.append(synset)
                    nouns.append(lemma)
    return nominal_bigrams, verbs, nouns, verb_synsets, noun_synsets

def get_related_verbs(file_name):
    jsonfile = open(project+ '/outputStanford/'+ file_name+ '.json', 'r')
    jsonstr = jsonfile.read()
    data = json.loads(jsonstr)
    jsonfile.close()
    related_verbs={}
    file= open(project+'/OntologyFiles/NounCount.txt', 'r')
    lines= file.readlines()
    file.close()
    for line in lines:
        noun, count= line.split('\t')
        count= int(count.strip('\n'))
        if count> 6:
            related_verbs[noun]= {}
    for i in range(len(data['sentences'])):
        words= []
        target_nouns=[]
        sentence_tokens= data['sentences'][i]['tokens']
        for index in range(len(sentence_tokens)):
            word = sentence_tokens[index]['word']
            lemma = sentence_tokens[index]['lemma']
            lemma = lemma.lower()
            if lemma in related_verbs.keys():
                target_nouns.append(lemma)
            if all(ord(c) < 128 for c in word):
                words.append(str(word))
        if len(target_nouns) >0:
            for index in range(len(sentence_tokens)):
                lemma= sentence_tokens[index]['lemma']
                lemma= lemma.lower()
                pos=  str(sentence_tokens[index]['pos'])
                if all(ord(c) < 128 for c in lemma):
                    if pos in verb_tags:
                        synset= lesk(words, lemma, 'v')
                        if synset!= None:
                            for noun in target_nouns:
                                if synset not in related_verbs[noun].keys():
                                    related_verbs[noun][synset]=0
                                related_verbs[noun][synset] += 1
    file= open(project+'/OntologyFiles/NounsToVerbs.txt', 'w')
    for key in related_verbs.keys():
        file.write(str(key))
        for verb in related_verbs[key].keys():
            file.write('\t'+str(verb.name()) + '\t'+str(related_verbs[key][verb]))
        file.write('\n')
    file.close()
    return related_verbs


def order_list(list, file_name, using_synsets= False):
    dic={}
    for item in list:
        if item!= None:
            if item not in dic.keys():
                dic[item]= 0
            dic[item]+=1
    file = open(project+'/OntologyFiles/'+file_name, 'w')
    for key, value in sorted(dic.items(), key=lambda k: k[1], reverse=True):
        if using_synsets:
            definition= str(key.definition())
            lemma= str(key.name())
            file.write(lemma + '\t' + str(value)+'\t'+ definition)
        else:
            file.write(str(key) + '\t' + str(value))
        file.write('\n')
    file.close()
    print("Done writing {}".format(file_name))

def write_NGrams(file_list):
    bigrams=[]
    verb_list=[]
    noun_list=[]
    verb_synset_list=[]
    noun_synset_list=[]
    for file_name in file_list:
        bigram, verb, noun, verb_synset, noun_synset= extract_Ngrams(file_name)
        bigrams+= bigram
        verb_list+= verb
        noun_list+= noun
        verb_synset_list+= verb_synset
        noun_synset_list+= noun_synset
    order_list(bigrams, "BigramCount.txt")
    order_list(verb_list, "VerbCount.txt")
    order_list(noun_list, "NounCount.txt")
    order_list(verb_synset_list, "vSynsets.txt", using_synsets= True)
    order_list(noun_synset_list, "nSynsets.txt", using_synsets= True)

#fileList=['2017_South_Sudan_famine', 'Stunted_growth', 'Paragraphs_SSudan', 'History_Sudan_Aid', 'Monitoring_Humanitarian_Aid', 'Thesis_Sudan', 'Food_security']


def clean_text(text_init):
    ###Use BeautifulSoup to refine html. Re-write the code, see documentation to decide
    lines = (line.strip() for line in text_init.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text_init = '\n'.join(chunk for chunk in chunks if chunk)
    text=""
    for letter in text_init:
        if ord(letter)<129:
            text+= str(letter)
    return text

def get_synonyms(synset):
    semcor = wordnet_ic.ic('ic-semcor.dat')
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


def set_embeddings(embedding_file= 'embeddings.txt'):
    f=open( '/Users/evangeliaspiliopoulou/Desktop/WorldModelers/' + embedding_file)
    text= f.read()
    f.close()
    embeddings={}
    terms= text.split('\n')
    for term in terms:
        vector= term.split(' ')
        word= vector[0]
        vector= vector[1:]
        vector = [float(i) for i in vector]
        embeddings[word]= np.array(vector)
    return embeddings

def get_phrase_embeddings(phrase, embeddings):
    words= filter(lambda a: a!='', phrase.split(' '))
    vector = np.zeros(50)
    word_number=0
    for word in words:
        if word in embeddings:
            vector+= embeddings[word]
            word_number+=1
    if word_number> 0:
        vector= vector/word_number
    return vector

def set_FN_embeddings():
    embeddings={}
    frames= fn.frames()
    vector= np.zeros(len(frames))
    for i in range(len(frames)):
        name= frames[i].name
        vector_i= np.copy(vector)
        vector_i[i]= 1.0
        embeddings[name]= vector_i
    return embeddings, len(frames)

def get_FN_embeddings(frame_list, fn_embeddings, dim):
    # frames = fn.frames()
    vector = np.zeros(dim)
    if len(frame_list)==0:
        return vector
    for frame in frame_list:
        vector_i= fn_embeddings[frame]
        vector+= vector_i
    if len(frame_list)> 0:
        vector= vector/len(frame_list)
    return vector

def cluster_words(path, using_FN=True):
    embeddings= set_embeddings('embeddings.txt')
    dim=50
    if using_FN:
        FrameNet= FrameNetFrames()
        fn_embeddings, fn_dim= set_FN_embeddings()
        dim+= fn_dim
    inverse_embeddings={}
    f= open(path+ 'NounCount.txt')
    words= f.read().split('\n')
    f.close()
    f = open(path + 'VerbCount.txt')
    words+= f.read().split('\n')
    f.close()
    word_vectors = np.zeros(dim)
    for item in words:
        word, ccount= item.split('\t')
        word_embedding = get_phrase_embeddings(word, embeddings)
        if using_FN:
            frames= FrameNet.get_phrase_frames(word)
            word_embedding = np.append(word_embedding, get_FN_embeddings(frames, fn_embeddings, fn_dim))
        word_vectors= np.vstack([word_vectors, word_embedding])
        if str(word_embedding) not in inverse_embeddings:
            inverse_embeddings[str(word_embedding)]= word
    f= open(path+'Variables_Len4.txt')
    variables= f.read().split('\n')
    f.close()
    variable_vectors=np.zeros(dim)
    for variable in variables:
        variable= variable.lower()
        variable_embedding= get_phrase_embeddings(v, embeddings)
        if using_FN:
            frames= FrameNet.get_phrase_frames(variable)
            variable_embedding = np.append(variable_embedding, get_FN_embeddings(frames, fn_embeddings, fn_dim))
        variable_vectors= np.vstack([variable_vectors, variable_embedding])
        if str(variable_embedding) not in inverse_embeddings:
            inverse_embeddings[str(variable_embedding)]= variable
    return variable_vectors, word_vectors, inverse_embeddings

def run_K_means(X, Y, inverse_embeddings, joint=False):
    if joint:
        kmeans = KMeans(n_clusters=100, random_state=0).fit(np.vstack([X, Y]))
    else:
        kmeans = KMeans(n_clusters=100, random_state=0).fit(X)
    Y_pred= kmeans.predict(Y)
    clusters= {i: {'X':[], 'Y':[]} for i in range(101)}
    for i in range(len(X)):
        if str(X[i]) in inverse_embeddings:
            word= inverse_embeddings[str(X[i])]
            label= kmeans.labels_[i]
            clusters[label]['X'].append(word)
    for i in range(len(Y_pred)):
        if str(Y[i]) in inverse_embeddings:
            word = inverse_embeddings[str(Y[i])]
            label = Y_pred[i]
            clusters[label]['Y'].append(word)
    return clusters


file_list= set(os.listdir(project+ '/outputStanford'))
file_list= file_list- {'.DS_Store'}
write_NGrams(file_list)
#relatedVerbList(fileList[0])
###Use command line or whatever function in order to cluster words
