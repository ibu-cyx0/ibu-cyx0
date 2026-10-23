"""Convert source-prepped.png to a self-typing ASCII SVG inside a terminal-window card.
Usage: python scripts/make_ascii_svg.py [--dark|--light] [--full|--head|--face|--crop 0.8] [--sharp]
                                         [--cols 130] [--gamma 0.85] [--lift 0.75] [--width 560]
                                         [--title "ibu-cyx0 / ascii-portrait"]
  --dark / --light : dark card with light glyphs (matches the profile theme) / light card
  --full / --head / --face : whole subject / head+shoulders / tight head crop
  --crop F : keep the top fraction F of the subject (0.8 = head to chest)
  --bright : bright areas = dense glyphs (face glows, dark hair/clothes fade) - best on the dark card
  --sketch K : add outline glow around features (eyes, nose, jaw, hair); K = strength, try 1.0
  --sharp : boost local contrast + sharpen (clearer eyes, nose, mouth)
  --cols N: characters per row (more = finer detail; card width stays fixed)
  --gamma G, --lift L : tone controls (lower gamma = bolder, lower lift = lighter clothes)
  --title T: text in the window title bar (use --title "" to hide the bar)
Output: ascii-portrait.svg   (prints the card's width x height)"""
import sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from xml.sax.saxutils import escape

RAMP = " .,:;-~+=*xzoO0#%8&@"      # sparse -> dense
BG_CUTOFF = 247
ASPECT = 8.0 / 4.8                  # line height / char width


def flag(n):
    return n in sys.argv


def val(n, default, cast=float):
    return cast(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else default


def build_lines(path="source-prepped.png", cols=130, head=False, face=False, crop=None,
                sharp=False, gamma=1.0, lift=1.0, sketch=0.0, bright=False):
    img = Image.open(path).convert("L")
    a = np.array(img)
    ys, xs = np.where(a < BG_CUTOFF)
    if len(xs):
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        if crop:
            y1 = y0 + int((y1 - y0) * crop)
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
    if face or sharp:
        img = ImageOps.autocontrast(img, cutoff=1)
        big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        big = big.filter(ImageFilter.UnsharpMask(radius=30, percent=70, threshold=0))
        big = big.filter(ImageFilter.UnsharpMask(radius=3, percent=200, threshold=2))
        img = big
    w, h = img.size
    rows = max(1, round(cols * h / w / ASPECT))
    g = np.array(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32)
    subj = g < BG_CUTOFF
    if bright:                                        # drop the blended silhouette fringe
        q = np.pad(subj, 1, constant_values=True)
        subj = subj & q[:-2, 1:-1] & q[2:, 1:-1] & q[1:-1, :-2] & q[1:-1, 2:]
    lo, hi = np.percentile(g[subj], [2, 98]) if subj.any() else (0, 255)
    v = np.clip((g - lo) / max(hi - lo, 1), 0, 1) ** lift
    dens = (v if bright else (1 - v)) ** gamma        # default: dark pixels = dense glyphs
    if sketch > 0:                                    # outline glow from image gradients
        f = np.array(img, dtype=np.float32)
        gy, gx = np.gradient(f)
        mag = Image.fromarray(np.clip(np.hypot(gx, gy) * 4, 0, 255).astype(np.uint8))
        m = np.array(mag.resize((cols, rows), Image.BOX), dtype=np.float32)
        m = np.clip(m / max(np.percentile(m[subj], 96), 1), 0, 1) if subj.any() else m
        dens = np.clip(0.45 * dens + sketch * 0.9 * m, 0, 1)
    return ["".join(" " if not subj[r, c] else RAMP[min(len(RAMP) - 1, int(dens[r, c] * len(RAMP)))]
                    for c in range(cols)) for r in range(rows)]


def write_svg(lines, cols, dark, width, title):
    CHAR_W = width / cols
    LINE_H = CHAR_W * ASPECT
    FONT = LINE_H
    rows = len(lines)
    PADX, PADB = 14, 14
    top = 40 if title else 14
    W, H = width + PADX * 2, rows * LINE_H + top + PADB
    if dark:
        bg, fg, edge, bar, muted, cur = "#07140d", "#bfe8cf", "#1d3b2a", "#0d2217", "#86b79b", "#4ade80"
    else:
        bg, fg, edge, bar, muted, cur = "#f6f8fa", "#24292f", "#d0d7de", "#eaeef2", "#57606a", "#0969da"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.1f} {H:.1f}">',
         f'<rect x="0.5" y="0.5" width="{W-1:.1f}" height="{H-1:.1f}" rx="8" fill="{bg}" stroke="{edge}"/>']
    if title:
        o += [f'<path d="M0.5 28 V8.5 Q0.5 0.5 8.5 0.5 H{W-8.5:.1f} Q{W-0.5:.1f} 0.5 {W-0.5:.1f} 8.5 V28 Z" fill="{bar}"/>',
              f'<line x1="0.5" y1="28" x2="{W-0.5:.1f}" y2="28" stroke="{edge}"/>',
              '<circle cx="16" cy="14" r="4.5" fill="#ff5f56"/><circle cx="32" cy="14" r="4.5" fill="#ffbd2e"/>'
              '<circle cx="48" cy="14" r="4.5" fill="#27c93f"/>',
              f'<text x="{W/2:.1f}" y="17.5" text-anchor="middle" style="font:10px Consolas,monospace;fill:{muted}">{escape(title)}</text>']
    o.append(f'<style>.a{{font-family:"Fira Code",Consolas,"Courier New",monospace;font-size:{FONT:.2f}px;'
             f'fill:{fg};white-space:pre}}</style><defs>')
    DUR, step = 0.45, min(0.05, 4.0 / rows)
    for i in range(rows):
        o.append(f'<clipPath id="c{i}"><rect x="{PADX}" y="{top + i*LINE_H:.2f}" width="0" height="{LINE_H:.2f}">'
                 f'<animate attributeName="width" from="0" to="{width:.1f}" begin="{i*step:.2f}s" dur="{DUR}s" fill="freeze"/>'
                 f'</rect></clipPath>')
    o.append('</defs>')
    for i, ln in enumerate(lines):
        t, y = i * step, top + i * LINE_H + FONT * 0.85
        if ln.strip():
            o.append(f'<text class="a" xml:space="preserve" x="{PADX}" y="{y:.2f}" textLength="{len(ln)*CHAR_W:.2f}" '
                     f'lengthAdjust="spacing" clip-path="url(#c{i})">{escape(ln)}</text>')
        o.append(f'<rect y="{top + i*LINE_H:.2f}" width="3" height="{LINE_H:.2f}" fill="{cur}" opacity="0" x="{PADX}">'
                 f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
                 f'<animate attributeName="x" from="{PADX}" to="{PADX + width:.1f}" begin="{t:.2f}s" dur="{DUR}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0" begin="{t+DUR:.2f}s"/></rect>')
    o.append('</svg>')
    open("ascii-portrait.svg", "w", encoding="utf-8").write("\n".join(o))
    return W, H


if __name__ == "__main__":
    cols = val("--cols", 130, int)
    dark = not flag("--light")
    lines = build_lines(cols=cols, crop=val("--crop", 0) or None, head=flag("--head"), face=flag("--face"), sharp=flag("--sharp"),
                        gamma=val("--gamma", 1.0), lift=val("--lift", 1.0), sketch=val("--sketch", 0.0), bright=flag("--bright"))
    title = val("--title", "ibu-cyx0 / ascii-portrait", str)
    W, H = write_svg(lines, cols, dark, val("--width", 560), title)
    print(f"wrote ascii-portrait.svg ({cols}x{len(lines)} chars), card {W:.0f}x{H:.0f}")
