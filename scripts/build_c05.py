"""
#5 Parallel coordinates: one line per era.

Input:  raw/pkm_sets.json, raw/ygo_cardsets.json
Output: data/c05_parallel.json

Axes (each has its own unit):
  Sets released       sets in the era
  Sets per year       sets / era length in years
  Cards per set       average cards per set
  Share of all cards  % of that game's cards released in the era

Rules:
  - MIN_CARDS = 10: drop promo sets with fewer than 10 cards (same as c06).
  - LAST_COMPLETE_YEAR = 2025: skip the unfinished year.
  - Pokémon eras use the "series" field; "Other" and series with
    fewer than 3 sets are dropped.
  - Yu-Gi-Oh has no series field, so eras follow the anime air years.
  - Era length = first to last year with a release in the data.

Run: python scripts/build_c05.py
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKM = ROOT / "raw" / "pkm_sets.json"
YGO = ROOT / "raw" / "ygo_cardsets.json"
OUT = ROOT / "data" / "c05_parallel.json"

MIN_CARDS = 10
LAST_COMPLETE_YEAR = 2025
MIN_SETS_PER_ERA = 3
EXCLUDED_POKEMON_SERIES = {"Other"}

# Yu-Gi-Oh eras by anime air years (no series field in the data).
YGO_ERAS = [
    ("Duel Monsters", 2002, 2004), ("GX", 2005, 2008), ("5D's", 2009, 2011),
    ("Zexal", 2012, 2014), ("Arc-V", 2015, 2017), ("VRAINS", 2018, 2019),
    ("SEVENS", 2020, 2021), ("GO RUSH!!", 2022, 2023), ("Current", 2024, 2025),
]


def ygo_era(year):
    for name, start, end in YGO_ERAS:
        if start <= year <= end:
            return name
    return None


def collect(records, date_field, size_field, era_of):
    """Per era: set count, card count, first year, last year."""
    buckets = defaultdict(lambda: {"sets": 0, "cards": 0,
                                   "first": 9999, "last": 0})
    for rec in records:
        raw = rec.get(date_field)
        cards = rec.get(size_field) or 0
        if not raw or cards < MIN_CARDS:
            continue
        year = int(raw.replace("/", "-")[:4])
        if year > LAST_COMPLETE_YEAR:
            continue
        era = era_of(rec, year)
        if era is None:
            continue
        b = buckets[era]
        b["sets"] += 1
        b["cards"] += cards
        b["first"] = min(b["first"], year)
        b["last"] = max(b["last"], year)
    return buckets


def to_rows(game, buckets):
    total_cards = sum(b["cards"] for b in buckets.values())
    rows = []
    for era, b in buckets.items():
        if b["sets"] < MIN_SETS_PER_ERA:
            continue
        years = b["last"] - b["first"] + 1
        rows.append({
            "game": game,
            "era": era,
            "Sets released": b["sets"],
            "Cards per set": round(b["cards"] / b["sets"], 1),
            "Sets per year": round(b["sets"] / years, 1),
            "Share of all cards": round(b["cards"] / total_cards * 100, 1),
            "_years": f'{b["first"]}-{b["last"]}',
        })
    rows.sort(key=lambda r: r["era"])
    return rows


def main() -> None:
    pkm = json.loads(PKM.read_text(encoding="utf-8"))
    ygo = json.loads(YGO.read_text(encoding="utf-8"))

    pkm_buckets = collect(
        pkm, "releaseDate", "total",
        lambda rec, _year: (None if rec.get("series") in EXCLUDED_POKEMON_SERIES
                            else rec.get("series")))
    ygo_buckets = collect(
        ygo, "tcg_date", "num_of_cards",
        lambda _rec, year: ygo_era(year))

    rows = to_rows("Pokémon", pkm_buckets) + to_rows("Yu-Gi-Oh", ygo_buckets)

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    print(f"{len(rows)} eras")
    for game in ("Pokémon", "Yu-Gi-Oh"):
        sel = [r for r in rows if r["game"] == game]
        print(f"  {game} — {len(sel)} eras")
        for r in sel:
            print(f"     {r['era']:22} {r['_years']:10} "
                  f"sets {r['Sets released']:3d}  "
                  f"cards/set {r['Cards per set']:6.1f}  "
                  f"sets/yr {r['Sets per year']:5.1f}  "
                  f"share {r['Share of all cards']:5.1f}%")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()