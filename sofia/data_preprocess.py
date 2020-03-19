import string
import enchant
from nltk.tokenize import sent_tokenize
import PyPDF2
import os

#d=  enchant.Dict("en_US")

def remove_empty_lines(text_init):
    lines=text_init.split('\n')
    new_lines=[]
    for line in lines:
        line=line.strip('\n')
        if len(line)>10:
            new_lines.append(line)
    return '\n'.join(new_lines)

def clean_text(text_init):
    text_init= remove_empty_lines(text_init)
    sentences = sent_tokenize(text_init)
    text=""
    for sentence in sentences:
        for letter in sentence:
            if ord(letter) < 128:
                if letter != '\n':
                    text += letter
        if len(sentence)>0 and sentence[-1]!= '.':
                text+= '.'
        text+= '\n'
    lines = text.split('\n')
    text_final = ""
    for line in lines:
        line = line.strip('\n')
        sentence = line.strip(' ')
        if len(sentence.split(' ')) > 30:
            if '\n' in sentence:
                i = sentence.index('\n')
                text_final +=  sentence[:i] + '. ' + sentence[i:]
        elif len(sentence.split(' ')) > 4:
            text_final += sentence + '\n'
    return text_final


def preprocess_docs(doc_list, path):
    for doc in doc_list:
        print(doc)
        f=open(path+doc)
        text_init=f.read()
        f.close()
        clean_doc= clean_text(text_init)
        f = open(path + doc, 'w')
        f.write(clean_doc)
        f.close()

def pdf2text(path):
    files = os.listdir(path)
    for f in files:
        try:
            pdfFileObj = open(path+ '/' + f, 'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            text = ""
            for page in range(pdfReader.numPages):
                text += pdfReader.getPage(page).extractText()
            f=f.strip('.pdf')
            file = open(path+'_text/' + f+'.txt', 'w')
            file.write(text)
            file.close()
        except:
            print('Non-parsed...')
        print(f)

def remove_annotations(text_init, limit_left, limit_right):
    annotation_spans={}
    text= ''
    i=0
    new_i=0
    while i< len(text_init):
        letter_curr= text_init[i]
        if limit_left== letter_curr:
            annotation= letter_curr
            loop= True
            loop2 = True
            start=0
            end=1
            while loop:
                i += 1
                letter_curr = text_init[i]
                annotation+= letter_curr
                if limit_right== letter_curr and loop2:
                    i+=1
                    letter_curr = text_init[i]
                    annotation += letter_curr
                    start = new_i
                    while loop2:
                        if limit_left== letter_curr:
                            loop2=False
                            end= new_i
                            new_i-=1
                        else:
                            text += letter_curr
                            i += 1
                            new_i += 1
                            letter_curr = text_init[i]
                            annotation += letter_curr
                elif limit_right== letter_curr:
                    loop= False
                    annotation_spans[(start, end)] = annotation
        else:
            text+= letter_curr
        i += 1
        new_i += 1
    return text, annotation_spans