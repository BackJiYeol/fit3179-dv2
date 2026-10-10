// Finds every .chart[data-spec] slot on the page, fetches its
// Vega-Lite spec and renders it. A missing spec shows an inline
// error without stopping the remaining charts.

const EMBED_OPT = {
  actions: {export:true, source:true, compiled:false, editor:true},
  renderer: "canvas",
  config: {
    font: "Inter, Segoe UI, system-ui, sans-serif",
    axis:  {labelColor:"#5b6577", titleColor:"#14181f", titleFontWeight:600,
            labelFontSize:12, titleFontSize:12, grid:false, domainColor:"#dfe4ec",
            tickColor:"#dfe4ec"},
    legend:{labelColor:"#5b6577", titleColor:"#14181f", titleFontSize:12, labelFontSize:12},
    view:  {stroke:null}
  }
};

async function drawAll(){
  const nodes = document.querySelectorAll(".chart[data-spec]");
  for (const el of nodes){
    el.classList.add("is-loading");
    try{
      const res = await fetch(el.dataset.spec);
      if(!res.ok) throw new Error(`${res.status} ${res.statusText} — ${el.dataset.spec}`);
      const spec = await res.json();
      spec.width  = spec.width  ?? "container";
      await vegaEmbed(el, spec, EMBED_OPT);
      el.classList.remove("is-loading");
    }catch(err){
      el.classList.remove("is-loading");
      el.classList.add("is-error");
      el.textContent = "⚠ " + err.message;
      console.error(el.dataset.spec, err);
    }
  }
}
document.addEventListener("DOMContentLoaded", drawAll);
