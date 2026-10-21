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

## Data sources
- Pokémon TCG: [pokemon-tcg-data](https://github.com/PokemonTCG/pokemon-tcg-data), 176 sets, 20,635 cards
- Yu-Gi-Oh: [Yugioh-Database-Downloader](https://github.com/KianBennett/Yugioh-Database-Downloader), 7,968 cards; [YGOPRODeck card sets API](https://db.ygoprodeck.com/api/v7/cardsets.php)
- Magic: The Gathering: [Scryfall `/catalog/card-names`](https://api.scryfall.com/catalog/card-names), 35,176 card names
- One Piece: [punk-records `english/index/by_name.json`](https://raw.githubusercontent.com/buhbbl/punk-records/main/english/index/by_name.json), 1,170 card names
- Google Trends, worldwide, 2021-10-02 to 2026-10-02
- Natural Earth 110m country boundaries

## Notes
- Google Trends values are a relative index (100 = peak week), not search counts.