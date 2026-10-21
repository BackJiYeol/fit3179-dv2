"""
#10 Bump chart: quarterly rank of the four games below Pokémon.

Input:  data/c10_timeseries.json  weekly Google Trends values (build_c10.py)
Output: data/c10_bump.json

Method:
  - Weekly values are too noisy for ranks, so average per quarter first.
  - Drop partial quarters (fewer than 10 weeks per game).
  - Rank the four games per quarter (1 = highest average).
  - Pokémon is left out: it is first in every quarter.

Run: python scripts/build_c10_bump.py
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "c10_timeseries.json"
OUT = ROOT / "data" / "c10_bump.json"

rows = json.load(open(SRC, encoding="utf-8"))

def to_quarter(d):
    y, m, _ = d.split("-")
    q = (int(m) - 1) // 3 + 1
    return int(y), q

# quarterly mean per game (excluding Pokémon)
sums = defaultdict(float)
counts = defaultdict(int)
for r in rows:
    if r["game"] == "Pokémon":
        continue
    y, q = to_quarter(r["date"])
    key = (y, q, r["game"])
    sums[key] += r["value"]
    counts[key] += 1

quarters = sorted(set((y, q) for (y, q, _g) in sums.keys()))
games = sorted(set(g for (_y, _q, g) in sums.keys()))

# drop partial first/last quarters
qweeks = defaultdict(int)
for (y, q, _g), c in counts.items():
    qweeks[(y, q)] += c
full_quarters = [qq for qq in quarters if qweeks[qq] >= len(games) * 10]
quarters = full_quarters if full_quarters else quarters

rows_out = []
for qi, (y, q) in enumerate(quarters):
    period_label = f"{str(y)[2:]} Q{q}"
    vals = []
    for g in games:
        key = (y, q, g)
        if counts.get(key, 0) == 0:
            continue
        avg = sums[key] / counts[key]
        vals.append((g, avg))
    vals.sort(key=lambda t: -t[1])  # highest avg interest = rank 1
    GAME_SHORT = {
        "Magic: The Gathering": "Magic",
        "Sports cards": "Sports cards",
        "Yu-Gi-Oh": "Yu-Gi-Oh",
        "One Piece": "One Piece",
    }
    for rank, (g, avg) in enumerate(vals, start=1):
        rows_out.append({
            "period": period_label,
            "period_order": qi,
            "game": g,
            "game_short": GAME_SHORT.get(g, g),
            "avg_value": round(avg, 2),
            "rank": rank,
            "is_last": qi == len(quarters) - 1,
        })

json.dump(rows_out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"wrote {OUT.relative_to(ROOT)}: {len(rows_out)} rows, {len(quarters)} quarters ({quarters[0]} to {quarters[-1]})")
print("games ranked:", games)

# sanity check: print final-quarter standings
last_q = quarters[-1]
final = [r for r in rows_out if r["period_order"] == len(quarters) - 1]
final.sort(key=lambda r: r["rank"])
print(f"final quarter {last_q} standings:")
for r in final:
    print(f"  #{r['rank']} {r['game']} (avg {r['avg_value']})")