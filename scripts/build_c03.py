"""
c03_sankey 생성 스크립트  (3번 Sankey — raw Vega)
---------------------------------------------------------------
입력 : raw/pkm_sets.json      Pokémon TCG 세트 목록 (176세트)
       raw/ygo_cardsets.json  Yu-Gi-Oh 세트 목록 (1,035세트)
       (출처는 build_c06.py 와 동일)

출력 : data/c03_sankey_nodes.json  — 노드(막대) 좌표
       data/c03_sankey_links.json — 리본(흐름) 좌표(선·면 둘 다 그릴 수 있게
                                    중심선 + 위/아래 경계를 같이 저장)

구조: Game → Set → Era  (합쳐짐은 "같은 게임 안에서"만 일어나게)
  Game  (2개: Pokémon, Yu-Gi-Oh)
    → Set   (era당 카드 수 상위 2세트만 — "그 외 세트"는 아예 뺐음, 판단 2) 참고)
      → Era (5년 단위, 같은 게임의 top 2세트가 다시 합쳐짐 = merge)

  ⚠ 이 차트는 "그 시대에 나온 전체 카드"가 아니라 **게임별·era별 상위
  2세트만**을 다룬다. era 막대의 높이도 top 2세트 합일 뿐, 전체 카드
  수가 아니다 — index.html 부제에 "상위 2세트만, 나머지는 제외"라고
  반드시 명시할 것 (안 그러면 막대 높이를 전체 카드 수로 오해함).

  raw Vega에는 Sankey 전용 transform이 없다(wordcloud와 다름). 그래서
  레이아웃(막대 위치, 리본 두께·곡선)을 전부 이 파이썬 스크립트에서
  계산해서 좌표로 저장하고, Vega 스펙은 그 좌표를 그대로 그리기만 한다.
  (c09 hexbin과 같은 방식 — 기하 계산은 파이썬, 그리기는 Vega)

왜 "Game → Set → Era" 순서인가 (Game → Era → Set 가 아니라)
  처음엔 Game → Era → Set 로 만들었다. 그러면 era 지점에서 두 게임을
  "겹치게" 그리고 싶어지는데, 그건 Pokémon 카드 수 + Yu-Gi-Oh 카드 수를
  더한다는 뜻이 된다 — 두 게임은 카탈로그 크기 자체가 다른 별개의
  집합이라(Pokémon 18,515장 vs Yu-Gi-Oh 36,294장, 이 공통 구간 기준)
  더해도 의미 있는 숫자가 안 나온다. 이 프로젝트에서 계속 지켜온
  "크기 다른 걸 그냥 합치면 안 된다" 원칙(word cloud의 %, choropleth
  정규화)과 정면으로 부딪힘.
  Game → Set → Era 순서면 merge가 "Set → Era" 지점에서 일어나는데,
  이건 **같은 게임의 세트들끼리만** 더하는 것이라 정당하다(같은 카탈로그
  안의 합산). 그래서 순서를 바꿨다. era 막대는 여전히 같은 시대의
  두 게임을 아주 가깝게(거의 맞닿게) 배치해서 비교는 가능하게 하되,
  실제 수치는 섞지 않는다.

판단이 들어간 지점 (보고서에 명시할 것)
  1) MIN_CARDS = 10, 공통 구간 계산법은 build_c05/c06.py와 동일 규칙을
     재사용했다 (이유도 동일: 같은 데이터로 다른 차트의 숫자가 서로
     모순돼 보이면 안 되기 때문).
  2) era당 top 2세트만 보여주고 "그 외 세트"는 완전히 뺐다.
     처음엔 top 2 + "Other sets"로 다 보여줬는데, 두 가지 문제가 있었다:
       a) 세트 이름 라벨을 붙이면(판단 3 참고) top 2는 아주 가늘어서
          Other의 거대한 리본 옆에서 라벨이 안 읽혔다.
       b) 더 중요한 건, Other를 그대로 두면 "이 차트는 전체 카드를
          다룬다"는 인상을 주는데, 그러면서 top 2세트만 이름이 보이는
          게 오히려 혼란스러웠다.
     그래서 Other를 아예 빼고 **차트의 범위 자체를 "상위 2세트"로
     좁혔다** — era 막대 높이도 top 2세트 합으로 다시 계산한다
     (전체 카드 수가 아님). 대신 이 범위 제한을 **제목/부제에 명시**해야
     한다 — 안 그러면 "나머지 세트는 어디 갔냐"는 질문에 답을 못 하고,
     막대 높이를 전체 카드 수로 오해하게 만드는 게 더 심각한 Lie Factor
     문제가 된다 (압축이나 묵시적 생략과 달리, "상위 2개만 보여준다"는
     걸 밝히는 건 정직한 축소이지 왜곡이 아니다).
     1개만 보여주면 "왜 하필 1개냐"는 임의성이 더 커 보여서 2개로 정함.
  3) Set 레벨(중간 칼럼)에도 이제 세트 이름을 상시 라벨로 표시한다 —
     Other를 빼서 노드 수가 42개→32개로 줄고 각 노드가 더 커져서
     (판단 2 참고) 라벨끼리 안 겹친다. 세트 사이·그룹 사이 모두에
     여백(NODE_PAD)을 둬서 라벨 두 줄이 포개지지 않게 했다.
  4) 리본 두께(card 수)와 막대 높이는 **같은 척도**를 쓴다 — 즉 1장 =
     1 단위 높이. 그래야 "막대 높이 = 그 교차점을 지나는 카드 수
     총합"이라는 Sankey의 기본 약속(flow conservation)이 깨지지 않는다
     (이제 그 "총합"은 상위 2세트 기준이라는 걸 부제에 밝혀야 함 —
     판단 2 참고).

실행 : python scripts/build_c03.py
"""
import json
import math
from pathlib import Path

MIN_CARDS = 10
LAST_COMPLETE_YEAR = 2025
ERAS = [(2001, 2005), (2006, 2010), (2011, 2015), (2016, 2020), (2021, 2025)]
TOP_SETS_PER_ERA = 2

GAME_COLOR = {"Pokémon": "#0072B2", "Yu-Gi-Oh": "#CC79A7"}
GAME_COLOR_OTHER = {"Pokémon": "#9ecae1", "Yu-Gi-Oh": "#e3b8cf"}

ROOT = Path(__file__).resolve().parent.parent
PKM = ROOT / "raw" / "pkm_sets.json"
YGO = ROOT / "raw" / "ygo_cardsets.json"
OUT_NODES = ROOT / "data" / "c03_sankey_nodes.json"
OUT_LINKS = ROOT / "data" / "c03_sankey_links.json"

# 칼럼 x좌표 (0~1). Vega 스펙에서 width를 곱해 픽셀로 바꾼다.
COL_X = {"game": 0.03, "set": 0.5, "era": 0.97}
NODE_PAD = 0.012          # 같은 칼럼 안에서 서로 다른 항목 사이 여백(값 단위 비율)
ERA_PAIR_GAP = 0.0        # era 쌍(두 게임) 사이는 거의 0 — "겹쳐 보이게"
POINTS_PER_SEGMENT = 16    # 리본 곡선 부드럽게 그릴 보간점 수


def year_month(raw_date):
    d = raw_date.replace("/", "-")
    return int(d[0:4]), int(d[5:7])


def to_index(ym):
    return ym[0] * 12 + (ym[1] - 1)


def load_records(path, date_field, size_field, name_field):
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for r in raw:
        d = r.get(date_field)
        if not d:
            continue
        size = r.get(size_field) or 0
        if size < MIN_CARDS:
            continue
        y, m = year_month(d)
        out.append({"year": y, "month": m, "size": size, "name": r.get(name_field)})
    return out


def smooth_edge(t):
    """S자 곡선 보간 가중치 (0~1) — Sankey 리본의 표준 모양."""
    return (1 - math.cos(math.pi * t)) / 2


def curve_points(x0, y0, x1, y1, n=POINTS_PER_SEGMENT):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * smooth_edge(t)
        pts.append((x, y))
    return pts


def main():
    pkm = load_records(PKM, "releaseDate", "total", "name")
    ygo = load_records(YGO, "tcg_date", "num_of_cards", "set_name")

    start = max(to_index(min((r["year"], r["month"]) for r in pkm)),
                to_index(min((r["year"], r["month"]) for r in ygo)))
    end = min(to_index(max((r["year"], r["month"]) for r in pkm)),
              to_index(max((r["year"], r["month"]) for r in ygo)),
              to_index((LAST_COMPLETE_YEAR, 12)))

    def in_window(r):
        return start <= to_index((r["year"], r["month"])) <= end

    # ---- 1. era별·게임별 top-N 세트 계산 (Other 없음 — 아래 설명) ----
    # branch: {"id","game","era","label","value","is_other"} (is_other는 항상 False,
    # 호환을 위해 필드는 남겨둠)
    #
    # "Other sets"를 완전히 뺐다. 그 대신 이 차트가 다루는 범위 자체를
    # "게임별·era별 상위 2세트"로 좁혔다 — 즉 era 막대의 높이도 더 이상
    # "그 시대에 나온 전체 카드 수"가 아니라 "그 시대 top 2세트의 카드 수 합"이다.
    # (Other를 숨기고 era 높이만 전체로 두면 리본 합과 막대 높이가 안 맞는
    # 더 나쁜 문제가 생긴다 — 자세한 이유는 이 파일 docstring의 판단 5) 참고.)
    # 그래서 **제목·부제에 "상위 2세트만, 나머지는 제외했다"는 걸 명시해야 한다.**
    branches = []
    era_game_total = {}  # (era_label, game) -> top-N 세트 합 (전체 카드 수 아님)
    game_total = {"Pokémon": 0, "Yu-Gi-Oh": 0}

    for lo, hi in ERAS:
        era_label = f"{lo}-{hi}"
        for game, recs in (("Pokémon", pkm), ("Yu-Gi-Oh", ygo)):
            sub = [r for r in recs if lo <= r["year"] <= hi and in_window(r)]
            if not sub:
                era_game_total[(era_label, game)] = 0
                continue
            top_sets = sorted(sub, key=lambda r: -r["size"])[:TOP_SETS_PER_ERA]
            top_sum = sum(r["size"] for r in top_sets)
            era_game_total[(era_label, game)] = top_sum
            game_total[game] += top_sum

            for r in top_sets:
                branches.append({
                    "id": f"set::{era_label}::{game}::{r['name']}",
                    "game": game, "era": era_label,
                    "label": r["name"], "value": r["size"], "is_other": False,
                })

    # ---- 2. 노드 레이아웃 ----
    nodes = []

    # 2a. Game 칼럼 — Pokémon 위, Yu-Gi-Oh 아래. 높이 = 그 게임 총합(카드 수).
    # (y scale의 range가 [height,0] 이라 cursor가 큰(나중에 쌓는) 쪽이 위로 간다 —
    #  그래서 "위로 보내고 싶은 쪽을 나중에" 순서로 돈다)
    cursor = 0.0
    game_y = {}
    for game in ("Yu-Gi-Oh", "Pokémon"):
        y0, y1 = cursor, cursor + game_total[game]
        game_y[game] = (y0, y1)
        nodes.append({"id": f"game::{game}", "col": "game", "x": COL_X["game"],
                       "y0": y0, "y1": y1, "label": game, "game": game,
                       "kind": "game", "value": game_total[game]})
        cursor = y1 + NODE_PAD * (game_total["Pokémon"] + game_total["Yu-Gi-Oh"])

    # 2b. Set 칼럼 — era(오름차순으로 쌓아서 "나중에 쌓는" 2021-2025가 위로 가게) →
    #     게임(Yu-Gi-Oh, Pokémon 순으로 쌓아서 Pokémon이 위로) → top 2세트.
    set_total = sum(b["value"] for b in branches)
    pad_unit = NODE_PAD * set_total
    cursor = 0.0
    set_y = {}
    for lo, hi in ERAS:
        era_label = f"{lo}-{hi}"
        for game in ("Yu-Gi-Oh", "Pokémon"):
            group = [b for b in branches if b["era"] == era_label and b["game"] == game]
            group.sort(key=lambda b: (b["is_other"], -b["value"]))
            for b in group:
                y0, y1 = cursor, cursor + b["value"]
                set_y[b["id"]] = (y0, y1)
                nodes.append({"id": b["id"], "col": "set", "x": COL_X["set"],
                               "y0": y0, "y1": y1, "label": b["label"],
                               "game": b["game"], "kind": "other" if b["is_other"] else "set",
                               "era": era_label, "value": b["value"]})
                cursor = y1 + pad_unit  # 세트 하나하나 사이에도 여백 — top 세트 라벨끼리
                                        # 안 겹치려면 그룹 사이뿐 아니라 항목 사이에도 필요

    # 2c. Era 칼럼 — era를 오름차순으로 쌓아서 2021-2025가 맨 위로 가게 하고,
    #     그 안에서는 Yu-Gi-Oh, Pokémon 순으로 쌓아 Pokémon이 위 + 두 막대가 거의 맞닿게.
    cursor = 0.0
    era_y = {}
    for lo, hi in ERAS:
        era_label = f"{lo}-{hi}"
        pair_start = cursor
        for game in ("Yu-Gi-Oh", "Pokémon"):
            v = era_game_total.get((era_label, game), 0)
            y0, y1 = cursor, cursor + v
            era_y[(era_label, game)] = (y0, y1)
            nodes.append({"id": f"era::{era_label}::{game}", "col": "era", "x": COL_X["era"],
                           "y0": y0, "y1": y1, "label": era_label, "game": game,
                           "kind": "era", "era": era_label, "value": v})
            cursor = y1 + ERA_PAIR_GAP
        cursor = pair_start + (era_game_total.get((era_label, "Pokémon"), 0)
                                + era_game_total.get((era_label, "Yu-Gi-Oh"), 0))
        cursor += pad_unit * 1.6  # era 쌍 사이는 더 크게 띄움

    # ---- 3. 링크(리본) 포인트 생성 ----
    # game -> set : game 노드 안에서 순서대로 쌓은 slice 중심 -> set 노드 중심(세로 전체를 그 링크가 다 씀)
    # set -> era  : set 노드 중심 -> era 노드 안에서 쌓은 slice 중심
    link_rows = []
    game_cursor = {g: game_y[g][0] for g in game_y}

    # game -> set 링크를 위해 game 쪽에서도 era(오름차순)-게임군 순서를 따라 slice를 배정
    for lo, hi in ERAS:
        era_label = f"{lo}-{hi}"
        for game in ("Pokémon", "Yu-Gi-Oh"):
            group = [b for b in branches if b["era"] == era_label and b["game"] == game]
            group.sort(key=lambda b: (b["is_other"], -b["value"]))
            for b in group:
                gy0 = game_cursor[game]
                gy1 = gy0 + b["value"]
                game_cursor[game] = gy1
                g_center = (gy0 + gy1) / 2
                s_y0, s_y1 = set_y[b["id"]]
                s_center = (s_y0 + s_y1) / 2
                half = b["value"] / 2
                link_id = f"link1::{b['id']}"
                pts = curve_points(COL_X["game"], g_center, COL_X["set"], s_center)
                for seq, (x, y) in enumerate(pts):
                    link_rows.append({
                        "link": link_id, "seq": seq, "x": x,
                        "y_lo": y - half, "y_hi": y + half,
                        "game": game, "kind": "other" if b["is_other"] else "set",
                    })

    era_cursor = {}
    for key in era_y:
        era_cursor[key] = era_y[key][0]
    for lo, hi in ERAS:
        era_label = f"{lo}-{hi}"
        for game in ("Pokémon", "Yu-Gi-Oh"):
            group = [b for b in branches if b["era"] == era_label and b["game"] == game]
            group.sort(key=lambda b: (b["is_other"], -b["value"]))
            for b in group:
                s_y0, s_y1 = set_y[b["id"]]
                s_center = (s_y0 + s_y1) / 2
                ey0 = era_cursor[(era_label, game)]
                ey1 = ey0 + b["value"]
                era_cursor[(era_label, game)] = ey1
                e_center = (ey0 + ey1) / 2
                half = b["value"] / 2
                link_id = f"link2::{b['id']}"
                pts = curve_points(COL_X["set"], s_center, COL_X["era"], e_center)
                for seq, (x, y) in enumerate(pts):
                    link_rows.append({
                        "link": link_id, "seq": seq, "x": x,
                        "y_lo": y - half, "y_hi": y + half,
                        "game": game, "kind": "other" if b["is_other"] else "set",
                    })

    OUT_NODES.write_text(json.dumps(nodes, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_LINKS.write_text(json.dumps(link_rows, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(nodes)} nodes -> {OUT_NODES.relative_to(ROOT)}")
    print(f"{len(link_rows)} link points ({len(branches)*2} links) -> {OUT_LINKS.relative_to(ROOT)}")
    print("game totals:", game_total)


if __name__ == "__main__":
    main()