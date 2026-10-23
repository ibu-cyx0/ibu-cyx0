"""Build stats-card.svg (terminal-style dashboard).
Reads data/contributions.json (auto numbers) and stats.json (what to show / manual numbers).
Usage: python scripts/make_stats_svg.py [--height 335]
Height is matched to ascii-portrait.svg (shown 370px wide) unless --height is given."""
import json, math, os, re, sys
from datetime import datetime
from xml.sax.saxutils import escape

DATA = json.load(open("data/contributions.json"))
days = DATA["days"]
user = DATA.get("user", "ibu-cyx0")
CFG = json.load(open("stats.json")) if os.path.exists("stats.json") else {}


def fmt(s):
    d = datetime.strptime(s, "%Y-%m-%d")
    return f"{d.strftime('%b')} {d.day}"


# ---- auto stats --------------------------------------------------------
total = sum(d["count"] for d in days)
active = [d for d in days if d["count"] > 0]
best = max(days, key=lambda d: d["count"])
avg = total / len(active) if active else 0
runs, cur = [], []
for d in days:
    if d["count"] > 0:
        cur.append(d)
    elif cur:
        runs.append(cur); cur = []
if cur:
    runs.append(cur)
longest = max(runs, key=len) if runs else []
cur_run = []
if runs:
    gap = (datetime.strptime(days[-1]["date"], "%Y-%m-%d") - datetime.strptime(runs[-1][-1]["date"], "%Y-%m-%d")).days
    if gap <= 1:
        cur_run = runs[-1]
rng = lambda r: ("start one today" if not r else fmt(r[0]["date"]) if len(r) == 1
                 else f'{fmt(r[0]["date"])} – {fmt(r[-1]["date"])}')
plural = lambda n: " day" if n == 1 else " days"
AUTO = {
    "current_streak": dict(value=str(len(cur_run)), unit=plural(len(cur_run)), caption=rng(cur_run), highlight=True),
    "longest_streak": dict(value=str(len(longest)), unit=plural(len(longest)), caption=rng(longest)),
    "contributions": dict(value=f"{total:,}", unit="", caption="in the last year"),
    "active_days": dict(value=str(len(active)), unit=f" / {len(days)}", caption=f"{100*len(active)/len(days):.0f}% of the year"),
    "best_day": dict(value=str(best["count"]), unit="", caption=fmt(best["date"])),
    "avg_active_day": dict(value=f"{avg:.1f}", unit="", caption="contributions"),
}
DEFAULT_TILES = [{"label": l, "source": s} for l, s in [
    ("current streak", "current_streak"), ("longest streak", "longest_streak"), ("contributions", "contributions"),
    ("active days", "active_days"), ("best day", "best_day"), ("avg / active day", "avg_active_day")]]

tiles = []
for t in (CFG.get("tiles") or DEFAULT_TILES)[:8]:
    base = dict(AUTO.get(t.get("source", ""), dict(value="", unit="", caption="", highlight=False)))
    base.update({k: t[k] for k in ("value", "unit", "caption", "highlight") if k in t})
    tiles.append((str(t.get("label", t.get("source", ""))), str(base["value"]), str(base.get("unit", "")),
                  str(base.get("caption", "")), bool(base.get("highlight", False))))

# ---- chart data ----------------------------------------------------------
ch = CFG.get("chart", {})
show_chart = ch.get("show", True)
if ch.get("mode", "auto") == "manual" and ch.get("values"):
    vals = [float(v) for v in ch["values"]]
    letters = [str(x) for x in (ch.get("labels") or [""] * len(vals))][:len(vals)]
else:
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    keys = sorted(months)[-12:]
    vals = [months[k] for k in keys]
    letters = [datetime.strptime(k, "%Y-%m").strftime("%b")[0] for k in keys]
chart_title = ch.get("title", "contributions / month")

# ---- size ------------------------------------------------------------------
W, H = 490, None
if "--height" in sys.argv:
    H = int(sys.argv[sys.argv.index("--height") + 1])
elif os.path.exists("ascii-portrait.svg"):
    m = re.search(r'width="(\d+)" height="(\d+)"', open("ascii-portrait.svg").read())
    if m:
        H = round(int(m.group(2)) * 370 / int(m.group(1)))
H = H or 335

BG, EDGE, BAR, TILE, MUTED, GREEN, TEXT = "#07140d", "#1d3b2a", "#0d2217", "#0b1d13", "#86b79b", "#4ade80", "#d9f2e3"
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
     f'<text x="{W/2}" y="17.5" text-anchor="middle" font-size="10" fill="{MUTED}">{escape(str(CFG.get("title", f"{user} / contribution-stats")))}</text>']

top, gap, pad = 40, 8, 14
rows = max(1, math.ceil(len(tiles) / 2))
chart_h = max(92, int(H * 0.32)) if show_chart else 0
tile_h = (H - top - pad - chart_h - (gap if show_chart else 0) - gap * (rows - 1)) / rows
cell_w = (W - pad * 2 - gap) / 2
for i, (label, big, small, cap, hi) in enumerate(tiles):
    full = (i == len(tiles) - 1 and i % 2 == 0)           # a lone last tile spans the row
    x = pad + (0 if full else (i % 2) * (cell_w + gap))
    tw = (W - 2 * pad) if full else cell_w
    y = top + (i // 2) * (tile_h + gap)
    fs = max(11, min(22, tile_h * 0.38, (tw - 24) / (0.62 * max(len(big) + len(small) * 0.6, 1))))
    o.append(f'<g class="t" style="animation-delay:{0.08*i+0.1:.2f}s">'
             f'<rect x="{x:.1f}" y="{y:.1f}" width="{tw:.1f}" height="{tile_h:.1f}" rx="6" fill="{TILE}" stroke="{EDGE}"/>'
             f'<text x="{x+10:.1f}" y="{y+15:.1f}" font-size="9" fill="{MUTED}">{escape(label)}</text>'
             f'<text x="{x+10:.1f}" y="{y+tile_h*0.66:.1f}" font-size="{fs:.0f}" font-weight="bold" fill="{GREEN if hi else TEXT}">'
             f'{escape(big)}<tspan font-size="11" font-weight="normal" fill="{MUTED}">{escape(small)}</tspan></text>'
             f'<text x="{x+10:.1f}" y="{y+tile_h-7:.1f}" font-size="8.5" fill="{MUTED}">{escape(cap)}</text></g>')

if show_chart and vals:
    cy = top + rows * (tile_h + gap)
    o.append(f'<rect x="{pad}" y="{cy:.1f}" width="{W-2*pad}" height="{chart_h:.1f}" rx="6" fill="{TILE}" stroke="{EDGE}"/>')
    o.append(f'<text x="{pad+10}" y="{cy+15:.1f}" font-size="9" fill="{MUTED}">{escape(chart_title)}</text>')
    inner_x, inner_w = pad + 14, W - 2 * pad - 28
    base, maxh = cy + chart_h - 18, chart_h - 46
    vmax = max(vals) if max(vals) > 0 else 1
    slot = inner_w / len(vals)
    bw = min(slot * 0.62, 34)
    for i, (v, c) in enumerate(zip(vals, letters)):
        h = max(2, v / vmax * maxh) if v > 0 else 2
        x = inner_x + i * slot + (slot - bw) / 2
        fill = GREEN if v == vmax and v > 0 else "#16a34a" if v > 0 else "#14532d"
        o.append(f'<rect class="b" style="animation-delay:{0.4+0.05*i:.2f}s" x="{x:.1f}" y="{base-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{fill}"/>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{base+11:.1f}" font-size="8" text-anchor="middle" fill="{MUTED}">{escape(c)}</text>')
        if v == vmax and v > 0:
            o.append(f'<text x="{x+bw/2:.1f}" y="{base-h-4:.1f}" font-size="8.5" text-anchor="middle" fill="{GREEN}">{v:g}</text>')
o.append('</svg>')
open("stats-card.svg", "w", encoding="utf-8").write("\n".join(o))
print(f"wrote stats-card.svg {W}x{H} | {len(tiles)} tiles, chart={'on' if show_chart else 'off'}")
