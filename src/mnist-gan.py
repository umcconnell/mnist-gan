#!/usr/bin/env python
# coding: utf-8

# # MNIST-GAN

# Generate handwritten digits by training a GAN on the MNIST dataset.
# 
# This project is adapted from Boldizsar Zopcsak's great [GAN-Tutorial-Notebook](https://github.com/BoldizsarZopcsak/GAN-Tutorial-Notebook) (go check it out!). The original project is licensed under the [MIT License](https://github.com/BoldizsarZopcsak/GAN-Tutorial-Notebook/blob/master/LICENSE).<br>
# This project is licensed under the MIT License as well.

# ## Introduction

# This is a quick primer on GANs. For a more thorough write-up check out these links:
# - [A Beginner's Guide to Generative Adversarial Networks](https://pathmind.com/wiki/generative-adversarial-network-gan)
# - [A Gentle Introduction to Generative Adversarial Networks](https://machinelearningmastery.com/what-are-generative-adversarial-networks-gans/)
# - [Generative Adversarial Nets - Original Paper by Ian Goodfellow](https://arxiv.org/pdf/1406.2661.pdf)

# A GAN (Generative Adversarial Network) is a technique, in which two neural networks compete against each other, to improve their individual performance. GANs are mostly used for AI image generation, such as the generation of new faces.
# 
# A GAN comprises two parts: a **generator model** and a **discriminator model**<br>
# The generator creates new samples resembling the training set (i.e. handwritten digits in our case), while the discriminator tries to discern between real samples from the training set and fake samples generated by the generator model.

# ### Training

# Training a GAN is done in two steps.
# 
# #### Step 1: Training the Discriminator
# 
# In the first the discriminator is trained. The discriminator is fed some real samples from the training set, labelled as such (usually with a `1`), and some fake samples generated by the discriminator, labelled as fake samples (usually with a `0`). Then, standard backpropagation is applied onto the discriminator only.
# 
# ![Step 1: Training the discriminator](../static/mnist-gan-1.png)
# 
# #### Step 2: Training the Generator
# 
# Next, the generator is trained. First, the generator generates a batch of fake images. These are fed to the discriminator with real labels (usually a `1`). The error is then backpropagated to the generator, but only the generator weights are updated.
# 
# ![Step 2: Training the generator](../static/mnist-gan-2.png)

# ## Setup

# In[ ]:


import numpy as np
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')


# In[ ]:


import torch

import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import torchvision
import torchvision.transforms as transforms


# In[ ]:


BATCH_SIZE = 200
EPOCHS = 20

# GAN configurations
LATENT_DIM = 100
REAL_LABEL = 1
FAKE_LABEL = 0


# ## Loading MNIST Dataset

# We'll be using the MNIST dataset to train our GAN. It contains images of handwritten digits. Loading MNIST is trivial using `torchvision`.
# 
# Before we can use the images to train the network, it's a best practice to normalize the images. The images are black-and-white, represented by values from [0, 1]. The transformation will bring the values in a range of [-1, 1]:

# In[ ]:


transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5), (0.5))
])


# In[ ]:


dataset = torchvision.datasets.MNIST(
    root='./data', download=True, transform=transform
)
dataloader = torch.utils.data.DataLoader(
    dataset, batch_size=int(BATCH_SIZE/2), shuffle=True, num_workers=2
)


# ## Visualizing

# Let's visualize our training set before actually using it:

# In[ ]:


dataiter = iter(dataloader)
images, labels = dataiter.next()


# In[ ]:


def show_img(img):
    img = img / 2 + 0.5 # unnormalize
    npimg = img.numpy()
    plt.imshow(npimg[:, :], cmap='gray_r')
    plt.show()


# In[ ]:


show_img(images[0].squeeze())
print('Label: %s' % labels[0].item())


# ## Latent Space

# The generator creates new images by upsampling a random seed, the so-called latent space.
# 
# We'll create a helper function that creates a minibatch of latent spaces:

# In[ ]:


def generate_latent_points(latent_dim, n_samples):
    return torch.rand(n_samples, latent_dim)


# In[ ]:


# Show random latent_space / seed
img = generate_latent_points(28*28, 1).view(28, -1)
show_img(img)


# ## Model

# The `Model` class will be used as a base for the `Generator` and `Discriminator` class. It mainly offers the `predict` method, to run the model without accumulating gradients, and the `train_on` method, used to train a model on a batch and backpropagate.

# In[ ]:


class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        
    def forward(self, x):
        return self.model(x)
    
    def predict(self, x):
        return self.model(x).detach()
        
    def train_on(self, x, y, criterion, optimizer):
        output = self.model(x)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()
        return loss


# ## Generator

# First we'll define a helper class to reshape tensors. This will be used as a layer in our network and reshape input tensors to a desired size:

# In[ ]:


class Reshape(nn.Module):
    def __init__(self, shape):
        super(Reshape, self).__init__()
        self.shape = shape
    
    def forward(self, x):
        return x.view(*self.shape)


# The Generator takes a latent space as input and upsamples this seed to a random image of a digit:

# In[ ]:


class Generator(Model):
    def __init__(self):
        super(Generator, self).__init__()
        self.model = nn.Sequential(
            # Pass the latent space through a fully-connected layer
            nn.Linear(LATENT_DIM, 128*7*7),
            nn.BatchNorm1d(128*7*7),
            nn.LeakyReLU(0.2),
            
            # Reshape 1D tensor to a 7x7 image
            Reshape((-1, 128, 7, 7)),
            
            # Upsample to 14x14
            nn.ConvTranspose2d(128, 128, 4, stride=2),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),
            
            # Upsample to 28x28
            nn.ConvTranspose2d(128, 128, 4, stride=2),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),
            
            nn.Conv2d(128, 1, 7),
            nn.Tanh()
        )


# ### Generator Test

# Let's test the generator just to check that it works:

# In[ ]:


generator_example = Generator()
generator_example.train(False) # Set the generator to evaluation mode
latent_points_example = generate_latent_points(LATENT_DIM, 1)

generated_image_example = generator_example.predict(latent_points_example)
show_img(generated_image_example.squeeze())


# ## Discriminator

# The discriminator takes in an image an assesses, whether the image is real or fake

# In[ ]:


class Discriminator(Model):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.model = nn.Sequential(
            nn.Conv2d(1, 64, 3, stride=2),
            nn.LeakyReLU(0.2),
            nn.Dropout(p=0.4),
            
            nn.Conv2d(64, 64, 3, stride=2),
            nn.LeakyReLU(0.2),
            nn.Dropout(p=0.4),
            
            nn.Flatten(),
            nn.Linear(2304, 1),
            nn.Sigmoid()
        )


# ### Discriminator Test

# Let's now test discriminator just to check that it works:

# In[ ]:


discriminator_example = Discriminator()

prediction_example = discriminator_example(generated_image_example)
print('Discriminator Prediction: %f' % prediction_example.item())


# ## Training

# First we'll try setting up pytorch to use a CUDA-capable GPU. If no GPU is detected, the GAN will be trained on CPU:

# In[ ]:


dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device "%s" for training' % dev)


# Next we'll create the networks and move them to our selected device:

# In[ ]:


generator = Generator().to(dev)
discriminator = Discriminator().to(dev)


# We'll also define the optimizers, used to train the networks, and our loss function:

# In[ ]:


generator_optimizer = optim.Adam(generator.parameters(), lr=0.0002, betas=(0.5, 0.999))
discriminator_optimizer = optim.Adam(discriminator.parameters(), lr=0.0002, betas=(0.5, 0.999))
criterion = nn.BCELoss()


# Now let's finally train our GAN:

# In[ ]:


for epoch in range(EPOCHS):
    for i, data in enumerate(dataloader, 0):
        # ===========================
        # STEP 1: Train Discriminator
        # ===========================
        
        # MNIST training data
        # data[0] are the images, data[1] are the labels (e.g. 1, 2, 3, 4, ...) that we don't need
        real_imgs = data[0].to(dev)
        real_labels = torch.zeros(int(BATCH_SIZE/2)).fill_(REAL_LABEL)
        
        # Fake training data
        latent_points = generate_latent_points(LATENT_DIM, int(BATCH_SIZE/2)).to(dev)
        fake_imgs = generator.predict(latent_points).detach()
        fake_labels = torch.zeros(int(BATCH_SIZE/2)).fill_(FAKE_LABEL)

        discriminator_optimizer.zero_grad()

        # Combine real and fake half-batches to one full batch 
        images_all = torch.cat((real_imgs, fake_imgs))
        labels_all = torch.cat((real_labels, fake_labels)).unsqueeze(1).to(dev)
        
        discriminator_loss = discriminator.train_on(
            images_all, labels_all, criterion, discriminator_optimizer
        )
        
        # =======================
        # STEP 2: Train Generator
        # =======================
        generator_optimizer.zero_grad()

        fake_batch = generate_latent_points(LATENT_DIM, BATCH_SIZE).to(dev)
        fake_batch_labels = torch.zeros(BATCH_SIZE).fill_(REAL_LABEL).unsqueeze(1).to(dev)

        generator_imgs = generator(fake_batch)
        generator_loss = criterion(discriminator(generator_imgs), fake_batch_labels)
        generator_loss.backward()
        generator_optimizer.step()

        # ===============================
        # STEP 3: Logging and Visualizing
        # ===============================
        if i % 25 == 0:
            print('Epoch: %.2i    Batch Number: %.3i / %.3i    Generator Loss: %.9f    Discriminator Loss: %.9f' %
                 (epoch, i, len(dataloader), generator_loss.item(), discriminator_loss.item()))
            # show_img(fake_imgs.to("cpu")[0].squeeze().detach())
            
            fig = plt.figure()
            for a in range(30):
                ax = fig.add_subplot(6, 6, a + 1)
                plt.imshow(fake_imgs.to("cpu").detach()[a, 0, :, :], cmap='gray_r')
            
            plt.savefig('figs/plot  epoch ' + '%02d' % epoch + '  batch ' + '%05d' % i + '.png', dpi=600)
            plt.close()

