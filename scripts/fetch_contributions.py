"""Scrape the public GitHub contribution calendar (no token needed)."""
import json, os, sys
from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "ibu-cyx0")
URL = f"https://github.com/users/{USER}/contributions"

def fetch_days():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {}
    for t in soup.find_all("tool-tip"):
        txt = t.get_text(" ", strip=True)
        tips[t.get("for")] = txt
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        d = td.get("data-date")
        if not d:
            continue
        level = int(td.get("data-level", 0))
        txt = tips.get(td.get("id"), "")
        count = 0
        if txt and not txt.startswith("No contributions"):
            try:
                count = int(txt.split()[0])
            except ValueError:
                count = 0
        days.append({"date": d, "count": count, "level": level})
    days.sort(key=lambda x: x["date"])
    return days

def stats(days):
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"]) if days else None
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)
    # current streak (today may still be empty)
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif d is days[-1]:
            continue
        else:
            break
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    return {"total": total, "current_streak": current, "longest_streak": longest,
            "best_day": best, "monthly": months}

if __name__ == "__main__":
    days = fetch_days()
    if not days:
        sys.exit("No contribution cells parsed; GitHub markup may have changed.")
    os.makedirs("data", exist_ok=True)
    with open("data/contributions.json", "w") as f:
        json.dump({"user": USER, "days": days, "stats": stats(days)}, f, indent=1)
    print(f"{len(days)} days, {sum(d['count'] for d in days)} contributions")
