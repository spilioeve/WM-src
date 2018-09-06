from DataLoader import Loader
import torch
import torch.nn as nn
import numpy as np


dataLoader= Loader('/Users/evangeliaspiliopoulou/Desktop/WorldModelers/PennDTB')

trainX, trainY= dataLoader.getData('train')
devX, devY= dataLoader.getData('dev')

def train():
    return 0

def test():
    return 0

##Actually should I just import the models as they used to be in Bi-LSTM-CRF
##Or maybe Bi-LSTM-CNN???
## Check how to do the appropriate connections in the model
## Can I impose hard constraints directly on the CRF???

##Search about Constrained CRFs. Is that a thing????
#This can actually be the solution to the constraint satisfaction+neural component in the model



model= nn.LSTM()