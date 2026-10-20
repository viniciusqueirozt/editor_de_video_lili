"use strict";
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const icon = name => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const clock = seconds => { seconds = Math.max(0, seconds || 0); return `${String(Math.floor(seconds / 60)).padStart(2,"0")}:${String(Math.floor(seconds % 60)).padStart(2,"0")}`; };
const precise = seconds => `${Number(seconds).toFixed(1).replace(".",",")} s`;
const player = $("#player"), voice = $("#voice-player");
let project = null, selected = null, projects = [], queue = Promise.resolve(), toastTimer, uploadRunning = false, playing = false, seekBusy = false, loadedSource = "", dragId = null;

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: {"Content-Type":"application/json", ...options.headers} });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Não foi possível concluir.");
  return result;
}
function toast(message, error = false) {
  clearTimeout(toastTimer); const node = $("#toast"); node.textContent = message; node.className = error ? "error" : ""; node.hidden = false;
  toastTimer = setTimeout(() => {node.hidden = true;}, error ? 8500 : 5000);
}
function assetUrl(asset, kind="proxy") { return `/api/projects/${project.id}/media/${asset.id}/${kind}`; }
function frameUrl(clip) { return assetUrl(assetFor(clip),"frame.jpg")+"?at="+clip.start; }
function assetFor(clip) { return project.media.find(m => m.id === clip.media_id); }
function currentClip() { return project?.timeline.find(c => c.id === selected); }
function index() { return project?.timeline.findIndex(c => c.id === selected) ?? -1; }
function before(i = index()) { return project.timeline.slice(0, Math.max(0,i)).reduce((a,c) => a + c.end - c.start, 0); }
function elapsed() { const c = currentClip(); return c ? before() + Math.min(c.end - c.start, Math.max(0, player.currentTime - c.start)) : 0; }

function mutate(operation, args, message) {
  queue = queue.then(async () => {
    if (!project) return;
    pause(); $("#save-status").textContent = "Salvando…";
    const id = project.id;
    try {
      project = await api(`/api/projects/${id}/commands`, {method:"POST", body:JSON.stringify({operation,args,expected_revision:project.revision,actor:"editor"})});
      render(); if (message) toast(message); return true;
    } catch (error) {
      toast(error.message, true);
      project = await api(`/api/projects/${id}`); render(); return false;
    }
  }).catch(error => toast(error.message,true));
  return queue;
}
async function listProjects() {
  projects = await api("/api/projects");
  $("#project-select").innerHTML = projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join("") || '<option value="">Nenhum projeto</option>';
  if (project) $("#project-select").value = project.id;
}
async function openProject(id) {
  await queue; pause();
  project = await api(`/api/projects/${id}`); selected = project.timeline[0]?.id || null; loadedSource = "";
  localStorage.setItem("lili-project",id); render(); await refreshJobs();
}
function render() {
  if (!project) return;
  if (!project.timeline.some(c => c.id === selected)) selected = project.timeline[0]?.id || null;
  $("#project-name").textContent = project.name;
  $("#project-select").value = project.id;
  const option = $("#project-select").selectedOptions[0]; if(option) option.textContent = project.name;
  $("#save-status").innerHTML = '<i></i> Salvo neste computador';
  $("#project-note").hidden = !project.description; $("#project-note").textContent = project.description;
  $("#media-count").textContent = project.media.length;
  $("#ready-count").textContent = `${project.media.filter(m=>m.status==="ready").length} prontos`;
  if (document.activeElement !== $("#script-input")) $("#script-input").value = project.script;
  $("#script-blocks").innerHTML = project.blocks.map((b,i)=>`<div class="script-block"><strong>BLOCO ${String(i+1).padStart(2,"0")}</strong>${esc(b.text)}</div>`).join("");
  $("#media-list").innerHTML = project.media.map(m => {
    const ready = m.status === "ready", video = m.kind === "video";
    return `<article class="media-card">${ready && video ? `<img class="media-thumb" alt="" src="${assetUrl(m,"thumbnail")}">` : `<span class="media-thumb audio-thumb">${icon(m.kind==="audio"?"mic":"film")}</span>`}<div class="media-detail"><p class="media-name" title="${esc(m.name)}">${esc(m.name)}</p><p class="media-info">${ready ? `${precise(m.duration)} · ${video ? `${m.width}×${m.height}` : "Áudio"}` : esc(m.status==="error" ? "Falha ao importar" : "Preparando…")}</p>${ready ? `<button class="media-add" data-add="${m.id}">${icon(video ? "plus" : "mic")}${video ? "Adicionar" : "Usar narração"}</button>` : `<span class="microcopy">${esc(m.error || "Criando prévia")}</span>`}</div>${ready && video ? `<input class="tags-input" data-tags="${m.id}" aria-label="Etiquetas de ${esc(m.name)}" placeholder="Etiquetas: passeio, Cora…" value="${esc((m.tags||[]).join(", "))}">` : ""}</article>`;
  }).join("") || '<p class="empty-note">Cada gravação guarda um momento.<br>Importe o primeiro para começar.</p>';
  $("#media-list").querySelectorAll("[data-add]").forEach(button=>button.addEventListener("click",()=>{
    const m = project.media.find(a=>a.id===button.dataset.add);
    if(m.kind==="audio") { mutate("narration_set",{media_id:m.id},"Narração adicionada. Revise os volumes e a duração."); setInspector("voice"); }
    else mutate("clip_add",{media_id:m.id,start:0,end:Math.min(4,m.duration)},"Cena adicionada à sequência.");
  }));
  $("#media-list").querySelectorAll("[data-tags]").forEach(input=>input.addEventListener("change",()=>mutate("media_annotate",{media_id:input.dataset.tags,tags:input.value.split(",").map(s=>s.trim()).filter(Boolean)},"Etiquetas salvas.")));
  renderTimeline(); renderInspector(); renderRequests(); updatePlayer();
  $("#undo-button").disabled = !project.undo_available;
  $("#draft-button").disabled = !project.script.trim() || !project.media.some(m=>m.kind==="video" && m.status==="ready");
  $("#export-button").disabled = !project.timeline.length;
  $("#export-summary").textContent = `${project.timeline.length} cenas · ${precise(project.duration)} · versão ${project.revision}`;
}
function renderTimeline() {
  const clips = project.timeline;
  $("#clip-count").textContent = `${clips.length} ${clips.length===1?"cena":"cenas"}`;
  $("#total-duration").textContent = `Duração total ${clock(project.duration)}`;
  $("#timeline-subtitle").textContent = clips.length ? "Selecione uma cena para ajustar seus detalhes." : "Escolha os momentos. Encontre o ritmo.";
  $("#timeline").innerHTML = clips.map((c,i)=>`<button draggable="true" class="timeline-clip ${c.id===selected?"selected":""}" data-clip="${c.id}" aria-label="Cena ${i+1}: ${esc(c.label)}, ${precise(c.end-c.start)}" aria-pressed="${c.id===selected}"><img src="${frameUrl(c)}" alt=""><span class="clip-number">${String(i+1).padStart(2,"0")}</span><span class="clip-name">${esc(c.label)}</span><span class="clip-time">${precise(c.end-c.start)}</span>${c.locked?`<span class="clip-lock">${icon("lock")}</span>`:""}</button>`).join("") || '<div class="timeline-empty"><span>01</span><p>Os momentos que você escolher aparecem aqui.</p></div>';
  $("#timeline").querySelectorAll("[data-clip]").forEach(button=>{
    button.addEventListener("click",()=>selectClip(button.dataset.clip));
    button.addEventListener("dragstart",e=>{dragId=button.dataset.clip;e.dataTransfer.effectAllowed="move";e.dataTransfer.setData("text/plain",dragId);});
    button.addEventListener("dragover",e=>e.preventDefault());
    button.addEventListener("drop",e=>{e.preventDefault();const target=project.timeline.findIndex(c=>c.id===button.dataset.clip);if(dragId&&dragId!==button.dataset.clip)mutate("clip_move",{clip_id:dragId,index:target});dragId=null;});
    button.addEventListener("dragend",()=>{dragId=null;});
  });
}
function selectClip(id, resume=false) {
  pause(); selected=id; renderTimeline();renderInspector();updatePlayer(resume);
}
function renderInspector() {
  const c = currentClip();
  if(!c) $("#scene-inspector").innerHTML = '<div class="empty-note">Selecione uma cena da sequência.<br>Os detalhes aparecem aqui.</div>';
  else {
    const m=assetFor(c), i=index();
    $("#scene-inspector").innerHTML = `<span class="scene-chip">${icon("film")} CENA ${String(i+1).padStart(2,"0")}</span><label class="field-label" for="scene-source">Tomada</label><select id="scene-source" ${c.locked?"disabled":""}>${project.media.filter(m=>m.kind==="video"&&m.status==="ready").map(a=>`<option value="${a.id}" ${a.id===c.media_id?"selected":""}>${esc(a.name)}</option>`).join("")}</select><label class="field-label" for="scene-label">Nome da cena</label><input id="scene-label" maxlength="160" value="${esc(c.label)}" ${c.locked?"disabled":""}><div class="trim-fields"><div><label class="field-label" for="clip-start">Entrada · segundos</label><input id="clip-start" type="number" inputmode="decimal" min="0" max="${m.duration}" step="0.1" value="${c.start}" ${c.locked?"disabled":""}></div><div><label class="field-label" for="clip-end">Saída · segundos</label><input id="clip-end" type="number" inputmode="decimal" min="0.1" max="${m.duration}" step="0.1" value="${c.end}" ${c.locked?"disabled":""}></div></div><p class="selected-duration">Duração da cena: ${precise(c.end-c.start)}</p><label class="field-label" for="scene-title">Texto sobre a cena</label><textarea id="scene-title" rows="2" maxlength="160" placeholder="Um título breve, se fizer sentido." ${c.locked?"disabled":""}>${esc(c.title)}</textarea><label class="field-label" for="clip-volume">Som original</label><div class="range-row"><input id="clip-volume" type="range" min="0" max="100" value="${Math.round(c.volume*100)}" ${c.locked?"disabled":""}><output id="clip-volume-value">${Math.round(c.volume*100)}%</output></div><hr class="divider"><button class="lock-control ${c.locked?"locked":""}" id="lock-clip" aria-pressed="${c.locked}">${icon("lock")}<span><strong>${c.locked?"Cena protegida":"Proteger esta escolha"}</strong><small>Preserva a tomada e seus ajustes.</small></span></button><div class="reorder-buttons"><button class="button secondary" id="move-left" ${i===0?"disabled":""}>${icon("left")}Antes</button><button class="button secondary" id="move-right" ${i===project.timeline.length-1?"disabled":""}>Depois${icon("right")}</button></div><button class="danger-button" id="remove-clip" ${c.locked?"disabled":""}>${icon("trash")}Remover da sequência</button>`;
    const update=changes=>mutate("clip_update",{clip_id:c.id,...changes});
    $("#clip-start").addEventListener("change",e=>update({start:Number(e.target.value)}));
    $("#clip-end").addEventListener("change",e=>update({end:Number(e.target.value)}));
    $("#scene-label").addEventListener("change",e=>update({label:e.target.value}));
    $("#scene-title").addEventListener("change",e=>update({title:e.target.value}));
    $("#scene-source").addEventListener("change",e=>{const a=project.media.find(m=>m.id===e.target.value);update({media_id:a.id,start:0,end:Math.min(c.end-c.start,a.duration)});});
    $("#clip-volume").addEventListener("input",e=>{$("#clip-volume-value").value=`${e.target.value}%`;player.volume=Number(e.target.value)/100;});
    $("#clip-volume").addEventListener("change",e=>update({volume:Number(e.target.value)/100}));
    $("#lock-clip").addEventListener("click",()=>update({locked:!c.locked}));
    $("#move-left").addEventListener("click",()=>mutate("clip_move",{clip_id:c.id,index:i-1}));
    $("#move-right").addEventListener("click",()=>mutate("clip_move",{clip_id:c.id,index:i+1}));
    $("#remove-clip").addEventListener("click",()=>mutate("clip_remove",{clip_id:c.id}));
  }
  const n=project.narration, audios=project.media.filter(m=>m.status==="ready"&&m.has_audio), na=n&&project.media.find(m=>m.id===n.media_id);
  $("#voice-inspector").innerHTML = `<p class="help">Monte as cenas primeiro. Depois, traga a narração para encontrar o ritmo final.</p><label class="field-label" for="voice-source">Arquivo de narração</label><select id="voice-source"><option value="">Sem narração adicional</option>${audios.map(a=>`<option value="${a.id}" ${a.id===n?.media_id?"selected":""}>${esc(a.name)}</option>`).join("")}</select><button class="button secondary full" id="import-voice" style="margin-top:12px">${icon("upload")}Importar áudio</button>${n?`<label class="field-label" for="voice-volume">Volume da narração</label><div class="range-row"><input id="voice-volume" type="range" min="0" max="100" value="${Math.round(n.volume*100)}"><output id="voice-volume-value">${Math.round(n.volume*100)}%</output></div><label class="field-label" for="voice-offset">Começar após · segundos</label><input id="voice-offset" type="number" min="0" max="3600" step="0.1" value="${n.offset}"><div class="voice-note ${na.duration+n.offset>project.duration+0.1?"voice-warning":""}">${na.duration+n.offset>project.duration+0.1?"A narração ultrapassa a montagem. Prolongue as cenas para ouvir a fala completa na exportação.":"A narração acompanha a montagem. Ajuste o som original de cada cena para equilibrar a voz."}<br>Áudio: ${precise(na.duration)} · montagem: ${precise(project.duration)}</div>`:'<div class="voice-note">A Elisa continua gravando a própria voz. A narração adicional pode ser adicionada depois.</div>'}`;
  $("#voice-source").addEventListener("change",e=>mutate("narration_set",{media_id:e.target.value||null}));
  $("#import-voice").addEventListener("click",()=>$("#file-input").click());
  if(n){$("#voice-volume").addEventListener("input",e=>{$("#voice-volume-value").value=`${e.target.value}%`;voice.volume=Number(e.target.value)/100;});$("#voice-volume").addEventListener("change",e=>mutate("narration_set",{...n,volume:Number(e.target.value)/100}));$("#voice-offset").addEventListener("change",e=>mutate("narration_set",{...n,offset:Number(e.target.value)}));}
}
function renderRequests(){const pending=project.requests.filter(r=>r.status==="pending").length;$("#request-count").textContent=pending?`(${pending})`:"";$("#requests-list").innerHTML=[...project.requests].reverse().map(r=>`<article class="request-card ${r.status==="done"?"done":""}"><small>${r.status==="done"?"CONCLUÍDO":"AGUARDANDO O CODEX"}</small><p>${esc(r.text)}</p>${r.result?`<p class="help">${esc(r.result)}</p>`:""}</article>`).join("");}
function setInspector(name){document.querySelectorAll("[data-inspector]").forEach(b=>b.classList.toggle("active",b.dataset.inspector===name));$("#scene-inspector").hidden=name!=="scene";$("#voice-inspector").hidden=name!=="voice";$("#step-visual").classList.toggle("active",name==="scene");$("#step-voice").classList.toggle("active",name==="voice");}
function pause(){playing=false;player.pause();voice.pause();$("#play-button").innerHTML=icon("play");$("#play-button").setAttribute("aria-label","Reproduzir montagem");}
async function play(){if(!currentClip())return;if(index()===project.timeline.length-1&&player.currentTime>=currentClip().end-.04){selectClip(project.timeline[0].id,true);return;}playing=true;$("#play-button").innerHTML=icon("pause");$("#play-button").setAttribute("aria-label","Pausar montagem");try{await player.play();syncVoice();}catch(e){pause();toast("Não foi possível reproduzir. Aguarde a importação ou tente novamente.",true);}}
function updatePlayer(resume=false){
  const c=currentClip(), m=c&&assetFor(c);$("#preview-empty").hidden=!!c;player.hidden=!c;$("#preview-title").textContent=c?c.title.match(/.{1,30}(?:\s|$)|\S{1,30}/g)?.map(s=>s.trim()).join("\n")||c.title:"";
  if(!c){player.removeAttribute("src");loadedSource="";updateTime();return;}
  const source=assetUrl(m);
  const seekAndPlay=()=>{player.currentTime=c.start;updateTime();if(resume)play();};
  player.onloadedmetadata=seekAndPlay;
  player.poster=frameUrl(c);
  if(loadedSource!==source){player.onloadedmetadata=seekAndPlay;player.src=source;loadedSource=source;player.load();}
  else if(player.readyState>=1) seekAndPlay();
  player.volume=Math.min(1,c.volume);
  const narration=project.narration;
  if(narration){const a=project.media.find(m=>m.id===narration.media_id);const src=assetUrl(a);if(voice.getAttribute("src")!==src){voice.src=src;voice.load();}voice.volume=Math.min(1,narration.volume);}else{voice.removeAttribute("src");voice.load();}
  $("#scene-position").textContent=`Cena ${index()+1} de ${project.timeline.length}`;updateTime();
}
function syncVoice(){if(!project?.narration||!playing)return;const time=elapsed()-project.narration.offset;if(time<0||time>=voice.duration){voice.pause();return;}if(voice.readyState>=1&&Math.abs(voice.currentTime-time)>.3)voice.currentTime=time;if(voice.paused)voice.play().catch(()=>{});}
function updateTime(){if(!project)return;const t=elapsed();$("#timecode").innerHTML=`${clock(t)} <span>/ ${clock(project.duration)}</span>`;$("#seek").max=project.duration||1;if(!seekBusy)$("#seek").value=t;}
function advance(){if(!playing)return;const i=index();if(i<project.timeline.length-1)selectClip(project.timeline[i+1].id,true);else pause();}
player.addEventListener("timeupdate",()=>{updateTime();syncVoice();const c=currentClip();if(c&&playing&&player.currentTime>=c.end-.035)advance();});player.addEventListener("ended",advance);
player.addEventListener("error",()=>{if(currentClip())toast("A prévia não abriu. Aguarde a importação ou consulte o arquivo original.",true);});
$("#play-button").addEventListener("click",()=>playing?pause():play());
$("#previous-clip").addEventListener("click",()=>{if(index()>0)selectClip(project.timeline[index()-1].id);});
$("#next-clip").addEventListener("click",()=>{if(index()<project.timeline.length-1)selectClip(project.timeline[index()+1].id);});
$("#seek").addEventListener("pointerdown",()=>{seekBusy=true;});$("#seek").addEventListener("change",e=>{seekBusy=false;pause();let t=Number(e.target.value),offset=0;for(const c of project.timeline){const length=c.end-c.start;if(t<=offset+length){selected=c.id;renderTimeline();renderInspector();updatePlayer();const seek=()=>{player.currentTime=c.start+t-offset;updateTime();};if(player.readyState>=1)seek();else player.onloadedmetadata=seek;break;}offset+=length;}});

async function uploadFiles(files){
  if(uploadRunning){toast("Aguarde o envio atual terminar.");return;}if(!project)return;
  uploadRunning=true;$("#upload-progress").hidden=false;
  const projectId=project.id;
  try{for(const file of files){$("#upload-label").textContent=`Enviando ${file.name}`;$("#upload-meter").value=0;await new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open("PUT",`/api/projects/${projectId}/upload?name=${encodeURIComponent(file.name)}`);xhr.upload.addEventListener("progress",e=>{if(e.lengthComputable)$("#upload-meter").value=e.loaded/e.total*100;});xhr.addEventListener("load",()=>{let data;try{data=JSON.parse(xhr.responseText);}catch{reject(new Error("Resposta inválida no envio."));return;}xhr.status<400?resolve(data):reject(new Error(data.error||"Falha no envio."));});xhr.addEventListener("error",()=>reject(new Error("O envio foi interrompido.")));xhr.send(file);});}toast("Arquivos recebidos. As prévias estão sendo preparadas.");if(project.id===projectId){project=await api(`/api/projects/${projectId}`);render();}}
  catch(e){toast(e.message,true);}finally{uploadRunning=false;$("#upload-progress").hidden=true;$("#file-input").value="";}
}
$("#file-input").addEventListener("change",e=>uploadFiles([...e.target.files]));["#import-top","#import-zone"].forEach(s=>$(s).addEventListener("click",()=>$("#file-input").click()));
$("#import-zone").addEventListener("dragover",e=>e.preventDefault());$("#import-zone").addEventListener("drop",e=>{e.preventDefault();uploadFiles([...e.dataTransfer.files]);});
document.querySelectorAll("[data-tab]").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll("[data-tab]").forEach(t=>t.classList.toggle("active",t===b));["media","script","requests"].forEach(t=>$("#tab-"+t).hidden=t!==b.dataset.tab);}));
document.querySelectorAll("[data-inspector]").forEach(b=>b.addEventListener("click",()=>setInspector(b.dataset.inspector)));
$("#step-visual").addEventListener("click",()=>setInspector("scene"));$("#step-voice").addEventListener("click",()=>{setInspector("voice");if(matchMedia("(max-width:640px)").matches)$(".inspector").scrollIntoView({behavior:"smooth",block:"start"});});
$("#save-script").addEventListener("click",()=>mutate("script_update",{script:$("#script-input").value},"Roteiro salvo."));
$("#request-form").addEventListener("submit",async e=>{e.preventDefault();const input=$("#request-input");if(!input.value.trim())return;if(await mutate("request_add",{text:input.value},"Pedido salvo para o Codex. A execução depende de uma sessão do agente."))input.value="";});
$("#undo-button").addEventListener("click",()=>mutate("undo",{},"Última alteração desfeita."));
$("#draft-button").addEventListener("click",async()=>{await queue;if(!project)return;if(project.timeline.length&&!confirm("Substituir a sequência pelo rascunho baseado no roteiro e nas etiquetas? Você poderá desfazer."))return;pause();try{const data=await api(`/api/projects/${project.id}/draft`,{method:"POST",body:JSON.stringify({expected_revision:project.revision})});project=data.project;selected=project.timeline[0]?.id;render();toast(data.warnings.length?`Rascunho montado. ${data.warnings.length} blocos sem correspondência de etiquetas precisam de revisão.`:"Rascunho montado pelas etiquetas. Revise a seleção das tomadas.");}catch(e){toast(e.message,true);}});
$("#project-select").addEventListener("change",e=>openProject(e.target.value).catch(e=>toast(e.message,true)));
$("#new-project").addEventListener("click",()=>$("#new-dialog").showModal());
$("#new-form").addEventListener("submit",async e=>{e.preventDefault();try{const p=await api("/api/projects",{method:"POST",body:JSON.stringify({name:$("#new-name").value,script:$("#new-script").value})});$("#new-dialog").close();$("#new-form").reset();await listProjects();await openProject(p.id);}catch(e){toast(e.message,true);}});
document.querySelectorAll(".close-dialog").forEach(b=>b.addEventListener("click",()=>b.closest("dialog").close()));
async function showExports(){pause();$("#export-dialog").showModal();await refreshJobs();}
$("#export-button").addEventListener("click",showExports);$("#step-export").addEventListener("click",showExports);
$("#start-export").addEventListener("click",async()=>{await queue;try{await api(`/api/projects/${project.id}/exports`,{method:"POST",body:JSON.stringify({expected_revision:project.revision,quality:$("#export-quality").value})});toast("Exportação iniciada. Você pode continuar revisando o projeto.");await refreshJobs();}catch(e){toast(e.message,true);}});
async function refreshJobs(){if(!project)return;const jobs=await api(`/api/projects/${project.id}/jobs`),exports=jobs.filter(j=>j.kind==="export").reverse();const running=exports.some(j=>["queued","running"].includes(j.status));$("#start-export").disabled=running||!project.timeline.length;$("#export-jobs").innerHTML=exports.map(j=>`<div class="export-job"><strong>${j.status==="done"?"Seu vídeo está pronto.":j.status==="error"?"A exportação não terminou.":"Preparando seu vídeo…"}</strong>${j.status==="done"?`<small>${j.result.width} × ${j.result.height} · ${precise(j.result.duration)} · versão ${j.result.revision}</small><a href="${j.result.url}" download>Baixar vídeo MP4 ↓</a>`:j.status==="error"?`<p>${esc(j.error)}</p>`:`<progress max="100" value="${j.progress}"></progress><small>${j.progress}% · você pode fechar esta janela.</small>`}</div>`).join("");}
$("#context-button").addEventListener("click",async()=>{try{const context=await api(`/api/projects/${project.id}/context`),blob=new Blob([JSON.stringify(context,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="lili-contexto.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Contexto salvo. O Codex também pode acessar o projeto pela CLI ou pelo MCP.");}catch(e){toast(e.message,true);}});
document.addEventListener("keydown",e=>{if(e.code==="Space"&&!/INPUT|TEXTAREA|SELECT|BUTTON/.test(document.activeElement.tagName)&&!document.querySelector("dialog[open]")){e.preventDefault();playing?pause():play();}});
setInterval(async()=>{if(!project||document.hidden)return;try{const fresh=await api(`/api/projects/${project.id}`);const editing=/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);if(fresh.revision!==project.revision&&!editing&&!playing){project=fresh;render();}if($("#export-dialog").open)await refreshJobs();}catch{$("#save-status").textContent="Servidor desconectado";}},2500);
(async()=>{try{await listProjects();if(!projects.length){const p=await api("/api/projects",{method:"POST",body:JSON.stringify({name:"Minha primeira história"})});await listProjects();await openProject(p.id);}else{const saved=localStorage.getItem("lili-project");await openProject(projects.some(p=>p.id===saved)?saved:projects[0].id);}}catch(e){toast("Não foi possível abrir o estúdio. "+e.message,true);}})();
