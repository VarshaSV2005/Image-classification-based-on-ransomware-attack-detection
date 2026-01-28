import os
import torch
import numpy as np
from train_on_exe_files import ExeClassifier  # Import the model class
import sys

def load_exe_model(model_path='model/exe_classifier_model.pth'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = ExeClassifier()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model, device

def predict_exe_file(filepath, model, device, max_length=1024*1024):
    with open(filepath, 'rb') as f:
        data = f.read()

    data = np.frombuffer(data, dtype=np.uint8)
    if len(data) < max_length:
        data = np.pad(data, (0, max_length - len(data)), 'constant')
    else:
        data = data[:max_length]

    data = data.astype(np.float32) / 255.0
    tensor = torch.tensor(data).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        conf, pred = torch.max(probs, 0)
        label = "Ransomware" if pred.item() == 1 else "Legitimate"
        return label, conf.item()

def predict_folder(folder_path, model, device):
    affected_files = []
    safe_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.exe'):
                filepath = os.path.join(root, file)
                try:
                    label, conf = predict_exe_file(filepath, model, device)
                    if label == "Ransomware":
                        affected_files.append((filepath, conf))
                    else:
                        safe_files.append((filepath, conf))
                except Exception as e:
                    print(f"Error predicting on {filepath}: {e}")

    return affected_files, safe_files

if __name__ == '__main__':
    model, device = load_exe_model()

    if len(sys.argv) < 2:
        print("Usage: python predict_exe.py <file_or_folder_path>")
        sys.exit(1)

    input_path = sys.argv[1]

    if os.path.isfile(input_path):
        if input_path.endswith('.exe'):
            label, conf = predict_exe_file(input_path, model, device)
            print(f"{input_path}: {label} (confidence: {conf:.4f})")
        else:
            print("Please provide a .exe file or a folder containing .exe files.")
    elif os.path.isdir(input_path):
        affected_files, safe_files = predict_folder(input_path, model, device)

        print("Affected Files (Ransomware):")
        for filepath, conf in affected_files:
            print(f"  {filepath}: {conf:.4f}")

        print("\nSafe Files (Legitimate):")
        for filepath, conf in safe_files:
            print(f"  {filepath}: {conf:.4f}")

        print(f"\nSummary: {len(affected_files)} affected, {len(safe_files)} safe")
    else:
        print("Invalid path provided.")
