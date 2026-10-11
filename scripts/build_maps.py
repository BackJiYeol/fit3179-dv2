"""
지도 3종 데이터 생성 스크립트  (#7 Choropleth / #8 Proportional symbol / #9 Bin map)
---------------------------------------------------------------
입력 : csv/geo_5games.csv        Google Trends geoMap, 검색어 5개, Worldwide,
                                 2021-10-02 ~ 2026-10-02. 값은 각 나라 안에서의
                                 5개 검색어 간 비중(%)이다.
       csv/geo_tradingcards.csv  같은 기간, 검색어 'trading cards' 하나.
                                 값은 나라 간 상대 지수(0~100).
       raw/ne_110m_places.geojson  Natural Earth populated places.
                                 지도에 면이 없는 도시국가의 좌표를 얻는 용도.
       data/ne_110m_admin_0_countries.topojson
                                 Natural Earth 110m 국경 (177개국).
                                 unit 에서 제공한 Week 8 Studio 예제의 파일을
                                 그대로 쓴다. TopoJSON objects 이름은
                                 'ne_110m_admin_0_countries'.
                                 나라별 좌표(LABEL_X/LABEL_Y)는 Natural Earth
                                 geojson 원본에서 뽑아 raw/country_points.json
                                 으로 따로 저장해 두었다.

출력 : data/c07_share.json     [{"country": "...", "pct": 93.0}, ...]
       data/c08_symbol.json    [{"country": "...", "value": 100, "lon": .., "lat": ..}, ...]
       data/c09_runnerup.json  [{"country": "...", "runnerup": "...", "pct": 7.0,
                                 "lon": .., "lat": ..}, ...]

⚠ 두 CSV 의 값은 뜻이 다르다. 섞어서 비교하면 안 된다.
   geo_5games.csv    : 한 나라 '안에서' 5개 검색어가 나눠 가진 비중. 행 합계 ≈ 100%.
                       나라끼리 비교하면 "그 나라에서 포켓몬이 얼마나 압도적인가"다.
   geo_tradingcards.csv: 'trading cards' 한 검색어의 나라 '간' 상대 지수.
                       최고 나라가 100이고 나머지는 그에 대한 비율이다.

판단이 들어간 지점 (보고서에 명시할 것)
  1) '<1' -> 0.5  (다른 스크립트와 같은 규칙)
  2) 값이 하나도 없는 나라는 제외한다. 결과적으로 5게임 44개국,
     trading cards 51개국만 남는다. 이것은 "수집가가 없다"가 아니라
     "구글 검색으로 측정되지 않는다"는 뜻이며, 지도에서 결측국을
     회색으로 따로 칠해 그 사실을 드러낸다.
  3) 이름 표기 통일 (RENAME). 'Türkiye' -> 'Turkey' (구글은 새 공식 국명,
     Natural Earth 는 옛 표기), 'United States' -> 'United States of America'.
     같은 나라를 두 출처가 다르게 적는 경우이며, 값은 건드리지 않는다.
     매칭 실패를 그냥 두면 지도에서 그 나라가 조용히 사라지므로,
     아래 main() 은 매칭되지 않은 이름을 반드시 출력한다.
  4) Singapore / Hong Kong / St. Helena 는 Natural Earth 110m 국경 데이터에
     아예 없다 (축척이 너무 커서 생략된 지역).
     - #7 Choropleth 에서는 칠할 면이 없으므로 빠진다.
     - #8 / #9 는 점만 필요하므로 Natural Earth 의 populated places 에서
       좌표를 가져와 포함한다. Singapore 는 One Piece 가 2위인 단 두 나라
       중 하나라서 빠지면 #9 의 범례가 성립하지 않는다.
     둘 다 같은 Natural Earth 데이터 계열이므로 출처가 늘어나지 않는다.

실행 : python scripts/build_maps.py
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

# CSV 헤더의 검색어 -> 차트에 표시할 이름
GAME = {
    "Pokemon cards": "Pokémon",
    "Yugioh cards": "Yu-Gi-Oh",
    "Magic the Gathering cards": "Magic: The Gathering",
    "One Piece cards": "One Piece",
    "sports cards": "Sports cards",
}

# Google Trends 표기 -> Natural Earth 110m 표기.
# 같은 나라를 두 출처가 다르게 적는 경우만 맞춘다. 데이터는 건드리지 않는다.
RENAME = {
    "Türkiye": "Turkey",                      # 구글은 새 공식 국명, NE 는 옛 표기
    "United States": "United States of America",
}

# 110m 국경에 없어 populated places 에서 좌표를 가져올 나라
PLACE_FALLBACK = {"Singapore": "Singapore", "Hong Kong": "Hong Kong"}


def to_number(raw):
    """'83%' -> 83.0, '<1' -> 0.5, 빈칸 -> None"""
    v = raw.strip().rstrip("%").strip()
    if not v:
        return None
    return 0.5 if v.startswith("<") else float(v)


def read_geo_csv(path):
    """Trends geoMap CSV 에서 (검색어 목록, 값이 있는 행들) 을 돌려준다."""
    rows = list(csv.reader(path.open(encoding="utf-8-sig")))
    i = next(j for j, r in enumerate(rows) if r and r[0] in ("국가", "Country"))
    columns = [c.split(":")[0].strip() for c in rows[i][1:]]
    body = [r for r in rows[i + 1:]
            if r and r[0] and any(c.strip() for c in r[1:])]
    return columns, body


def load_points():
    """나라 -> (lon, lat). 국경 라벨 좌표 + 도시국가 보정."""
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

    # ---------- #7 과 #9 : 5게임 비중 ----------
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

    # ---------- #8 : trading cards 관심도 ----------
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

    # 매칭 실패는 조용히 사라지면 안 되므로 반드시 보고한다.
    # encoding="utf-8" 를 반드시 적는다. 적지 않으면 Windows 한국어 환경에서
    # 기본값 cp949 로 읽으려다 UnicodeDecodeError 가 난다.
    topo = json.loads(
        (ROOT / "data" / "ne_110m_admin_0_countries.topojson")
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
