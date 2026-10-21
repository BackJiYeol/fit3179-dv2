"""
#7 Choropleth, #8 Proportional symbol map, and country points for #9.

Input:  csv/geo_5games.csv        Google Trends, 5 games by country
        csv/geo_tradingcards.csv  Google Trends, "trading cards" by country
        raw/country_points.json   country label points
        raw/ne_110m_places.geojson  points for city-states missing at 110m
Output: data/c07_share.json   Pokémon share of the 5 games per country
        data/c08_symbol.json  "trading cards" interest per country
        data/c09_runnerup.json  largest non-Pokémon game per country, with point

Run: python scripts/build_maps.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GEO_5 = ROOT / "csv" / "geo_5games.csv"
GEO_TC = ROOT / "csv" / "geo_tradingcards.csv"
PLACES = ROOT / "raw" / "ne_110m_places.geojson"
CENTROID = ROOT / "raw" / "country_points.json"

OUT_SHARE = ROOT / "data" / "c07_share.json"
OUT_SYMBOL = ROOT / "data" / "c08_symbol.json"
OUT_RUNNER = ROOT / "data" / "c09_runnerup.json"

# Google Trends writes headers in the browser language. Our CSVs were saved
# from a Korean browser, so the header row starts with "\uad6d\uac00" ("Country").
HEADER_FIRST_CELL = ("Country", "\uad6d\uac00")

# Search term in the CSV header -> display name
GAME = {
    "Pokemon cards": "Pokémon",
    "Yugioh cards": "Yu-Gi-Oh",
    "Magic the Gathering cards": "Magic: The Gathering",
    "One Piece cards": "One Piece",
    "sports cards": "Sports cards",
}

# Google Trends name -> Natural Earth 110m name (names only, values unchanged)
RENAME = {
    "Türkiye": "Turkey",
    "United States": "United States of America",
}

# Too small for the 110m borders: take the point from populated places
PLACE_FALLBACK = {"Singapore": "Singapore", "Hong Kong": "Hong Kong"}


def to_number(raw):
    """'83%' -> 83.0, '<1' -> 0.5, blank -> None"""
    v = raw.strip().rstrip("%").strip()
    if not v:
        return None
    return 0.5 if v.startswith("<") else float(v)


def read_geo_csv(path):
    """Return (search terms, rows with values) from a Trends geoMap CSV."""
    rows = list(csv.reader(path.open(encoding="utf-8-sig")))
    i = next(j for j, r in enumerate(rows) if r and r[0] in HEADER_FIRST_CELL)
    columns = [c.split(":")[0].strip() for c in rows[i][1:]]
    body = [r for r in rows[i + 1:]
            if r and r[0] and any(c.strip() for c in r[1:])]
    return columns, body


def load_points():
    """Country -> (lon, lat), plus city-state points."""
    points = json.loads(CENTROID.read_text(encoding="utf-8"))
    places = json.loads(PLACES.read_text(encoding="utf-8"))
    for feature in places["features"]:
        p = feature["properties"]
        for trends_name, place_name in PLACE_FALLBACK.items():
            if p.get("NAME") == place_name:
                points[trends_name] = [p["LONGITUDE"], p["LATITUDE"]]
    return points


def main() -> None:
    points = load_points()

    # ---------- #7 and #9: share of the 5 games ----------
    columns, body = read_geo_csv(GEO_5)
    share_rows, runner_rows = [], []

    for r in body:
        raw_name = r[0]
        name = RENAME.get(raw_name, raw_name)
        values = {GAME[c]: (to_number(r[j + 1]) or 0.0)
                  for j, c in enumerate(columns)}
        ranked = sorted(values.items(), key=lambda kv: -kv[1])

        share_rows.append({"country": name, "pct": values["Pokémon"]})

        lonlat = points.get(name) or points.get(raw_name)
        if lonlat:
            runner_rows.append({
                "country": name,
                "runnerup": ranked[1][0],
                "pct": ranked[1][1],
                "lon": lonlat[0],
                "lat": lonlat[1],
            })

    # ---------- #8: "trading cards" interest ----------
    columns_tc, body_tc = read_geo_csv(GEO_TC)
    symbol_rows = []
    for r in body_tc:
        raw_name = r[0]
        name = RENAME.get(raw_name, raw_name)
        value = to_number(r[1])
        lonlat = points.get(name) or points.get(raw_name)
        if value is None or not lonlat:
            continue
        symbol_rows.append({
            "country": name, "value": value,
            "lon": lonlat[0], "lat": lonlat[1],
        })

    for path, rows in ((OUT_SHARE, share_rows),
                       (OUT_SYMBOL, symbol_rows),
                       (OUT_RUNNER, runner_rows)):
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        print(f"{len(rows):3d} rows -> {path.relative_to(ROOT)}")

    # Report countries that failed to match the map.
    topo = json.loads(
        (ROOT / "data" / "WorldMapWithGraticules.topojson")
        .read_text(encoding="utf-8"))
    map_names = {g["properties"]["NAME"] for g in
                 topo["objects"]["ne_110m_admin_0_countries"]["geometries"]}
    no_area = sorted({r["country"] for r in share_rows} - map_names)
    no_point = sorted({r["country"] for r in share_rows}
                      - {r["country"] for r in runner_rows})
    print(f"  no map area ({len(no_area)}): {no_area}")
    print(f"  no point    ({len(no_point)}): {no_point}")

    from collections import Counter
    print("  runner-up:", dict(Counter(r["runnerup"] for r in runner_rows)))
    pcts = sorted(r["pct"] for r in share_rows)
    print(f"  Pokémon share: {pcts[0]:.0f}% ~ {pcts[-1]:.0f}%")


if __name__ == "__main__":
    main()
