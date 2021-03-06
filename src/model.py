import torch
from torchvision import models
import torch.nn as nn
import torch.nn.functional as F


class GoNet(nn.Module):
    """ Neural Network class
        Two stream model:
        ________
       |        | conv layers              Untrained Fully
       |Previous|------------------>|      Connected Layers
       | frame  |                   |    ___     ___     ___
       |________|                   |   |   |   |   |   |   |   fc4
                   Pretrained       |   |   |   |   |   |   |    * (left)
                   CaffeNet         |-->|fc1|-->|fc2|-->|fc3|--> * (top)
                   Convolution      |   |   |   |   |   |   |    * (right)
                   layers           |   |___|   |___|   |___|    * (bottom)
        ________                    |   (4096)  (4096)  (4096)  (4)
       |        |                   |
       | Current|------------------>|
       | frame  |
       |________|

    """
    def __init__(self):
        super(GoNet, self).__init__()
        caffenet = models.alexnet(pretrained=True)
        self.convnet = nn.Sequential(*list(caffenet.children())[:-1])
        for param in self.convnet.parameters():
            param.requires_grad = False
        self.classifier = nn.Sequential(
                nn.Linear(256*6*6*2, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4),
                )
        self.weight_init()

    def weight_init(self):
        for m in self.classifier.modules():
            # fully connected layers are weight initialized with
            # mean=0 and std=0.005 (in tracker.prototxt) and
            # biases are set to 1
            # tracker.prototxt link: https://goo.gl/iHGKT5
            if isinstance(m, nn.Linear):
                m.bias.data.fill_(1)
                m.weight.data.normal_(0, 0.005)

    def forward(self, x, y):
        x1 = self.convnet(x)
        x1 = x1.view(x.size(0), 256*6*6)
        x2 = self.convnet(y)
        x2 = x2.view(x.size(0), 256*6*6)
        x = torch.cat((x1, x2), 1)
        x = self.classifier(x)
        return x

class SPPGoNet(nn.Module):
    """ Neural Network class
        Two stream model:
        ________
       |        | conv layers              Untrained Fully
       |Previous|------------------>|      Connected Layers
       | frame  |                   |    ___     ___     ___
       |________|                   |   |   |   |   |   |   |   fc4
                   Pretrained       |   |   |   |   |   |   |    * (left)
                   CaffeNet         |-->|fc1|-->|fc2|-->|fc3|--> * (top)
                   Convolution      |   |   |   |   |   |   |    * (right)
                   layers           |   |___|   |___|   |___|    * (bottom)
        ________                    |   (4096)  (4096)  (4096)  (4)
       |        |                   |
       | Current|------------------>|
       | frame  |
       |________|

    """
    def __init__(self):
        super(SPPGoNet, self).__init__()
        caffenet = models.alexnet(pretrained=True)
        self.convnet = nn.Sequential(*list(caffenet.children())[:-2])
        self.avgPool1 = nn.AdaptiveAvgPool2d([7, 7])
        self.avgPool2 = nn.AdaptiveAvgPool2d([7, 7])

        for param in self.convnet.parameters():
            param.requires_grad = False
        self.classifier = nn.Sequential(
                nn.Linear(256*7*7*4, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4),
                )
        self.weight_init()

    def weight_init(self):
        for m in self.classifier.modules():
            # fully connected layers are weight initialized with
            # mean=0 and std=0.005 (in tracker.prototxt) and
            # biases are set to 1
            # tracker.prototxt link: https://goo.gl/iHGKT5
            if isinstance(m, nn.Linear):
                m.bias.data.fill_(1)
                m.weight.data.normal_(0, 0.005)

    def forward(self, x1, x2, x1_x2, x2_x2):
        # x1 = self.convnet(x1)
        # x1 = x1.view(x1.size(0), 256*6*6)
        # x2 = self.convnet(x2)
        # x2 = x2.view(x2.size(0), 256*6*6)
        x1_x2 = self.convnet(x1_x2)

        x1 = x1_x2[:, :, 3:10, 3:10]
        x1 = x1.contiguous().view(x1.size(0), 256*7*7)


        x1_x2 = self.avgPool1(x1_x2)
        x1_x2 = x1_x2.view(x1_x2.size(0), 256*7*7)

        x2_x2 = self.convnet(x2_x2)

        x2 = x2_x2[:,:, 3:10, 3:10]
        x2 = x2.contiguous().view(x2.size(0), 256*7*7)

        x2_x2 = self.avgPool2(x2_x2)
        x2_x2 = x2_x2.view(x2_x2.size(0), 256*7*7)


        x = torch.cat((x1, x2, x1_x2, x2_x2), 1)
        x = self.classifier(x)
        return x

class SPPSqueezeGoNet(nn.Module):
    """ Neural Network class
        Two stream model:
        ________
       |        | conv layers              Untrained Fully
       |Previous|------------------>|      Connected Layers
       | frame  |                   |    ___     ___     ___
       |________|                   |   |   |   |   |   |   |   fc4
                   Pretrained       |   |   |   |   |   |   |    * (left)
                   CaffeNet         |-->|fc1|-->|fc2|-->|fc3|--> * (top)
                   Convolution      |   |   |   |   |   |   |    * (right)
                   layers           |   |___|   |___|   |___|    * (bottom)
        ________                    |   (4096)  (4096)  (4096)  (4)
       |        |                   |
       | Current|------------------>|
       | frame  |
       |________|

    """
    def __init__(self):
        super(SPPSqueezeGoNet, self).__init__()
        caffenet = models.squeezenet1_1(pretrained=True)
        squeezenet_feature_layers = list(caffenet.children())[:-1]
        self.convnet = nn.Sequential(*list(*squeezenet_feature_layers)[:-5])
        self.avgPool1 = nn.AdaptiveAvgPool2d([7, 7])
        self.avgPool2 = nn.AdaptiveAvgPool2d([7, 7])

        for param in self.convnet.parameters():
            param.requires_grad = False
        self.classifier = nn.Sequential(
                nn.Linear(256*7*7*4, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4),
                )
        self.weight_init()

    def weight_init(self):
        for m in self.classifier.modules():
            # fully connected layers are weight initialized with
            # mean=0 and std=0.005 (in tracker.prototxt) and
            # biases are set to 1
            # tracker.prototxt link: https://goo.gl/iHGKT5
            if isinstance(m, nn.Linear):
                m.bias.data.fill_(1)
                m.weight.data.normal_(0, 0.005)

    def forward(self, x1, x2, x1_x2, x2_x2):
        x1_x2 = F.upsample(x1_x2, size=(128, 128), mode='bilinear')
        x2_x2 = F.upsample(x2_x2, size=(128, 128), mode='bilinear')


        x1_x2 = self.convnet(x1_x2)

        x1 = x1_x2[:, :, 4:11, 4:11]
        x1 = x1.contiguous().view(x1.size(0), 256*7*7)


        x1_x2 = self.avgPool1(x1_x2)
        x1_x2 = x1_x2.view(x1_x2.size(0), 256*7*7)

        x2_x2 = self.convnet(x2_x2)

        x2 = x2_x2[:, :, 4:11, 4:11]
        x2 = x2.contiguous().view(x2.size(0), 256*7*7)

        x2_x2 = self.avgPool2(x2_x2)
        x2_x2 = x2_x2.view(x2_x2.size(0), 256*7*7)


        x = torch.cat((x1, x2, x1_x2, x2_x2), 1)
        x = self.classifier(x)
        return x

class SPPSqueezeGoNet2(nn.Module):
    """ Neural Network class
        Two stream model:
        ________
       |        | conv layers              Untrained Fully
       |Previous|------------------>|      Connected Layers
       | frame  |                   |    ___     ___     ___
       |________|                   |   |   |   |   |   |   |   fc4
                   Pretrained       |   |   |   |   |   |   |    * (left)
                   CaffeNet         |-->|fc1|-->|fc2|-->|fc3|--> * (top)
                   Convolution      |   |   |   |   |   |   |    * (right)
                   layers           |   |___|   |___|   |___|    * (bottom)
        ________                    |   (4096)  (4096)  (4096)  (4)
       |        |                   |
       | Current|------------------>|
       | frame  |
       |________|

    """
    def __init__(self):
        super(SPPSqueezeGoNet2, self).__init__()
        caffenet = models.squeezenet1_1(pretrained=True)
        squeezenet_feature_layers = list(caffenet.children())[:-1]
        self.convnet = nn.Sequential(*list(*squeezenet_feature_layers)[:-4])
        self.avgPool1 = nn.AdaptiveAvgPool2d([5, 5])
        self.avgPool2 = nn.AdaptiveAvgPool2d([5, 5])

        for param in self.convnet.parameters():
            param.requires_grad = False
        self.classifier = nn.Sequential(
                nn.Linear(256*5*5*4, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4096),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(4096, 4),
                )
        self.weight_init()

    def weight_init(self):
        for m in self.classifier.modules():
            # fully connected layers are weight initialized with
            # mean=0 and std=0.005 (in tracker.prototxt) and
            # biases are set to 1
            # tracker.prototxt link: https://goo.gl/iHGKT5
            if isinstance(m, nn.Linear):
                m.bias.data.fill_(1)
                m.weight.data.normal_(0, 0.005)

    def forward(self, x1, x2, x1_x2, x2_x2):
        x1_x2 = F.upsample(x1_x2, size=(256, 256), mode='bilinear')
        x2_x2 = F.upsample(x2_x2, size=(256, 256), mode='bilinear')


        x1_x2 = self.convnet(x1_x2)

        x1 = x1_x2[:, :, 5:10, 5:10]
        x1 = x1.contiguous().view(x1.size(0), 256*5*5)


        x1_x2 = self.avgPool1(x1_x2)
        x1_x2 = x1_x2.view(x1_x2.size(0), 256*5*5)

        x2_x2 = self.convnet(x2_x2)

        x2 = x2_x2[:, :, 5:10, 5:10]
        x2 = x2.contiguous().view(x2.size(0), 256*5*5)

        x2_x2 = self.avgPool2(x2_x2)
        x2_x2 = x2_x2.view(x2_x2.size(0), 256*5*5)


        x = torch.cat((x1, x2, x1_x2, x2_x2), 1)
        x = self.classifier(x)
        return x