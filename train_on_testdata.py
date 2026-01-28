import os
import math
import io
import shutil
from PIL import Image
import torch
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader, random_split
import torch.nn as nn
import torch.optim as optim

from app import DeepCNN, device


ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_EXE_DIR = os.path.join(ROOT, 'Test Data', 'Benign Test Data')
OUT_TRAIN_DIR = os.path.join(ROOT, 'train_images')
BENIGN_DIR = os.path.join(OUT_TRAIN_DIR, 'benign')
RANSOM_DIR = os.path.join(OUT_TRAIN_DIR, 'ransomware')
RANSOM_SOURCE = os.path.join(ROOT, 'dataset', 'ransomware', 'lanczos_120')
os.makedirs(BENIGN_DIR, exist_ok=True)
os.makedirs(RANSOM_DIR, exist_ok=True)


def bytes_to_grayscale_image(bts):
    if not bts:
        raise ValueError("Empty file")
    num = len(bts)
    side = int(math.ceil(math.sqrt(num)))
    needed = side * side
    if num < needed:
        bts = bts + bytes([0]) * (needed - num)
    img = Image.frombytes('L', (side, side), bts)
    return img


def convert_exes_to_images(src_dir, out_dir):
    print(f"Converting EXE files from {src_dir} -> {out_dir}")
    count = 0
    for fname in os.listdir(src_dir):
        fpath = os.path.join(src_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, 'rb') as f:
                b = f.read()
            img = bytes_to_grayscale_image(b)
            # resize to 128x128 to match training
            img = img.resize((128, 128))
            outname = os.path.splitext(fname)[0] + '.png'
            outpath = os.path.join(out_dir, outname)
            img.save(outpath)
            count += 1
        except Exception as e:
            print(f"Failed to convert {fname}: {e}")
    print(f"Converted {count} files.")


def prepare_ransomware_images(src_dir, out_dir, max_files=None):
    print(f"Copying ransomware images from {src_dir} -> {out_dir}")
    files = [f for f in os.listdir(src_dir) if f.lower().endswith('.png')]
    if max_files:
        files = files[:max_files]
    for f in files:
        src = os.path.join(src_dir, f)
        dst = os.path.join(out_dir, f)
        if not os.path.exists(dst):
            shutil.copy(src, dst)
    print(f"Copied {len(files)} ransomware images.")


def train_model(data_dir, epochs=20, batch_size=16, lr=1e-4):
    # Enhanced data augmentation
    train_transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((128, 128)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    val_transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    dataset = ImageFolder(data_dir, transform=train_transform)
    print(f"Dataset classes: {dataset.classes}; samples={len(dataset)}")

    # split
    val_size = max(1, int(0.2 * len(dataset)))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    # Apply different transforms
    train_ds.dataset.transform = train_transform
    val_ds.dataset.transform = val_transform

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    model = DeepCNN().to(device)
    # optionally load existing weights if present
    model_path = os.path.join(ROOT, 'model', 'ransomware_cnn_model.pth')
    if os.path.exists(model_path):
        try:
            state = torch.load(model_path, map_location=device)
            model.load_state_dict(state)
            print("Loaded existing model weights for fine-tuning.")
        except Exception as e:
            print("Could not load existing weights:", e)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0

    for epoch in range(1, epochs+1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            outputs = model(xb)
            loss = criterion(outputs, yb)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * xb.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == yb).sum().item()
            total += xb.size(0)

        train_loss = running_loss / total if total else 0
        train_acc = correct / total if total else 0

        # validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                yb = yb.to(device)
                outputs = model(xb)
                loss = criterion(outputs, yb)
                val_loss += loss.item() * xb.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == yb).sum().item()
                val_total += xb.size(0)

        val_loss = val_loss / val_total if val_total else 0
        val_acc = val_correct / val_total if val_total else 0

        scheduler.step()

        print(f"Epoch {epoch}/{epochs} - train_loss={train_loss:.4f} train_acc={train_acc:.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f}")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            out_model = os.path.join(ROOT, 'model', 'ransomware_cnn_model_enhanced.pth')
            torch.save(model.state_dict(), out_model)
            print(f"Saved best model with val_acc={val_acc:.4f}")

    print(f"Training complete. Best validation accuracy: {best_val_acc:.4f}")


if __name__ == '__main__':
    # Step 1: convert EXEs
    convert_exes_to_images(TEST_EXE_DIR, BENIGN_DIR)
    # Step 2: prepare ransomware images
    prepare_ransomware_images(RANSOM_SOURCE, RANSOM_DIR, max_files=200)
    # Step 3: quick training
    train_model(OUT_TRAIN_DIR, epochs=20, batch_size=8, lr=1e-4)
