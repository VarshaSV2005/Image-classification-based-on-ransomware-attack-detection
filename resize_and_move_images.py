import os
from PIL import Image
from pathlib import Path

# Source folder
source_folder = "imgs"

# Destination folder
dest_folder = Path("dataset/ransomware/nearest_120")

# Ensure destination exists
dest_folder.mkdir(parents=True, exist_ok=True)

# Target size
target_size = (120, 120)

# Process each image
for filename in os.listdir(source_folder):
    if filename.endswith(".png"):
        img_path = os.path.join(source_folder, filename)
        img = Image.open(img_path).convert("L")  # Ensure grayscale
        img_resized = img.resize(target_size, Image.NEAREST)  # Use nearest for consistency with dataset

        # Save to destination
        dest_path = dest_folder / f"synthetic_{filename}"
        img_resized.save(dest_path)

print(f"Resized and moved {len(os.listdir(source_folder))} images to {dest_folder}")
