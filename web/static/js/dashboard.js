async function startAgents(){
  const prompt=document.getElementById("mission").value||"demo görev";
  const r=await fetch("/api/agents/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt})});
  document.getElementById("status").textContent=JSON.stringify(await r.json(),null,2);
}
async function newChat(){
  const agent_id=document.getElementById("agent").value;
  await fetch("/api/chats/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({agent_id})});
  renderChats();
}
async function sendMsg(id){
  const box=document.getElementById("m_"+id);
  const message=box.value; if(!message) return;
  await fetch("/api/chats/message",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({chat_id:id,message})});
  box.value=""; renderChats();
}
async function chatAction(path,id){await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({chat_id:id})});renderChats();}
async function renderChats(){
  const r=await fetch("/api/chats"); const chats=await r.json();
  const el=document.getElementById("chats");
  el.innerHTML=chats.map(c=>`<div class="chat"><b>${c.title}</b> | ${c.status} | token:${c.tokens_total}
  <div>${c.messages.slice(-6).map(m=>`<div><small>${m.sender}:</small> ${m.text}</div>`).join("")}</div>
  <input id="m_${c.chat_id}" placeholder="mesaj..."/>
  <button onclick="sendMsg('${c.chat_id}')">Gönder</button>
  <button onclick="chatAction('/api/chats/pause','${c.chat_id}')">Duraklat</button>
  <button onclick="chatAction('/api/chats/resume','${c.chat_id}')">Devam</button>
  <button onclick="chatAction('/api/chats/delete','${c.chat_id}')">Sil</button></div>`).join("");
}
setInterval(renderChats,1200); renderChats();
