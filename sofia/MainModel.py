from sofia.DataLoader import Loader
import torch
import torch.nn as nn
from sofia.BiLSTM_CRF import BiLSTM_CRF
import torch.optim as optim
import torch.autograd as autograd
import string
import os
import time


torch.manual_seed(1)
dtype= torch.LongTensor
start= time.time()
dataDim= 15000#####
epochs=100

def sentenceToVector(seq):
    tensor = torch.LongTensor(seq)
    return autograd.Variable(tensor)

def train(epochs, dim, hidden_dim, trainX, trainY):
    target_size=15
    #loss_fn = torch.nn.MSELoss(size_average=False)
    model = nn.Sequential(nn.LSTM(dim, hidden_dim // 2,
                    num_layers=1, bidirectional=True),
                          nn.ReLU(),
                                nn.Linear(hidden_dim, target_size))
    #hidden2tag = nn.Linear(hidden_dim, self.tagset_size)
    #hidden= (autograd.Variable(torch.randn(2, 1, hidden_dim // 2)),
     #autograd.Variable(torch.randn(2, 1, hidden_dim // 2)))

    optimizer = optim.SGD(model.parameters(), lr=0.01, weight_decay=1e-4)
    for t in range(epochs):
        end = time.time()
        print("Epoch number {}".format(t))
        print("Time {}".format(end - start))
        ####
        for i in range(len(trainX)):
            ####
            model.zero_grad()
            x= sentenceToVector(trainX[i])
            y= sentenceToVector(trainY[i])
            y_pred= model(x)
            #loss = loss_fn(y_pred, y)
            #loss.backward()
            # for param in model.parameters():
            #     param.data -= learning_rate * param.grad.data
            neg_log_likelihood = model.neg_log_likelihood(x, y)
            neg_log_likelihood.backward()
            optimizer.step()
    return model

def test(path, data, model, dataFile, labels, dim):
    file = open(path + '/output_' + dataFile, 'w')
    index=0
    for sentence, tags, predicates, items in dev:
        if index%100==0:
            print(index)
        index+=1
        #inputVector = sentenceToVector(sentence, vocabulary) #Or Ontonotes?
        inputVector = sentenceToVector(sentence, vocabulary, predicates)
        output= model(inputVector)[1]
        for i in range(len(items)):
            outLabel= getLabel(output[i], labels)
            file.write(items[i]+' '+outLabel+'\n')
        file.write('\n')
    file.close()

##Actually should I just import the models as they used to be in Bi-LSTM-CRF
##Or maybe Bi-LSTM-CNN???
## Check how to do the appropriate connections in the model
## Can I impose hard constraints directly on the CRF???

##Search about Constrained CRFs. Is that a thing????
#This can actually be the solution to the constraint satisfaction+neural component in the model



def main(hidden_dim):
    dataLoader = Loader('/Users/evangeliaspiliopoulou/Desktop/WorldModelers/PennDTB')

    trainX, trainY = dataLoader.getData('train')
    devX, devY = dataLoader.getData('dev')
    testX, testY = dataLoader.getData('test')

    #model = BiLSTM_CRF(labels, EMBEDDING_DIM, HIDDEN_DIM)
    model= train(epochs, dim, hidden_dim, trainX, trainY)

    test(path, devX, model, dataFile, labels, dim)

