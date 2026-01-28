import os
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from torch.utils.data import Dataset, DataLoader

class ExeDataset(Dataset):
    def __init__(self, benign_dir, ransomware_dirs, max_length=1024*1024):
        self.max_length = max_length
        self.samples = []

        # Load benign files
        if os.path.exists(benign_dir):
            for fname in os.listdir(benign_dir):
                if fname.endswith('.exe'):
                    fpath = os.path.join(benign_dir, fname)
                    self.samples.append((fpath, 0))  # 0 for benign

        # Load ransomware files from multiple directories
        if isinstance(ransomware_dirs, str):
            ransomware_dirs = [ransomware_dirs]

        for ransomware_dir in ransomware_dirs:
            if os.path.exists(ransomware_dir):
                for fname in os.listdir(ransomware_dir):
                    if fname.endswith('.exe') or fname.endswith('.bat'):
                        fpath = os.path.join(ransomware_dir, fname)
                        self.samples.append((fpath, 1))  # 1 for ransomware

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        fpath, label = self.samples[idx]

        # Read file bytes
        with open(fpath, 'rb') as f:
            data = f.read()

        # Convert to numpy array of bytes
        data = np.frombuffer(data, dtype=np.uint8)

        # Pad or truncate to fixed length
        if len(data) < self.max_length:
            data = np.pad(data, (0, self.max_length - len(data)), 'constant')
        else:
            data = data[:self.max_length]

        # Convert to float and normalize to [0,1]
        data = data.astype(np.float32) / 255.0

        return torch.tensor(data), torch.tensor(label, dtype=torch.long)

class ExeClassifier(nn.Module):
    def __init__(self, input_size=1024*1024, hidden_size=512, num_classes=2):
        super(ExeClassifier, self).__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size//2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size//2, hidden_size//4),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        self.classifier = nn.Linear(hidden_size//4, num_classes)

    def forward(self, x):
        features = self.encoder(x)
        return self.classifier(features)

def test_model_accuracy():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load model
    model = ExeClassifier().to(device)
    model_path = os.path.join("model", "exe_classifier_model.pth")

    if os.path.exists(model_path):
        state = torch.load(model_path, map_location=device)
        model.load_state_dict(state)
        model.eval()
        print("✅ Model loaded successfully")
    else:
        print("❌ Model not found")
        return

    # Create test dataset
    benign_dir = os.path.join('Test Data', 'Benign Test Data')
    ransomware_dirs = ['Test Data', 'generated_exes']

    dataset = ExeDataset(benign_dir, ransomware_dirs)
    print(f"Dataset size: {len(dataset)} samples")

    if len(dataset) == 0:
        print("No test files found!")
        return

    # Create data loader
    test_loader = DataLoader(dataset, batch_size=4, shuffle=False)

    # Evaluate
    all_labels = []
    all_preds = []

    with torch.no_grad():
        for xb, yb in test_loader:
            xb = xb.to(device)
            yb = yb.to(device)

            outputs = model(xb)
            _, preds = torch.max(outputs, 1)

            all_labels.extend(yb.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())

    # Calculate accuracy
    accuracy = accuracy_score(all_labels, all_preds)
    print(f"✅ Model Accuracy: {accuracy * 100:.2f}%")

    # Classification report
    print("\n📊 Classification Report:")
    print(classification_report(all_labels, all_preds, target_names=['Benign', 'Ransomware']))

    # Class distribution
    benign_count = sum(1 for label in all_labels if label == 0)
    ransomware_count = sum(1 for label in all_labels if label == 1)
    print(f"\n📈 Dataset Distribution:")
    print(f"Benign files: {benign_count}")
    print(f"Ransomware files: {ransomware_count}")

if __name__ == '__main__':
    test_model_accuracy()
