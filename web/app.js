"use strict";
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const icon = name => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const clock = seconds => { seconds = Math.max(0, seconds || 0); return `${String(Math.floor(seconds / 60)).padStart(2,"0")}:${String(Math.floor(seconds % 60)).padStart(2,"0")}`; };
const precise = seconds => `${Number(seconds).toFixed(1).replace(".",",")} s`;
const player = $("#player"), voice = $("#voice-player");
let project = null, selected = null, projects = [], queue = Promise.resolve(), toastTimer, uploadRunning = false, playing = false, seekBusy = false, loadedSource = "", dragId = null;
let cursor = 0, playerLoading = false, playTicket = 0, playbackFrame = 0;
let importBatch = null, pendingRemoval = null, aiAvailable = null, aiStarting = false, aiJobsKey = "";
const aiNotified = new Set();

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: {"Content-Type":"application/json", ...options.headers} });
  if(response.status===401){location.assign("/auth/login");throw new Error("Entre novamente para continuar.");}
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
function elapsed() { return cursor; }

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
  project = await api(`/api/projects/${id}`); selected = project.timeline[0]?.id || null; loadedSource = ""; cursor = 0;
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
    return `<article class="media-card"><button class="icon-button media-delete" data-delete-media="${m.id}" aria-label="Excluir arquivo ${esc(m.name)}" title="Excluir arquivo" ${["ready","error"].includes(m.status)?"":"disabled"}>${icon("trash")}</button>${ready && video ? `<img class="media-thumb" alt="" src="${assetUrl(m,"thumbnail")}">` : `<span class="media-thumb audio-thumb">${icon(m.kind==="audio"?"mic":"film")}</span>`}<div class="media-detail"><p class="media-name" title="${esc(m.name)}">${esc(m.name)}</p><p class="media-info">${ready ? `${precise(m.duration)} · ${video ? `${m.width}×${m.height}` : "Áudio"}` : esc(m.status==="error" ? "Falha ao importar" : "Preparando…")}</p>${ready ? `<button class="media-add" data-add="${m.id}">${icon(video ? "plus" : "mic")}${video ? "Adicionar" : "Usar narração"}</button>` : `<span class="microcopy">${esc(m.error || "Criando prévia")}</span>`}</div>${ready && video ? `<input class="tags-input" data-tags="${m.id}" aria-label="Etiquetas de ${esc(m.name)}" placeholder="Etiquetas: passeio, Cora…" value="${esc((m.tags||[]).join(", "))}">` : ""}</article>`;
  }).join("") || '<p class="empty-note">Cada gravação guarda um momento.<br>Importe o primeiro para começar.</p>';
  $("#media-list").querySelectorAll("[data-add]").forEach(button=>button.addEventListener("click",()=>{
    const m = project.media.find(a=>a.id===button.dataset.add);
    if(m.kind==="audio") { mutate("narration_set",{media_id:m.id},"Narração adicionada. Revise os volumes e a duração.").then(ok=>{if(ok)openInspector("voice");}); }
    else mutate("clip_add",{media_id:m.id,start:0,end:Math.min(4,m.duration)},"Cena adicionada à sequência.").then(ok=>{if(ok)closeSheet();});
  }));
  $("#media-list").querySelectorAll("[data-tags]").forEach(input=>input.addEventListener("change",()=>mutate("media_annotate",{media_id:input.dataset.tags,tags:input.value.split(",").map(s=>s.trim()).filter(Boolean)},"Etiquetas salvas.")));
  $("#media-list").querySelectorAll("[data-delete-media]").forEach(button=>button.addEventListener("click",()=>confirmMediaRemoval(button.dataset.deleteMedia)));
  const trash=project.trash||[];
  $("#trash-count").textContent=trash.length?`(${trash.length})`:"";
  $("#trash-list").innerHTML=trash.map(m=>`<article class="trash-card"><div>${icon(m.kind==="audio"?"mic":"film")}<strong>${esc(m.name)}</strong></div><button class="button secondary" data-restore-media="${m.id}">Restaurar</button></article>`).join("")||'<p class="empty-note">Nenhum arquivo na Lixeira.</p>';
  $("#trash-list").querySelectorAll("[data-restore-media]").forEach(button=>button.addEventListener("click",()=>mutate("media_restore",{media_id:button.dataset.restoreMedia},"Arquivo restaurado à biblioteca.")));
  renderTimeline(); renderRequests(); seekTo(Math.min(cursor, project.duration));
  $("#undo-button").disabled = !project.undo_available;
  $("#draft-button").disabled = !project.script.trim() || !project.media.some(m=>m.kind==="video" && m.status==="ready");
  $("#export-button").disabled = !project.timeline.length;
  $("#export-summary").textContent = `${project.timeline.length} cenas · ${precise(project.duration)} · versão ${project.revision}`;
  setImportControls();updateImportStatus(project);
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
function pause(){
  playing=false; playTicket++; player.pause(); voice.pause();
  cancelAnimationFrame(playbackFrame); playbackFrame=0;
  $("#play-button").innerHTML=icon("play");
  $("#play-button").setAttribute("aria-label","Reproduzir montagem");
}
async function play(){
  if(!currentClip()) return;
  if(cursor >= project.duration-.015) seekTo(0);
  const ticket=++playTicket; playing=true;
  $("#play-button").innerHTML=icon("pause");
  $("#play-button").setAttribute("aria-label","Pausar montagem");
  try {
    await player.play();
    if(ticket!==playTicket || !playing) return;
    syncVoice();
    cancelAnimationFrame(playbackFrame); playbackFrame=requestAnimationFrame(playbackTick);
  } catch(e) {
    if(ticket!==playTicket || e.name==="AbortError") return;
    pause(); toast("A prévia não pôde iniciar. Aguarde o carregamento e tente novamente.",true);
  }
}
function markSelection(){
  document.querySelectorAll("[data-clip]").forEach(node=>{
    const active=node.dataset.clip===selected;
    node.classList.toggle("selected",active);
    node.querySelector(".clip-body")?.setAttribute("aria-pressed",active);
  });
  renderInspector();
}
function selectClip(id, resume=false){
  pause(); selected=id; markSelection(); updatePlayer(false,before());
  if(resume) play();
}
function seekTo(time){
  if(!project) return;
  pause();
  cursor=Math.max(0,Math.min(project.duration,Number(time)||0));
  let offset=0;
  for(let i=0;i<project.timeline.length;i++){
    const c=project.timeline[i], length=c.end-c.start;
    if(cursor < offset+length-.00001 || i===project.timeline.length-1){selected=c.id;break;}
    offset+=length;
  }
  markSelection(); updatePlayer(false,cursor);
}
function updatePlayer(resume=false, time=before()){
  const c=currentClip(), m=c&&assetFor(c);
  $("#preview-empty").hidden=!!c; player.hidden=!c;
  $("#preview-title").textContent=c?.title || "";
  cursor=Math.max(0,Math.min(project.duration,time));
  if(!c){player.removeAttribute("src");loadedSource="";cursor=0;updateTime();return;}
  const source=assetUrl(m), clipId=c.id;
  const position=Math.min(c.end-.001,c.start+Math.max(0,cursor-before()));
  const seekAndPlay=()=>{
    if(currentClip()?.id!==clipId) return;
    if(Math.abs(player.currentTime-position)>.008){playerLoading=true;player.currentTime=position;}
    else playerLoading=false;
    if(resume && playing) play();
  };
  player.onloadedmetadata=seekAndPlay;
  player.poster=frameUrl(c); player.volume=Math.min(1,c.volume);
  if(loadedSource!==source){
    playerLoading=true; voice.pause(); player.src=source; loadedSource=source; player.load();
  } else if(player.readyState>=1) seekAndPlay();
  const narration=project.narration;
  if(narration){
    const a=project.media.find(m=>m.id===narration.media_id), src=assetUrl(a);
    if(voice.getAttribute("src")!==src){voice.src=src;voice.load();}
    voice.volume=Math.min(1,narration.volume);
  } else if(voice.hasAttribute("src")){voice.removeAttribute("src");voice.load();}
  $("#scene-position").textContent=`Cena ${index()+1} de ${project.timeline.length}`;
  updateTime();
}
function syncVoice(){
  if(!project?.narration||!playing||playerLoading||player.seeking||player.paused){voice.pause();return;}
  const time=cursor-project.narration.offset;
  if(time<0||time>=voice.duration){voice.pause();return;}
  if(voice.readyState>=1&&Math.abs(voice.currentTime-time)>.12) voice.currentTime=time;
  if(voice.paused) voice.play().catch(()=>{});
}
function updateTime(){
  if(!project) return;
  const time=Math.max(0,Math.min(project.duration,cursor));
  const stamp=t=>`${clock(t)}.${String(Math.floor((t%1)*100+.00001)).padStart(2,"0")}`;
  $("#timecode").innerHTML=`${stamp(time)} <span>/ ${stamp(project.duration)}</span>`;
  $("#seek").max=project.duration||1;
  if(!seekBusy) $("#seek").value=time;
  updatePlayhead(time);
}
function advance(){
  if(!playing) return;
  const i=index();
  if(i < project.timeline.length-1){
    cursor=before(i+1); selected=project.timeline[i+1].id;
    voice.pause(); markSelection(); updatePlayer(true,cursor);
  }else{cursor=project.duration;pause();updateTime();}
}
function playbackTick(){
  playbackFrame=0;
  if(!playing) return;
  const c=currentClip();
  if(c&&!playerLoading&&!player.seeking){
    cursor=before()+Math.max(0,Math.min(c.end-c.start,player.currentTime-c.start));
    updateTime();syncVoice();
    if(player.currentTime>=c.end-.012){advance();return;}
  }
  playbackFrame=requestAnimationFrame(playbackTick);
}
player.addEventListener("seeked",()=>{playerLoading=false;syncVoice();});
player.addEventListener("waiting",()=>voice.pause());
player.addEventListener("ended",advance);
player.addEventListener("error",()=>{if(currentClip()){pause();toast("A prévia não abriu. Aguarde a importação ou consulte o arquivo original.",true);}});
$("#play-button").addEventListener("click",()=>playing?pause():play());
$("#previous-clip").addEventListener("click",()=>{if(index()>0)selectClip(project.timeline[index()-1].id);});
$("#next-clip").addEventListener("click",()=>{if(index()<project.timeline.length-1)selectClip(project.timeline[index()+1].id);});
$("#seek").addEventListener("pointerdown",()=>{seekBusy=true;});
$("#seek").addEventListener("input",e=>seekTo(Number(e.target.value)));
$("#seek").addEventListener("change",()=>{seekBusy=false;updateTime();});
$("#seek").addEventListener("pointercancel",()=>{seekBusy=false;updateTime();});

async function uploadFiles(files){
  if(uploadRunning){toast("Aguarde o envio atual terminar.");return;}if(!project||!files.length)return;
  uploadRunning=true;$("#upload-progress").hidden=false;$("#dismiss-upload").hidden=true;
  const projectId=project.id;
  importBatch={projectId,total:files.length,mediaIds:[],error:""};setImportControls();
  try{
    for(const [index,file] of files.entries()){
      $("#upload-label").textContent=`Enviando ${index+1} de ${files.length}: ${file.name}`;$("#upload-meter").value=0;
      const upload=await api(`/api/projects/${projectId}/uploads`,{method:"POST",body:JSON.stringify({name:file.name,size:file.size})});
      for(let offset=0;offset<file.size;offset+=upload.chunk_size){
        const end=Math.min(file.size,offset+upload.chunk_size);
        const sendBlock=()=>new Promise((resolve,reject)=>{
          const xhr=new XMLHttpRequest();
          xhr.open("PUT",`/api/projects/${projectId}/uploads/${upload.upload_id}?offset=${offset}`);
          xhr.timeout=180000;
          xhr.upload.addEventListener("progress",e=>{if(e.lengthComputable)$("#upload-meter").value=(offset+e.loaded)/file.size*100;});
          xhr.addEventListener("load",()=>{
            if(xhr.status===401){location.assign("/auth/login");reject(new Error("Entre novamente para continuar."));return;}
            let data;try{data=JSON.parse(xhr.responseText);}catch{reject(new Error("Falha na conexão durante o envio."));return;}
            xhr.status<400?resolve(data):reject(new Error(data.error||"Falha no envio."));
          });
          xhr.addEventListener("error",()=>reject(new Error("O envio foi interrompido. Verifique a conexão.")));
          xhr.addEventListener("timeout",()=>reject(new Error("A conexão demorou demais para enviar o vídeo.")));
          xhr.send(file.slice(offset,end));
        });
        // A repeat of the same block is acknowledged without appending it twice.
        try{await sendBlock();}catch(first){await sendBlock();}
      }
      const imported=await api(`/api/projects/${projectId}/uploads/${upload.upload_id}/complete`,{method:"POST",body:"{}"});
      importBatch.mediaIds.push(imported.media_id);
    }
    toast("Arquivos recebidos. As prévias estão sendo preparadas.");
    if(project.id===projectId){project=await api(`/api/projects/${projectId}`);render();}
  }
  catch(e){importBatch.error=e.message;toast(e.message,true);}finally{uploadRunning=false;setImportControls();updateImportStatus(project);$("#file-input").value="";}
}
function setImportControls(){
  ["#project-select","#new-project","#import-main","#import-mobile","#import-top","#import-zone"].forEach(selector=>$(selector).disabled=uploadRunning||!project);
}
async function openAIEditor(){
  if(!project)return;
  pause();closeSheet();
  $("#ai-dialog").showModal();
  $("#ai-readiness").textContent="Verificando roteiro e arquivos…";$("#start-ai-edit").disabled=true;
  try{
    await queue;
    if($("#script-input").value!==project.script){if(!await mutate("script_update",{script:$("#script-input").value},"Roteiro salvo para a montagem."))return;}
    aiAvailable=await api("/api/ai/status");
    await refreshJobs();
  }catch(error){$("#ai-readiness").textContent=error.message;}
}
function renderAIJobs(jobs){
  const edits=jobs.filter(j=>j.kind==="ai_edit").reverse(),running=edits.some(j=>["queued","running"].includes(j.status));
  const videos=project.media.filter(m=>m.kind==="video"&&m.status==="ready");
  let reason="";
  if(!project.script.trim())reason="Adicione o roteiro em Arquivos → Roteiro e tente novamente.";
  else if(uploadRunning||project.media.some(m=>m.status==="processing"))reason="Aguarde o envio e a preparação de todos os arquivos.";
  else if(project.media.some(m=>m.status!=="ready"))reason="Há arquivos com falha. Reimporte ou envie esses arquivos à Lixeira.";
  else if(!videos.length)reason="Importe pelo menos um vídeo em Arquivos.";
  else if(videos.length>40)reason="Esta versão aceita até 40 vídeos por montagem.";
  else if(aiAvailable&&!aiAvailable.available)reason="O Codex precisa estar instalado e conectado no notebook.";
  $("#ai-readiness").textContent=reason||`${videos.length} vídeo(s) prontos · roteiro salvo · ${project.timeline.length} cenas na montagem atual`;
  $("#ai-replace-note").textContent=project.timeline.length?"Ao iniciar, a IA substituirá a montagem atual, preservando cenas protegidas. Você poderá desfazer. Evite editar enquanto a IA trabalha: mudanças no projeto impedem a aplicação do resultado.":"A primeira montagem aparecerá na linha do tempo. Mantenha o notebook ligado durante a análise.";
  $("#start-ai-edit").disabled=!!reason||running||aiStarting||!aiAvailable?.available;
  $("#ai-edit-button").classList.toggle("ai-running",running);
  $("#ai-mobile").classList.toggle("ai-running",running);
  const jobsKey=JSON.stringify([project.id,edits.slice(0,1)]);
  if(jobsKey!==aiJobsKey){
    aiJobsKey=jobsKey;
    $("#ai-jobs").innerHTML=edits.slice(0,1).map(j=>`<article class="ai-job ${j.status}"><strong>${j.status==="done"?"Montagem aplicada à linha do tempo":j.status==="error"?"A montagem não foi aplicada":esc(j.stage||"Aguardando análise do Codex")}</strong>${j.status==="done"?`<p>${esc(j.result.summary)}</p><small>${j.result.clip_count} cenas · ${precise(j.result.duration)} · versão ${j.result.revision}</small><button class="button secondary full" data-ai-review>Revisar na linha do tempo</button><details><summary>Observações da montagem</summary>${j.result.warnings.map(w=>`<p class="ai-warning">${esc(w)}</p>`).join("")}</details>`:j.status==="error"?`<p>${esc(j.error)}</p>`:'<p>Você pode fechar esta janela e acompanhar pelo botão Editar com IA.</p><progress aria-label="Edição com IA em andamento"></progress>'}</article>`).join("");
    $("#ai-jobs").querySelectorAll("[data-ai-review]").forEach(b=>b.addEventListener("click",async()=>{try{await queue;project=await api(`/api/projects/${project.id}`);selected=project.timeline[0]?.id||null;cursor=0;render();$("#ai-dialog").close();closeSheet();}catch(error){toast(error.message,true);}}));
  }
  for(const j of edits){
    if(["queued","running"].includes(j.status)){aiNotified.add("running-"+j.id);continue;}
    if(aiNotified.has("running-"+j.id)&&!aiNotified.has(j.id)){
      aiNotified.add(j.id);toast(j.status==="done"?"A IA concluiu a montagem. Abra Editar com IA para revisar.":"A edição com IA não terminou. Abra Editar com IA para ver o motivo.",j.status==="error");
    }
  }
}
$("#ai-edit-button").addEventListener("click",openAIEditor);
$("#ai-mobile").addEventListener("click",openAIEditor);
$("#start-ai-edit").addEventListener("click",async()=>{
  if(aiStarting)return;aiStarting=true;$("#start-ai-edit").disabled=true;
  await queue;const id=project.id;
  try{
    await api(`/api/projects/${id}/ai-edit`,{method:"POST",body:JSON.stringify({expected_revision:project.revision,instructions:$("#ai-instructions").value})});
    toast("A IA começou a analisar o roteiro e os vídeos.");
  }catch(error){toast(error.message,true);}finally{aiStarting=false;await refreshJobs();}
});
function updateImportStatus(snapshot){
  const status=$("#upload-progress");
  if(!importBatch||snapshot?.id!==importBatch.projectId){status.hidden=true;return;}
  status.hidden=false;
  if(uploadRunning)return;
  $("#dismiss-upload").hidden=false;
  const assets=importBatch.mediaIds.map(id=>[...snapshot.media,...(snapshot.trash||[])].find(m=>m.id===id));
  const ready=assets.filter(m=>m?.status==="ready").length,failed=assets.filter(m=>m?.status==="error").length;
  if(importBatch.error){$("#upload-label").textContent=`Envio interrompido: ${importBatch.error}`;$("#upload-meter").value=0;}
  else if(failed){$("#upload-label").textContent=`${ready} prontos · ${failed} com falha. Veja os detalhes em Arquivos.`;$("#upload-meter").value=100;}
  else if(ready===importBatch.total){$("#upload-label").textContent=ready===1?"Arquivo pronto para usar.":`${ready} arquivos prontos para usar.`;$("#upload-meter").value=100;}
  else{$("#upload-label").textContent=`Arquivos recebidos. Preparando prévias (${ready} de ${importBatch.total} prontas)…`;$("#upload-meter").removeAttribute("value");}
}
function openFilePicker(){
  if(!project)return;if(uploadRunning){toast("Aguarde o envio atual terminar.");return;}
  pause();$("#file-input").click();
}
function markMobilePanel(name){document.querySelectorAll("[data-mobile-panel]").forEach(button=>{if(button.dataset.mobilePanel===name)button.setAttribute("aria-current","page");else button.removeAttribute("aria-current");});}
function closeSheet(){delete document.body.dataset.mobileSheet;$("#sheet-backdrop").hidden=true;markMobilePanel("timeline");}
function openInspector(name){setInspector(name);markMobilePanel("scene");revealPanel(".inspector");}
function revealPanel(selector){
  if(matchMedia("(max-width:640px)").matches){
    document.body.dataset.mobileSheet=selector===".library"?"library":"inspector";$("#sheet-backdrop").hidden=false;return;
  }
  if(matchMedia("(max-width:930px)").matches)$(selector).scrollIntoView({behavior:matchMedia("(prefers-reduced-motion:reduce)").matches?"auto":"smooth",block:"start"});
}
function openLibraryTab(name,focus=false){
  document.querySelectorAll("[data-tab]").forEach(tab=>tab.classList.toggle("active",tab.dataset.tab===name));
  ["media","script","requests","trash"].forEach(tab=>$("#tab-"+tab).hidden=tab!==name);
  markMobilePanel(name);revealPanel(".library");
  if(focus)$(name==="requests"?"#request-input":"#script-input").focus({preventScroll:true});
}
function confirmMediaRemoval(id){
  const m=project.media.find(a=>a.id===id);if(!m)return;
  pause();pendingRemoval={projectId:project.id,mediaId:id,revision:project.revision};
  const clips=project.timeline.filter(c=>c.media_id===id), narration=project.narration?.media_id===id, locked=clips.some(c=>c.locked);
  $("#delete-media-name").textContent=m.name;
  $("#delete-media-impact").textContent=locked?"Este arquivo tem cenas protegidas. Desproteja essas cenas em Ajustes antes de excluir.":clips.length||narration?`Também serão removidas ${clips.length} cena(s) da linha do tempo${narration?" e a faixa de narração":""}. A duração e o encaixe dos cortes seguintes podem mudar.`:"Este arquivo não está sendo usado na montagem.";
  $("#confirm-delete-media").disabled=locked;
  $("#delete-media-dialog").showModal();
}
$("#delete-media-form").addEventListener("submit",async e=>{
  e.preventDefault();const target=pendingRemoval;if(!target)return;
  // Await queued edits, then require review again if any usage may have changed.
  await queue;
  if(project.id!==target.projectId){$("#delete-media-dialog").close();return;}
  if(project.revision!==target.revision){$("#delete-media-dialog").close();toast("O projeto mudou. Revise a exclusão novamente.",true);return;}
  $("#confirm-delete-media").disabled=true;
  if(await mutate("media_remove",{media_id:target.mediaId,remove_usage:true},"Arquivo enviado à Lixeira. Você pode desfazer."))$("#delete-media-dialog").close();
  else $("#confirm-delete-media").disabled=false;
});
document.querySelectorAll("[data-close-sheet]").forEach(b=>b.addEventListener("click",closeSheet));
$("#sheet-backdrop").addEventListener("click",closeSheet);
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!document.querySelector("dialog[open]"))closeSheet();});
matchMedia("(max-width:640px)").addEventListener("change",()=>closeSheet());
$("#file-input").addEventListener("change",e=>uploadFiles([...e.target.files]));
["#import-top","#import-zone","#import-main","#import-mobile"].forEach(s=>$(s).addEventListener("click",openFilePicker));
$("#codex-main").addEventListener("click",()=>openLibraryTab("requests",true));
$("#view-uploaded").addEventListener("click",()=>openLibraryTab("media"));
$("#dismiss-upload").addEventListener("click",()=>{importBatch=null;$("#upload-progress").hidden=true;});
document.querySelectorAll("[data-mobile-panel]").forEach(button=>button.addEventListener("click",()=>{
  const name=button.dataset.mobilePanel;
  if(name==="timeline"){closeSheet();markMobilePanel(name);$(".timeline-panel").scrollIntoView({behavior:"auto",block:"start"});}
  else if(name==="scene"){openInspector("scene");}
  else openLibraryTab(name,name==="requests");
}));
$("#import-zone").addEventListener("dragover",e=>e.preventDefault());$("#import-zone").addEventListener("drop",e=>{e.preventDefault();uploadFiles([...e.dataTransfer.files]);});
document.querySelectorAll("[data-tab]").forEach(button=>button.addEventListener("click",()=>openLibraryTab(button.dataset.tab)));
document.querySelectorAll("[data-inspector]").forEach(b=>b.addEventListener("click",()=>setInspector(b.dataset.inspector)));
$("#step-visual").addEventListener("click",()=>setInspector("scene"));$("#step-voice").addEventListener("click",()=>{setInspector("voice");if(matchMedia("(max-width:640px)").matches)revealPanel(".inspector");});
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
async function refreshJobs(){if(!project)return;const jobs=await api(`/api/projects/${project.id}/jobs`),exports=jobs.filter(j=>j.kind==="export").reverse();renderAIJobs(jobs);const running=exports.some(j=>["queued","running"].includes(j.status));$("#start-export").disabled=running||!project.timeline.length;$("#export-jobs").innerHTML=exports.map(j=>`<div class="export-job"><strong>${j.status==="done"?"Seu vídeo está pronto.":j.status==="error"?"A exportação não terminou.":"Preparando seu vídeo…"}</strong>${j.status==="done"?`<small>${j.result.width} × ${j.result.height} · ${precise(j.result.duration)} · versão ${j.result.revision}</small><a href="${j.result.url}" download>Baixar vídeo MP4 ↓</a>`:j.status==="error"?`<p>${esc(j.error)}</p>`:`<progress max="100" value="${j.progress}"></progress><small>${j.progress}% · você pode fechar esta janela.</small>`}</div>`).join("");}
$("#context-button").addEventListener("click",async()=>{try{const context=await api(`/api/projects/${project.id}/context`),blob=new Blob([JSON.stringify(context,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="lili-contexto.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Contexto salvo. O Codex também pode acessar o projeto pela CLI ou pelo MCP.");}catch(e){toast(e.message,true);}});
document.addEventListener("keydown",e=>{if(e.code==="Space"&&!/INPUT|TEXTAREA|SELECT|BUTTON/.test(document.activeElement.tagName)&&!document.querySelector("dialog[open]")){e.preventDefault();playing?pause():play();}});
setInterval(async()=>{if(!project||document.hidden||timelineGesture)return;try{const fresh=await api(`/api/projects/${project.id}`);updateImportStatus(fresh);const editing=/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);if(fresh.revision!==project.revision&&!editing&&!playing&&!timelineGesture){project=fresh;render();}await refreshJobs();}catch{$("#save-status").textContent="Servidor desconectado";}},2500);
(async()=>{try{await listProjects();if(!projects.length){const p=await api("/api/projects",{method:"POST",body:JSON.stringify({name:"Minha primeira história"})});await listProjects();await openProject(p.id);}else{const saved=localStorage.getItem("lili-project");await openProject(projects.some(p=>p.id===saved)?saved:projects[0].id);}}catch(e){toast("Não foi possível abrir o estúdio. "+e.message,true);}})();

if("serviceWorker" in navigator&&window.isSecureContext)navigator.serviceWorker.register("/sw.js").catch(()=>{});
$("#phone-help").addEventListener("click",()=>{
  $("#phone-connection-note").textContent=location.protocol==="https:"?`Endereço deste estúdio: ${location.origin}`:"O acesso por este endereço funciona apenas no notebook. Prepare o login e ative o endereço remoto para abrir no iPhone.";
  $("#phone-dialog").showModal();
});
fetch("/auth/status").then(r=>r.ok?r.json():null).then(data=>{if(data?.authenticated)$("#logout-form").hidden=false;}).catch(()=>{});
