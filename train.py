import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

# === 1. Parametry ===
DATA_DIR = "dataset"  # folder z good/ i bad/
MODEL_PATH = "market_model.pth"
BATCH_SIZE = 16
EPOCHS = 5  # na start, potem można zwiększyć
LR = 0.001

# === 2. Transformacje obrazów (przycinanie, zmiana rozmiaru, normalizacja) ===
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# === 3. Dataset i DataLoader ===
dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# === 4. Model (ResNet18 z transfer learningiem) ===
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 2)  # 2 klasy: good, bad

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# === 5. Loss i optimizer ===
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LR)

# === 6. Trening ===
for epoch in range(EPOCHS):
    running_loss = 0.0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    print(f"[{epoch+1}/{EPOCHS}] Loss: {running_loss/len(train_loader):.4f}")

# === 7. Zapis modelu ===
torch.save(model.state_dict(), MODEL_PATH)
print(f"Model zapisany do {MODEL_PATH}")