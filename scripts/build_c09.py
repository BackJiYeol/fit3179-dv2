"""
#9 Pie chart map: each country's split of search interest across 5 games.

Input:  csv/geo_5games.csv     Google Trends export, 5 games by country
        data/c09_runnerup.json country points (made by build_maps.py)
Output: data/c09_pie_long.json one row per (country, game)

Design:
  - Slices = all 5 games, raw shares, not renormalised. Dropping Pokémon
    and rescaling the rest to 100% would hide how dominant it is.
  - All pies are the same size; the spec draws them with a stack transform.

Run: python scripts/build_maps.py first, then python scripts/build_c09.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "csv" / "geo_5games.csv"
IN_COORDS = ROOT / "data" / "c09_runnerup.json"
OUT_JSON = ROOT / "data" / "c09_pie_long.json"

# Google Trends name -> Natural Earth name
NAME_FIX = {
    "United States": "United States of America",
    "Türkiye": "Turkey",
}

GAME_COLUMNS = [
    ("Pokemon cards", "Pokemon"),
    ("Yugioh cards", "Yu-Gi-Oh"),
    ("sports cards", "Sports cards"),
    ("Magic the Gathering cards", "Magic: The Gathering"),
    ("One Piece cards", "One Piece"),
]
ORDER = {name: i for i, (_, name) in enumerate(GAME_COLUMNS)}


def parse_pct(s):
    s = s.strip()
    if not s:
        return None
    if s.startswith("<"):
        return 0.5  # "<1%" -> 0.5
    return float(s.rstrip("%"))


def main():
    coords = {c["country"]: (c["lon"], c["lat"]) for c in json.loads(IN_COORDS.read_text(encoding="utf-8"))}

    rows = list(csv.reader(IN_CSV.open(encoding="utf-8-sig")))
    header = rows[2]  # rows 0-1: category line and a blank line
    col_idx = {}
    for key, _ in GAME_COLUMNS:
        for i, h in enumerate(header):
            if h.startswith(key):
                col_idx[key] = i
                break

    out = []
    n_countries = 0
    for row in rows[3:]:
        if not row or not row[0]:
            continue
        country_raw = row[0].strip()
        pcts_raw = [row[col_idx[key]] if col_idx[key] < len(row) else "" for key, _ in GAME_COLUMNS]
        pcts = [parse_pct(p) for p in pcts_raw]
        if any(p is None for p in pcts):
            continue  # country with no data

        country = NAME_FIX.get(country_raw, country_raw)
        if country not in coords:
            print(f"warning: no point for {country}, skipped")
            continue
        lon, lat = coords[country]
        pokemon_pct = pcts[0]
        total_nonpokemon = round(100 - pokemon_pct, 1)

        n_countries += 1
        for (col_key, game_name), pct in zip(GAME_COLUMNS, pcts):
            out.append({
                "country": country,
                "game": game_name,
                "order": ORDER[game_name],
                "pct": pct,
                "lon": lon,
                "lat": lat,
                "total_nonpokemon": total_nonpokemon,
                "pokemon_pct": pokemon_pct,
            })

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"{n_countries} countries, {len(out)} rows -> {OUT_JSON.relative_to(ROOT)}")
    nonpoke_vals = sorted(set(r["total_nonpokemon"] for r in out))
    print(f"non-Pokémon share: {min(nonpoke_vals)}% to {max(nonpoke_vals)}%")


if __name__ == "__main__":
    main()