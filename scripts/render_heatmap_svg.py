"""Render data/contributions.json as an animated 53x7 heatmap SVG."""
import json
from datetime import datetime

# Green "matrix" theme: empty days are a dim green tint, active days glow brighter.
# Empty days stay visibly different from active ones so the graph stays truthful.
PALETTE = ["#10301f", "#14532d", "#16a34a", "#22c55e", "#4ade80", "#bbf7d0"]
CARD_BG = "#07140d"
CELL, GAP, LEFT, TOP = 12, 3, 40, 70
STEP = CELL + GAP

data = json.load(open("data/contributions.json"))
days, st = data["days"], data["stats"]

first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
offset = (first.weekday() + 1) % 7  # Sunday = row 0
weeks = (offset + len(days) + 6) // 7
W = LEFT + weeks * STEP + 20
H = TOP + 7 * STEP + 56

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<style>',
 'text{font-family:"Fira Code",Consolas,monospace;fill:#86b79b;font-size:10px}',
 '.t{fill:#4ade80;font-size:13px}',
 '.c{opacity:0;animation:in .5s ease-out forwards}',
 '@keyframes in{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}',
 '</style>',
 f'<rect width="{W}" height="{H}" rx="8" fill="{CARD_BG}"/>',
 f'<text class="t" x="{LEFT}" y="24">{st["total"]:,} contributions in the last year</text>',
 f'<text x="{LEFT}" y="42">current streak {st["current_streak"]}d  |  longest {st["longest_streak"]}d</text>']

for i, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    out.append(f'<text x="6" y="{TOP + i*STEP + 10}">{lab}</text>')

last_month = None
last_label_col = -99
for idx, d in enumerate(days):
    pos = idx + offset
    col, row = pos // 7, pos % 7
    x, y = LEFT + col * STEP, TOP + row * STEP
    m = d["date"][:7]
    if m != last_month and row < 7:
        if (last_month is not None or col == 0) and col - last_label_col >= 4:
            name = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%b")
            out.append(f'<text x="{x}" y="{TOP-8}">{name}</text>')
            last_label_col = col
        last_month = m
    delay = (col + row) * 0.02
    lvl = min(d["level"], 5)
    out.append(f'<rect class="c" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" '
               f'width="{CELL}" height="{CELL}" rx="2" fill="{PALETTE[lvl]}"><title>{d["count"]} on {d["date"]}</title></rect>')

ly = TOP + 7 * STEP + 22
lx = W - 20 - 6 * STEP - 70
out.append(f'<text x="{lx}" y="{ly+10}">Less</text>')
for i, c in enumerate(PALETTE):
    out.append(f'<rect x="{lx+34+i*STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>')
out.append(f'<text x="{lx+38+6*STEP}" y="{ly+10}">More</text>')
out.append('</svg>')
open("contrib-heatmap.svg", "w").write("\n".join(out))
print("wrote contrib-heatmap.svg")
