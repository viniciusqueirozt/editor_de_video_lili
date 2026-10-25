"use strict";

// The track, ruler, waveform and playhead share one scale in pixels / second.
let timelineScale=30, timelineZoom=1, timelineGesture=null, suppressClipClick=false;
const waveforms=new Map();
const trackScroll=$("#timeline-scroll"), trackCanvas=$("#timeline");
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
const roundTime=value=>Math.round(value*1000)/1000;

function renderTimeline(){
  if(!project) return;
  const clips=project.timeline, available=Math.max(200,trackScroll.clientWidth-24);
  timelineScale=Math.max(3,Math.min(100,available/Math.max(project.duration,10)))*timelineZoom;
  const width=Math.max(available,project.duration*timelineScale)+24;
  trackCanvas.style.width=`${width}px`;
  $("#clip-count").textContent=`${clips.length} ${clips.length===1?"cena":"cenas"}`;
  $("#total-duration").textContent=`Duração ${precise(project.duration)}`;
  $("#timeline-subtitle").textContent=clips.length?"Selecione • apare pelas bordas • divida no cursor":"Adicione um vídeo para começar.";
  if(!timelineGesture)$("#timeline-hint").textContent="Régua: posicione ou use dois dedos para ampliar. Precisão: avance por quadro e apare no cursor.";
  $("#timeline-zoom").value=timelineZoom;
  const step=[.1,.25,.5,1,2,5,10,15,30,60,120,300,600].find(s=>s*timelineScale>=65)||600;
  const ticks=[];
  for(let t=0;t<=width/timelineScale;t+=step){
    const label=step<1?`${t.toFixed(1)}s`:clock(t);
    ticks.push(`<span class="ruler-tick" style="left:${t*timelineScale}px">${label}</span>`);
  }
  $("#time-ruler").innerHTML=ticks.join("");
  let offset=0;
  $("#video-track").innerHTML=clips.map((c,i)=>{
    const length=clipDuration(c), left=offset*timelineScale, width=length*timelineScale;
    offset+=length;
    const frames=Math.max(1,Math.min(3,Math.ceil(width/75)));
    const strip=Array.from({length:frames},(_,j)=>{
      const at=roundTime(c.start+(c.end-c.start-.04)*j/Math.max(1,frames-1));
      return `<img draggable="false" alt="" loading="lazy" src="${assetUrl(assetFor(c),"frame.jpg")}?at=${Math.max(0,at)}">`;
    }).join("");
    const trimHandle=edge=>`<button class="trim-handle trim-${edge}" data-edge="${edge}" aria-label="${edge==="start"?"Aparar início":"Aparar fim"} da cena ${i+1}" title="Arraste para aparar" ${c.locked?"disabled":""}></button>`;
    return `<div class="timeline-clip ${c.id===selected?"selected":""} ${width<45?"narrow":""}" data-clip="${c.id}" style="left:${left}px;width:${width}px">
      <button class="clip-body" draggable="true" aria-pressed="${c.id===selected}" aria-label="Cena ${i+1}: ${esc(c.label)}, ${precise(length)}" title="${esc(c.label)} · ${precise(length)}">
        <span class="clip-filmstrip">${strip}</span><span class="clip-caption">${String(i+1).padStart(2,"0")} · ${esc(c.label)}</span><span class="clip-duration">${precise(length)}</span>${c.locked?`<span class="clip-lock">${icon("lock")}</span>`:""}
      </button>${trimHandle("start")}${trimHandle("end")}</div>`;
  }).join("") || '<div class="track-empty">Importe um vídeo e clique em Adicionar.</div>';
  $("#video-track").querySelectorAll("[data-clip]").forEach(node=>{
    const body=node.querySelector(".clip-body");
    body.addEventListener("click",e=>{
      if(suppressClipClick){suppressClipClick=false;return;}
      const c=project.timeline.find(c=>c.id===node.dataset.clip);
      const i=project.timeline.indexOf(c), rect=node.getBoundingClientRect();
      const local=e.detail===0?0:clamp((e.clientX-rect.left)/timelineScale,0,clipDuration(c)-.001);
      seekTo(before(i)+local);setInspector("scene");
    });
    body.addEventListener("dragstart",e=>{dragId=node.dataset.clip;e.dataTransfer.effectAllowed="move";e.dataTransfer.setData("text/plain",dragId);node.classList.add("dragging");});
    node.addEventListener("dragover",e=>{if(dragId){e.preventDefault();node.classList.add("drop-target");}});
    node.addEventListener("dragleave",()=>node.classList.remove("drop-target"));
    node.addEventListener("drop",e=>{
      e.preventDefault();node.classList.remove("drop-target");
      const target=project.timeline.findIndex(c=>c.id===node.dataset.clip);
      if(dragId&&dragId!==node.dataset.clip) mutate("clip_move",{clip_id:dragId,index:target},"Cena reordenada.");
      dragId=null;
    });
    body.addEventListener("dragend",()=>{dragId=null;node.classList.remove("dragging");document.querySelectorAll(".drop-target").forEach(n=>n.classList.remove("drop-target"));});
    node.querySelectorAll("[data-edge]").forEach(handle=>handle.addEventListener("pointerdown",beginTrim));
  });
  renderTransitionJoins();
  renderAudioTrack();renderMusicTrack();renderCaptionTrack(); updatePlayhead(cursor);
}

function renderMusicTrack(){
  const track=$("#music-track");track.hidden=!editorFeatures.music_track;$("#music-track-label").hidden=!editorFeatures.music_track;
  if(!editorFeatures.music_track)return;
  const m=project.music,length=m?Math.max(0,Math.min(m.end-m.start,project.duration-m.offset)):0;
  const asset=project.media.find(a=>a.id===m?.media_id);
  track.innerHTML=m&&length>0?`<button class="music-region" style="left:${m.offset*timelineScale}px;width:${length*timelineScale}px">${esc(asset.name)}</button>`:'<button class="add-voice-track">'+(m?'Música após o fim · ajustar':'+ Adicionar música')+'</button>';
  track.querySelector("button").addEventListener("click",()=>openInspector("music"));
}
function renderCaptionTrack(){
  const track=$("#caption-track");track.hidden=!editorFeatures.subtitles;$("#caption-track-label").hidden=!editorFeatures.subtitles;
  if(!editorFeatures.subtitles)return;
  track.innerHTML=(project.captions||[]).map(c=>{const end=Math.min(c.end,project.duration);return end>c.start?`<button class="caption-region" data-caption="${c.id}" style="left:${c.start*timelineScale}px;width:${(end-c.start)*timelineScale}px" title="${esc(c.text)}">${esc(c.text)}</button>`:"";}).join("");
  track.querySelectorAll("[data-caption]").forEach(button=>button.addEventListener("click",()=>{selectedCaption=button.dataset.caption;const c=project.captions.find(c=>c.id===selectedCaption);seekTo(c.start);renderCaptionInspector();openInspector("captions");}));
}

function renderAudioTrack(){
  const n=project.narration, track=$("#audio-track");
  if(!n){track.innerHTML='<button class="add-voice-track" id="add-voice-track">+ Adicionar narração</button>';$("#add-voice-track").addEventListener("click",()=>openInspector("voice"));return;}
  const asset=project.media.find(m=>m.id===n.media_id), visible=Math.max(0,Math.min(asset.duration,project.duration-n.offset));
  if(visible<=0){track.innerHTML='<button class="add-voice-track" id="add-voice-track">Narração começa após o fim · ajustar</button>';$("#add-voice-track").addEventListener("click",()=>openInspector("voice"));return;}
  track.innerHTML=`<button class="audio-region" id="audio-region" style="left:${n.offset*timelineScale}px;width:${visible*timelineScale}px" title="${esc(asset.name)}"><svg id="audio-waveform" preserveAspectRatio="none" aria-hidden="true"></svg><span>${icon("mic")}${esc(asset.name)}</span><small id="waveform-status">Lendo áudio…</small></button>`;
  $("#audio-region").addEventListener("click",()=>openInspector("voice"));
  const pid=project.id, key=`${pid}/${asset.id}`;
  if(!waveforms.has(key)) waveforms.set(key,api(assetUrl(asset,"waveform.json")).catch(error=>{waveforms.delete(key);throw error;}));
  waveforms.get(key).then(data=>{
    if(project?.id!==pid||project.narration?.media_id!==asset.id||!$("#audio-waveform"))return;
    const count=Math.max(1,Math.min(1200,Math.ceil(visible*timelineScale/3))), points=[];
    const endIndex=data.peaks.length*Math.min(1,visible/data.duration);
    const maximum=Math.max(.01,...data.peaks);
    for(let i=0;i<count;i++){
      const start=Math.floor(i*endIndex/count), end=Math.max(start+1,Math.ceil((i+1)*endIndex/count));
      const amplitude=Math.max(0,...data.peaks.slice(start,end))/maximum*15;
      points.push(`M${i*3+1.5},${19-amplitude}v${Math.max(1,amplitude*2)}`);
    }
    $("#audio-waveform").setAttribute("viewBox",`0 0 ${count*3} 38`);
    $("#audio-waveform").innerHTML=`<path d="${points.join(" ")}"/>`;
    $("#waveform-status").hidden=true;
  }).catch(()=>{if(project?.id===pid&&$("#waveform-status"))$("#waveform-status").textContent="Forma de onda indisponível";});
}

function updatePlayhead(time){
  const head=$("#timeline-playhead");
  head.style.transform=`translateX(${time*timelineScale}px)`;
  head.setAttribute("aria-valuemax",project?.duration||0);
  head.setAttribute("aria-valuenow",roundTime(time));
  head.setAttribute("aria-valuetext",`${precise(time)} de ${precise(project?.duration||0)}`);
  const c=currentClip(), local=c?time-before():0;
  $("#split-button").disabled=!c||c.locked||local<.1-.00001||clipDuration(c)-local<.1-.00001||project.timeline.length>=100;
  $("#delete-button").disabled=!c||c.locked;
  $("#duplicate-button").disabled=!c||project.timeline.length>=100;
  if(playing){
    const x=time*timelineScale;
    if(x>trackScroll.scrollLeft+trackScroll.clientWidth-35||x<trackScroll.scrollLeft)trackScroll.scrollLeft=Math.max(0,x-40);
  }
}

function pointerTime(e){return clamp((e.clientX-trackCanvas.getBoundingClientRect().left)/timelineScale,0,project.duration);}
const rulerPointers=new Map();
let rulerFrame=0;
function pinchGeometry(points){
  const [a,b]=points;
  return {distance:Math.abs(a-b),center:(a+b)/2};
}
function moveRulerPinch(){
  rulerFrame=0;
  const gesture=timelineGesture;if(gesture?.type!=="pinch"||rulerPointers.size!==2)return;
  const geometry=pinchGeometry([...rulerPointers.values()]);
  timelineZoom=clamp(gesture.zoom*geometry.distance/gesture.distance,.5,8);
  renderTimeline();
  trackScroll.scrollLeft=Math.max(0,gesture.anchor*timelineScale-(geometry.center-trackScroll.getBoundingClientRect().left));
}
trackCanvas.addEventListener("pointerdown",e=>{
  if(e.button!==0||!project?.timeline.length||e.target.closest("button")) return;
  if(timelineGesture?.type==="trim"||timelineGesture?.type==="drain")return;
  if(e.pointerType==="touch"&&e.target.closest("#time-ruler")){
    if(rulerPointers.size>=2)return;
    rulerPointers.set(e.pointerId,e.clientX);
    if(rulerPointers.size===2){
      const geometry=pinchGeometry([...rulerPointers.values()]);
      if(geometry.distance<8){rulerPointers.delete(e.pointerId);return;}
      const original=timelineGesture?.originalCursor??cursor;
      timelineGesture={type:"pinch",distance:geometry.distance,zoom:timelineZoom,anchor:(geometry.center-trackCanvas.getBoundingClientRect().left)/timelineScale};
      trackCanvas.setPointerCapture(e.pointerId);seekTo(original);return;
    }
  }
  if(timelineGesture)return;
  pause();timelineGesture={type:"seek",pointerId:e.pointerId,originalCursor:cursor};
  trackCanvas.setPointerCapture(e.pointerId);seekTo(pointerTime(e));
});
trackCanvas.addEventListener("pointermove",e=>{
  if(rulerPointers.has(e.pointerId))rulerPointers.set(e.pointerId,e.clientX);
  if(timelineGesture?.type==="pinch"){
    if(!rulerFrame)rulerFrame=requestAnimationFrame(moveRulerPinch);return;
  }
  if(timelineGesture?.type==="seek"&&e.pointerId===timelineGesture.pointerId)seekTo(pointerTime(e));
});
function endScrub(e){
  if((timelineGesture?.type==="pinch"||timelineGesture?.type==="drain")&&!rulerPointers.has(e.pointerId))return;
  rulerPointers.delete(e.pointerId);
  if(trackCanvas.hasPointerCapture(e.pointerId))trackCanvas.releasePointerCapture(e.pointerId);
  if(timelineGesture?.type==="pinch"||timelineGesture?.type==="drain"){
    cancelAnimationFrame(rulerFrame);rulerFrame=0;
    timelineGesture=rulerPointers.size?{type:"drain"}:null;return;
  }
  if(timelineGesture?.type==="seek"&&e.pointerId===timelineGesture.pointerId)timelineGesture=null;
}
trackCanvas.addEventListener("pointerup",endScrub);trackCanvas.addEventListener("pointercancel",endScrub);

function beginTrim(e){
  if(e.button!==0||timelineGesture)return;
  e.preventDefault();e.stopPropagation();pause();
  const handle=e.currentTarget,node=handle.closest("[data-clip]"),c=project.timeline.find(c=>c.id===node.dataset.clip);
  if(c.locked)return;
  const originalCursor=cursor;
  selected=c.id;markSelection();updatePlayer(false,before());
  timelineGesture={type:"trim",clip:{...c},edge:handle.dataset.edge,x:e.clientX,pointerId:e.pointerId,node,revision:project.revision,changed:null,originalCursor};
  handle.setPointerCapture(e.pointerId);node.classList.add("trimming");
  handle.addEventListener("pointermove",moveTrim);
  handle.addEventListener("pointerup",finishTrim,{once:true});
  handle.addEventListener("pointercancel",cancelTrim,{once:true});
  $("#timeline-hint").textContent="Arraste para escolher a entrada ou a saída. Solte para salvar.";
}
function moveTrim(e){
  const gesture=timelineGesture;
  if(gesture?.type!=="trim"||gesture.pointerId!==e.pointerId)return;
  const c=gesture.clip, edge=gesture.edge, speed=c.speed||1, delta=(e.clientX-gesture.x)/timelineScale*speed;
  const minimum=minimumClipLength(c)*speed;
  const asset=assetFor(c), value=roundTime(edge==="start"?clamp(c.start+delta,0,c.end-minimum):clamp(c.end+delta,c.start+minimum,asset.duration));
  gesture.changed={[edge]:value};
  const start=edge==="start"?value:c.start, end=edge==="end"?value:c.end;
  const width=(end-start)/speed*timelineScale;
  gesture.node.style.width=`${width}px`;
  // In trim preview, reveal the moving source edge; ripple settles on save.
  gesture.node.style.left=`${(before()+(edge==="start"?(start-c.start)/speed:0))*timelineScale}px`;
  $("#clip-start").value=start;$("#clip-end").value=end;
  $("#timeline-hint").textContent=`Entrada ${precise(start)} → saída ${precise(end)} · duração ${precise((end-start)/speed)}`;
  if(loadedSource===assetUrl(asset)){
    previewSeek={source:loadedSource,clipId:c.id,position:edge==="start"?start:Math.max(start,end-.001),resume:false};
    playerLoading=true;flushPreviewSeek();
  }
}
function clearTrim(handle){
  handle.removeEventListener("pointermove",moveTrim);handle.removeEventListener("pointerup",finishTrim);handle.removeEventListener("pointercancel",cancelTrim);
  if(timelineGesture&&handle.hasPointerCapture(timelineGesture.pointerId))handle.releasePointerCapture(timelineGesture.pointerId);
}
function finishTrim(e){
  const gesture=timelineGesture;if(gesture?.type!=="trim")return;
  clearTrim(e.currentTarget);timelineGesture=null;suppressClipClick=true;
  setTimeout(()=>{suppressClipClick=false;},0);
  if(gesture.changed&&gesture.changed[gesture.edge]!==gesture.clip[gesture.edge]){
    cursor=trimmedCursor(gesture.clip,gesture.edge,gesture.changed[gesture.edge],before());
    mutate("clip_update",{clip_id:gesture.clip.id,...gesture.changed},"Corte ajustado e salvo.");
  }else{renderTimeline();seekTo(gesture.originalCursor);}
}
function cancelTrim(e){const original=timelineGesture?.originalCursor??cursor;clearTrim(e.currentTarget);timelineGesture=null;renderTimeline();seekTo(original);}

// Montage output is 30 fps; stepping uses its grid, not the source's VFR frames.
function frameStep(time,direction,duration){
  const frame=time*30, nearest=Math.round(frame);
  const atFrame=Math.abs(frame-nearest)<.00001;
  const next=atFrame?nearest+direction:direction>0?Math.ceil(frame):Math.floor(frame);
  return clamp(next/30,0,duration);
}
function parseMontageTime(value){
  const text=String(value).trim().replace(",",".");
  if(/^\d+(?:\.\d{1,3})?$/.test(text))return Number(text);
  if(!/^\d+:\d{2}(?:\.\d{1,3})?$/.test(text))return null;
  const [minutes,seconds]=text.split(":").map(Number);
  return seconds<60?minutes*60+seconds:null;
}
function montageTime(time){
  const ms=Math.round(Math.max(0,time)*1000);
  return `${String(Math.floor(ms/60000)).padStart(2,"0")}:${String(Math.floor(ms/1000)%60).padStart(2,"0")}.${String(ms%1000).padStart(3,"0")}`;
}
function minimumClipLength(c){
  return Math.max(.1,(c.fade_in||0)+(c.fade_out||0),(c.audio_fade_in||0)+(c.audio_fade_out||0));
}
function cursorTrim(c,edge,time,offset){
  if(!c||c.locked||!Number.isFinite(time))return null;
  const value=roundTime(c.start+(time-offset)*(c.speed||1));
  const start=edge==="start"?value:c.start,end=edge==="end"?value:c.end;
  if(start<c.start||end>c.end||start>=end||(end-start)/(c.speed||1)<minimumClipLength(c)-.000001||value===c[edge])return null;
  return {[edge]:value};
}
function trimmedCursor(c,edge,value,offset){
  const length=((edge==="end"?value:c.end)-(edge==="start"?value:c.start))/(c.speed||1);
  return offset+(edge==="end"?Math.max(0,length-.001):0);
}
let precisionSaving=false;
function updatePrecisionControls(){
  const c=currentClip(),available=!!c&&!precisionSaving;
  $("#precision-open").disabled=!c;$("#timecode").disabled=!c;
  if(!$("#precision-dialog").open)return;
  const input=$("#precision-time");
  input.disabled=precisionSaving;$("#precision-go").disabled=precisionSaving;
  if(document.activeElement!==input)input.value=montageTime(cursor);
  $("#precision-scene").textContent=c?`Cena ${index()+1} · ${c.label}`:"Adicione uma cena para começar.";
  $("#precision-status").textContent=precisionSaving?"Salvando corte…":playerLoading||player.seeking?"Buscando quadro…":"Posição pronta";
  $("#precision-back").disabled=!available||cursor<=0;
  $("#precision-forward").disabled=!available||cursor>=project.duration;
  $("#precision-undo").disabled=precisionSaving||!project.undo_available;
  for(const edge of ["start","end"])$("#precision-"+edge).disabled=!available||playerLoading||player.seeking||!cursorTrim(c,edge,cursor,before());
  $("#precision-trim-note").textContent=c?.locked?"Esta cena está protegida. Desproteja nos ajustes para aparar.":"Apara somente a cena selecionada. O restante da sequência se aproxima; narração, música e legendas mantêm suas posições. Você pode desfazer.";
}
function openPrecision(){
  if(!currentClip())return;
  pause();$("#precision-error").hidden=true;$("#precision-time").removeAttribute("aria-invalid");$("#precision-dialog").showModal();updatePrecisionControls();
  $("#precision-time").value=montageTime(cursor);
}
$("#precision-open").addEventListener("click",openPrecision);
$("#timecode").addEventListener("click",openPrecision);
$("#precision-undo").addEventListener("click",async()=>{
  if(precisionSaving||!project.undo_available)return;
  precisionSaving=true;updatePrecisionControls();
  try{await mutate("undo",{},"Última alteração desfeita.");}
  finally{precisionSaving=false;updatePrecisionControls();}
});
$("#precision-form").addEventListener("submit",e=>{
  e.preventDefault();if(precisionSaving)return;
  const input=$("#precision-time"),time=parseMontageTime(input.value),error=$("#precision-error");
  if(time===null||!Number.isFinite(time)||time>project.duration){
    error.textContent=`Use uma posição entre 0 e ${montageTime(project.duration)}.`;error.hidden=false;input.setAttribute("aria-invalid","true");return;
  }
  error.hidden=true;input.removeAttribute("aria-invalid");input.blur();seekTo(time);
});
for(const [id,direction] of [["back",-1],["forward",1]])$("#precision-"+id).addEventListener("click",()=>seekTo(frameStep(cursor,direction,project.duration)));
for(const edge of ["start","end"])$("#precision-"+edge).addEventListener("click",async()=>{
  if(precisionSaving||playerLoading||player.seeking)return;
  const c=currentClip(),changes=cursorTrim(c,edge,cursor,before());if(!changes)return;
  precisionSaving=true;cursor=trimmedCursor(c,edge,changes[edge],before());updatePrecisionControls();
  try{await mutate("clip_update",{clip_id:c.id,...changes},"Corte no cursor salvo. Você pode desfazer.");}
  finally{precisionSaving=false;updatePrecisionControls();}
});

function setTimelineZoom(value){
  const anchor=cursor;timelineZoom=clamp(Number(value),.5,8);renderTimeline();
  trackScroll.scrollLeft=Math.max(0,anchor*timelineScale-trackScroll.clientWidth/2);
}
$("#timeline-zoom").addEventListener("input",e=>setTimelineZoom(e.target.value));
$("#zoom-in").addEventListener("click",()=>setTimelineZoom(timelineZoom+.5));
$("#zoom-out").addEventListener("click",()=>setTimelineZoom(timelineZoom-.5));
$("#fit-timeline").addEventListener("click",()=>{setTimelineZoom(1);trackScroll.scrollLeft=0;});
$("#split-button").addEventListener("click",()=>{
  const c=currentClip();if(!c||$("#split-button").disabled)return;
  mutate("clip_split",{clip_id:c.id,at:roundTime(c.start+(cursor-before())*(c.speed||1))},"Clipe dividido no cursor. Você pode desfazer.");
});
$("#delete-button").addEventListener("click",()=>{const c=currentClip();if(c&&!c.locked)mutate("clip_remove",{clip_id:c.id},"Cena removida. Você pode desfazer.");});
$("#duplicate-button").addEventListener("click",()=>{const c=currentClip();if(c&&!$("#duplicate-button").disabled)mutate("clip_duplicate",{clip_id:c.id},"Cena duplicada. A cópia pode ser ajustada livremente.");});
trackScroll.addEventListener("keydown",e=>{
  if(/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||!project)return;
  if(e.key==="ArrowLeft"||e.key==="ArrowRight"){
    e.preventDefault();const direction=e.key==="ArrowLeft"?-1:1;seekTo(e.shiftKey?cursor+direction:frameStep(cursor,direction,project.duration));
  }else if(e.key==="Home"){e.preventDefault();seekTo(0);}
  else if(e.key==="End"){e.preventDefault();seekTo(project.duration);}
});
document.addEventListener("keydown",e=>{
  if(/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)||document.querySelector("dialog[open]"))return;
  if(e.key.toLowerCase()==="s"&&!e.ctrlKey&&!e.metaKey){e.preventDefault();$("#split-button").click();}
  if((e.ctrlKey||e.metaKey)&&["z","y"].includes(e.key.toLowerCase())){e.preventDefault();const redo=e.shiftKey||e.key.toLowerCase()==="y";if(redo?project?.redo_available:project?.undo_available)mutate(redo?"redo":"undo",{},redo?"Alteração refeita.":"Última alteração desfeita.");}
});
let resizeFrame=0;
new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(project&&!timelineGesture)renderTimeline();});}).observe(trackScroll);

// A draft is local until Apply; no command or history entry is sent by the preview.
let transitionDraft=null,transitionSaving=false,transitionPreviewEnd=null;
function transitionPair(left,right){
  const at=project.timeline.findIndex(c=>c.id===left);
  return at>=0&&project.timeline[at+1]?.id===right?[project.timeline[at],project.timeline[at+1]]:null;
}
function transitionMaximum(pair){return Math.floor(Math.min(3,...pair.map(clipDuration))*100+.000001)/100;}
function transitionListForPreview(){
  const items=project?.transitions||[];
  if(!transitionDraft||transitionDraft.projectId!==project?.id||transitionDraft.revision!==project.revision)return items;
  const kept=items.filter(t=>t.left!==transitionDraft.left||t.right!==transitionDraft.right);
  return transitionDraft.kind==="none"?kept:[...kept,transitionDraft];
}
function transitionBlend(clip,time,items){
  let result={color:"black",opacity:0};if(!clip)return result;
  for(const t of items){
    const half=t.duration/2;let opacity=0;
    if(t.right===clip.id&&time<half)opacity=1-time/half;
    if(t.left===clip.id&&time>clipDuration(clip)-half)opacity=1-(clipDuration(clip)-time)/half;
    if(opacity>result.opacity)result={color:t.kind,opacity:clamp(opacity,0,1)};
  }
  return result;
}
function updateTransitionPreview(){
  const blend=transitionBlend(currentClip(),cursor-before(),transitionListForPreview()),veil=$("#transition-veil");
  veil.hidden=blend.opacity<=0;veil.style.background=blend.color;veil.style.opacity=blend.opacity;
}
function renderTransitionJoins(){
  const supported=!!editorFeatures.pair_transitions,button=$("#transitions-open");
  button.hidden=!supported;button.disabled=project.timeline.length<2;
  if(!supported)return;
  let offset=0;
  project.timeline.forEach((clip,i)=>{
    offset+=clipDuration(clip);if(i===project.timeline.length-1)return;
    const right=project.timeline[i+1],active=(project.transitions||[]).some(t=>t.left===clip.id&&t.right===right.id);
    const node=document.createElement("button");node.type="button";node.className="transition-join";node.style.left=`${offset*timelineScale}px`;
    node.setAttribute("aria-label",`Transição entre cenas ${i+1} e ${i+2}`);node.setAttribute("aria-haspopup","dialog");node.classList.toggle("applied",active);
    node.textContent=active?"◆":"⋈";node.addEventListener("click",()=>openTransition(clip.id,right.id));$("#video-track").append(node);
  });
}
function refreshTransitionDraft(){
  if(!transitionDraft)return;
  const pair=transitionPair(transitionDraft.left,transitionDraft.right);if(!pair)return;
  pause();transitionPreviewEnd=null;
  const maximum=transitionMaximum(pair);transitionDraft.duration=clamp(transitionDraft.duration,.1,maximum);
  const locked=pair.some(c=>c.locked);
  $("#transition-duration").max=maximum;$("#transition-duration").value=transitionDraft.duration;$("#transition-duration").disabled=transitionDraft.kind==="none"||transitionSaving||locked;
  $("#transition-duration-value").textContent=`${transitionDraft.duration.toFixed(2).replace(".",",")} s`;
  $("#transition-limit").textContent=`Até ${maximum.toFixed(2).replace(".",",")} s neste encontro. Metade antes e metade depois do corte.`;
  $("#transition-draft-status").textContent=locked?"Desproteja as duas cenas para alterar esta transição.":transitionSaving?"Salvando…":"Prévia local. Aplicar salva uma alteração; Cancelar descarta.";
  $("#transition-apply").disabled=locked||transitionSaving;
  $("#transition-pair").disabled=transitionSaving;$("#transition-preview").disabled=transitionSaving;
  document.querySelectorAll("[data-transition-kind]").forEach(b=>{b.setAttribute("aria-pressed",b.dataset.transitionKind===transitionDraft.kind);b.disabled=locked||transitionSaving;});
  updateTransitionPreview();
}
function chooseTransitionPair(left,right){
  const saved=(project.transitions||[]).find(t=>t.left===left&&t.right===right);
  transitionDraft={...transitionDraft,left,right,kind:saved?.kind||"none",duration:saved?.duration||.5};refreshTransitionDraft();
}
async function openTransition(left,right){
  await queue;if(!editorFeatures.pair_transitions||project.timeline.length<2)return;
  pause();closeSheet();
  const pair=transitionPair(left,right)||project.timeline.slice(Math.min(Math.max(0,index()),project.timeline.length-2),Math.min(Math.max(0,index()),project.timeline.length-2)+2);
  transitionDraft={projectId:project.id,revision:project.revision,originalCursor:cursor};
  $("#transition-pair").innerHTML=project.timeline.slice(0,-1).map((c,i)=>`<option value="${c.id}">${i+1} → ${i+2} · ${esc(c.label)} / ${esc(project.timeline[i+1].label)}</option>`).join("");
  $("#transition-pair").value=pair[0].id;chooseTransitionPair(pair[0].id,pair[1].id);$("#transition-dialog").showModal();
}
$("#transitions-open").addEventListener("click",()=>openTransition());
$("#transition-pair").addEventListener("change",e=>{const at=project.timeline.findIndex(c=>c.id===e.target.value);chooseTransitionPair(project.timeline[at].id,project.timeline[at+1].id);});
for(const button of document.querySelectorAll("[data-transition-kind]"))button.addEventListener("click",()=>{transitionDraft.kind=button.dataset.transitionKind;refreshTransitionDraft();});
$("#transition-duration").addEventListener("input",e=>{transitionDraft.duration=Number(e.target.value);refreshTransitionDraft();});
$("#transition-preview").addEventListener("click",()=>{
  if(!transitionDraft||transitionSaving)return;
  const at=project.timeline.findIndex(c=>c.id===transitionDraft.right),boundary=before(at),half=transitionDraft.kind==="none"?.2:transitionDraft.duration/2;
  seekTo(Math.max(before(at-1),boundary-half-.2));transitionPreviewEnd=Math.min(project.duration,boundary+half+.2);play();
});
$("#transition-dialog").addEventListener("close",()=>{
  const original=transitionDraft?.originalCursor;pause();transitionPreviewEnd=null;transitionDraft=null;
  if(original!==undefined)seekTo(original);else updateTransitionPreview();
});
$("#transition-apply").addEventListener("click",async()=>{
  if(!transitionDraft||transitionSaving)return;
  if(transitionDraft.projectId!==project.id||transitionDraft.revision!==project.revision){toast("O projeto mudou. Reabra a transição para revisar.",true);$("#transition-dialog").close();return;}
  const {left,right,kind,duration}=transitionDraft;
  transitionSaving=true;refreshTransitionDraft();
  try{const ok=await mutate("transition_set",{left,right,kind,duration},kind==="none"?"Corte seco aplicado.":"Transição salva. Você pode desfazer.");if(ok){transitionDraft=null;$("#transition-dialog").close();}}
  finally{transitionSaving=false;refreshTransitionDraft();}
});
