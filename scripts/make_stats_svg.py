"""Build stats-card.svg (terminal-style dashboard) from data/contributions.json.
Usage: python scripts/make_stats_svg.py [--height 335]
If --height is omitted it is matched to ascii-portrait.svg (shown 370px wide) so both cards line up."""
import json, re, sys, os
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

DATA = json.load(open("data/contributions.json"))
days = DATA["days"]
user = DATA.get("user", "ibu-cyx0")
fmt = lambda s: datetime.strptime(s, "%Y-%m-%d").strftime("%b %-d") if os.name != "nt" else \
    datetime.strptime(s, "%Y-%m-%d").strftime("%b %d").replace(" 0", " ")

# ---- stats -------------------------------------------------------------
total = sum(d["count"] for d in days)
active = [d for d in days if d["count"] > 0]
best = max(days, key=lambda d: d["count"])
avg = total / len(active) if active else 0

def runs():
    out, cur = [], []
    for d in days:
        if d["count"] > 0:
            cur.append(d)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out

R = runs()
longest = max(R, key=len) if R else []
# current streak: run that ends on the last day, or the day before it (today may still be empty)
cur_run = []
if R:
    last = R[-1]
    end = datetime.strptime(last[-1]["date"], "%Y-%m-%d")
    final = datetime.strptime(days[-1]["date"], "%Y-%m-%d")
    if (final - end).days <= 1:
        cur_run = last
rng = lambda r: ("start one today" if not r else fmt(r[0]["date"]) if len(r) == 1
                 else f'{fmt(r[0]["date"])} – {fmt(r[-1]["date"])}')
plural = lambda n: " day" if n == 1 else " days"

months = {}
for d in days:
    months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
keys = sorted(months)[-12:]
vals = [months[k] for k in keys]
letters = [datetime.strptime(k, "%Y-%m").strftime("%b")[0] for k in keys]

# ---- size --------------------------------------------------------------
W = 490
H = None
if "--height" in sys.argv:
    H = int(sys.argv[sys.argv.index("--height") + 1])
elif os.path.exists("ascii-portrait.svg"):
    m = re.search(r'width="(\d+)" height="(\d+)"', open("ascii-portrait.svg").read())
    if m:
        H = round(int(m.group(2)) * 370 / int(m.group(1)))
H = H or 335

BG, EDGE, BAR, TILE, MUTED, GREEN, TEXT = "#07140d", "#1d3b2a", "#0d2217", "#0b1d13", "#86b79b", "#4ade80", "#d9f2e3"
tiles = [
    ("current streak", f"{len(cur_run)}", plural(len(cur_run)), rng(cur_run), True),
    ("longest streak", f"{len(longest)}", plural(len(longest)), rng(longest), False),
    ("contributions", f"{total:,}", "", "in the last year", False),
    ("active days", f"{len(active)}", f" / {len(days)}", f"{100*len(active)/len(days):.0f}% of the year", False),
    ("best day", f"{best['count']}", "", fmt(best["date"]), False),
    ("avg / active day", f"{avg:.1f}", "", "contributions", False),
]

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     '<style>text{font-family:"Fira Code",Consolas,"Courier New",monospace}'
     '.t{opacity:0;animation:in .5s ease-out forwards}'
     '.b{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:grow .7s ease-out forwards}'
     '@keyframes in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}'
     '@keyframes grow{to{transform:scaleY(1)}}</style>',
     f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="{BG}" stroke="{EDGE}"/>',
     f'<path d="M0.5 28 V8.5 Q0.5 0.5 8.5 0.5 H{W-8.5} Q{W-0.5} 0.5 {W-0.5} 8.5 V28 Z" fill="{BAR}"/>',
     f'<line x1="0.5" y1="28" x2="{W-0.5}" y2="28" stroke="{EDGE}"/>',
     '<circle cx="16" cy="14" r="4.5" fill="#ff5f56"/><circle cx="32" cy="14" r="4.5" fill="#ffbd2e"/><circle cx="48" cy="14" r="4.5" fill="#27c93f"/>',
     f'<text x="{W/2}" y="17.5" text-anchor="middle" font-size="10" fill="{MUTED}">{escape(user)} / contribution-stats</text>']

# tiles: 2 columns x 3 rows
top, gap, pad = 40, 8, 14
tile_w = (W - pad * 2 - gap) / 2
chart_h = max(92, int(H * 0.32))
tile_h = (H - top - pad - chart_h - gap * 3) / 3
for i, (label, big, small, cap, hi) in enumerate(tiles):
    x = pad + (i % 2) * (tile_w + gap)
    y = top + (i // 2) * (tile_h + gap)
    d = f'{0.08*i+0.1:.2f}s'
    o.append(f'<g class="t" style="animation-delay:{d}">'
             f'<rect x="{x:.1f}" y="{y:.1f}" width="{tile_w:.1f}" height="{tile_h:.1f}" rx="6" fill="{TILE}" stroke="{EDGE}"/>'
             f'<text x="{x+10:.1f}" y="{y+15:.1f}" font-size="9" fill="{MUTED}">{escape(label)}</text>'
             f'<text x="{x+10:.1f}" y="{y+tile_h*0.66:.1f}" font-size="{min(22, tile_h*0.38):.0f}" font-weight="bold" '
             f'fill="{GREEN if hi else TEXT}">{escape(big)}<tspan font-size="11" font-weight="normal" fill="{MUTED}">{escape(small)}</tspan></text>'
             f'<text x="{x+10:.1f}" y="{y+tile_h-7:.1f}" font-size="8.5" fill="{MUTED}">{escape(cap)}</text></g>')

# monthly bar chart
cy = top + 3 * tile_h + 3 * gap
o.append(f'<rect x="{pad}" y="{cy:.1f}" width="{W-2*pad}" height="{chart_h:.1f}" rx="6" fill="{TILE}" stroke="{EDGE}"/>')
o.append(f'<text x="{pad+10}" y="{cy+15:.1f}" font-size="9" fill="{MUTED}">contributions / month</text>')
inner_x, inner_w = pad + 14, W - 2 * pad - 28
base = cy + chart_h - 18
maxh = chart_h - 46
vmax = max(vals) if vals and max(vals) > 0 else 1
slot = inner_w / len(vals)
bw = slot * 0.62
for i, (v, ch) in enumerate(zip(vals, letters)):
    h = max(2, v / vmax * maxh) if v > 0 else 2
    x = inner_x + i * slot + (slot - bw) / 2
    fill = GREEN if v == vmax and v > 0 else "#16a34a" if v > 0 else "#14532d"
    o.append(f'<rect class="b" style="animation-delay:{0.4+0.05*i:.2f}s" x="{x:.1f}" y="{base-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{fill}"/>')
    o.append(f'<text x="{x+bw/2:.1f}" y="{base+11:.1f}" font-size="8" text-anchor="middle" fill="{MUTED}">{ch}</text>')
    if v == vmax and v > 0:
        o.append(f'<text x="{x+bw/2:.1f}" y="{base-h-4:.1f}" font-size="8.5" text-anchor="middle" fill="{GREEN}">{v}</text>')
o.append('</svg>')
open("stats-card.svg", "w", encoding="utf-8").write("\n".join(o))
print(f"wrote stats-card.svg {W}x{H} | streak {len(cur_run)}d, longest {len(longest)}d, active {len(active)}/{len(days)}")
