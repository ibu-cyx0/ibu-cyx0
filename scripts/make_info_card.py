"""Hand-authored neofetch-style info card -> info-card.svg (STATIC=1 for frozen frame)."""
import os
from xml.sax.saxutils import escape

STATIC = os.environ.get("STATIC") == "1"
ROWS = [
 ("Now",        "SOC Analyst | Blue Team | Detection & Response", "#00d4ff"),
 ("Prev",       "SOC Analyst Intern @ The Mind IT (Jan-Apr 2026)", "#7c3aed"),
 ("Education",  "B.E. Cyber Security, Paavai Engineering College", "#00ff88"),
 ("Stack",      "Splunk, Wazuh, Sentinel, Defender, ELK, Python", "#ffb86c"),
 ("Certs",      "CSA, EHE, Splunk Core User, Cisco CyberOps", "#00d4ff"),
 ("Recognition","Wazuh Ambassador (Jun 2026)", "#7c3aed"),
 ("TryHackMe",  "Top 5% globally, 30+ rooms", "#00ff88"),
 ("Highlights", "CTI automation, ML alert triage, SOC home lab", "#ffb86c"),
]
W, LH, TOP = 490, 24, 62
H = TOP + len(ROWS) * LH + 24

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<style>text{font-family:"Fira Code",Consolas,monospace;font-size:12px;fill:#c8d8e8}'
 '.k{font-weight:bold}'
 + ('' if STATIC else '.l{opacity:0;animation:in .45s ease-out forwards}'
    '@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}')
 + '</style>',
 f'<rect width="{W}" height="{H}" rx="8" fill="#0d1117" stroke="#30363d"/>',
 f'<rect width="{W}" height="28" rx="8" fill="#161b22"/>',
 '<circle cx="16" cy="14" r="5" fill="#ff5f56"/><circle cx="34" cy="14" r="5" fill="#ffbd2e"/><circle cx="52" cy="14" r="5" fill="#27c93f"/>',
 f'<text x="{W//2}" y="18" text-anchor="middle" style="fill:#8b949e">ibu-cyx0@soc-workstation: ~</text>',
 f'<text x="16" y="50" style="fill:#00ff88">$ neofetch</text>']
for i, (k, v, c) in enumerate(ROWS):
    y = TOP + i * LH + 14
    cls = "l" if not STATIC else ""
    delay = f' style="animation-delay:{0.25*i+0.3:.2f}s"' if not STATIC else ""
    o.append(f'<g class="{cls}"{delay}><text class="k" x="16" y="{y}" style="fill:{c}">{escape(k)}</text>'
             f'<text x="120" y="{y}">{escape(v)}</text></g>')
o.append('</svg>')
open("info-card.svg", "w").write("\n".join(o))
print("wrote info-card.svg")
