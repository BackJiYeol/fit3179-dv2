# FIT3179 Data Visualisation 2: Who is collecting trading cards?

Live site: https://backjiyeol.github.io/fit3179-dv2/

## Structure
```
index.html              page (5 sections, 11 charts)
css/style.css           styles
js/main.js              embeds every .chart[data-spec] with Vega-Embed
specs/                  Vega and Vega-Lite chart specs
data/*.json             chart data
csv/                    original Google Trends downloads (unchanged)
raw/                    original set lists and map helpers (unchanged)
scripts/                Python scripts that build data/ from csv/ and raw/
```

## Run locally
Serve the folder, for example `python -m http.server`, then open
http://localhost:8000. Opening index.html as `file://` blocks fetch.

## Rebuild the data
```
python scripts/build_c01.py
python scripts/build_c05.py
python scripts/build_c06.py
python scripts/build_maps.py
python scripts/build_c09.py      # needs build_maps.py first
python scripts/build_c10.py
python scripts/build_c10_bump.py # needs build_c10.py first
```
c02, c03 and c04 were built from full card dumps that are too large for
this repo. Their method is described under Data processing.

## Data processing
- c01: mean of 262 weekly Google Trends values per game.
- c02: Pokémon counted by species; other games by words of 3+ letters in
  card names. Top 12 per game, as % of that game's cards.
- c03: Pokémon cards per era grouped by special subtype (EX, GX, V, ex, ...).
  Ordinary cards left out.
- c04: cards per rarity tier per year. Rarity labels grouped into 5 tiers
  per game. Pokémon promos dropped.
- c05, c06: sets under 10 cards dropped (Yu-Gi-Oh counts single promos as
  sets). 2026 dropped. Yu-Gi-Oh eras follow anime air years.
- c06: window 2002-03 to 2025-12, the months both games were active.
- c07 to c09: country names matched to Natural Earth
  (Türkiye -> Turkey, United States -> United States of America).
- c09: raw shares of all 5 games, not renormalised.
- c10 bump: quarterly means, then rank of the four games below Pokémon.
- Google Trends '<1' is read as 0.5.

## Data sources
- Pokémon TCG: [pokemon-tcg-data](https://github.com/PokemonTCG/pokemon-tcg-data), 176 sets, 20,635 cards
- Yu-Gi-Oh: [Yugioh-Database-Downloader](https://github.com/KianBennett/Yugioh-Database-Downloader), 7,968 cards; [YGOPRODeck card sets API](https://db.ygoprodeck.com/api/v7/cardsets.php)
- Magic: The Gathering: [Scryfall `/catalog/card-names`](https://api.scryfall.com/catalog/card-names), 35,176 card names
- One Piece: [punk-records `english/index/by_name.json`](https://raw.githubusercontent.com/buhbbl/punk-records/main/english/index/by_name.json), 1,170 card names
- Google Trends, worldwide, 2021-10-02 to 2026-10-02
- Natural Earth 110m country boundaries

## Notes
- Google Trends values are a relative index (100 = peak week), not search counts.
- The Google Trends CSVs were downloaded from a Korean-language browser, so
  their header lines are in Korean. The scripts accept both Korean and English headers.
