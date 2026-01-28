# robust_convert.py
import os
import sys
import csv
import math
from PIL import Image

INPUT_CSV = r"C:\Users\ADMIN\Downloads\major prj\Ransomware_CNN\synthetic_ransomware_bytes.csv"
OUTPUT_RGB = "imgs"
OUTPUT_GRAY = "imgs_gray"

os.makedirs(OUTPUT_RGB, exist_ok=True)
os.makedirs(OUTPUT_GRAY, exist_ok=True)

def file_exists(path):
    if not os.path.isfile(path):
        print(f"[ERROR] CSV not found: {path}")
        return False
    print(f"[OK] Found CSV: {path} ({os.path.getsize(path)} bytes)")
    return True

def preview_csv(path, n=5):
    print("[INFO] CSV preview (first rows):")
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        rdr = csv.reader(f)
        for i, row in enumerate(rdr):
            print(f" row {i}: {row[:8]}{'...' if len(row)>8 else ''}")
            if i+1>=n:
                break

# Try using net2i if available
def try_net2i(path, outfolder):
    try:
        from net2i.convert import Converter
    except Exception as e:
        print(f"[INFO] net2i not available or import failed: {e}")
        return False

    try:
        print("[INFO] Creating Converter and running toImage() ...")
        conv = Converter(path)
        conv.toImage(outfolder)
        print("[INFO] net2i.toImage() finished.")
        return True
    except Exception as e:
        print(f"[ERROR] net2i conversion failed: {e}")
        return False

# Fallback: parse CSV rows that are space/comma-separated bytes/hex and create images
def fallback_parse_and_make_images(path, outfolder_rgb, outfolder_gray):
    print("[INFO] Falling back to local parser -> making images from CSV rows.")
    created = 0
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        rdr = csv.reader(f)
        for idx, row in enumerate(rdr):
            # combine row fields into a single token list
            tokens = []
            for cell in row:
                # split on spaces if a single cell contains many tokens
                parts = [p for p in cell.replace(',', ' ').split() if p]
                tokens.extend(parts)
            if not tokens:
                continue

            # try to convert tokens to bytes
            byte_list = []
            for t in tokens:
                try:
                    # handle '0x4D', '4D' hex or decimal
                    if t.lower().startswith('0x'):
                        v = int(t, 16)
                    elif all(c in "0123456789abcdefABCDEF" for c in t) and len(t) in (2,):
                        v = int(t, 16)
                    else:
                        v = int(t)  # decimal fallback
                    byte_list.append(v & 0xFF)
                except Exception:
                    # ignore tokens that are not numbers
                    continue

            if not byte_list:
                continue

            b = bytes(byte_list)

            # Decide image mode: RGB if length %3 == 0 and >3, else grayscale
            mode = 'L'
            raw = b
            if len(b) >= 3 and len(b) % 3 == 0:
                mode = 'RGB'
            # Determine square size
            if mode == 'RGB':
                num_pixels = len(b) // 3
            else:
                num_pixels = len(b)
            side = int(math.ceil(math.sqrt(num_pixels)))
            # pad bytes
            if mode == 'RGB':
                needed = side*side*3
            else:
                needed = side*side
            if len(b) < needed:
                raw = b + bytes([0]) * (needed - len(b))

            try:
                if mode == 'RGB':
                    img = Image.frombytes('RGB', (side, side), raw)
                else:
                    img = Image.frombytes('L', (side, side), raw)
                fname = f"row_{idx:05d}.{ 'png'}"
                outpath = os.path.join(outfolder_rgb, fname)
                img.save(outpath)
                # also save grayscale version
                gray = img.convert("L")
                gray.save(os.path.join(outfolder_gray, fname))
                created += 1
            except Exception as e:
                print(f"[WARN] Failed to create image for row {idx}: {e}")
    print(f"[INFO] Fallback created {created} images.")
    return created

def list_output(folder):
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]
    print(f"[INFO] {folder}: {len(files)} files. Sample: {files[:8]}")

def main():
    if not file_exists(INPUT_CSV):
        return
    preview_csv(INPUT_CSV, n=3)

    # First try net2i
    ok = try_net2i(INPUT_CSV, OUTPUT_RGB)

    # If net2i produced files, show them. If not, run fallback.
    if ok:
        list_output(OUTPUT_RGB)
        # if nothing created, fallback
        if len(os.listdir(OUTPUT_RGB)) == 0:
            print("[INFO] net2i produced 0 files -> running fallback parser.")
            fallback_parse_and_make_images(INPUT_CSV, OUTPUT_RGB, OUTPUT_GRAY)
    else:
        fallback_parse_and_make_images(INPUT_CSV, OUTPUT_RGB, OUTPUT_GRAY)

    list_output(OUTPUT_RGB)
    list_output(OUTPUT_GRAY)
    print("[DONE] All done.")

if __name__ == "__main__":
    main()
