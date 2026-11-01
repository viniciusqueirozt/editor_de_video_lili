"use strict";
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const icon = name => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const clock = seconds => { seconds = Math.max(0, seconds || 0); return `${String(Math.floor(seconds / 60)).padStart(2,"0")}:${String(Math.floor(seconds % 60)).padStart(2,"0")}`; };
const precise = seconds => `${Number(seconds).toFixed(1).replace(".",",")} s`;
const player = $("#player"), voice = $("#voice-player"), musicPlayer = $("#music-player");
let project = null, selected = null, projects = [], queue = Promise.resolve(), toastTimer, uploadRunning = false, playing = false, seekBusy = false, loadedSource = "", dragId = null;
let cursor = 0, playerLoading = false, playTicket = 0, playbackFrame = 0;
let previewSeek = null;
let editorFeatures = {};
const uploadState = {pending:null, cancel:false, completing:false, available:false};
let importBatch = null, pendingRemoval = null, aiAvailable = null, aiStarting = false, aiJobsKey = "";
const aiNotified = new Set();
let selectingMedia=false;
let selectedCaption=null,pendingSRT=null;
const selectedMedia=new Set();
let pendingProjectRemoval=null;
let previewReturnPoints=[];

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: {"Content-Type":"application/json", ...options.headers} });
  if(response.status===401){location.assign("/auth/login");throw new Error("Entre novamente para continuar.");}
  const result = await response.json();
  if (!response.ok) throw Object.assign(new Error(result.error || "Não foi possível concluir."),{status:response.status});
  return result;
}
function toast(message, error = false) {
  clearTimeout(toastTimer); const node = $("#toast"); node.textContent = message; node.className = error ? "error" : ""; node.hidden = false;
  toastTimer = setTimeout(() => {node.hidden = true;}, error ? 8500 : 5000);
}
function assetUrl(asset, kind="proxy") { return `/api/projects/${project.id}/media/${asset.id}/${kind}`; }
function frameUrl(clip) { return assetUrl(assetFor(clip),"frame.jpg")+"?at="+clip.start; }
function assetFor(clip) { return project.media.find(m => m.id === clip.media_id); }
$("#expand-preview").addEventListener("click",()=>{
  pause();
  const dialog=$("#preview-dialog"),slot=$("#expanded-preview-slot");
  if(dialog.open)return;
  for(const node of [$("#preview-stage"),document.querySelector(".playback")]){
    const marker=document.createComment("preview-return");node.before(marker);previewReturnPoints.push({node,marker});slot.append(node);
  }
  dialog.showModal();updateTime();
});
$("#preview-dialog").addEventListener("close",()=>{
  pause();
  for(const {node,marker} of previewReturnPoints){marker.replaceWith(node);}
  previewReturnPoints=[];$("#expand-preview").focus();updateTime();
});
function currentClip() { return project?.timeline.find(c => c.id === selected); }
function index() { return project?.timeline.findIndex(c => c.id === selected) ?? -1; }
function clipDuration(clip){return (clip.end-clip.start)/(clip.speed||1);}
function before(i = index()) { return project.timeline.slice(0, Math.max(0,i)).reduce((a,c) => a + clipDuration(c), 0); }
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
  selectingMedia=false;selectedMedia.clear();selectedCaption=null;
  project = await api(`/api/projects/${id}`); exportJobRunning=false; selected = project.timeline[0]?.id || null; loadedSource = ""; cursor = 0;
  localStorage.setItem("lili-project",id);history.replaceState(null,"",`/editor?project=${id}`); render(); await refreshJobs();
}
function render() {
  if (!project) return;
  if (!project.timeline.some(c => c.id === selected)) selected = project.timeline[0]?.id || null;
  $("#project-name").textContent = project.name;
  $("#project-select").value = project.id;
  const option = $("#project-select").selectedOptions[0]; if(option) option.textContent = project.name;
  $("#save-status").innerHTML = '<i></i> Salvo neste computador';
  const projectNotice=[project.recovery_notice,project.description].filter(Boolean).join(" ");
  $("#project-note").hidden = !projectNotice; $("#project-note").textContent = projectNotice;
  $("#media-count").textContent = project.media.length;
  $("#ready-count").textContent = `${project.media.filter(m=>m.status==="ready").length} prontos`;
  if (document.activeElement !== $("#script-input")) $("#script-input").value = project.script;
  $("#script-blocks").innerHTML = project.blocks.map((b,i)=>`<div class="script-block"><strong>BLOCO ${String(i+1).padStart(2,"0")}</strong>${esc(b.text)}</div>`).join("");
  $("#media-list").innerHTML = project.media.map(m => {
    const ready = m.status === "ready", video = m.kind === "video";
    return `<article class="media-card">${selectingMedia?`<label class="media-pick"><input type="checkbox" data-pick-media="${m.id}" aria-label="Selecionar ${esc(m.name)}" ${selectedMedia.has(m.id)?"checked":""} ${["ready","error"].includes(m.status)?"":"disabled"}></label>`:""}<button class="icon-button media-delete" data-delete-media="${m.id}" aria-label="Excluir arquivo ${esc(m.name)}" title="Excluir arquivo" ${["ready","error"].includes(m.status)?"":"disabled"}>${icon("trash")}</button>${ready && video ? `<img class="media-thumb" alt="" src="${assetUrl(m,"thumbnail")}">` : `<span class="media-thumb audio-thumb">${icon(m.kind==="audio"?"mic":"film")}</span>`}<div class="media-detail"><p class="media-name" title="${esc(m.name)}">${esc(m.name)}</p><p class="media-info">${ready ? `${precise(m.duration)} · ${video ? `${m.is_still?"Foto · ":""}${m.width}×${m.height}` : "Áudio"}` : esc(m.status==="error" ? "Falha ao importar" : "Preparando…")}</p>${ready ? `<button class="media-add" data-add="${m.id}">${icon(video ? "plus" : "mic")}${video ? "Adicionar" : "Usar narração"}</button>${editorFeatures.music_track&&m.has_audio?`<button class="music-library-button" data-use-music="${m.id}">Usar como música</button>`:""}` : `<span class="microcopy">${esc(m.error || "Criando prévia")}</span>`}</div>${ready && video ? `<input class="tags-input" data-tags="${m.id}" aria-label="Etiquetas de ${esc(m.name)}" placeholder="Etiquetas: passeio, Cora…" value="${esc((m.tags||[]).join(", "))}">` : ""}</article>`;
  }).join("") || '<p class="empty-note">Cada gravação guarda um momento.<br>Importe o primeiro para começar.</p>';
  $("#media-list").querySelectorAll("[data-add]").forEach(button=>button.addEventListener("click",()=>{
    const m = project.media.find(a=>a.id===button.dataset.add);
    if(m.kind==="audio") { mutate("narration_set",{media_id:m.id},"Narração adicionada. Revise os volumes e a duração.").then(ok=>{if(ok)openInspector("voice");}); }
    else mutate("clip_add",{media_id:m.id,start:0,end:Math.min(4,m.duration)},"Cena adicionada à sequência.").then(ok=>{if(ok)closeSheet();});
  }));
  $("#media-list").querySelectorAll("[data-use-music]").forEach(button=>button.addEventListener("click",()=>mutate("music_set",{media_id:button.dataset.useMusic},"Música adicionada. Revise o volume.").then(ok=>{if(ok)openInspector("music");})));
  $("#media-list").querySelectorAll("[data-tags]").forEach(input=>input.addEventListener("change",()=>mutate("media_annotate",{media_id:input.dataset.tags,tags:input.value.split(",").map(s=>s.trim()).filter(Boolean)},"Etiquetas salvas.")));
  $("#media-list").querySelectorAll("[data-delete-media]").forEach(button=>button.addEventListener("click",()=>confirmMediaRemoval(button.dataset.deleteMedia)));
  for(const id of selectedMedia) if(!project.media.some(m=>m.id===id))selectedMedia.delete(id);
  $("#media-list").querySelectorAll("[data-pick-media]").forEach(input=>input.addEventListener("change",()=>{input.checked?selectedMedia.add(input.dataset.pickMedia):selectedMedia.delete(input.dataset.pickMedia);updateMediaSelection();}));
  updateMediaSelection();
  const trash=project.trash||[];
  $("#trash-count").textContent=trash.length?`(${trash.length})`:"";
  $("#trash-list").innerHTML=trash.map(m=>`<article class="trash-card"><div>${icon(m.kind==="audio"?"mic":"film")}<strong>${esc(m.name)}</strong></div><button class="button secondary" data-restore-media="${m.id}">Restaurar</button></article>`).join("")||'<p class="empty-note">Nenhum arquivo na Lixeira.</p>';
  $("#trash-list").querySelectorAll("[data-restore-media]").forEach(button=>button.addEventListener("click",()=>mutate("media_restore",{media_id:button.dataset.restoreMedia},"Arquivo restaurado à biblioteca.")));
  renderMusicInspector();renderCaptionInspector();renderTimeline(); renderRequests(); seekTo(Math.min(cursor, project.duration),true);
  $("#undo-button").disabled = !project.undo_available;$("#redo-button").hidden=!editorFeatures.redo;$("#redo-button").disabled=!project.redo_available;
  $("#draft-button").disabled = !project.script.trim() || !project.media.some(m=>m.kind==="video" && m.status==="ready");
  $("#export-button").disabled = !project.timeline.length;
  configureExportControls();updateExportSummary();
  const width=project.settings.width,height=project.settings.height;
  $("#canvas-label").textContent=`${width===height?"1:1":width>height?"16:9":"9:16"} · ${width}×${height}`;
  $("#expand-preview").disabled=!project.timeline.length;
  $("#video-frame").style.setProperty("--canvas-ratio",`${width/height}`);
  $("#video-frame").style.aspectRatio=`${width}/${height}`;
  setImportControls();updateImportStatus(project);
}
function renderInspector() {
  const c = currentClip();
  if(!c) $("#scene-inspector").innerHTML = '<div class="empty-note">Selecione uma cena da sequência.<br>Os detalhes aparecem aqui.</div>';
  else {
    const m=assetFor(c), i=index();
    $("#scene-inspector").innerHTML = `<span class="scene-chip">${icon("film")} CENA ${String(i+1).padStart(2,"0")}</span><label class="field-label" for="scene-source">Tomada</label><select id="scene-source" ${c.locked?"disabled":""}>${project.media.filter(m=>m.kind==="video"&&m.status==="ready").map(a=>`<option value="${a.id}" ${a.id===c.media_id?"selected":""}>${esc(a.name)}</option>`).join("")}</select><label class="field-label" for="scene-label">Nome da cena</label><input id="scene-label" maxlength="160" value="${esc(c.label)}" ${c.locked?"disabled":""}><div class="trim-fields"><div><label class="field-label" for="clip-start">Entrada · segundos</label><input id="clip-start" type="number" inputmode="decimal" min="0" max="${m.duration}" step="0.1" value="${c.start}" ${c.locked?"disabled":""}></div><div><label class="field-label" for="clip-end">Saída · segundos</label><input id="clip-end" type="number" inputmode="decimal" min="0.1" max="${m.duration}" step="0.1" value="${c.end}" ${c.locked?"disabled":""}></div></div>${editorFeatures.framing_watermark?`<fieldset class="effect-fields"><legend>Enquadramento</legend><label class="field-label" for="scene-framing">Ajuste à tela</label><select id="scene-framing" ${c.locked?"disabled":""}><option value="contain" ${(c.framing||"contain")==="contain"?"selected":""}>Mostrar vídeo inteiro</option><option value="cover" ${c.framing==="cover"?"selected":""}>Preencher tela · recorta bordas</option></select>${["x","y"].map(axis=>`<label class="field-label" for="scene-pan-${axis}">Posição ${axis==="x"?"horizontal":"vertical"}</label><input id="scene-pan-${axis}" type="range" min="0" max="100" value="${Math.round((c["pan_"+axis]??.5)*100)}" ${c.locked?"disabled":""}>`).join("")}<label class="mirror-control"><input id="scene-mirror" type="checkbox" ${c.mirror?"checked":""} ${c.locked?"disabled":""}> Espelhar horizontalmente</label></fieldset>`:""}<p class="selected-duration">Duração na montagem: ${precise(clipDuration(c))}</p>${editorFeatures.clip_speed?`<label class="field-label" for="scene-speed">Velocidade</label><select id="scene-speed" ${c.locked?"disabled":""}>${[.25,.5,.75,1,1.25,1.5,2,3,4].map(value=>`<option value="${value}" ${(c.speed||1)===value?"selected":""}>${value}×${value===1?" · normal":""}</option>`).join("")}</select><p class="help">Altera a duração da cena. Confira a narração e os fades após mudar.</p>`:""}${editorFeatures.visual_fades?`<fieldset class="effect-fields"><legend>Entrada e saída para preto</legend><div class="trim-fields">${["in","out"].map((side)=>`<div><label class="field-label" for="scene-fade-${side}">${side==="in"?"Entrada":"Saída"} · segundos</label><input id="scene-fade-${side}" type="number" min="0" max="${clipDuration(c)}" step="0.1" value="${c["fade_"+side]||0}" ${c.locked?"disabled":""}></div>`).join("")}</div><p class="help">0 desativa. Mantém a duração e o sincronismo da montagem.</p></fieldset>`:""}${editorFeatures.color_adjustments?`<fieldset class="effect-fields"><legend>Luz e cor</legend>${[["brightness","Brilho",50,150],["contrast","Contraste",50,150],["saturation","Saturação",0,200]].map(([key,label,min,max])=>`<label class="field-label" for="scene-${key}">${label} · <output id="${key}-value">${Math.round((c[key]??1)*100)}%</output></label><input id="scene-${key}" type="range" min="${min}" max="${max}" value="${Math.round((c[key]??1)*100)}" ${c.locked?"disabled":""}>`).join("")}<button id="reset-color" class="button secondary full" ${c.locked?"disabled":""}>Restaurar cor original</button></fieldset>`:""}<label class="field-label" for="scene-title">Texto sobre a cena</label><textarea id="scene-title" rows="2" maxlength="160" placeholder="Um título breve, se fizer sentido." ${c.locked?"disabled":""}>${esc(c.title)}</textarea>${editorFeatures.caption_styles?`<div class="caption-controls">${[["font","Fonte",[["sans","Simples · Arial"],["serif","Editorial · Georgia"],["mono","Monoespaçada · Consolas"]],"sans"],["size","Tamanho",[["small","Pequeno"],["medium","Médio"],["large","Grande"]],"medium"],["position","Posição",[["legacy","Clássica"],["top","Parte superior"],["center","Centro"],["bottom","Parte inferior"]],"legacy"]].map(([key,label,options,defaultValue])=>`<label class="field-label" for="title-${key}">${label}</label><select id="title-${key}" ${c.locked?"disabled":""}>${options.map(([value,name])=>`<option value="${value}" ${(c["title_"+key]||defaultValue)===value?"selected":""}>${name}</option>`).join("")}</select>`).join("")}<p class="help">Texto manual por cena. Fontes locais, sem download ou assinatura.</p></div>`:""}<label class="field-label" for="clip-volume">Som original</label><div class="range-row"><input id="clip-volume" type="range" min="0" max="100" value="${Math.round(c.volume*100)}" ${c.locked?"disabled":""}><output id="clip-volume-value">${Math.round(c.volume*100)}%</output></div>${editorFeatures.scene_audio_fades?`<fieldset class="effect-fields"><legend>Fades do som original</legend><div class="trim-fields">${["in","out"].map(side=>`<div><label class="field-label" for="audio-fade-${side}">${side==="in"?"Entrada":"Saída"} · segundos</label><input id="audio-fade-${side}" type="number" min="0" max="${clipDuration(c)}" step="0.1" value="${c["audio_fade_"+side]||0}" ${c.locked?"disabled":""}></div>`).join("")}</div><p class="help">Suaviza o som da cena sem mudar a imagem. A exportação limita picos.</p></fieldset>`:""}<hr class="divider"><button class="lock-control ${c.locked?"locked":""}" id="lock-clip" aria-pressed="${c.locked}">${icon("lock")}<span><strong>${c.locked?"Cena protegida":"Proteger esta escolha"}</strong><small>Preserva a tomada e seus ajustes.</small></span></button><div class="reorder-buttons"><button class="button secondary" id="move-left" ${i===0?"disabled":""}>${icon("left")}Antes</button><button class="button secondary" id="move-right" ${i===project.timeline.length-1?"disabled":""}>Depois${icon("right")}</button></div><button class="danger-button" id="remove-clip" ${c.locked?"disabled":""}>${icon("trash")}Remover da sequência</button>`;
    const update=changes=>mutate("clip_update",{clip_id:c.id,...changes});
    for(const key of ["brightness","contrast","saturation"]){
      $("#scene-"+key)?.addEventListener("input",e=>{$("#"+key+"-value").value=e.target.value+"%";updatePreviewGrade({...c,[key]:Number(e.target.value)/100});});
      $("#scene-"+key)?.addEventListener("change",e=>update({[key]:Number(e.target.value)/100}));
    }
    $("#reset-color")?.addEventListener("click",()=>update({brightness:1,contrast:1,saturation:1}));
    $("#scene-speed")?.addEventListener("change",e=>update({speed:Number(e.target.value)}));
    $("#scene-framing")?.addEventListener("change",e=>update({framing:e.target.value}));
    $("#scene-mirror")?.addEventListener("change",e=>update({mirror:e.target.checked}));
    for(const axis of ["x","y"])$("#scene-pan-"+axis)?.addEventListener("change",e=>update({["pan_"+axis]:Number(e.target.value)/100}));
    $("#clip-start").addEventListener("change",e=>update({start:Number(e.target.value)}));
    $("#clip-end").addEventListener("change",e=>update({end:Number(e.target.value)}));
    $("#scene-label").addEventListener("change",e=>update({label:e.target.value}));
    for(const side of ["in","out"])$("#audio-fade-"+side)?.addEventListener("change",e=>update({["audio_fade_"+side]:Number(e.target.value)}));
    for(const side of ["in","out"])$("#scene-fade-"+side)?.addEventListener("change",e=>update({["fade_"+side]:Number(e.target.value)}));
    for(const key of ["font","size","position"])$("#title-"+key)?.addEventListener("change",e=>update({["title_"+key]:e.target.value}));
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
  $("#voice-inspector").innerHTML = `<p class="help">Monte as cenas primeiro. Depois, traga a narração para encontrar o ritmo final.</p><label class="field-label" for="voice-source">Arquivo de narração</label><select id="voice-source"><option value="">Sem narração adicional</option>${audios.map(a=>`<option value="${a.id}" ${a.id===n?.media_id?"selected":""}>${esc(a.name)}</option>`).join("")}</select><button class="button secondary full" id="import-voice" style="margin-top:12px">${icon("upload")}Importar áudio</button>${n?`<button id="voice-timing" class="button secondary full">Ajustar tempo e ouvir prévia</button><label class="field-label" for="voice-volume">Volume da narração</label><div class="range-row"><input id="voice-volume" type="range" min="0" max="100" value="${Math.round(n.volume*100)}"><output id="voice-volume-value">${Math.round(n.volume*100)}%</output></div><label class="field-label" for="voice-offset">Começar após · segundos</label><input id="voice-offset" type="number" min="0" max="3600" step="0.1" value="${n.offset}"><label class="field-label" for="voice-fade_in">Entrada suave · segundos</label><input id="voice-fade_in" type="number" min="0" max="${na.duration}" step="0.1" value="${n.fade_in||0}"><label class="field-label" for="voice-fade_out">Saída suave · segundos</label><input id="voice-fade_out" type="number" min="0" max="${na.duration}" step="0.1" value="${n.fade_out||0}"><p class="help">A saída suave termina no fim do arquivo de narração. Use 0 para desativar.</p><div class="voice-note ${na.duration+n.offset>project.duration+0.1?"voice-warning":""}">${na.duration+n.offset>project.duration+0.1?"A narração ultrapassa a montagem. Prolongue as cenas para ouvir a fala completa na exportação.":"A narração acompanha a montagem. Ajuste o som original de cada cena para equilibrar a voz."}<br>Áudio: ${precise(na.duration)} · montagem: ${precise(project.duration)}</div>`:'<div class="voice-note">A Elisa continua gravando a própria voz. A narração adicional pode ser adicionada depois.</div>'}`;
  $("#voice-source").addEventListener("change",e=>mutate("narration_set",{media_id:e.target.value||null}));
  $("#import-voice").addEventListener("click",()=>$("#file-input").click());
  if(n){$("#voice-timing").addEventListener("click",()=>openAudioEdit("narration"));for(const key of ["fade_in","fade_out"]) $("#voice-"+key).addEventListener("change",e=>mutate("narration_set",{[key]:Number(e.target.value)}));$("#voice-volume").addEventListener("input",e=>{$("#voice-volume-value").value=`${e.target.value}%`;voice.volume=voiceGain({...n,volume:Number(e.target.value)/100},cursor-n.offset,na.duration);});$("#voice-volume").addEventListener("change",e=>mutate("narration_set",{volume:Number(e.target.value)/100}));$("#voice-offset").addEventListener("change",e=>mutate("narration_set",{offset:Number(e.target.value)}));}
}
function renderCaptionInspector(){
  $("#captions-tab").hidden=!editorFeatures.subtitles;
  if(!editorFeatures.subtitles)return;
  const captions=project.captions||[];
  if(!captions.some(c=>c.id===selectedCaption))selectedCaption=captions[0]?.id||null;
  const c=captions.find(c=>c.id===selectedCaption),outside=captions.filter(c=>c.end>project.duration+.001).length;
  $("#captions-inspector").innerHTML=`<p class="help">Faixa independente dos cortes. Edite os tempos ou importe um SRT de texto.</p><div class="caption-actions"><button id="add-caption" class="button secondary" ${project.duration<.1?"disabled":""}>+ No cursor</button><button id="import-srt" class="button secondary">Importar SRT</button></div>${captions.length?`<a class="upload-link" href="/api/projects/${project.id}/captions.srt" download>Baixar legendas SRT ↓</a>`:""}${outside?`<p class="voice-warning help">${outside} legenda(s) ultrapassam o fim da montagem. Confira os tempos antes de entregar.</p>`:""}${c?`<button id="caption-open-edit" class="button secondary full">Editar com prévia</button><label class="field-label" for="caption-selection">Legenda · ${captions.length} no projeto</label><select id="caption-selection">${captions.map((item,i)=>`<option value="${item.id}" ${item.id===c.id?"selected":""}>${i+1}. ${esc(item.text.slice(0,35))}</option>`).join("")}</select><div class="trim-fields"><div><label class="field-label" for="caption-start">Início · segundos</label><input id="caption-start" type="number" min="0" max="1800" step="0.1" value="${c.start}"></div><div><label class="field-label" for="caption-end">Fim · segundos</label><input id="caption-end" type="number" min="0.1" max="1800" step="0.1" value="${c.end}"></div></div><label class="field-label" for="caption-text">Texto</label><textarea id="caption-text" rows="3" maxlength="160">${esc(c.text)}</textarea>${[["title_font","Fonte",[["sans","Arial"],["serif","Georgia"],["mono","Consolas"]]],["title_size","Tamanho",[["small","Pequeno"],["medium","Médio"],["large","Grande"]]],["title_position","Posição",[["bottom","Inferior"],["center","Centro"],["top","Superior"]]]].map(([key,label,options])=>`<label class="field-label" for="caption-${key}">${label}</label><select id="caption-${key}">${options.map(([value,name])=>`<option value="${value}" ${value===c[key]?"selected":""}>${name}</option>`).join("")}</select>`).join("")}<button id="remove-caption" class="danger-button">Remover esta legenda</button>`:'<p class="empty-note">Nenhuma legenda temporizada ainda.</p>'}`;
  $("#add-caption").addEventListener("click",()=>openCaptionEdit());
  $("#import-srt").addEventListener("click",()=>$("#srt-input").click());
  if(!c)return;
  $("#caption-open-edit").addEventListener("click",()=>openCaptionEdit(c.id));
  const update=changes=>mutate("caption_update",{caption_id:c.id,...changes});
  $("#caption-selection").addEventListener("change",e=>{selectedCaption=e.target.value;const target=captions.find(item=>item.id===selectedCaption);seekTo(target.start);renderCaptionInspector();openInspector("captions");});
  for(const key of ["start","end"])$("#caption-"+key).addEventListener("change",e=>update({[key]:Number(e.target.value)}));
  $("#caption-text").addEventListener("change",e=>update({text:e.target.value}));
  for(const key of ["title_font","title_size","title_position"])$("#caption-"+key).addEventListener("change",e=>update({[key]:e.target.value}));
  $("#remove-caption").addEventListener("click",()=>mutate("caption_remove",{caption_id:c.id},"Legenda removida. Você pode desfazer."));
}
function updatePreviewSubtitle(time){
  const caption=(typeof captionPreviewItems==="function"?captionPreviewItems():project?.captions||[]).find(c=>c.start<=time&&time<c.end),node=$("#preview-subtitle");
  node.hidden=!caption;
  if(caption){renderPreviewCaption({...caption,title:caption.text},"#preview-subtitle");node.style.opacity=1;}
}
function renderRequests(){const pending=project.requests.filter(r=>r.status==="pending").length;$("#request-count").textContent=pending?`(${pending})`:"";$("#requests-list").innerHTML=[...project.requests].reverse().map(r=>`<article class="request-card ${r.status==="done"?"done":""}"><small>${r.status==="done"?"CONCLUÍDO":"AGUARDANDO O CODEX"}</small><p>${esc(r.text)}</p>${r.result?`<p class="help">${esc(r.result)}</p>`:""}</article>`).join("");}
function setInspector(name){$("#music-inspector").hidden=name!=="music";$("#captions-inspector").hidden=name!=="captions";document.querySelectorAll("[data-inspector]").forEach(b=>b.classList.toggle("active",b.dataset.inspector===name));$("#scene-inspector").hidden=name!=="scene";$("#voice-inspector").hidden=name!=="voice";$("#step-visual").classList.toggle("active",name==="scene");$("#step-voice").classList.toggle("active",name==="voice");}
function pause(){
  playing=false; playTicket++; player.pause(); voice.pause();musicPlayer.pause();
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
    syncVoice();syncMusic();
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
function seekTo(time, refreshInspector=false){
  if(!project) return;
  pause();
  const previousSelection=selected;
  cursor=Math.max(0,Math.min(project.duration,Number(time)||0));
  let offset=0;
  for(let i=0;i<project.timeline.length;i++){
    const c=project.timeline[i], length=clipDuration(c);
    if(cursor < offset+length-.00001 || i===project.timeline.length-1){selected=c.id;break;}
    offset+=length;
  }
  if(refreshInspector||selected!==previousSelection)markSelection();
  updatePlayer(false,cursor);
}
// Serialize media seeks: while one is decoding, retain only the newest request.
// A late seeked event must never mark an older frame as the requested frame.
function flushPreviewSeek(){
  const request=previewSeek;
  if(!request||request.source!==loadedSource||request.clipId!==currentClip()?.id)return;
  if(player.readyState<1||player.seeking)return;
  if(Math.abs(player.currentTime-request.position)>.001){
    playerLoading=true;player.currentTime=request.position;
  }else{
    if(player.readyState<2)return;
    previewSeek=null;playerLoading=false;
    if(request.resume&&playing)play();
  }
  if(typeof updatePrecisionControls==="function")updatePrecisionControls();
  if(typeof updateEffectControls==="function")updateEffectControls();
  if(typeof updateAudioControls==="function")updateAudioControls();
  if(typeof updateCaptionControls==="function")updateCaptionControls();
}
function updatePlayer(resume=false, time=before()){
  const c=currentClip(), m=c&&assetFor(c);
  $("#preview-empty").hidden=!!c; player.hidden=!c;
  renderPreviewCaption(c);renderPreviewFraming(c);
  cursor=Math.max(0,Math.min(project.duration,time));
  if(!c){previewSeek=null;playerLoading=false;player.removeAttribute("src");voice.pause();musicPlayer.pause();loadedSource="";cursor=0;$("#scene-position").textContent="Nenhuma cena";updateTime();return;}
  const source=assetUrl(m), clipId=c.id;
  const position=Math.min(c.end-.001,c.start+Math.max(0,cursor-before())*(c.speed||1));
  previewSeek={source,clipId,position,resume};playerLoading=true;
  player.playbackRate=c.speed||1;
  player.preservesPitch=true;
  player.onloadedmetadata=flushPreviewSeek;
  player.poster=frameUrl(c); player.volume=Math.min(1,c.volume);
  if(loadedSource!==source){
    playerLoading=true; voice.pause();musicPlayer.pause(); player.src=source; loadedSource=source; player.load();
  } else flushPreviewSeek();
  const narration=typeof audioPreviewTrack==="function"?audioPreviewTrack("narration"):project.narration;
  if(narration){
    const a=project.media.find(m=>m.id===narration.media_id), src=assetUrl(a);
    if(voice.getAttribute("src")!==src){voice.src=src;voice.load();}
    voice.volume=voiceGain(narration,cursor-narration.offset,a.duration);
  } else if(voice.hasAttribute("src")){voice.removeAttribute("src");voice.load();}
  const music=typeof audioPreviewTrack==="function"?audioPreviewTrack("music"):project.music;
  if(music){const source=assetUrl(project.media.find(m=>m.id===music.media_id));if(musicPlayer.getAttribute("src")!==source){musicPlayer.src=source;musicPlayer.load();}}
  else if(musicPlayer.hasAttribute("src")){musicPlayer.removeAttribute("src");musicPlayer.load();}
  $("#scene-position").textContent=`Cena ${index()+1} de ${project.timeline.length}`;
  updateTime();
}
function voiceGain(n,time,duration){
  if(time<0||time>=duration) return 0;
  const envelope=Math.max(0,Math.min(1,n.fade_in?time/n.fade_in:1,n.fade_out?(duration-time)/n.fade_out:1));
  return Math.min(1,n.volume*envelope);
}
function syncVoice(){
  const n=typeof audioPreviewTrack==="function"?audioPreviewTrack("narration"):project?.narration;
  if(!n||!playing||playerLoading||player.seeking||player.paused){voice.pause();return;}
  const time=cursor-n.offset;
  const asset=project.media.find(m=>m.id===project.narration.media_id);
  voice.volume=voiceGain(n,time,asset.duration);
  if(time<0||time>=asset.duration){voice.pause();return;}
  if(voice.readyState>=1&&Math.abs(voice.currentTime-time)>.12) voice.currentTime=time;
  if(voice.paused) voice.play().catch(()=>{});
}
function musicGain(m,time,narration,narrationDuration=0){
  const local=time-m.offset,length=m.end-m.start;
  if(local<0||local>=length)return 0;
  const envelope=Math.max(0,Math.min(1,m.fade_in?local/m.fade_in:1,m.fade_out?(length-local)/m.fade_out:1));
  const duck=m.duck&&narration&&time>=narration.offset&&time<narration.offset+narrationDuration ? .25 : 1;
  return Math.min(1,m.volume*envelope*duck);
}
function syncMusic(){
  const m=typeof audioPreviewTrack==="function"?audioPreviewTrack("music"):project?.music;
  if(!m||!playing||playerLoading||player.seeking||player.paused){musicPlayer.pause();return;}
  const voiceAsset=project.media.find(a=>a.id===project.narration?.media_id);
  musicPlayer.volume=musicGain(m,cursor,typeof audioPreviewTrack==="function"?audioPreviewTrack("narration"):project.narration,voiceAsset?.duration||0);
  const local=cursor-m.offset;
  if(local<0||local>=m.end-m.start){musicPlayer.pause();return;}
  const time=m.start+local;
  if(musicPlayer.readyState>=1&&Math.abs(musicPlayer.currentTime-time)>.12)musicPlayer.currentTime=time;
  if(musicPlayer.paused)musicPlayer.play().catch(()=>{});
}
function renderMusicInspector(){
  $("#music-tab").hidden=!editorFeatures.music_track;
  if(!editorFeatures.music_track)return;
  const m=project.music,assets=project.media.filter(a=>a.status==="ready"&&a.has_audio),asset=assets.find(a=>a.id===m?.media_id);
  $("#music-inspector").innerHTML=`<p class="help">Música independente da voz e do som das cenas. Importe um áudio que você tenha direito de usar.</p><label class="field-label" for="music-source">Arquivo de música</label><select id="music-source"><option value="">Sem música</option>${assets.map(a=>`<option value="${a.id}" ${a.id===m?.media_id?"selected":""}>${esc(a.name)}</option>`).join("")}</select><button id="import-music" class="button secondary full">Importar áudio</button>${m?`<button id="music-timing" class="button secondary full">Ajustar tempo e ouvir prévia</button>${[["start","Entrada no arquivo",asset.duration],["end","Saída no arquivo",asset.duration],["offset","Começar na montagem",1800],["fade_in","Entrada suave",m.end-m.start],["fade_out","Saída suave",m.end-m.start]].map(([key,label,max])=>`<label class="field-label" for="music-${key}">${label} · segundos</label><input id="music-${key}" type="number" min="0" max="${max}" step="0.1" value="${m[key]}">`).join("")}<label class="field-label" for="music-volume">Volume · <output id="music-volume-value">${Math.round(m.volume*100)}%</output></label><input id="music-volume" type="range" min="0" max="100" value="${Math.round(m.volume*100)}"><label class="mirror-control"><input id="music-duck" type="checkbox" ${m.duck?"checked":""}> Abaixar música durante narração</label><p class="help">Reduz a música para 25% do volume escolhido durante a faixa de narração adicional. A exportação protege os picos da mistura.</p>${m.offset+m.end-m.start>project.duration?'<p class="voice-note">A música será cortada no fim da montagem.</p>':""}<button id="remove-music" class="danger-button">Remover música</button>`:""}`;
  $("#music-source").addEventListener("change",e=>mutate("music_set",{media_id:e.target.value||null}));
  $("#import-music").addEventListener("click",()=>$("#file-input").click());
  if(m){$("#music-timing").addEventListener("click",()=>openAudioEdit("music"));for(const key of ["start","end","offset","fade_in","fade_out","volume"])$("#music-"+key).addEventListener("change",e=>mutate("music_set",{[key]:Number(e.target.value)/(key==="volume"?100:1)}));
    $("#music-volume").addEventListener("input",e=>$("#music-volume-value").textContent=e.target.value+"%");
    $("#music-duck").addEventListener("change",e=>mutate("music_set",{duck:e.target.checked}));
    $("#remove-music").addEventListener("click",()=>mutate("music_set",{media_id:null}));}
}
function renderPreviewFraming(clip){
  player.style.objectFit=clip?.framing||"contain";
  player.style.objectPosition=`${(clip?.pan_x??.5)*100}% ${(clip?.pan_y??.5)*100}%`;
  player.style.transform=clip?.mirror?"scaleX(-1)":"none";
  const node=$("#preview-watermark"),mark=project?.settings?.watermark;
  node.textContent=mark?.text||"";node.hidden=!clip||!mark;
  if(mark){
    const right=mark.position.endsWith("right"),bottom=mark.position.startsWith("bottom");
    node.style.right=right?"4%":"auto";node.style.left=right?"auto":"4%";
    node.style.bottom=bottom?"4%":"auto";node.style.top=bottom?"auto":"4%";
    node.style.opacity=mark.opacity;
  }
}
function captionLines(clip){
  const limit={small:38,medium:30,large:22}[clip?.title_size||"medium"];
  return (clip?.title||"").split("\n").flatMap(paragraph=>{
    const words=paragraph.trim().split(/\s+/).filter(Boolean),lines=[];let line="";
    for(const word of words){let chars=Array.from(word);
      if(line&&Array.from(line).length+1+chars.length<=limit){line+=" "+word;continue;}
      if(line){lines.push(line);line="";}
      while(chars.length>limit){lines.push(chars.slice(0,limit).join(""));chars=chars.slice(limit);}
      line=chars.join("");
    }
    if(line||!lines.length)lines.push(line);return lines;
  });
}
function renderPreviewCaption(clip,target="#preview-title"){
  const title=$(target),position=clip?.title_position||"legacy";
  title.textContent=captionLines(clip).join("\n");
  title.style.fontFamily={sans:"Arial, sans-serif",serif:"Georgia, serif",mono:"Consolas, monospace"}[clip?.title_font||"sans"];
  const ratio=({small:.035,medium:.044,large:.06}[clip?.title_size||"medium"]),lines=captionLines(clip).length;
  const frameRatio=project?.settings?project.settings.height/project.settings.width:16/9;
  title.style.fontSize=(Math.min(ratio,.6*frameRatio/(lines*1.2))*100)+"cqw";
  title.style.top={legacy:"32%",top:"10%",center:"50%",bottom:"82%"}[position];
  title.style.transform=position==="bottom"?"translateY(-100%)":position==="center"?"translateY(-50%)":"none";
}
function gradeValues(clip){
  const brightness=clip?.brightness??1,contrast=clip?.contrast??1,saturation=clip?.saturation??1;
  const luma=[.2126,.7152,.0722],matrix=[];
  for(let i=0;i<3;i++)matrix.push(...luma.map((v,j)=>v*(1-saturation)+(i===j?saturation:0)),0,0);
  matrix.push(0,0,0,1,0);
  return {slope:brightness*contrast,offset:.5*(1-contrast)*brightness,matrix,active:brightness!==1||contrast!==1||saturation!==1};
}
function updatePreviewGrade(clip){
  const grade=gradeValues(typeof effectPreviewClip==="function"?effectPreviewClip(clip):clip);
  for(const channel of ["r","g","b"]){$("#grade-"+channel).setAttribute("slope",grade.slope);$("#grade-"+channel).setAttribute("intercept",grade.offset);}
  $("#grade-saturation").setAttribute("values",grade.matrix.join(" "));
  const gain=clip?sceneFadeGain(clip,cursor-before()):1;
  player.style.filter=`${grade.active?"url(#lili-color-grade) ":""}brightness(${gain})`;
}
function originalGain(clip,time){return voiceGain({volume:clip.volume,fade_in:clip.audio_fade_in||0,fade_out:clip.audio_fade_out||0},time,clipDuration(clip));}
function sceneFadeGain(clip,time){
  const length=clipDuration(clip);
  return Math.max(0,Math.min(1,clip.fade_in?time/clip.fade_in:1,clip.fade_out?(length-time)/clip.fade_out:1));
}
function updateSceneFade(){
  const clip=currentClip(),gain=clip?sceneFadeGain(clip,cursor-before()):1;
  updatePreviewGrade(clip);if(clip)player.volume=originalGain(clip,cursor-before());
  $("#preview-title").style.opacity=gain;
  if(typeof updateTransitionPreview==="function")updateTransitionPreview();
}
function updateTime(){
  if(!project) return;
  const time=Math.max(0,Math.min(project.duration,cursor));
  const stamp=t=>`${clock(t)}.${String(Math.floor((t%1)*100+.00001)).padStart(2,"0")}`;
  $("#timecode").innerHTML=`${stamp(time)} <span>/ ${stamp(project.duration)}</span>`;
  $("#seek").max=project.duration||1;
  if(!seekBusy) $("#seek").value=time;
  updatePlayhead(time);updateSceneFade();updatePreviewSubtitle(time);
  if(typeof updatePrecisionControls==="function")updatePrecisionControls();
  if(typeof updateEffectControls==="function")updateEffectControls();
  if(typeof updateAudioControls==="function")updateAudioControls();
  if(typeof updateCaptionControls==="function")updateCaptionControls();
}
function advance(){
  if(!playing) return;
  if(typeof stopEffectPlayback==="function"&&stopEffectPlayback())return;
  if(typeof stopCaptionPlayback==="function"&&stopCaptionPlayback())return;
  const i=index();
  if(i < project.timeline.length-1){
    cursor=before(i+1); selected=project.timeline[i+1].id;
    voice.pause();musicPlayer.pause(); markSelection(); updatePlayer(true,cursor);
  }else{cursor=project.duration;pause();updateTime();}
}
function playbackTick(){
  playbackFrame=0;
  if(!playing) return;
  const c=currentClip();
  if(c&&!playerLoading&&!player.seeking){
    cursor=before()+Math.max(0,Math.min(clipDuration(c),(player.currentTime-c.start)/(c.speed||1)));
    updateTime();syncVoice();syncMusic();
    if(typeof transitionPreviewEnd!=="undefined"&&transitionPreviewEnd!==null&&cursor>=transitionPreviewEnd){transitionPreviewEnd=null;pause();return;}
    if(typeof effectPreviewEnd!=="undefined"&&effectPreviewEnd!==null&&cursor>=effectPreviewEnd-1/30){stopEffectPlayback();return;}
    if(typeof stopCaptionPlayback==="function"&&stopCaptionPlayback())return;
    if(player.currentTime>=c.end-.012){advance();return;}
  }
  playbackFrame=requestAnimationFrame(playbackTick);
}
player.addEventListener("seeked",()=>{flushPreviewSeek();syncVoice();syncMusic();});
player.addEventListener("loadeddata",flushPreviewSeek);
player.addEventListener("waiting",()=>{voice.pause();musicPlayer.pause();});
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
  if(uploadState.pending){toast("Cancele o envio pendente antes de importar outros arquivos.",true);return;}
  uploadState.cancel=false;uploadState.completing=false;
  uploadRunning=true;$("#upload-progress").hidden=false;$("#dismiss-upload").hidden=true;
  const projectId=project.id;
  importBatch={projectId,total:files.length,mediaIds:[],error:""};setImportControls();
  try{
    try{uploadState.available=(await api("/api/health")).features?.upload_cancel===true;}catch{uploadState.available=false;}
    syncUploadCancelControl();
    for(const [index,file] of files.entries()){
      if(uploadState.cancel)throw new Error("Cancelamento solicitado.");
      $("#upload-label").textContent=`Enviando ${index+1} de ${files.length}: ${file.name}`;$("#upload-meter").value=0;
      const upload=await api(`/api/projects/${projectId}/uploads`,{method:"POST",body:JSON.stringify({name:file.name,size:file.size})});
      uploadState.pending=uploadState.available?{projectId, id:upload.upload_id}:null;
      for(let offset=0;offset<file.size;offset+=upload.chunk_size){
        if(uploadState.cancel)throw new Error("Cancelamento solicitado.");
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
        try{await sendBlock();}catch(first){if(uploadState.cancel)throw first;await sendBlock();}
      }
      if(uploadState.cancel)throw new Error("Cancelamento solicitado.");
      uploadState.completing=true;syncUploadCancelControl();
      const imported=await api(`/api/projects/${projectId}/uploads/${upload.upload_id}/complete`,{method:"POST",body:"{}"});
      uploadState.pending=null;uploadState.completing=false;syncUploadCancelControl();
      importBatch.mediaIds.push(imported.media_id);
    }
    toast("Arquivos recebidos. As prévias estão sendo preparadas.");
    if(project.id===projectId){project=await api(`/api/projects/${projectId}`);render();}
  }
  catch(e){
    let message=e.message;
    if(uploadState.cancel){try{message=await cancelPendingUpload();}catch(cancelError){message=cancelError.message;}}
    importBatch.error=message;toast(message,Boolean(uploadState.pending)||!uploadState.cancel);
  }finally{
    uploadRunning=false;uploadState.cancel=false;uploadState.completing=false;
    setImportControls();updateImportStatus(project);$("#file-input").value="";
  }
}
function syncUploadCancelControl(){
  const button=$("#cancel-upload");
  button.hidden=!uploadState.available||(!uploadRunning&&!uploadState.pending);
  button.disabled=uploadState.cancel||uploadState.completing;
  button.textContent=uploadState.cancel?"Cancelando…":"Cancelar envio";
}
async function cancelPendingUpload(){
  const pending=uploadState.pending;
  if(pending){
    try{
      const result=await api(`/api/projects/${pending.projectId}/uploads/${pending.id}/cancel`,{method:"POST",body:"{}"});
      if(result.cancelled!==true)throw new Error("O cancelamento não foi confirmado. Tente novamente.");
    }catch(e){
      if(e.status!==404)throw new Error("Não foi possível confirmar o cancelamento. Verifique a conexão e tente Cancelar envio novamente.");
      uploadState.pending=null;
      return "O envio não está mais pendente. Confira os arquivos já recebidos.";
    }
  }
  uploadState.pending=null;
  return "Envio cancelado. Os arquivos já recebidos foram preservados.";
}
async function requestUploadCancel(){
  if(!uploadState.available||uploadState.cancel||uploadState.completing||(!uploadRunning&&!uploadState.pending))return;
  uploadState.cancel=true;syncUploadCancelControl();
  if(uploadRunning){$("#upload-label").textContent="Cancelamento solicitado. Aguardando o bloco atual…";return;}
  try{importBatch.error=await cancelPendingUpload();toast(importBatch.error);}
  catch(e){importBatch.error=e.message;toast(e.message,true);}
  finally{uploadState.cancel=false;setImportControls();updateImportStatus(project);}
}
function setImportControls(){
  ["#project-select","#new-project","#import-main","#import-mobile","#import-top","#import-zone"].forEach(selector=>$(selector).disabled=uploadRunning||Boolean(uploadState.pending)||!project);
  syncUploadCancelControl();
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
    $("#ai-jobs").innerHTML=edits.slice(0,1).map(j=>`<article class="ai-job ${j.status}"><strong>${j.status==="done"?"Montagem aplicada à linha do tempo":j.status==="error"?"A montagem não foi aplicada":esc(j.stage||"Aguardando análise do Codex")}</strong>${j.status==="done"?`<p>${esc(j.result.summary)}</p><small>${j.result.clip_count} cenas · ${precise(j.result.duration)} · versão ${j.result.revision}${j.result.bytes?` · ${(j.result.bytes/1024/1024).toFixed(1)} MB`:""}</small><button class="button secondary full" data-ai-review>Revisar na linha do tempo</button><details><summary>Observações da montagem</summary>${j.result.warnings.map(w=>`<p class="ai-warning">${esc(w)}</p>`).join("")}</details>`:j.status==="error"?`<p>${esc(j.error)}</p>`:'<p>Você pode fechar esta janela e acompanhar pelo botão Editar com IA.</p><progress aria-label="Edição com IA em andamento"></progress>'}</article>`).join("");
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
  $("#dismiss-upload").hidden=Boolean(uploadState.pending);
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
  if(matchMedia("(max-width:740px)").matches){
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
function updateMediaSelection(){
  $("#select-media").textContent=selectingMedia?"Cancelar seleção":"Selecionar";
  $("#select-all-media").hidden=!selectingMedia;
  $("#remove-selected-media").hidden=!selectingMedia;
  $("#remove-selected-media").disabled=!selectedMedia.size;
  $("#selection-count").textContent=selectingMedia?`${selectedMedia.size} selecionado(s)`:"";
}
$("#select-media").addEventListener("click",()=>{selectingMedia=!selectingMedia;selectedMedia.clear();render();});
$("#select-all-media").addEventListener("click",()=>{project.media.filter(m=>["ready","error"].includes(m.status)).forEach(m=>selectedMedia.add(m.id));render();});
$("#remove-selected-media").addEventListener("click",()=>confirmMediaRemoval([...selectedMedia]));
function confirmMediaRemoval(value){
  const ids=Array.isArray(value)?value:[value], assets=ids.map(id=>project.media.find(a=>a.id===id));
  if(!ids.length||assets.some(a=>!a))return;
  pause();pendingRemoval={projectId:project.id,mediaIds:ids,revision:project.revision};
  const clips=project.timeline.filter(c=>ids.includes(c.media_id)), narration=ids.includes(project.narration?.media_id), music=ids.includes(project.music?.media_id), locked=clips.some(c=>c.locked);
  $("#delete-media-title").textContent=ids.length>1?`Excluir ${ids.length} arquivos?`:"Excluir arquivo?";
  $("#delete-media-name").textContent=ids.length>1?assets.slice(0,4).map(a=>a.name).join(", ")+(ids.length>4?` e mais ${ids.length-4}`:""):assets[0].name;
  $("#delete-media-impact").textContent=locked?"A seleção contém cenas protegidas. Desproteja-as ou retire esses arquivos da seleção antes de excluir.":clips.length||narration||music?`Também serão removidas ${clips.length} cena(s) da linha do tempo${narration?" e a faixa de narração":""}${music?" e a faixa de música":""}. Você pode recuperar tudo com um único Desfazer.`:"Os arquivos selecionados não estão em uso na montagem.";
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
  if(await mutate("media_remove_many",{media_ids:target.mediaIds,remove_usage:true},"Arquivos enviados à Lixeira. Você pode desfazer."))$("#delete-media-dialog").close();
  else $("#confirm-delete-media").disabled=false;
});
document.querySelectorAll("[data-close-sheet]").forEach(b=>b.addEventListener("click",closeSheet));
$("#sheet-backdrop").addEventListener("click",closeSheet);
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!document.querySelector("dialog[open]"))closeSheet();});
matchMedia("(max-width:740px)").addEventListener("change",()=>closeSheet());
$("#srt-input").addEventListener("change",async e=>{
  const file=e.target.files[0];if(!file||!project)return;
  try{
    if(file.size>1000000)throw new Error("Use um SRT de até 1 MB.");
    pendingSRT={projectId:project.id,revision:project.revision,text:await file.text()};
    $("#srt-summary").textContent=`${file.name} · ${(project.captions||[]).length} legenda(s) atuais.`;
    $("#srt-dialog").showModal();
  }catch(error){toast(error.message,true);}finally{e.target.value="";}
});
$("#confirm-srt").addEventListener("click",async()=>{
  await queue;const value=pendingSRT;if(!value)return;
  if(project.id!==value.projectId||project.revision!==value.revision){$("#srt-dialog").close();toast("O projeto mudou. Selecione o SRT novamente para revisar a substituição.",true);return;}
  $("#confirm-srt").disabled=true;
  try{if(await mutate("captions_import",{srt:value.text},"Legendas importadas. Revise os tempos.")){$("#srt-dialog").close();pendingSRT=null;openInspector("captions");}}
  finally{$("#confirm-srt").disabled=false;}
});
$("#file-input").addEventListener("change",e=>uploadFiles([...e.target.files]));
["#import-top","#import-zone","#import-main","#import-mobile"].forEach(s=>$(s).addEventListener("click",openFilePicker));
$("#codex-main").addEventListener("click",()=>openLibraryTab("requests",true));
$("#view-uploaded").addEventListener("click",()=>openLibraryTab("media"));
$("#cancel-upload").addEventListener("click",requestUploadCancel);
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
$("#step-visual").addEventListener("click",()=>setInspector("scene"));$("#step-voice").addEventListener("click",()=>{setInspector("voice");if(matchMedia("(max-width:740px)").matches)revealPanel(".inspector");});
$("#save-script").addEventListener("click",()=>mutate("script_update",{script:$("#script-input").value},"Roteiro salvo."));
$("#request-form").addEventListener("submit",async e=>{e.preventDefault();const input=$("#request-input");if(!input.value.trim())return;if(await mutate("request_add",{text:input.value},"Pedido salvo para o Codex. A execução depende de uma sessão do agente."))input.value="";});
$("#redo-button").addEventListener("click",()=>mutate("redo",{},"Alteração refeita."));
$("#undo-button").addEventListener("click",()=>mutate("undo",{},"Última alteração desfeita."));
$("#draft-button").addEventListener("click",async()=>{await queue;if(!project)return;if(project.timeline.length&&!confirm("Substituir a sequência pelo rascunho baseado no roteiro e nas etiquetas? Você poderá desfazer."))return;pause();try{const data=await api(`/api/projects/${project.id}/draft`,{method:"POST",body:JSON.stringify({expected_revision:project.revision})});project=data.project;selected=project.timeline[0]?.id;render();toast(data.warnings.length?`Rascunho montado. ${data.warnings.length} blocos sem correspondência de etiquetas precisam de revisão.`:"Rascunho montado pelas etiquetas. Revise a seleção das tomadas.");}catch(e){toast(e.message,true);}});
$("#project-select").addEventListener("change",e=>openProject(e.target.value).catch(e=>toast(e.message,true)));
$("#new-project").addEventListener("click",()=>$("#new-dialog").showModal());
$("#new-form").addEventListener("submit",async e=>{e.preventDefault();try{const p=await api("/api/projects",{method:"POST",body:JSON.stringify({name:$("#new-name").value,script:$("#new-script").value})});$("#new-dialog").close();$("#new-form").reset();await listProjects();await openProject(p.id);}catch(e){toast(e.message,true);}});
document.querySelectorAll(".close-dialog").forEach(b=>b.addEventListener("click",()=>b.closest("dialog").close()));
let exportSubmitting=false,exportBusyProject=null,exportJobRunning=false;
function exportReadiness(p){
  const notes=[],media=new Map((p.media||[]).map(a=>[a.id,a])),duration=p.duration||0;
  const add=(level,text,target)=>notes.push({level,text,target});
  if(!p.timeline.length)add("error","Adicione uma cena à montagem antes de gerar o vídeo.","scene");
  const used=new Set(p.timeline.map(c=>c.media_id));for(const track of [p.narration,p.music])if(track)used.add(track.media_id);
  const unavailable=[...used].filter(id=>{const a=media.get(id);return !a||a.deleted_at||a.status!=="ready";});
  if(unavailable.length)add("error",`${unavailable.length} arquivo(s) usado(s) na montagem ainda não estão prontos ou disponíveis. Confira a biblioteca.`,"library");
  const n=p.narration,voice=n&&media.get(n.media_id);
  if(n&&voice){if(n.offset>=duration)add("warning","A narração começa depois do fim do vídeo e não será ouvida.","voice");else if(n.offset+voice.duration>duration+.001)add("warning",`A narração ultrapassa o vídeo em ${precise(n.offset+voice.duration-duration)}. Parte da fala ficará de fora.`,"voice");}
  const m=p.music;
  if(m){if(m.offset>=duration)add("warning","A música começa depois do fim do vídeo e não será ouvida.","music");else if(m.fade_out>0&&m.offset+m.end-m.start>duration+.001)add("warning","O vídeo termina antes do fim da música: a saída suave escolhida não termina dentro da entrega.","music");}
  const outside=(p.captions||[]).filter(c=>c.end>duration+.001).length;
  if(outside)add("warning",`${outside} legenda(s) ultrapassam a duração da montagem. Só o trecho dentro do vídeo aparece.`,"captions");
  const sceneSound=p.timeline.some(c=>media.get(c.media_id)?.has_audio&&(c.volume??1)>0);
  const extraSound=!!(n&&voice&&n.volume>0&&n.offset<duration)||!!(m&&media.get(m.media_id)&&m.volume>0&&m.offset<duration);
  if(p.timeline.length&&!sceneSound&&!extraSound)add("warning","Esta montagem não tem áudio audível. Se o silêncio foi intencional, pode gerar o vídeo assim.","voice");
  return notes;
}
function updateExportAction(){
  if(!project)return;
  $("#start-export").disabled=exportSubmitting||exportBusyProject===project.id||exportJobRunning||exportReadiness(project).some(n=>n.level==="error");
  $("#export-request-status").textContent=exportSubmitting?"Enviando a exportação…":exportBusyProject===project.id?"Confirmando o andamento. Aguarde a atualização da fila.":exportJobRunning?"Aguarde a exportação em andamento terminar.":"";
}
function renderExportReadiness(){
  const notes=exportReadiness(project),root=$("#export-readiness");
  root.innerHTML=notes.length?`<h3>Antes de entregar</h3>${notes.map(n=>`<div class="export-review-note ${n.level}"><p>${esc(n.text)}</p><button type="button" class="button secondary" data-export-review="${n.target}">Revisar ${({library:"arquivos",scene:"cenas",voice:"narração",music:"música",captions:"legendas"})[n.target]}</button></div>`).join("")}<p class="help">Avisos permitem gerar mesmo assim. Arquivos indisponíveis precisam ser resolvidos primeiro.</p>`:'<p class="help">Sem pendências detectadas nos tempos e no cadastro dos arquivos. Confira também a prévia antes de entregar.</p>';
  root.querySelectorAll("[data-export-review]").forEach(b=>b.addEventListener("click",()=>{pause();$("#export-dialog").close();if(b.dataset.exportReview==="library")openLibraryTab("media");else openInspector(b.dataset.exportReview);}));
  updateExportAction();
}
async function submitExport(){
  if(exportSubmitting||!project||exportBusyProject===project.id||exportJobRunning)return;
  const intended={id:project.id,quality:$("#export-quality").value};exportSubmitting=true;updateExportAction();
  try{
    await queue;
    if(project?.id!==intended.id){toast("O projeto selecionado mudou. Abra a exportação do projeto desejado.",true);return;}
    if(exportReadiness(project).some(n=>n.level==="error")){renderExportReadiness();return;}
    exportBusyProject=intended.id;
    await api(`/api/projects/${intended.id}/exports`,{method:"POST",body:JSON.stringify({expected_revision:project.revision,quality:intended.quality})});
    toast("Exportação enviada. Você pode acompanhar a fila abaixo.");
  }catch(e){toast(e.message+" Confira a fila antes de tentar novamente.",true);}
  finally{
    exportSubmitting=false;
    if(project?.id===intended.id){try{await refreshJobs();}catch{toast("Não foi possível atualizar a fila. A exportação pode ter sido recebida; aguarde a reconexão antes de tentar novamente.",true);}updateExportAction();}
    else updateExportAction();
  }
}
function exportProfile(settings,quality){
  const scales={preview:.5,balanced:2/3,full:1,high:1},scale=scales[quality]||1;
  return {width:Math.max(2,Math.round(settings.width*scale/2)*2),height:Math.max(2,Math.round(settings.height*scale/2)*2)};
}
function configureExportControls(){
  $("#watermark-controls").hidden=!editorFeatures.framing_watermark;
  const mark=project.settings.watermark;
  $("#watermark-text").value=mark?.text||"";$("#watermark-position").value=mark?.position||"bottom_right";
  $("#watermark-opacity").value=Math.round((mark?.opacity??.6)*100);
  $("#format-controls").hidden=!editorFeatures.export_profiles;
  if(!editorFeatures.export_profiles)return;
  const quality=$("#export-quality"),selectedQuality=quality.value;
  quality.innerHTML=[["full","Entrega final"],["balanced","Equilibrada · arquivo menor"],["high","Alta qualidade · arquivo maior"],["preview","Prévia leve"]].map(([value,label])=>{const size=exportProfile(project.settings,value);return `<option value="${value}">${label} · ${size.width} × ${size.height}</option>`;}).join("");
  quality.value=selectedQuality||"full";
  $("#project-format").value=project.settings.width===project.settings.height?"square":project.settings.width>project.settings.height?"landscape":"vertical";
}
function updateExportSummary(){
  if(!project)return;const size=exportProfile(project.settings,$("#export-quality").value);
  const ratio=project.settings.width===project.settings.height?"1:1":project.settings.width>project.settings.height?"16:9":"9:16";
  $("#export-glance").innerHTML=`<span><small>Tela</small><strong>${ratio}</strong></span><span><small>Resolução</small><strong>${size.width} × ${size.height}</strong></span><span><small>Arquivo</small><strong>MP4</strong></span>`;
  $("#export-profile-note").textContent={preview:"Para conferir a montagem e compartilhar uma prévia leve.",balanced:"Para aprovação e envio rápido, com resolução reduzida.",full:"Para a entrega do dia a dia, usando os arquivos originais.",high:"Menos compressão e arquivo maior. Mantém a resolução da entrega final."}[$("#export-quality").value];
  $("#export-summary").textContent=`${project.timeline.length} cenas · ${precise(project.duration)} · versão ${project.revision}. O tamanho final depende do conteúdo.`;
  renderExportReadiness();
}
$("#apply-watermark").addEventListener("click",()=>mutate("watermark_set",{text:$("#watermark-text").value,position:$("#watermark-position").value,opacity:Number($("#watermark-opacity").value)/100},"Marca d'água atualizada. Confira a prévia."));
$("#project-format").addEventListener("change",e=>mutate("settings_update",{format:e.target.value},"Formato da montagem atualizado."));
$("#export-quality").addEventListener("change",updateExportSummary);
async function showExports(){pause();$("#export-dialog").showModal();await refreshJobs();}
$("#export-button").addEventListener("click",showExports);$("#step-export").addEventListener("click",showExports);
$("#start-export").addEventListener("click",submitExport);
function exportJobCard(job){
  const done=job.status==="done"&&job.result,failed=job.status==="error",result=job.result;
  const stale=done&&result.revision!==project.revision;
  const heading=done?"Pronto para baixar":failed?"A exportação não terminou":"Preparando seu vídeo";
  const badge=done?(stale?"Versão anterior":"Versão atual"):failed?"Revisar":"Em andamento";
  const quality={preview:"Prévia",balanced:"Equilibrada",full:"Entrega final",high:"Alta qualidade"}[result?.quality]||"MP4";
  const safeId=typeof job.id==="string"&&/^[a-f0-9]{32}$/.test(job.id);
  const progress=Math.max(0,Math.min(100,Number(job.progress)||0));
  return `<article class="export-card"><div class="export-card-heading"><strong>${heading}</strong><span class="export-badge ${failed?"failed":stale?"older":""}">${badge}</span></div>${done?`<p class="export-facts">${esc(quality)} · ${esc(result.width)} × ${esc(result.height)} · ${precise(result.duration)}${result.bytes?` · ${(result.bytes/1024/1024).toFixed(1)} MB`:""}</p><p class="help">Versão ${esc(result.revision)}${stale?` · projeto agora na versão ${project.revision}`:""}</p>${safeId?`<a class="button primary export-download" href="/api/projects/${project.id}/exports/${job.id}/video.mp4" download>Baixar vídeo MP4 ${icon("down")}</a>`:""}`:failed?`<p class="help">${esc(job.error||"Tente novamente após conferir os arquivos.")}</p>`:`<progress max="100" value="${progress}" aria-label="Andamento da exportação"></progress><p class="help">${progress}% · você pode fechar esta janela.</p>`}</article>`;
}
function renderExportJobs(jobs){
  const root=$("#export-jobs"),expanded=root.querySelector("details")?.open;
  root.innerHTML=jobs.length?exportJobCard(jobs[0])+(jobs.length>1?`<details class="export-history" ${expanded?"open":""}><summary>Exportações anteriores (${jobs.length-1})</summary>${jobs.slice(1).map(exportJobCard).join("")}</details>`:""):'<p class="export-empty">Seu vídeo final aparecerá aqui. Escolha a saída e toque em Gerar vídeo.</p>';
}
async function refreshJobs(){
  if(!project)return;const id=project.id,jobs=await api(`/api/projects/${id}/jobs`);if(project?.id!==id)return;
  const exports=jobs.filter(j=>j.kind==="export").reverse();renderAIJobs(jobs);
  exportJobRunning=exports.some(j=>["queued","running"].includes(j.status));
  if(exportBusyProject===id)exportBusyProject=null;
  updateExportAction();renderExportJobs(exports);
}

setInterval(async()=>{if(!project||document.hidden||timelineGesture)return;try{const fresh=await api(`/api/projects/${project.id}`);updateImportStatus(fresh);const editing=/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);if(fresh.revision!==project.revision&&!editing&&!playing&&!timelineGesture&&!$("#transition-dialog").open&&!$("#effects-dialog").open&&!$("#audio-edit-dialog").open&&!$("#caption-edit-dialog").open){project=fresh;render();}await refreshJobs();}catch(error){if(error.status===404){location.replace("/");return;}$("#save-status").textContent="Servidor desconectado";}},2500);
(async()=>{try{try{editorFeatures=(await api("/api/health")).features||{};}catch{}document.body.classList.toggle("has-subtitles",Boolean(editorFeatures.subtitles));document.body.classList.toggle("has-music",Boolean(editorFeatures.music_track));if(editorFeatures.still_images)$("#file-input").accept+=",.jpg,.jpeg,.png,.webp";await listProjects();if(!projects.length){location.replace("/");return;}const requested=new URLSearchParams(location.search).get("project"),saved=requested||localStorage.getItem("lili-project");if(requested&&!projects.some(p=>p.id===requested)){location.replace("/");return;}const showAI=new URLSearchParams(location.search).get("panel")==="ai";await openProject(projects.some(p=>p.id===saved)?saved:projects[0].id);if(showAI)await openAIEditor();}catch(e){toast("Não foi possível abrir o estúdio. "+e.message,true);}})();

if("serviceWorker" in navigator&&window.isSecureContext)navigator.serviceWorker.register("/sw.js").catch(()=>{});
$("#phone-help").addEventListener("click",()=>{
  $("#phone-connection-note").textContent=location.protocol==="https:"?`Endereço deste estúdio: ${location.origin}`:"O acesso por este endereço funciona apenas no notebook. Prepare o login e ative o endereço remoto para abrir no iPhone.";
  $("#phone-dialog").showModal();
});
fetch("/auth/status").then(r=>r.ok?r.json():null).then(data=>{
  if(data?.authenticated)$("#logout-form").hidden=false;
  const supported=data?.features?.logout_all===true;
  $("#security-button").hidden=!supported;$("#menu-security").hidden=!supported;
}).catch(()=>{});
for(const id of ["security-button","menu-security"])$("#"+id).addEventListener("click",()=>{$("#project-menu-dialog").close();$("#security-dialog").showModal();});

$("#delete-project-current").addEventListener("click",async()=>{
  await queue;if(!project||uploadRunning){toast("Aguarde o envio terminar.",true);return;}
  pause();pendingProjectRemoval={id:project.id,revision:project.revision};
  $("#delete-project-name").textContent=project.name;$("#delete-project-dialog").showModal();
});
$("#delete-project-form").addEventListener("submit",async e=>{
  e.preventDefault();const target=pendingProjectRemoval;if(!target)return;
  const button=$("#confirm-delete-project");button.disabled=true;
  try{await queue;await api(`/api/projects/${target.id}/trash`,{method:"POST",body:JSON.stringify({expected_revision:target.revision})});location.assign("/#trash");}
  catch(error){$("#delete-project-dialog").close();toast(error.message+" Revise e tente novamente.",true);}finally{button.disabled=false;}
});

$("#project-menu-button").addEventListener("click",()=>{pause();closeSheet();$("#project-menu-dialog").showModal();});
for(const [menu,target] of [["menu-new-project","new-project"],["menu-delete-project","delete-project-current"],["menu-phone-help","phone-help"]]){
 $("#"+menu).addEventListener("click",()=>{$("#project-menu-dialog").close();$("#"+target).click();});
}
