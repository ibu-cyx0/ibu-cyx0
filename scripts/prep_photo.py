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
res = out[..., 0].astype(np.uint8)

# auto-crop to the subject, add a margin, and pad to a 5:6 portrait frame
ys, xs = np.where((alpha[..., 0] > 0.15) if use_rembg or alpha.min() < 1 else (res < 235))
if len(xs):
    m = int(0.06 * max(xs.max() - xs.min(), ys.max() - ys.min()))
    x0, x1 = max(0, xs.min() - m), min(res.shape[1], xs.max() + m)
    y0, y1 = max(0, ys.min() - m), min(res.shape[0], ys.max() + m)
    res = res[y0:y1, x0:x1]
h, w = res.shape
tw = max(w, int(h * 5 / 6)); th = max(h, int(w * 6 / 5))
canvas = np.full((th, tw), 255, np.uint8)
canvas[(th - h) // 2:(th - h) // 2 + h, (tw - w) // 2:(tw - w) // 2 + w] = res
Image.fromarray(canvas, "L").save("source-prepped.png")
print("wrote source-prepped.png")
