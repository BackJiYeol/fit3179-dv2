"""
#6 Calendar heatmap: set releases per month, both games.

Input:  raw/pkm_sets.json      (github.com/PokemonTCG/pokemon-tcg-data, sets/en.json)
        raw/ygo_cardsets.json  (db.ygoprodeck.com/api/v7/cardsets.php)
Output: data/c06_calendar.json
        [{"game": "Pokémon", "year": 2002, "month": 3, "sets": 1, "pct": 0.57}, ...]

Method:
  - Common window only: from the later first release to the earlier last
    release (2002-03 to 2025-12), so both panels share one time axis.
  - Every month in the window is kept; months with no release get sets=0.
  - pct = sets that month / that game's sets in the window x 100.
    Shares, not counts, because the two games release at different scales.
  - Date formats differ: Pokémon "1999/01/09" (releaseDate),
    Yu-Gi-Oh "2015-05-28" (tcg_date). Both start with year-month.
    
Run: python scripts/build_c06.py
"""
import json
from collections import Counter
from pathlib import Path

# Sets with fewer cards are promos, not expansions (see docstring).
MIN_CARDS = 10

# Skip the unfinished year.
LAST_COMPLETE_YEAR = 2025

ROOT = Path(__file__).resolve().parent.parent
PKM = ROOT / "raw" / "pkm_sets.json"
YGO = ROOT / "raw" / "ygo_cardsets.json"
OUT = ROOT / "data" / "c06_calendar.json"


def year_month(raw_date: str):
    """'1999/01/09' or '2015-05-28' -> (year, month)."""
    d = raw_date.replace("/", "-")
    return int(d[0:4]), int(d[5:7])


def count_sets(records, date_field, size_field):
    """Count dated sets with at least MIN_CARDS cards per (year, month)."""
    counter = Counter()
    no_date = 0
    too_small = 0
    for rec in records:
        raw = rec.get(date_field)
        if not raw:
            no_date += 1
            continue
        if (rec.get(size_field) or 0) < MIN_CARDS:
            too_small += 1
            continue
        counter[year_month(raw)] += 1
    return counter, no_date, too_small


def main() -> None:
    pkm = json.loads(PKM.read_text(encoding="utf-8"))
    ygo = json.loads(YGO.read_text(encoding="utf-8"))

    # Card-count field: total (Pokémon), num_of_cards (Yu-Gi-Oh)
    pkm_counts, pkm_no_date, pkm_small = count_sets(pkm, "releaseDate", "total")
    ygo_counts, ygo_no_date, ygo_small = count_sets(ygo, "tcg_date", "num_of_cards")

    def to_index(ym):
        """(year, month) -> running month number."""
        return ym[0] * 12 + (ym[1] - 1)

    # Common window, capped at December of the last complete year.
    start = max(to_index(min(pkm_counts)), to_index(min(ygo_counts)))
    end = min(to_index(max(pkm_counts)),
              to_index(max(ygo_counts)),
              to_index((LAST_COMPLETE_YEAR, 12)))

    rows = []
    for game, counts in (("Pokémon", pkm_counts), ("Yu-Gi-Oh", ygo_counts)):
        # Denominator: this game's sets inside the window only.
        window_total = sum(n for ym, n in counts.items()
                           if start <= to_index(ym) <= end)

        for t in range(start, end + 1):
            year, month = divmod(t, 12)
            month += 1
            n = counts.get((year, month), 0)
            rows.append({
                "game": game,
                "year": year,
                "month": month,
                "sets": n,
                "pct": round(n / window_total * 100, 2),
            })

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- summary ----
    for game, counts, no_date, small, total in (
        ("Pokémon", pkm_counts, pkm_no_date, pkm_small, len(pkm)),
        ("Yu-Gi-Oh", ygo_counts, ygo_no_date, ygo_small, len(ygo)),
    ):
        used = sum(counts.values())
        years = sorted({y for y, _ in counts})
        months = Counter()
        for (_, m), n in counts.items():
            months[m] += n
        print(f"{game}: {used}/{total} sets kept "
              f"({no_date} undated, {small} under {MIN_CARDS} cards), "
              f"{years[0]}-{years[-1]}")
        print("   by month " + " ".join(f"{m:02d}:{months[m]}" for m in range(1, 13)))

    zero = sum(1 for r in rows if r["sets"] == 0)
    first_row, last_row = rows[0], rows[len(rows) // 2 - 1]
    print(f"common window {first_row['year']}-{first_row['month']:02d} .. "
          f"{last_row['year']}-{last_row['month']:02d}")
    for game in ("Pokémon", "Yu-Gi-Oh"):
        g = [r for r in rows if r["game"] == game]
        z = sum(1 for r in g if r["sets"] == 0)
        print(f"   {game}: {sum(r['sets'] for r in g)} sets in window, "
              f"{z}/{len(g)} months with none ({z / len(g) * 100:.0f}%)")
    print(f"{len(rows)} cells ({zero} with zero releases) "
          f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()