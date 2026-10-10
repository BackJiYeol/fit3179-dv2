# FIT3179 DV2 — Who's Collecting Trading Cards?

## 구조
```
index.html          페이지 (섹션 5개 · 차트 슬롯 10개)
css/style.css       스타일
js/main.js          .chart[data-spec] 을 찾아 Vega-Lite 스펙을 불러와 그림
specs/*.vg.json     차트별 Vega-Lite 스펙  ← 여기를 하나씩 채우는 중
data/*.json         차트 데이터
data/_PROVENANCE.json  각 데이터의 출처·가공·판단이 들어간 지점 기록
```

## 차트를 추가하는 방법
1. `specs/cNN_xxx.vg.json` 에 Vega-Lite 스펙을 쓴다
2. 데이터는 `{"data": {"url": "data/cNN_xxx.json"}}` — 경로는 **index.html 기준**
3. `width` 는 쓰지 않아도 됨 (main.js가 `"container"` 로 채움)

## 로컬에서 보기
`python -m http.server` 로 띄워서 볼 것. `file://` 로 열면 fetch가 막힘.

## 데이터 출처
- Pokémon TCG: [pokemon-tcg-data](https://github.com/PokemonTCG/pokemon-tcg-data) — 176 sets / 20,635 cards
- Yu-Gi-Oh: [Yugioh-Database-Downloader](https://github.com/KianBennett/Yugioh-Database-Downloader) — 7,968 cards
- Google Trends: 2021-10-02 ~ 2026-10-02
- Natural Earth 110m country boundaries

⚠ Google Trends 값은 검색량이 아니라 **상대 지수**(쿼리 내 최고 주 = 100)

push test
git push test - 2026-10-10
