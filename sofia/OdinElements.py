import os
import subprocess

class OdinRead:

    def __init__(self, inputDoc):
        self.document= inputDoc
        self.path= os.getcwd()
        self.annotations={}


    #def getAnnotations(self):
    def preprocess(self, text):
        text = str(text)
        paragraphs= text.split('\n')
        fText=""
        for item in paragraphs:
            item= item.strip('\n')
            fText+= item+ ' '
        return fText


    def annotateDocument(self):
        f= open(self.document)
        text= f.read()
        f.close()
        text= self.preprocess(text)
        dir = os.path.dirname(self.path) + '/Eidos/eidos-master'
        os.chdir(dir)
        p = subprocess.Popen(['./shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout=  p.communicate(input= text +'\n:exit\n')
        os.chdir(self.path)
        annotations= self.getAnnotations()
        return annotations

    def getAnnotations(self):
        data=[]
        dir = os.path.dirname(self.path) + '/Eidos/eidos-master'
        f = open(dir+'/Eidos_Output.txt')
        output = f.read()
        f.close()
        output= output.strip('\n')
        sentences= output.split('\n\n')
        for index in range(len(sentences)):
            content= sentences[index]
            entIndex = content.index('entities:')
            relIndex = content.index('events:')
            entContent= content[entIndex:relIndex-1].split('\n')[1:]
            relContent= content[relIndex:].split('\n')[1:]
            entities=[]
            relations=[]
            quantifiers=[]
            misc= [] ###Just in case, erase it later once I config the code exactly
            for term in entContent:
                type= term.split('=>')
                if type[0]== 'Quantifier':
                    quantifiers.append(type[1])
                elif type[0]== 'NounPhrase,Entity':
                    entities.append(type[1])
                else:
                    misc.append(type[1])
            for term in relContent:
                EDic={}
                items= term.split('\t')
                for item in items:
                    i= item.split('=>')
                    EDic[i[0]]= i[-1]
                if 'cause' in EDic.keys() and 'effect' in EDic.keys():
                    relations.append(EDic)
            data.append({'entities': entities, 'quantifiers': quantifiers, 'CauseRelations': relations})
        return data







