from app import model, device

print("Device:", device)
try:
    total_params = sum(p.numel() for p in model.parameters())
    print("Total model params:", total_params)
    print("Model in eval mode:", not model.training)
except Exception as e:
    print("Error inspecting model:", e)
