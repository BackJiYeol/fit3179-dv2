"""
#9 Proportional pie chart symbol map — "Pokémon's slice is huge everywhere;
the sliver left over is a different colour in every country."

입력:
  - c09_world_composition.csv : 44개국 x 5게임 비율(%) (Google Trends geoMap.csv 원본)
  - c09_runnerup.json         : 같은 44개국의 (lon, lat) 좌표 (이미 만들어 둔 centroid)

디자인 결정 (이 파일에 그대로 기록):
  - 파이 슬라이스 = 5개 게임 전부(Pokemon 포함), 원래 비율 그대로(정규화 안 함).
    -> 4개 challenger만 100%로 재정규화하면 "Pokemon이 사실 압도적으로 크다"는
       진짜 그림을 숨기게 되어 Lie Factor(왜곡) 문제가 생김. 5개 다 그대로 보여주면
       "거의 다 Pokemon색, 아주 작은 조각만 다른 색" 그 자체가 스토리를 보여줌.
  - 파이 크기(반지름) = 100 - Pokemon% (= 나머지 4개 게임 합, "2위 싸움이 얼마나
    치열한가"를 나타내는 하나의 수치). 반지름은 sqrt scale로 매핑(Stevens' power law—
    원의 "넓이"가 값에 비례해야 사람이 크기를 정확히 비교할 수 있음. 반지름을 선형으로
    매핑하면 넓이가 값의 제곱으로 커져서 과장됨 = 전형적인 Lie Factor 감점 요인).
  - 색상(hue) = 게임 종류(nominal) — Pokemon은 중립 회색(배경 취급), 나머지 4개는
    #9 bin map에서 쓰던 동일한 색상(c07/c08과도 통일) 유지 → Gestalt Similarity로
    "이게 같은 걸 가리키는 색"임을 시각적으로 학습시킴.

출력: c09_pie_long.json — long format, 1행 = (country, game, pct, order, lon, lat, total_nonpokemon)
      pie 차트는 raw Vega에서 stack transform(groupby: country)으로 각 pie의 슬라이스를
      그려야 하므로(Vega-Lite는 지오코딩된 좌표에 pie glyph를 바로 못 찍음) long format이 필요.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IN_CSV = ROOT / "c09_world_composition.csv"
IN_COORDS = ROOT / "c09_runnerup.json"
OUT_JSON = ROOT / "c09_pie_long.json"

# CSV 국가명 -> c09_runnerup.json(및 Natural Earth) 국가명 매핑
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
        return 0.5  # "<1%" -> 0.5로 근사(국가 단위에서는 무시해도 될 만큼 작음)
    return float(s.rstrip("%"))


def main():
    coords = {c["country"]: (c["lon"], c["lat"]) for c in json.loads(IN_COORDS.read_text(encoding="utf-8"))}

    rows = list(csv.reader(IN_CSV.open(encoding="utf-8")))
    header = rows[2]  # 0번째: "카테고리: 모든 카테고리", 1번째: 빈 줄, 2번째가 실제 헤더
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
            continue  # 데이터 없는 나라(빈 칸) — 전체 스킵

        country = NAME_FIX.get(country_raw, country_raw)
        if country not in coords:
            print(f"경고: 좌표 없음 — {country} (CSV: {country_raw}) — 스킵")
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
    print(f"국가 {n_countries}개, 행 {len(out)}개 -> {OUT_JSON}")
    nonpoke_vals = sorted(set(r["total_nonpokemon"] for r in out))
    print(f"non-Pokemon 합계(2위 싸움 크기) 범위: {min(nonpoke_vals)}% ~ {max(nonpoke_vals)}%")


if __name__ == "__main__":
    main()