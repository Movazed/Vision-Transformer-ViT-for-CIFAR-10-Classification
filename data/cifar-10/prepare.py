import os
import numpy as np
from torchvision import datasets, transforms

mean = [0.4914, 0.4822, 0.4465]
std = [0.247, 0.243, 0.261]

train_transform = transforms.Compose([
    transforms.RandomCrop(32, padding=4),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),            
    transforms.Normalize(mean, std),  
])

test_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean,std),
])

train_dataset = datasets.CIFAR10(root='./data/cifar-10', train=True, download=True, transform=train_transform)
test_dataset = datasets.CIFAR10(root='./data/cifar-10', train=False, download=True, transform=test_transform)

train_images = np.array([train_dataset[i][0].numpy() for i in range(len(train_dataset))])
train_labels = np.array([train_dataset[i][1] for i in range(len(train_dataset))], dtype=np.int64)
test_images = np.array([test_dataset[i][0].numpy() for i in range(len(test_dataset))])
test_labels = np.array([test_dataset[i][1] for i in range(len(test_dataset))], dtype=np.int64)

train_images.tofile(os.path.join(os.path.dirname(__file__), 'train-images.bin'))
train_labels.tofile(os.path.join(os.path.dirname(__file__), 'train-labels.bin'))
test_images.tofile(os.path.join(os.path.dirname(__file__), 'test-images.bin'))
test_labels.tofile(os.path.join(os.path.dirname(__file__), 'test-labels.bin'))

print(f"Train data saved with shape {train_images.shape} and {train_labels.shape}")
print(f"Test data saved with shape {test_images.shape} and {test_labels.shape}")