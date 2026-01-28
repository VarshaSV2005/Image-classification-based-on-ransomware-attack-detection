# debug_predict.py
import os
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from app import model, device  # imports the model loaded in app.py

# same transform you used in app.py
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

IMG_FOLDER = "imgs_gray"
files = sorted([f for f in os.listdir(IMG_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))])

def predict_tensor(tensor):
    model.eval()
    with torch.no_grad():
        out = model(tensor.to(device))
        probs = torch.softmax(out, dim=1)
        return out.cpu().numpy(), probs.cpu().numpy()

# 1) run predictions on dataset and print summary
results = []
for fname in files:
    path = os.path.join(IMG_FOLDER, fname)
    img = Image.open(path).convert("L")
    t = transform(img).unsqueeze(0)  # [1,1,128,128]
    logits, probs = predict_tensor(t)
    pred = int(probs.argmax(axis=1)[0])
    conf = float(probs[0, pred])
    results.append((fname, pred, conf, probs[0, :].tolist()))

# print summary counts
from collections import Counter
counts = Counter([r[1] for r in results])
print("Prediction counts (label_index:count):", counts)
print("Sample results (first 10):")
for r in results[:10]:
    print(r[0], "pred=", r[1], "conf=", round(r[2],4), "probs=", [round(x,4) for x in r[3]])

# 2) test on a pure-black and pure-white image and random image
def make_test_image(mode="black"):
    if mode=="black":
        arr = np.zeros((128,128), dtype=np.uint8)
    elif mode=="white":
        arr = np.ones((128,128), dtype=np.uint8)*255
    else:
        arr = np.random.randint(0,256,(128,128),dtype=np.uint8)
    img = Image.fromarray(arr, mode='L')
    return img

for tname in ("black","white","random"):
    img = make_test_image(tname)
    tensor = transform(img).unsqueeze(0)
    _, probs = predict_tensor(tensor)
    pred = int(probs.argmax(axis=1)[0])
    conf = float(probs[0, pred])
    print(f"Test {tname}: pred={pred}, conf={conf:.4f}, probs={[round(x,4) for x in probs[0]]}")

# 3) inspect state_dict keys (optional check)
try:
    sd = model.state_dict()
    print("State dict keys sample:", list(sd.keys())[:8])
    # print basic stats of first conv weights
    first_conv = sd[list(sd.keys())[0]].cpu().numpy()
    print("First param shape:", first_conv.shape, " mean:", first_conv.mean(), " std:", first_conv.std())
except Exception as e:
    print("Could not inspect state_dict:", e)

# write results to CSV
import csv
with open("prediction_debug_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["filename","pred_index","confidence","probs"])
    for r in results:
        writer.writerow([r[0], r[1], r[2], "|".join([str(x) for x in r[3]])])

print("Wrote prediction_debug_results.csv")
