# Who is collecting trading cards?

FIT3179 Data Visualisation 2 · Back Jiyeol · 25 October 2026

Live page: https://backjiyeol.github.io/fit3179-dv2/

## Files
```
index.html      the page (5 sections, 11 charts)
css/style.css   layout and typography
js/main.js      embeds every chart with Vega-Embed
specs/          one readable JSON spec per chart (.vl.json = Vega-Lite, .vg.json = Vega)
data/           chart data and map files
dv2sketch.pdf   hand-drawn A4 sketch
```

To run locally, serve the folder (for example `python -m http.server`) and open http://localhost:8000.

## Data sources
- Pokémon TCG: [pokemon-tcg-data](https://github.com/PokemonTCG/pokemon-tcg-data)
- Yu-Gi-Oh: [Yugioh-Database-Downloader](https://github.com/KianBennett/Yugioh-Database-Downloader) and [YGOPRODeck API](https://db.ygoprodeck.com/api-guide/)
- Magic: The Gathering: [Scryfall](https://scryfall.com/docs/api)
- One Piece: [punk-records](https://github.com/buhbbl/punk-records)
- [Google Trends](https://trends.google.com/), worldwide, October 2021 to October 2026 (relative index, 100 = peak week)
- [Natural Earth](https://www.naturalearthdata.com/) 110m country boundaries

AI use: Claude (Anthropic) assisted with brainstorming, data-processing scripts, chart code and proofreading.
