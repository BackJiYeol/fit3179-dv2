"""
#1 Bar chart: average Google search interest per game.

Input : csv/time_5games.csv  (Google Trends, weekly, worldwide, 2021-2026)
Output: data/c01_ranking.json  [{"game", "value", "source"}]

value = mean of the 262 weekly index values (100 = peak week in the query).
"""
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "csv" / "time_5games.csv"
OUT = ROOT / "data" / "c01_ranking.json"

# Google Trends exports headers in the browser language. Our CSVs were saved
# from a Korean browser, so the first column is "\uc8fc" ("Week").
HEADER_FIRST_CELL = ("Week", "\uc8fc")

LABEL = {
    "Pokemon cards":             "Pokémon",
    "sports cards":              "Sports cards",
    "Yugioh cards":              "Yu-Gi-Oh",
    "One Piece cards":           "One Piece",
    "Magic the Gathering cards": "Magic: The Gathering",
}

SOURCE_NOTE = "Google Trends multiTimeline.csv, 5y weekly mean"


def to_number(raw: str) -> float:
    """'<1' becomes 0.5; anything else is read as a number."""
    raw = raw.strip()
    return 0.5 if raw.startswith("<") else float(raw)


def main() -> None:
    rows = list(csv.reader(SRC.open(encoding="utf-8-sig")))

    header_i = next(i for i, r in enumerate(rows) if r and r[0] in HEADER_FIRST_CELL)
    header = rows[header_i]
    body = [r for r in rows[header_i + 1:] if r and r[0]]

    columns = [c.split(":")[0].strip() for c in header[1:]]

    result = []
    for j, col in enumerate(columns):
        weekly = [to_number(r[j + 1]) for r in body]
        result.append({
            "game": LABEL[col],
            "value": round(statistics.mean(weekly), 1),
            "source": SOURCE_NOTE,
        })

    result.sort(key=lambda d: -d["value"])

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"{len(body)} weeks read from {SRC.name}")
    for d in result:
        print(f"  {d['game']:22} {d['value']:6.1f}")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
