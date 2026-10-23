"""Prep a photo for ASCII conversion: remove bg, boost local contrast, composite on white.
Usage: python scripts/prep_photo.py source-photo.jpg [--no-rembg]
Output: source-prepped.png (grayscale)"""
import sys
import cv2
import numpy as np
from PIL import Image

src = sys.argv[1]
use_rembg = "--no-rembg" not in sys.argv

img = Image.open(src).convert("RGB")
if use_rembg:
    from rembg import remove
    rgba = remove(img)                       # subject isolated, transparent bg
else:
    rgba = Image.open(src).convert("RGBA")   # keeps transparency if the PNG already has it
rgba = np.array(rgba)
alpha = rgba[..., 3:4].astype(np.float32) / 255.0

gray = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))   # local contrast
gray = clahe.apply(gray).astype(np.float32)

out = gray[..., None] * alpha + 255.0 * (1 - alpha)           # composite on pure white
Image.fromarray(out[..., 0].astype(np.uint8), "L").save("source-prepped.png")
print("wrote source-prepped.png")
