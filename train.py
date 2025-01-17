import os
import numpy as np
import torch

from model import ViTConfig, ViT

dataset = 'cifar-10'
block_size = 32 * 32 * 3
device = 'cpu'
device_type = 'cuda' if torch.cuda.is_available() else 'cpu'
dtype = 'bfloat16' if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else 'float16'

data_dir = os.path.join('data', dataset)
train_images = np.memmap(os.path.join(data_dir, 'train-images.bin'), dtype=np.float32, mode='r')
train_labels = np.memmap(os.path.join(data_dir, 'train-labels.bin'), dtype=np.int64, mode='r')
test_images = np.memmap(os.path.join(data_dir, 'test-images.bin'), dtype=np.float32, mode='r')
test_labels = np.memmap(os.path.join(data_dir, 'test-labels.bin'), dtype=np.int64, mode='r')

def get_batch(split, batch_size):
    image_data, label_data = (train_images, train_labels) if split == 'train' else (test_images, test_labels)
    ix = torch.randint(len(image_data) // block_size, (batch_size,))

    x = torch.stack([torch.from_numpy(np.copy(image_data[i*block_size:(i+1)*block_size].reshape(3, 32, 32))) for i in ix.numpy()])
    y = torch.from_numpy(label_data[ix.numpy()])

    if device_type == 'cuda':
        x = x.pin_memory().to(device, non_blocking=True)
        y = y.pin_memory().to(device, non_blocking=True)
    else:
        x, y = x.to(device), y.to(device)
    return x, y

iter_num = 0
best_val_loss = 1e9
grad_clip = 1.0

print("Initializing a new model from scratch")

config = ViTConfig()
model = ViT(config)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)

batch_size = 64
epochs = 500
warmup_epochs = 10

linear_warmup = torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=1/warmup_epochs, end_factor=1.0, total_iters=warmup_epochs-1, last_epoch=-1, verbose=True)
cos_decay = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=optimizer, T_max=epochs-warmup_epochs, eta_min=1e-5, verbose=True)

for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    for _ in range(len(train_images) // block_size // batch_size):
        inputs, labels = get_batch('train', batch_size)
        
        logits, loss = model(inputs, targets=labels)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        running_loss += loss.item()

    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0 
    with torch.no_grad():
        for _ in range(len(test_images) // block_size // batch_size):
            inputs, labels = get_batch('test', batch_size)

            logits, loss = model(inputs, targets=labels)

            val_loss += loss.item()

            _, predicted = torch.max(logits.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    print(f'Epoch {epoch+1}, Loss: {running_loss / (len(train_images) // block_size // batch_size)}\tValidation Loss: {val_loss / (len(test_images) // block_size // batch_size)}\tValidation Accuracy: {accuracy}%')

    if epoch < warmup_epochs:
        linear_warmup.step()
    else:
        cos_decay.step()


print('Finished Training')

model.eval()
test_loss = 0.0
correct = 0
total = 0

with torch.no_grad():
    for _ in range(len(test_images) // block_size // batch_size):
        inputs, labels = get_batch('test', batch_size)

        logits, loss = model(inputs, targets=labels)

        test_loss += loss.item()

        _, predicted = torch.max(logits.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

accuracy = 100 * correct / total
print(f'Test Loss: {test_loss / (len(test_images) // block_size // batch_size)}')
print(f'Test Accuracy: {accuracy}%')

print('Finished Testing')
