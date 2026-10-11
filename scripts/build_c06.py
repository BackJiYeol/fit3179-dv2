"""
c06_calendar.json 생성 스크립트  (6번 Calendar heatmap)
---------------------------------------------------------------
입력 : raw/pkm_sets.json      Pokémon TCG 세트 목록 (176세트)
                              출처: github.com/PokemonTCG/pokemon-tcg-data
                                    sets/en.json 을 그대로 저장한 것
       raw/ygo_cardsets.json  Yu-Gi-Oh 세트 목록 (1,035세트)
                              출처: db.ygoprodeck.com/api/v7/cardsets.php
                                    응답 JSON 을 그대로 저장한 것

출력 : data/c06_calendar.json
       [{"game": "Pokémon", "year": 1999, "month": 1,
         "sets": 1, "pct": 0.57}, ...]
       두 게임이 모두 존재한 공통 기간만 넣는다 (= 늦게 시작한 쪽의 첫
       발매월 ~ 먼저 끝난 쪽의 마지막 발매월). 그 안의 모든 연·월을
       빠짐없이 넣고, 세트가 없던 달도 sets=0 으로 넣는다.
       공통 기간으로 자르는 이유: 한쪽에만 데이터가 있는 구간이 있으면
       두 패널의 가로 길이가 달라져 리듬 비교가 어긋난다.
       sets=0 은 '측정된 0건'이며 차트에서 회색으로 그린다.

변환 : 세트 발매일(release date)에서 연·월만 꺼내 건수를 센다.
       카드 수가 아니라 '세트가 몇 번 나왔나'를 센다.
       pct = 그 칸의 세트 수 / 공통 기간 안에서 그 게임이 낸 세트 수 x 100.
       비율로 바꾸는 이유: 두 게임의 세트 수 규모가 달라, 건수를 그대로
       색에 넣으면 적게 내는 쪽이 전부 흐려져 보이지 않는다. 그리고 이
       차트가 묻는 것은 '규모'가 아니라 '시기'이므로 의미상으로도 맞다.

날짜 형식이 두 소스에서 다르다
  Pokémon : "1999/01/09"  (슬래시)   필드명 releaseDate
  Yu-Gi-Oh: "2015-05-28"  (하이픈)   필드명 tcg_date
  둘 다 앞 7글자가 연-월이므로 구분자만 통일해서 읽는다.

판단이 들어간 지점 (보고서에 명시할 것)
  0) MIN_CARDS = 10 — 카드가 10장 미만인 'set'은 양쪽 모두 제외한다.
     두 데이터베이스가 'set'을 다르게 세기 때문이다. 필터 전 분포:
                       1~9장   10~19장  20장 이상   중앙값
       Pokémon            3       25       148      111장
       Yu-Gi-Oh         525       28       478        8장
     Yu-Gi-Oh 쪽 525개는 대부분 프로모 1장짜리 배포, 틴, 스타터 덱이며
     Pokémon DB 가 세는 expansion 과 같은 단위가 아니다. 거르지 않으면
     "Yu-Gi-Oh 가 6배 자주 낸다"는 결론이 나오는데, 그것은 실제 발매
     빈도가 아니라 집계 기준의 차이다.
     임계값 10 은 임의 선택이다. 다만 양쪽에 같은 규칙을 적용하며,
     Pokémon 쪽 손실이 3/176 로 작아 한쪽만 깎는 비대칭이 생기지 않는다.
  1) Yu-Gi-Oh 세트 1,035개 중 발매일이 없는 4개는 제외.
  2) Yu-Gi-Oh 의 tcg_date 는 TCG(영문판) 발매일이다. 일본 OCG 발매일과
     다르며, Pokémon 쪽도 영문판 기준이므로 비교 기준은 맞다.
  3) 아직 끝나지 않은 해(2026)는 제외한다. 9월까지만 집계되어 있어
     완료된 해와 나란히 놓으면 "그 해에 적게 냈다"처럼 보인다.

실행 : python scripts/build_c06.py
"""
import json
from collections import Counter
from pathlib import Path

# 카드가 이 수보다 적은 'set'은 expansion 으로 보지 않고 제외한다.
# 자세한 이유는 위 docstring 의 판단 0) 참고.
MIN_CARDS = 10

# 아직 끝나지 않은 해는 제외한다.
LAST_COMPLETE_YEAR = 2025

ROOT = Path(__file__).resolve().parent.parent
PKM = ROOT / "raw" / "pkm_sets.json"
YGO = ROOT / "raw" / "ygo_cardsets.json"
OUT = ROOT / "data" / "c06_calendar.json"


def year_month(raw_date: str):
    """'1999/01/09' 와 '2015-05-28' 을 모두 (1999, 1) 형태로."""
    d = raw_date.replace("/", "-")
    return int(d[0:4]), int(d[5:7])


def count_sets(records, date_field, size_field):
    """발매일이 있고 카드가 MIN_CARDS 장 이상인 레코드만 세어
    Counter{(year, month): 건수} 를 돌려준다."""
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

    # Pokémon 쪽 카드 수 필드는 total, Yu-Gi-Oh 쪽은 num_of_cards
    pkm_counts, pkm_no_date, pkm_small = count_sets(pkm, "releaseDate", "total")
    ygo_counts, ygo_no_date, ygo_small = count_sets(ygo, "tcg_date", "num_of_cards")

    def to_index(ym):
        """(2001, 1) -> 월 단위 일련번호. 구간 계산을 쉽게 하기 위한 것."""
        return ym[0] * 12 + (ym[1] - 1)

    # 두 게임이 모두 존재한 공통 구간. 끝은 마지막 완결 연도의 12월까지.
    start = max(to_index(min(pkm_counts)), to_index(min(ygo_counts)))
    end = min(to_index(max(pkm_counts)),
              to_index(max(ygo_counts)),
              to_index((LAST_COMPLETE_YEAR, 12)))

    rows = []
    for game, counts in (("Pokémon", pkm_counts), ("Yu-Gi-Oh", ygo_counts)):
        # 분모는 '공통 구간 안에서 그 게임이 낸 세트 수'.
        # 구간 밖 세트까지 분모에 넣으면 두 게임의 비율이 서로 다른 모수를
        # 쓰게 되어 비교가 어긋난다.
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

    # ---- 확인용 출력 ----
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