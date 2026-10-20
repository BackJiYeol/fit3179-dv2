"""
#10 chart, advanced-idiom upgrade (2026-10-20): the bottom panel ("Pokémon
removed" line chart) becomes a Bump chart, so the dashboard keeps 8/10
advanced idioms after #3 was reclassified from advanced (Icicle/Mosaic,
Tree idiom family) to basic (plain stacked bar, Bar chart family) on
2026-10-19.

Why a Bump chart fits here specifically: #10's own title is "A boom at the
top, a changing of the guard below" -- the ORIGINAL design already implied
a rank story for the four challengers beneath Pokémon, but the old bottom
panel only plotted their raw values as a second line chart (still Line
chart family = basic, same idiom as the top panel, so it didn't add any
new idiom to the dashboard's diversity count either). A Bump chart plots
RANK over time instead of raw value, which is the literal idiom for
"changing of the guard" (Kirk 2019 calls this a slope graph; FIT3179 Week 5
Workshop's own idiom list names it directly as idiom #10, "Bump chart",
grouped with Slope chart / Streamgraph / Parallel coordinates -- confirming
it's taught and advanced-tier, not a Marimekko-style exclusion risk).

Data: reuses the exact same Google Trends weekly data as the existing #10
top panel (site/data/c10_timeseries.json, 2021-09-26 to 2026-09-27, 5
games) -- no new collection. Weekly resolution is too noisy for a rank
chart (ranks would flicker almost every week from search-interest noise),
so this script aggregates to quarterly means first, then ranks the four
non-Pokémon games within each quarter. Pokémon is excluded from the ranking
itself (it is #1 every single quarter by a huge margin -- that's the
"boom at the top" the TOP panel already shows; putting it in the bump
chart too would just draw a flat uninteresting line at rank 1 forever and
visually crowd out the actual story, which is what happens BELOW it).
"""
import json
from collections import defaultdict
from datetime import date

SRC = "c10_timeseries.json"
OUT = "c10_bump_data.json"

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

# drop the first and last quarter if they are partial (few weeks only),
# so the ranking isn't distorted by a half-quarter average
qweeks = defaultdict(int)
for (y, q, _g), c in counts.items():
    qweeks[(y, q)] += c
full_quarters = [qq for qq in quarters if qweeks[qq] >= games.__len__() * 10]
# (10 weeks/game minimum ~ roughly a full quarter's worth per game; drops
#  the partial first/last quarter automatically)
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
print(f"wrote {OUT} - {len(rows_out)} rows, {len(quarters)} quarters ({quarters[0]} to {quarters[-1]})")
print("games ranked:", games)

# sanity check: print final-quarter standings
last_q = quarters[-1]
final = [r for r in rows_out if r["period_order"] == len(quarters) - 1]
final.sort(key=lambda r: r["rank"])
print(f"final quarter {last_q} standings:")
for r in final:
    print(f"  #{r['rank']} {r['game']} (avg {r['avg_value']})")