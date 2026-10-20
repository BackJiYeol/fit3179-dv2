// Finds every .chart[data-spec] slot on the page, fetches its
// Vega-Lite spec and renders it. A missing spec shows an inline
// error without stopping the remaining charts.

const EMBED_OPT = {
  actions: {export:true, source:true, compiled:false, editor:true},
  renderer: "canvas",
  tooltip: {theme: "dark"},
  config: {
    background: null,                       // charts sit directly on the page background
    font: "Inter, Segoe UI, system-ui, sans-serif",
    axis:  {labelColor:"#a3aec0", titleColor:"#e9edf3", titleFontWeight:600,
            labelFontSize:12, titleFontSize:12, grid:false, gridColor:"#253042",
            domainColor:"#3a4557", tickColor:"#3a4557"},
    legend:{labelColor:"#a3aec0", titleColor:"#e9edf3", titleFontSize:12, labelFontSize:12},
    title: {color:"#e9edf3", subtitleColor:"#a3aec0"},
    header:{labelColor:"#a3aec0", titleColor:"#e9edf3"},
    text:  {fill:"#e9edf3"},                     // default for any text mark without its own colour
    view:  {stroke:null}
  }
};

async function drawAll(){
  // The word cloud measures every word with its font to lay them out. Bangers is used only
  // inside the chart canvas, so the browser would not fetch it on its own; load it explicitly
  // and wait, otherwise words get measured in a fallback font and then overlap once Bangers arrives.
  try { await Promise.all([document.fonts.load("20px Bangers"), document.fonts.ready]); } catch (e) {}
  const nodes = document.querySelectorAll(".chart[data-spec]");
  for (const el of nodes){
    el.classList.add("is-loading");
    try{
      const res = await fetch(el.dataset.spec);
      if(!res.ok) throw new Error(`${res.status} ${res.statusText} — ${el.dataset.spec}`);
      const spec = await res.json();
      const panels = spec.vconcat || spec.hconcat || spec.concat;
      if (panels) {
        const w = Math.max(240, el.clientWidth - 80);
        for (const p of panels) p.width = p.width ?? w;
      } else {
        spec.width = spec.width ?? "container";
      }
      await vegaEmbed(el, spec, EMBED_OPT);
      el.classList.remove("is-loading");
    }catch(err){
      el.classList.remove("is-loading");
      el.classList.add("is-error");
      // el.textContent = "⚠ " + err.message;
      console.error(el.dataset.spec, err);
    }
  }
}
document.addEventListener("DOMContentLoaded", drawAll);
