async function load(){const r=await fetch("/api/metrics");document.getElementById("metrics").textContent=JSON.stringify(await r.json(),null,2)}; setInterval(load,1200); load();
