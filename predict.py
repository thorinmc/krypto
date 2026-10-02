import torch
from torchvision import transforms, models
from PIL import Image

MODEL_PATH = "market_model.pth"
LABELS = ["bad", "good"]  # uwaga: kolejność zależy od folderów w dataset

# === Transformacje takie same jak w treningu ===
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# === Wczytaj model ===
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
num_features = model.fc.in_features
model.fc = torch.nn.Linear(num_features, 2)
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)  # batch size = 1

    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)
        label = LABELS[predicted.item()]
    return label

# === Test ===
if __name__ == "__main__":
    # Test tylko gdy odpalasz predict.py bezpośrednio
    test_image = "test.png"
    result = predict_image(test_image)
    print(f"Rynek wygląda na: {result}")