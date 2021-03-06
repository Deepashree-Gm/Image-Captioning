import torch
import torch.nn as nn
import torchvision.models as models


class EncoderCNN(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        self.embed = nn.Linear(resnet.fc.in_features, embed_size)

    def forward(self, images):
        features = self.resnet(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
    

class DecoderRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers=1):
        super().__init__()

        self.embed_size = embed_size
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        self.embed = nn.Embedding(vocab_size, embed_size)        
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True)        
        self.fc = nn.Linear(hidden_size,vocab_size)

    
    def forward(self, features, captions):
        captions = captions[:, :-1]
        captions = self.embed(captions)
        features = features.unsqueeze(1)
        cap_features = torch.cat((features,captions),1)
        x,_ = self.lstm(cap_features)
        x = self.fc(x)
        
        return x

    def sample(self, inputs, states=None, max_len=20):
        " accepts pre-processed image tensor (inputs) and returns predicted sentence (list of tensor ids of length max_len) "
        words = None
        count = 0
        preds = []
    
        while count<max_len and words!=1:
            outputs,states = self.lstm(inputs,states)
            lstm_preds = self.fc(outputs)
            prob, word = lstm_preds.max(2)
            words = word.item()
            preds.append(words)
            inputs = self.embed(word)
            
            count+=1
        
        return preds