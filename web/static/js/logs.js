async function load(){const r=await fetch("/api/logs");document.getElementById("logs").textContent=JSON.stringify(await r.json(),null,2)}
setInterval(load,1500); load();
