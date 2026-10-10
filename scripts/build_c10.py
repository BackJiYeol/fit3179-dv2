import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "csv" / "time_5games.csv"
OUT = ROOT / "data" / "c10_timeseries.json"

LABEL = {
    "Pokemon cards":             "Pokémon",
    "sports cards":              "Sports cards",
    "Yugioh cards":              "Yu-Gi-Oh",
    "One Piece cards":           "One Piece",
    "Magic the Gathering cards": "Magic: The Gathering",
}


def to_number(raw: str) -> float:
    """'<1' 을 0.5 로. 그 외에는 그대로 숫자 변환."""
    raw = raw.strip()
    return 0.5 if raw.startswith("<") else float(raw)


def main() -> None:
    rows = list(csv.reader(SRC.open(encoding="utf-8-sig")))

    header_i = next(i for i, r in enumerate(rows) if r and r[0] in ("주", "Week"))
    header = rows[header_i]
    body = [r for r in rows[header_i + 1:] if r and r[0]]

    columns = [c.split(":")[0].strip() for c in header[1:]]

    # wide -> long
    result = []
    for row in body:
        date = row[0]
        for j, col in enumerate(columns):
            result.append({
                "date":  date,
                "game":  LABEL[col],
                "value": to_number(row[j + 1]),
            })

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"{len(body)} weeks x {len(columns)} games = {len(result)} rows")
    print(f"  first: {result[0]}")
    print(f"  last:  {result[-1]}")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()