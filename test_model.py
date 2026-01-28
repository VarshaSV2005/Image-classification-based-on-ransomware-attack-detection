import torch
from torchvision import transforms
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import os
from app import DeepCNN, device, transform as app_transform

# Load the enhanced model
MODEL_PATH = os.path.join("model", "ransomware_cnn_model_enhanced.pth")
model = DeepCNN().to(device)
if os.path.exists(MODEL_PATH):
    state = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state)
    model.eval()
    print("✅ Enhanced model loaded successfully")
else:
    print("❌ Model not found")
    exit()

# Load test data (assuming dataset structure)
from torchvision.datasets import ImageFolder
test_dataset = ImageFolder(root="dataset", transform=app_transform)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Evaluate
all_labels, all_preds = [], []
with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, preds = torch.max(outputs, 1)
        all_labels.extend(labels.cpu().numpy())
        all_preds.extend(preds.cpu().numpy())

# Metrics
from sklearn.metrics import accuracy_score
acc = accuracy_score(all_labels, all_preds)
print(f"✅ Test Accuracy: {acc * 100:.2f}%")
print("📊 Classification Report:")
print(classification_report(all_labels, all_preds, target_names=["Benign", "Malicious"]))
print("Confusion Matrix:")
print(confusion_matrix(all_labels, all_preds))
