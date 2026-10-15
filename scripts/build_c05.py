"""
c05_parallel.json 생성 스크립트  (#5 Parallel coordinates)
---------------------------------------------------------------
입력 : raw/pkm_sets.json       Pokémon TCG 세트 목록
       raw/ygo_cardsets.json   Yu-Gi-Oh 세트 목록

출력 : data/c05_parallel.json
       [{"game":"Pokémon","era":"XY","Sets released":16,
         "Cards per set":120.3,"Sets per year":4.0,"Share of all cards":11.6}, ...]

네 축은 단위가 서로 다르다. 이것이 #4 Slope chart 와 구분되는 핵심이다.
  Sets released       개        그 시대에 나온 세트 수
  Cards per set       장        세트 하나의 평균 카드 수
  Sets per year       개/년     발매 속도 (세트 수 / 시대 길이)
  Share of all cards  %         그 게임 전체 카드 중 그 시대가 차지하는 비중

  Slope chart(#4)는 축 2개가 '같은 변수의 다른 시점'이라 기울기 자체가
  의미를 갖는다. Parallel coordinates 는 축마다 단위가 달라 기울기에는
  의미가 없고, '비슷한 모양으로 움직이는 선들의 무리'를 읽는 차트다.

판단이 들어간 지점 (보고서에 명시할 것)
  1) MIN_CARDS = 10 — 두 데이터베이스가 'set'을 다르게 센다. Pokémon 은
     expansion 을, Yu-Gi-Oh 는 프로모 1장짜리까지 'set'으로 센다.
     build_c06.py 와 같은 규칙을 양쪽에 똑같이 적용한다.
  2) LAST_COMPLETE_YEAR = 2025 — 끝나지 않은 해는 제외.
  3) 시대(era) 의 정의가 두 게임에서 다르다.
     Pokémon : 데이터에 있는 공식 'series' 필드를 그대로 쓴다.
     Yu-Gi-Oh: 대응하는 필드가 없어, 애니메이션 시리즈의 실제 방영 연도로
               9개 구간을 직접 나눴다. 공개된 방영 연도이며 지어낸 값이 아니다.
               두 게임의 '시대'가 같은 성격의 단위가 아니라는 점은 밝혀야 한다.
  4) Pokémon series 중 다음은 제외한다.
     - "Other": 여러 잡다한 세트를 묶은 분류이지 하나의 시대가 아니다.
     - 세트가 3개 미만인 series: 평균과 발매 속도가 한두 세트에 좌우된다.
       (NP 1세트, Gym 2세트, Mega Evolution 2세트 — 마지막 것은 2025년에
        막 시작한 시대라 아직 완결되지 않았다.)
  5) 시대 길이는 '그 시대에 실제로 세트가 나온 첫 해와 마지막 해'로 계산한다.
     공식 시작·종료일이 아니라 데이터에서 관측된 범위다.

실행 : python scripts/build_c05.py
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

# Yu-Gi-Oh 는 series 필드가 없어 애니메이션 방영 연도로 시대를 나눈다.
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
    """시대별로 (세트 수, 카드 수, 첫 해, 마지막 해) 를 모은다."""
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