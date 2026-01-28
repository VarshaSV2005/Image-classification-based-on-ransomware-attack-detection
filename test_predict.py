import torch
from PIL import Image
from torchvision import transforms
from app import model, device  # import your loaded model
import PyMuPDF

# Same transform used in app.py
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

def predict_from_path(img_path):
    img = Image.open(img_path).convert("L")
    img_t = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(img_t)
        probs = torch.softmax(outputs, dim=1)[0]
        conf, pred = torch.max(probs, 0)
        label = "Ransomware" if pred.item() == 1 else "Legitimate"
        return label, conf.item()

if __name__ == "__main__":
    test_img = r"imgs_gray\row_00200.png"   # change to your image
    label, conf = predict_from_path(test_img)
    print("Prediction:", label)
    print("Confidence:", conf)
