"""Convert source-prepped.png to a self-typing ASCII SVG (plays once, then freezes).
Usage: python scripts/make_ascii_svg.py [--light] [--full|--head|--face] [--sharp] [--cols 220]
                                         [--gamma 0.8] [--lift 0.6] [--width 640]
  --light : light card, dark glyphs (best for dark hair/clothes)
  --full  : whole subject, no crop (default)
  --head  : crop to head + shoulders      --face : tight head crop
  --sharp : boost local contrast + sharpen (clearer eyes/nose/mouth)
  --cols N: characters per row; more = finer detail (card width stays fixed)
  --gamma G: lower = darker/bolder shading (default 1.0)
  --lift L: lift dark areas so clothes show texture instead of a solid block (default 1.0; try 0.6)
  --width W: card width in px (default 640)
Output: ascii-portrait.svg"""
import sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from xml.sax.saxutils import escape

RAMP = " .,:;-~+=*xzoO0#%8&@"      # sparse -> dense
BG_CUTOFF = 247                     # near-white = background -> blank
ASPECT = 8.0 / 4.8                  # line height / char width


def flag(name):
    return name in sys.argv


def val(name, default, cast=float):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def build_lines(path="source-prepped.png", cols=220, light=True, head=False,
                face=False, sharp=False, gamma=1.0, lift=1.0):
    img = Image.open(path).convert("L")
    a = np.array(img)
    ys, xs = np.where(a < BG_CUTOFF)
    if len(xs):                                     # tight crop on the subject
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        if head:
            y1 = y0 + int((y1 - y0) * 0.60)
        if face:
            y1 = y0 + int((y1 - y0) * 0.41)
            sub = a[y0:y1, :] < BG_CUTOFF
            xs2 = np.where(sub.sum(axis=0) > 0.04 * (y1 - y0))[0]
            if len(xs2):
                x0, x1 = xs2.min(), xs2.max() + 1
        pad = int(0.04 * max(x1 - x0, y1 - y0))
        W0, H0 = img.size
        img = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(W0, x1 + pad), min(H0, y1 + pad)))
        img = ImageOps.expand(img, border=pad, fill=255)
    if face or sharp:                               # bring out eyes, nose, mouth
        img = ImageOps.autocontrast(img, cutoff=1)
        big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        big = big.filter(ImageFilter.UnsharpMask(radius=30, percent=70, threshold=0))   # local contrast
        big = big.filter(ImageFilter.UnsharpMask(radius=3, percent=200, threshold=2))   # fine detail
        img = big
    w, h = img.size
    rows = max(1, round(cols * h / w / ASPECT))
    g = np.array(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32)

    subj = g < BG_CUTOFF
    lo, hi = np.percentile(g[subj], [2, 98]) if subj.any() else (0, 255)
    v = np.clip((g - lo) / max(hi - lo, 1), 0, 1)
    v = v ** lift
    dens = (1 - v) ** gamma if light else v ** 0.85

    lines = []
    for r in range(rows):
        lines.append("".join(" " if not subj[r, c] else RAMP[min(len(RAMP) - 1, int(dens[r, c] * len(RAMP)))]
                             for c in range(cols)))
    return lines


def write_svg(lines, cols, light, width):
    CHAR_W = width / cols
    LINE_H = CHAR_W * ASPECT
    FONT = LINE_H * 1.0
    rows = len(lines)
    PAD = 12
    W, H = width + PAD * 2, rows * LINE_H + PAD * 2
    bg, fg, cur = ("#f6f8fa", "#24292f", "#0969da") if light else ("#0d1117", "#c8d8e8", "#00d4ff")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.1f} {H:.1f}">',
         f'<rect width="100%" height="100%" rx="8" fill="{bg}"/>',
         f'<style>text{{font-family:"Fira Code",Consolas,"Courier New",monospace;font-size:{FONT:.2f}px;'
         f'fill:{fg};white-space:pre}}</style><defs>']
    DUR = 0.45
    step = min(0.05, 4.0 / rows)                    # whole portrait types in ~4s
    for i in range(rows):
        t = i * step
        o.append(f'<clipPath id="c{i}"><rect x="{PAD}" y="{PAD + i*LINE_H:.2f}" width="0" height="{LINE_H:.2f}">'
                 f'<animate attributeName="width" from="0" to="{width:.1f}" begin="{t:.2f}s" dur="{DUR}s" fill="freeze"/>'
                 f'</rect></clipPath>')
    o.append('</defs>')
    for i, ln in enumerate(lines):
        t = i * step
        y = PAD + i * LINE_H + FONT * 0.85
        if ln.strip():
            o.append(f'<text xml:space="preserve" x="{PAD}" y="{y:.2f}" textLength="{len(ln)*CHAR_W:.2f}" '
                     f'lengthAdjust="spacing" clip-path="url(#c{i})">{escape(ln)}</text>')
        o.append(f'<rect y="{PAD + i*LINE_H:.2f}" width="3" height="{LINE_H:.2f}" fill="{cur}" opacity="0" x="{PAD}">'
                 f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
                 f'<animate attributeName="x" from="{PAD}" to="{PAD + width:.1f}" begin="{t:.2f}s" dur="{DUR}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0" begin="{t+DUR:.2f}s"/></rect>')
    o.append('</svg>')
    open("ascii-portrait.svg", "w", encoding="utf-8").write("\n".join(o))


if __name__ == "__main__":
    cols = val("--cols", 220, int)
    light = flag("--light")
    lines = build_lines(cols=cols, light=light, head=flag("--head"), face=flag("--face"),
                        sharp=flag("--sharp"), gamma=val("--gamma", 1.0), lift=val("--lift", 1.0))
    write_svg(lines, cols, light, val("--width", 640))
    print(f"wrote ascii-portrait.svg ({cols}x{len(lines)})")
