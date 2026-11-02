"use strict";

// The track, ruler, waveform and playhead share one scale in pixels / second.
let timelineScale=30, timelineZoom=1, timelineGesture=null, suppressClipClick=false;
const waveforms=new Map();
const trackScroll=$("#timeline-scroll"), trackCanvas=$("#timeline");
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
const roundTime=value=>Math.round(value*1000)/1000;
let timelineSnapEnabled=false;
try{timelineSnapEnabled=localStorage.getItem("lili-timeline-snap")==="on";}catch{}
function timelineSnapTargets(p,excludeAudio=null){
  const targets=[{time:0,label:"Início da montagem"},{time:p.duration,label:"Fim da montagem"}];let at=0;
  for(const [i,c] of p.timeline.entries()){at+=(c.end-c.start)/(c.speed||1);targets.push({time:at,label:i===p.timeline.length-1?"Fim da montagem":`Corte ${i+1} → ${i+2}`});}
  for(const [kind,label] of [["narration","Narração"],["music","Música"]]){
    const track=p[kind],asset=(p.media||[]).find(a=>a.id===track?.media_id);
    if(kind!==excludeAudio&&track&&asset){const length=audioRange(track,asset.duration).length;targets.push({time:track.offset,label:label+" · início"},{time:track.offset+length,label:label+" · fim"});}
  }
  for(const [i,c]of(p.captions||[]).entries())targets.push({time:c.start,label:`Legenda ${i+1} · entrada`},{time:c.end,label:`Legenda ${i+1} · saída`});
  return targets.filter(t=>Number.isFinite(t.time)&&t.time>=0&&t.time<=p.duration);
}
function nearestTimelineSnap(time,targets,scale,enabled,bypass=false){
  if(!enabled||bypass||!Number.isFinite(time)||!(scale>0))return null;
  const threshold=Math.min(8/scale,.15);let best=null,distance=Infinity;
  for(const target of targets){const delta=Math.abs(target.time-time);if(delta<=threshold+1e-9&&delta<distance){best=target;distance=delta;}}
  return best;
}
function showTimelineSnap(target){
  const guide=$("#timeline-snap-guide");guide.hidden=!target;
  if(target){guide.style.left=`${target.time*timelineScale}px`;guide.querySelector("span").textContent=target.label;}
}
function updateSnapControls(){
  const button=$("#timeline-snap-toggle");button.textContent=timelineSnapEnabled?"Ímã: ligado":"Ímã: desligado";button.setAttribute("aria-pressed",String(timelineSnapEnabled));
}
function snappedTrim(c,edge,delta,offset,assetDuration,targets,scale,enabled,bypass=false){
  const speed=c.speed||1,minimum=minimumClipLength(c)*speed;
  const lower=edge==="start"?0:c.start+minimum,upper=edge==="start"?c.end-minimum:assetDuration;
  let value=clamp(roundTime(clamp(c[edge]+delta,lower,upper)),lower,upper);
  const target=nearestTimelineSnap(offset+(value-c.start)/speed,targets,scale,enabled,bypass);
  if(target){const candidate=c.start+(target.time-offset)*speed;if(candidate>=lower-1e-9&&candidate<=upper+1e-9){value=clamp(roundTime(candidate),lower,upper);return {value,target};}}
  return {value,target:null};
}
$("#timeline-snap-toggle").addEventListener("click",()=>{
  timelineSnapEnabled=!timelineSnapEnabled;try{localStorage.setItem("lili-timeline-snap",timelineSnapEnabled?"on":"off");}catch{}
  showTimelineSnap(null);updateSnapControls();
});


function renderTimeline(){
  if(!project) return;
  if(timelineGesture?.type==="audio-move")cancelAudioMove(null,false);
  updateSnapControls();if(!timelineGesture)showTimelineSnap(null);
  const clips=project.timeline, available=Math.max(200,trackScroll.clientWidth-24);
  timelineScale=Math.max(3,Math.min(100,available/Math.max(project.duration,10)))*timelineZoom;
  const width=Math.max(available,project.duration*timelineScale)+24;
  trackCanvas.style.width=`${width}px`;
  $("#clip-count").textContent=`${clips.length} ${clips.length===1?"cena":"cenas"}`;
  $("#total-duration").textContent=`Duração ${precise(project.duration)}`;
  $("#timeline-subtitle").textContent=clips.length?"Selecione • apare pelas bordas • divida no cursor":"Adicione um vídeo para começar.";
  if(!timelineGesture)$("#timeline-hint").textContent="Régua: cursor e zoom com dois dedos. Áudio: arraste ↔ para mover ou toque para ajustar.";
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
        <span class="clip-filmstrip">${strip}</span><span class="clip-caption">${String(i+1).padStart(2,"0")} · ${esc(c.label)}</span><span class="clip-duration">${precise(length)}</span>${["brightness","contrast","saturation"].some(k=>(c[k]??1)!==1)?`<span class="clip-look" title="Cor ajustada" aria-hidden="true">◐</span>`:""}${c.locked?`<span class="clip-lock">${icon("lock")}</span>`:""}
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
  if(editorFeatures.music_track)renderSoundTrack("music",track);
}
function renderCaptionTrack(){
  const track=$("#caption-track");track.hidden=!editorFeatures.subtitles;$("#caption-track-label").hidden=!editorFeatures.subtitles;
  if(!editorFeatures.subtitles)return;
  track.innerHTML=(project.captions||[]).map(c=>{const end=Math.min(c.end,project.duration);return end>c.start?`<button class="caption-region" data-caption="${c.id}" aria-current="${c.id===selectedCaption}" style="left:${c.start*timelineScale}px;width:${(end-c.start)*timelineScale}px" title="${esc(c.text)}">${esc(c.text)}</button>`:"";}).join("");
  track.querySelectorAll("[data-caption]").forEach(button=>button.addEventListener("click",()=>{selectedCaption=button.dataset.caption;const c=project.captions.find(c=>c.id===selectedCaption);openCaptionEdit(c.id);}));
}

function renderAudioTrack(){renderSoundTrack("narration",$("#audio-track"));}
function renderSoundTrack(kind,track){
  const sound=project[kind],asset=project.media.find(a=>a.id===sound?.media_id),name=kind==="music"?"música":"narração";
  const length=sound&&asset?Math.max(0,Math.min(audioRange(sound,asset.duration).length,project.duration-sound.offset)):0;
  track.innerHTML=length>0?`<button class="audio-region has-move ${kind==="music"?"music-region":""}" id="${kind}-region" style="left:${sound.offset*timelineScale}px;width:${length*timelineScale}px" aria-label="Editar ${name}: ${esc(asset.name)}"><svg id="${kind}-waveform" preserveAspectRatio="none" aria-hidden="true"></svg><span>${icon(kind==="music"?"music":"mic")}${esc(asset.name)}</span></button><button type="button" class="audio-move-handle ${kind==="music"?"music-move-handle":""}" id="${kind}-move" style="left:${sound.offset*timelineScale}px" aria-label="Mover ${name}. Arraste para posicionar ou toque para ajustar os tempos." title="Arraste para mover ${name}; toque para ajustes" ${audioMoveSaving?"disabled":""}>↔</button>`:`<button class="add-voice-track">${sound?name+" após o fim · ajustar":"+ Adicionar "+name}</button>`;
  const open=()=>{if(!suppressAudioClick&&!audioMoveSaving&&!timelineGesture)sound?openAudioEdit(kind):openInspector(kind==="music"?"music":"voice");};
  track.querySelector("button").addEventListener("click",open);
  if(length>0){const handle=$("#"+kind+"-move");handle.addEventListener("click",open);handle.addEventListener("pointerdown",e=>beginAudioMove(e,kind));handle.addEventListener("pointermove",moveAudio);handle.addEventListener("pointerup",finishAudioMove);handle.addEventListener("pointercancel",cancelAudioMove);handle.addEventListener("lostpointercapture",cancelAudioMove);}
  if(length>0){const pid=project.id;getAudioWaveform(asset).then(data=>{
    const node=$("#"+kind+"-waveform");if(project?.id!==pid||project[kind]?.media_id!==asset.id||!node)return;
    drawAudioWaveform(node,data,audioRange(sound,asset.duration).start,length);
  }).catch(()=>{});}
}
// Only the 44px handle owns the drag; the waveform and empty track keep native scrolling.
let audioMoveSaving=false,suppressAudioClick=false;
function snappedAudioOffset(offset,length,maximum,targets,scale,enabled,bypass=false){
  const value=clamp(roundTime(offset),0,maximum);let best=null;
  for(const edge of [0,length]){
    const target=nearestTimelineSnap(value+edge,targets,scale,enabled,bypass);
    if(!target)continue;const candidate=target.time-edge;
    if(candidate<0||candidate>maximum)continue;
    const distance=Math.abs(candidate-value);
    if(!best||distance<best.distance)best={offset:clamp(roundTime(candidate),0,maximum),target,distance};
  }
  return best||{offset:value,target:null};
}
function validAudioMove(g){return project?.id===g.projectId&&project.revision===g.revision&&project[g.kind]?.media_id===g.baseline.media_id;}
function paintAudioMove(g,offset){
  g.node.style.left=`${offset*g.scale}px`;g.region.style.left=`${offset*g.scale}px`;
  const visible=Math.max(0,Math.min(g.length,project.duration-offset));
  g.region.style.width=`${visible*g.scale}px`;
  if(g.waveformData)drawAudioWaveform(g.waveform,g.waveformData,g.baseline.start??0,visible);
}
function beginAudioMove(e,kind){
  if(e.button!==0||timelineGesture||audioMoveSaving||!project?.timeline.length||!e.currentTarget.isConnected)return;
  const sound=project[kind],asset=project.media.find(a=>a.id===sound?.media_id);
  if(!asset||!sound)return;
  e.preventDefault();e.stopPropagation();pause();
  const node=e.currentTarget,region=$("#"+kind+"-region");
  timelineGesture={type:"audio-move",projectId:project.id,revision:project.revision,kind,baseline:{...sound},length:audioRange(sound,asset.duration).length,maximum:Math.min(kind==="music"?1800:3600,Math.max(0,project.duration-.1)),x:e.clientX,scroll:trackScroll.scrollLeft,scale:timelineScale,pointerId:e.pointerId,node,region,offset:sound.offset,moved:false};
  const gesture=timelineGesture;gesture.waveform=$("#"+kind+"-waveform");
  getAudioWaveform(asset).then(data=>{if(timelineGesture===gesture){gesture.waveformData=data;paintAudioMove(gesture,gesture.offset);}}).catch(()=>{});
  try{node.setPointerCapture(e.pointerId);}catch{cancelAudioMove();return;}
  node.classList.add("moving");region.classList.add("moving");
  $("#timeline-hint").textContent="Arraste ↔ para mover o áudio. Solte para salvar. Esc cancela. Toque abre ajustes.";
}
function moveAudio(e){
  const g=timelineGesture;if(g?.type!=="audio-move"||g.pointerId!==e.pointerId)return;
  e.stopPropagation();
  if(!validAudioMove(g)){cancelAudioMove();return;}
  const delta=e.clientX-g.x+trackScroll.scrollLeft-g.scroll;
  if(!g.moved&&Math.abs(delta)<6)return;g.moved=true;
  const snap=snappedAudioOffset(g.baseline.offset+delta/g.scale,g.length,g.maximum,timelineSnapTargets(project,g.kind),g.scale,timelineSnapEnabled,e.shiftKey);
  g.offset=snap.offset;showTimelineSnap(snap.target);paintAudioMove(g,g.offset);
  const overrun=g.offset+g.length>project.duration+.001;
  $("#timeline-hint").textContent=`${g.kind==="music"?"Música":"Narração"} · início ${montageTime(g.offset)} · fim ${montageTime(g.offset+g.length)}. ${overrun?"O fim ultrapassa o vídeo. ":""}Solte para salvar · Esc cancela.`;
}
function clearAudioMove(g,suppress){
  timelineGesture=null;showTimelineSnap(null);g.node.classList.remove("moving");g.region.classList.remove("moving");
  if(g.node.hasPointerCapture(g.pointerId))g.node.releasePointerCapture(g.pointerId);
  if(suppress){suppressAudioClick=true;setTimeout(()=>{suppressAudioClick=false;},0);}
}
async function finishAudioMove(e){
  const g=timelineGesture;if(g?.type!=="audio-move"||g.pointerId!==e.pointerId)return;
  // The release can be newer than the last delivered move event.
  moveAudio(e);if(timelineGesture!==g)return;
  const valid=validAudioMove(g);clearAudioMove(g,g.moved);
  if(!g.moved||g.offset===g.baseline.offset||!valid){paintAudioMove(g,g.baseline.offset);if(g.moved)renderTimeline();return;}
  audioMoveSaving=true;g.node.disabled=true;
  try{await mutate(g.kind==="music"?"music_set":"narration_set",{media_id:g.baseline.media_id,offset:g.offset},"Áudio movido. Você pode desfazer.",{projectId:g.projectId,revision:g.revision});}
  finally{audioMoveSaving=false;if(project){renderTimeline();if(project.id===g.projectId)$("#"+g.kind+"-move")?.focus({preventScroll:true});}}
}
function cancelAudioMove(e=null,redraw=true){
  const g=timelineGesture;if(g?.type!=="audio-move"||(e?.pointerId!==undefined&&e.pointerId!==g.pointerId))return;
  e?.stopPropagation?.();clearAudioMove(g,true);
  if(validAudioMove(g))paintAudioMove(g,g.baseline.offset);
  if(redraw&&project)renderTimeline();
}
document.addEventListener("pointerdown",e=>{if(timelineGesture?.type==="audio-move"&&e.pointerId!==timelineGesture.pointerId)cancelAudioMove();},true);
document.addEventListener("visibilitychange",()=>{if(document.hidden)cancelAudioMove();});
globalThis.addEventListener?.("blur",()=>cancelAudioMove());

function getAudioWaveform(asset){
  const key=`${project.id}/${asset.id}`;
  if(!waveforms.has(key))waveforms.set(key,api(assetUrl(asset,"waveform.json")).catch(error=>{waveforms.delete(key);throw error;}));
  return waveforms.get(key);
}
function drawAudioWaveform(node,data,start,length){
  const count=300,points=[],peaks=data.peaks,maximum=Math.max(.01,...peaks);
  for(let i=0;i<count;i++){
    const a=Math.floor((start+length*i/count)/data.duration*peaks.length),b=Math.ceil((start+length*(i+1)/count)/data.duration*peaks.length);
    const amplitude=Math.max(0,...peaks.slice(a,Math.max(a+1,b)))/maximum*16;
    points.push(`M${i+.5},${20-amplitude}v${Math.max(1,amplitude*2)}`);
  }
  node.setAttribute("viewBox",`0 0 ${count} 40`);node.innerHTML=`<path d="${points.join(" ")}"/>`;
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

function pointerTime(e){
  const time=clamp((e.clientX-trackCanvas.getBoundingClientRect().left)/timelineScale,0,project.duration);
  const snap=nearestTimelineSnap(time,timelineSnapTargets(project),timelineScale,timelineSnapEnabled,e.shiftKey);showTimelineSnap(snap);return snap?snap.time:time;
}
const rulerPointers=new Map();
let rulerFrame=0;
function pinchGeometry(points){
  const [a,b]=points;
  return {distance:Math.abs(a-b),center:(a+b)/2};
}
function moveRulerPinch(){
  showTimelineSnap(null);rulerFrame=0;
  const gesture=timelineGesture;if(gesture?.type!=="pinch"||rulerPointers.size!==2)return;
  const geometry=pinchGeometry([...rulerPointers.values()]);
  timelineZoom=clamp(gesture.zoom*geometry.distance/gesture.distance,.5,8);
  renderTimeline();
  trackScroll.scrollLeft=Math.max(0,gesture.anchor*timelineScale-(geometry.center-trackScroll.getBoundingClientRect().left));
}
trackCanvas.addEventListener("pointerdown",e=>{
  if(e.button!==0||!project?.timeline.length||e.target.closest("button")) return;
  if(["trim","drain","audio-move"].includes(timelineGesture?.type))return;
  if(e.pointerType==="touch"&&e.target.closest("#time-ruler")){
    if(rulerPointers.size>=2)return;
    rulerPointers.set(e.pointerId,e.clientX);
    if(rulerPointers.size===2){
      const geometry=pinchGeometry([...rulerPointers.values()]);
      if(geometry.distance<8){rulerPointers.delete(e.pointerId);return;}
      const original=timelineGesture?.originalCursor??cursor;
      showTimelineSnap(null);timelineGesture={type:"pinch",distance:geometry.distance,zoom:timelineZoom,anchor:(geometry.center-trackCanvas.getBoundingClientRect().left)/timelineScale};
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
  showTimelineSnap(null);
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
  const asset=assetFor(c),snap=snappedTrim(c,edge,delta,before(),asset.duration,timelineSnapTargets(project),timelineScale,timelineSnapEnabled,e.shiftKey),value=snap.value;
  showTimelineSnap(snap.target);
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
  showTimelineSnap(null);
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
  updateSnapControls();
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
  if(timelineGesture?.type==="audio-move"){if(e.key==="Escape"){e.preventDefault();cancelAudioMove();}return;}
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
    if(t.kind==="dissolve")continue;
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
  $("[data-transition-kind='dissolve']").hidden=!editorFeatures.dissolve_transitions;
  $("#transition-all-label").hidden=!editorFeatures.dissolve_transitions;
  const maximum=transitionMaximum(pair);transitionDraft.duration=clamp(transitionDraft.duration,.1,maximum);
  const locked=pair.some(c=>c.locked);
  $("#transition-duration").max=maximum;$("#transition-duration").value=transitionDraft.duration;$("#transition-duration").disabled=transitionDraft.kind==="none"||transitionSaving||locked;
  $("#transition-duration-value").textContent=`${transitionDraft.duration.toFixed(2).replace(".",",")} s`;
  $("#transition-limit").textContent=`Até ${maximum.toFixed(2).replace(".",",")} s neste encontro. Metade antes e metade depois do corte.`;
  $("#transition-draft-status").textContent=locked?"Desproteja as duas cenas para alterar esta transição.":transitionSaving?"Salvando…":"Prévia local. Aplicar salva uma alteração; Cancelar descarta.";
  $("#transition-apply").disabled=locked||transitionSaving;$("#transition-all").disabled=locked||transitionSaving;
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
  transitionDraft={projectId:project.id,revision:project.revision,originalCursor:cursor};$("#transition-all").checked=false;
  $("#transition-pair").innerHTML=project.timeline.slice(0,-1).map((c,i)=>`<option value="${c.id}">${i+1} → ${i+2} · ${esc(c.label)} / ${esc(project.timeline[i+1].label)}</option>`).join("");
  $("#transition-pair").value=pair[0].id;chooseTransitionPair(pair[0].id,pair[1].id);$("#transition-dialog").showModal();
}
$("#transitions-open").addEventListener("click",()=>openTransition());
$("#transition-pair").addEventListener("change",e=>{const at=project.timeline.findIndex(c=>c.id===e.target.value);chooseTransitionPair(project.timeline[at].id,project.timeline[at+1].id);});
for(const button of document.querySelectorAll("[data-transition-kind]"))button.addEventListener("click",()=>{transitionDraft.kind=button.dataset.transitionKind;refreshTransitionDraft();});
$("#transition-duration").addEventListener("input",e=>{transitionDraft.duration=Number(e.target.value);refreshTransitionDraft();});
$("#transition-preview").addEventListener("click",()=>{
  if(!transitionDraft||transitionSaving)return;
  if(transitionDraft.kind==="dissolve"){openSmoothPlayback({...transitionDraft});return;}
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
  try{const ok=await mutate("transition_set",{left,right,kind,duration,...($("#transition-all").checked?{all:true}:{})},kind==="none"?"Corte seco aplicado.":"Transição salva. Você pode desfazer.");if(ok){transitionDraft=null;$("#transition-dialog").close();}}
  finally{transitionSaving=false;refreshTransitionDraft();}
});

// Local looks are absolute grading targets. Strength blends from the saved scene,
// never from the previous slider event, so trying looks cannot accumulate edits.
const EFFECT_PRESETS=[
  {id:"current",name:"Atual",description:"Como a cena está salva",values:null},
  {id:"original",name:"Original",description:"Cor sem ajustes",values:{brightness:1,contrast:1,saturation:1}},
  {id:"soft",name:"Suave",description:"Menos contraste e cor",values:{brightness:1.04,contrast:.9,saturation:.9}},
  {id:"vivid",name:"Vivo",description:"Realça contraste e cor",values:{brightness:1.02,contrast:1.12,saturation:1.25}},
  {id:"editorial",name:"Editorial",description:"Contraste com cor discreta",values:{brightness:1,contrast:1.16,saturation:.82}},
  {id:"mono",name:"Preto e branco",description:"Imagem sem cor",values:{brightness:1,contrast:1.06,saturation:0}},
  {id:"light",name:"Mais luz",description:"Clareia sem mudar o corte",values:{brightness:1.12,contrast:1.02,saturation:1.02}}
];
let effectDraft=null,effectSaving=false,effectPreviewEnd=null;
function effectGrade(clip){return Object.fromEntries(["brightness","contrast","saturation"].map(key=>[key,clip?.[key]??1]));}
function mixEffectGrade(baseline,preset,strength){
  const target=preset.values||baseline,amount=clamp(Number.isFinite(strength)?strength:0,0,100)/100;
  return Object.fromEntries(Object.keys(baseline).map(key=>[key,Math.round((baseline[key]+(target[key]-baseline[key])*amount)*10000)/10000]));
}
function validEffectDraft(){return !!effectDraft&&effectDraft.projectId===project?.id&&effectDraft.revision===project.revision&&project.timeline.some(c=>c.id===effectDraft.clipId);}
function effectDraftGrade(){
  const preset=EFFECT_PRESETS.find(p=>p.id===effectDraft?.preset)||EFFECT_PRESETS[0];
  return mixEffectGrade(effectDraft.baseline,preset,effectDraft.strength);
}
function effectPreviewClip(clip){
  if(!validEffectDraft()||clip?.id!==effectDraft.clipId)return clip;
  return {...clip,...(effectDraft.comparing?effectDraft.baseline:effectDraftGrade())};
}
function effectChanges(){
  if(!validEffectDraft())return null;
  const values=effectDraftGrade();
  return Object.keys(values).some(k=>Math.abs(values[k]-effectDraft.baseline[k])>.00001)?values:null;
}
function stopEffectPlayback(){
  if(effectPreviewEnd===null)return false;
  const end=effectPreviewEnd;effectPreviewEnd=null;pause();
  cursor=Math.max(before(),end-.001);updatePlayer(false,cursor);return true;
}
function updateEffectControls(){
  const c=currentClip();$("#effects-open").hidden=!editorFeatures.color_adjustments;$("#effects-open").disabled=!c;
  if(!$("#effects-dialog").open||!effectDraft)return;
  const valid=validEffectDraft(),target=project?.timeline.find(c=>c.id===effectDraft.clipId),waiting=playerLoading||player.seeking;
  const preset=EFFECT_PRESETS.find(p=>p.id===effectDraft.preset)||EFFECT_PRESETS[0];
  $("#effects-selected-note").textContent=preset.id==="original"?"Original restaura brilho, contraste e saturação ao padrão. Desfazer recupera os ajustes anteriores.":`${preset.name} · ${preset.description}. Depois de aplicar, os valores ficam em Luz e cor; não é uma camada independente.`;
  $("#effects-strength").disabled=!valid||effectSaving||effectDraft.preset==="current";
  $("#effects-scene").disabled=effectSaving;$("#effects-strength").value=effectDraft.strength;$("#effects-strength-value").textContent=effectDraft.strength+"%";
  $("#effects-apply").disabled=!valid||effectSaving||waiting||target?.locked||effectDraft.comparing||!effectChanges();
  $("#effects-compare").disabled=!valid||effectSaving;$("#effects-compare").setAttribute("aria-pressed",effectDraft.comparing);
  $("#effects-compare").textContent=effectDraft.comparing?"Ver ajustado":"Ver antes";
  $("#effects-center").disabled=!valid||effectSaving;$("#effects-play").disabled=!valid||effectSaving;$("#effects-play").textContent=playing?"Pausar prévia":"Reproduzir cena";
  $("#effects-status").textContent=!valid?"O projeto mudou. Feche e reabra para revisar os ajustes.":effectSaving?"Salvando aparência…":target?.locked?"Prévia apenas: desproteja esta cena nos ajustes para aplicar.":waiting?"Carregando a cena…":effectDraft.comparing?"Mostrando os ajustes anteriores. Volte ao ajustado para aplicar.":effectChanges()?"Prévia local. Aplicar salva uma alteração; Cancelar descarta.":"Sem mudança nos ajustes salvos. Escolha uma aparência para comparar.";
  $("#effects-catalog").querySelectorAll("[data-effect]").forEach(b=>{b.setAttribute("aria-pressed",b.dataset.effect===effectDraft.preset);b.disabled=!valid||effectSaving;});
}
function effectFrameAt(clip,time,offset,assetDuration){
  const source=clip.start+clamp(time-offset,0,clipDuration(clip))*(clip.speed||1);
  // The frame API reserves 40 ms at the source end; never round beyond its bound.
  return Math.floor(clamp(source,0,Math.max(0,assetDuration-.04))*1000)/1000;
}
function renderEffectCatalog(clip){
  const asset=assetFor(clip),at=effectFrameAt(clip,cursor,before(),asset.duration);
  const frame=assetUrl(asset,"frame.jpg")+"?at="+at;
  $("#effects-catalog").innerHTML=EFFECT_PRESETS.map(p=>{
    const grade=gradeValues(p.values||effectDraft.baseline),id="effect-grade-"+p.id;
    const channels=["R","G","B"].map(channel=>`<feFunc${channel} type="linear" slope="${grade.slope}" intercept="${grade.offset}"/>`).join("");
    return `<button type="button" data-effect="${p.id}" aria-pressed="${p.id===effectDraft.preset}" title="${p.description}"><svg aria-hidden="true" width="0" height="0"><defs><filter id="${id}" color-interpolation-filters="sRGB"><feComponentTransfer>${channels}</feComponentTransfer><feColorMatrix type="matrix" values="${grade.matrix.join(" ")}"/></filter></defs></svg><img alt="" loading="lazy" src="${frame}" style="filter:url(#${id})"><span>${p.name}</span></button>`;
  }).join("");
  $("#effects-catalog").querySelectorAll("[data-effect]").forEach(b=>b.addEventListener("click",()=>chooseEffectPreset(b.dataset.effect)));
}
function chooseEffectPreset(id){
  if(!validEffectDraft()||effectSaving||!EFFECT_PRESETS.some(p=>p.id===id))return;
  effectDraft.preset=id;effectDraft.comparing=false;effectDraft.strength=100;updateTime();
}
function chooseEffectScene(id){
  if(effectSaving)return;
  pause();effectPreviewEnd=null;
  const c=project.timeline.find(c=>c.id===id);if(!c)return;
  effectDraft={...effectDraft,projectId:project.id,revision:project.revision,clipId:id,baseline:effectGrade(c),preset:"current",strength:100,comparing:false};
  if(selected!==id)selectClip(id);
  renderEffectCatalog(c);updateTime();
}
async function openEffects(){
  await queue;if(!currentClip()||!editorFeatures.color_adjustments||effectSaving)return;
  pause();closeSheet();effectDraft={originalCursor:cursor};
  $("#effects-scene").innerHTML=project.timeline.map((c,i)=>`<option value="${c.id}">${i+1} · ${esc(c.label)}</option>`).join("");
  $("#effects-scene").value=selected;chooseEffectScene(selected);$("#effects-dialog").showModal();updateEffectControls();
}
$("#effects-open").addEventListener("click",openEffects);
$("#effects-scene").addEventListener("change",e=>chooseEffectScene(e.target.value));
$("#effects-strength").addEventListener("input",e=>{
  if(!validEffectDraft()||effectSaving)return;
  effectDraft.strength=clamp(Number(e.target.value)||0,0,100);effectDraft.comparing=false;updateTime();
});
$("#effects-compare").addEventListener("click",()=>{if(validEffectDraft()&&!effectSaving){pause();effectPreviewEnd=null;effectDraft.comparing=!effectDraft.comparing;updateTime();}});
$("#effects-center").addEventListener("click",()=>{
  if(!validEffectDraft()||effectSaving)return;
  effectPreviewEnd=null;const c=project.timeline.find(c=>c.id===effectDraft.clipId);
  seekTo(before(project.timeline.indexOf(c))+clipDuration(c)/2);renderEffectCatalog(c);updateTime();
});
$("#effects-play").addEventListener("click",()=>{
  if(!validEffectDraft()||effectSaving)return;
  if(playing){effectPreviewEnd=null;pause();updateEffectControls();return;}
  const c=project.timeline.find(c=>c.id===effectDraft.clipId);seekTo(before(project.timeline.indexOf(c)));effectPreviewEnd=before()+clipDuration(c);play();updateEffectControls();
});
$("#effects-dialog").addEventListener("close",()=>{
  const original=effectDraft?.originalCursor;pause();effectPreviewEnd=null;effectDraft=null;
  if(original!==undefined)seekTo(original);else updateTime();
});
$("#effects-apply").addEventListener("click",async()=>{
  if(effectSaving||!effectDraft||$("#effects-apply").disabled)return;
  const changes=effectChanges();if(!changes)return;
  effectSaving=true;pause();effectPreviewEnd=null;updateEffectControls();
  try{const ok=await mutate("clip_update",{clip_id:effectDraft.clipId,...changes},"Aparência salva. Você pode desfazer ou ajustar a cor.");if(ok){effectDraft=null;$("#effects-dialog").close();}}
  finally{effectSaving=false;updateEffectControls();}
});


// Audio drafts use the existing atomic commands; experiments never mutate project.
let audioDraft=null,audioSaving=false;
function validAudioDraft(){return !!audioDraft&&project?.id===audioDraft.projectId&&project.revision===audioDraft.revision&&project[audioDraft.kind]?.media_id===audioDraft.baseline.media_id;}
function audioDraftProblem(){
  if(!validAudioDraft())return "O projeto mudou. Cancele e abra o áudio novamente.";
  const d=audioDraft.values,a=audioDraft.asset,music=audioDraft.kind==="music",length=audioRange(d,a.duration).length;
  if(!Number.isFinite(d.offset)||d.offset<0||d.offset>(music?1800:3600))return "Confira o início na montagem: de 0 até "+(music?1800:3600)+" segundos.";
  if((music||editorFeatures.narration_trim)&&(!Number.isFinite(d.start)||!Number.isFinite(d.end)||d.start<0||d.end>a.duration||Math.round(length*10000)<1000))return "Escolha pelo menos 0,1 s dentro do arquivo de áudio.";
  if(!Number.isFinite(d.volume)||d.volume<0||d.volume>(music?1:2))return "Confira o volume.";
  if(!Number.isFinite(d.fade_in)||!Number.isFinite(d.fade_out)||d.fade_in<0||d.fade_out<0||d.fade_in+d.fade_out>length+1e-9)return "As entradas e saídas suaves juntas devem caber no trecho. Reduza os fades ou aumente o trecho.";
  return "";
}
function audioPreviewTrack(kind){
  return validAudioDraft()&&audioDraft.kind===kind&&!audioDraftProblem()?audioDraft.values:project?.[kind];
}
function audioEditChanged(){return validAudioDraft()&&Object.keys(audioDraft.values).some(k=>audioDraft.values[k]!==audioDraft.baseline[k]);}
function writeAudioFields(){
  if(!audioDraft)return;const d=audioDraft.values;
  for(const key of ["offset","start","end"])if(d[key]!==undefined)$("#audio-edit-"+key).value=Number.isFinite(d[key])?montageTime(d[key]):"";
  for(const key of ["volume","fade_in","fade_out"])$("#audio-edit-"+key).value=key==="volume"?Math.round(d[key]*100):d[key];
  $("#audio-edit-duck").checked=d.duck??true;
}
function updateAudioControls(){
  if(!audioDraft)return;
  const problem=audioDraftProblem(),d=audioDraft.values,music=audioDraft.kind==="music",length=audioRange(d,audioDraft.asset.duration).length;
  $("#audio-edit-error").hidden=!problem;$("#audio-edit-error").textContent=problem;
  $("#audio-edit-apply").disabled=!!problem||audioSaving||!audioEditChanged();
  $("#audio-edit-status").textContent=audioSaving?"Salvando…":"Aplicar salva os ajustes de uma vez. Cancelar descarta a prévia.";
  $("#audio-edit-play").textContent=playing?"Pausar prévia":"Ouvir do cursor";$("#audio-edit-play").disabled=!!problem||audioSaving||!project.timeline.length||playerLoading;
  $("#audio-montage-seek").max=project.duration;$("#audio-montage-seek").value=cursor;$("#audio-montage-time").textContent=montageTime(cursor);
  if(document.activeElement!==$("#audio-seek-time"))$("#audio-seek-time").value=montageTime(cursor);
  $("#audio-mix-summary").textContent=`Volume ${Math.round(d.volume*100)}% · fades ${d.fade_in} / ${d.fade_out} s`;
  $("#audio-edit-volume-value").textContent=Math.round(d.volume*100)+"%";$("#audio-volume-note").hidden=d.volume<=1;
  for(const key of ["fade_in","fade_out"])$("#audio-edit-"+key).max=Math.max(0,length);
  $("#audio-edit-summary").textContent=problem?"A prévia usa o áudio salvo até corrigir os valores.":`Trecho ${precise(length)} · início ${montageTime(d.offset)} · fim ${montageTime(d.offset+length)}. `+(d.offset>=project.duration?"Começa após o fim da montagem; não será ouvido na saída.":d.offset+length>project.duration?"A exportação termina com a montagem; o fim deste áudio e seu fade podem ficar fora.":music?"A música pode abaixar para 25% durante a voz.":editorFeatures.narration_trim?"A narração usa apenas o trecho escolhido; o original é preservado.":"Este servidor ainda usa o arquivo inteiro da narração.");
  for(const node of $("#audio-edit-dialog").querySelectorAll("input,button"))if(node.id!=="audio-edit-apply"&&node.id!=="audio-edit-play")node.disabled=audioSaving;
  for(const edge of ["start","end"])$("#audio-trim-"+edge).disabled=audioSaving||!audioTrimAtCursor(edge);
  const start=d.start??0,span=length,total=audioDraft.asset.duration;
  const window=$("#audio-edit-window");window.hidden=!!problem;window.style.left=`${start/total*100}%`;window.style.width=`${span/total*100}%`;
  const position=cursor-d.offset+start,head=$("#audio-edit-cursor");head.hidden=!!problem||position<start||position>start+span;head.style.left=`${clamp(position/total*100,0,100)}%`;
}
function audioTrimAtCursor(edge){
  if(!validAudioDraft()||(audioDraft.kind!=="music"&&!editorFeatures.narration_trim)||audioDraftProblem())return null;
  const d=audioDraft.values,delta=cursor-d.offset;
  if(delta<=0||delta>=d.end-d.start)return null;
  const patch=edge==="start"?{start:roundTime(d.start+delta),offset:roundTime(cursor)}:{end:roundTime(d.start+delta)};
  const length=(patch.end??d.end)-(patch.start??d.start);
  return length>=Math.max(.1,d.fade_in+d.fade_out)-1e-9?patch:null;
}
async function openAudioEdit(kind){
  await queue;if(audioSaving||!project?.[kind]||!(kind==="narration"||kind==="music"))return;
  pause();closeSheet();const baseline={...project[kind]},asset=project.media.find(a=>a.id===baseline.media_id);
  if(!asset)return;
  if(kind==="narration"&&editorFeatures.narration_trim)Object.assign(baseline,{start:baseline.start??0,end:baseline.end??asset.duration});
  audioDraft={projectId:project.id,revision:project.revision,kind,baseline,values:{fade_in:0,fade_out:0,...baseline},asset,originalCursor:cursor};
  // Old projects may omit fades; avoid reporting a default as an edit.
  audioDraft.baseline={...audioDraft.values};
  $("#audio-edit-title").textContent=kind==="music"?"Música no tempo certo":"Narração no tempo certo";$("#audio-edit-name").textContent=asset.name;
  $("#audio-music-trim").hidden=kind!=="music"&&!editorFeatures.narration_trim;$("#audio-trim-note").textContent="Aparar início mantém o restante do áudio sincronizado. Não desloca vídeo, outras faixas ou legendas.";$("#audio-duck-label").hidden=kind!=="music";$("#audio-edit-volume").max=kind==="music"?100:200;
  $("#audio-seek-error").hidden=true;$("#audio-seek-time").value=montageTime(cursor);
  $("#audio-wave-note").textContent="Carregando forma de onda…";$("#audio-edit-wave").innerHTML="";writeAudioFields();$("#audio-edit-dialog").showModal();updateAudioControls();
  const draft=audioDraft;getAudioWaveform(asset).then(data=>{if(audioDraft!==draft)return;drawAudioWaveform($("#audio-edit-wave"),data,0,asset.duration);$("#audio-wave-note").textContent="Arquivo inteiro · área verde = trecho utilizado · linha = cursor.";}).catch(()=>{if(audioDraft===draft)$("#audio-wave-note").textContent="Forma de onda indisponível. Os ajustes de tempo continuam funcionando.";});
}
for(const key of ["offset","start","end","fade_in","fade_out"])$("#audio-edit-"+key).addEventListener("input",e=>{
  if(!validAudioDraft()||audioSaving)return;pause();audioDraft.values[key]=["offset","start","end"].includes(key)?parseMontageTime(e.target.value)??NaN:(e.target.value.trim()?Number(e.target.value):NaN);updateTime();
});
$("#audio-edit-volume").addEventListener("input",e=>{if(validAudioDraft()&&!audioSaving){pause();audioDraft.values.volume=Number(e.target.value)/100;updateTime();}});
$("#audio-edit-duck").addEventListener("change",e=>{if(validAudioDraft()&&!audioSaving){pause();audioDraft.values.duck=e.target.checked;updateTime();}});
$("#audio-montage-seek").addEventListener("input",e=>{if(audioDraft&&!audioSaving)seekTo(Number(e.target.value));});
for(const [key,direction] of [["back",-1],["forward",1]]){
  $("#audio-cursor-"+key).addEventListener("click",()=>{if(audioDraft&&!audioSaving)seekTo(frameStep(cursor,direction,project.duration));});
  $("#audio-offset-"+key).addEventListener("click",()=>{if(validAudioDraft()&&!audioSaving&&Number.isFinite(audioDraft.values.offset)){pause();audioDraft.values.offset=frameStep(audioDraft.values.offset,direction,audioDraft.kind==="music"?1800:3600);writeAudioFields();updateTime();}});
}
$("#audio-align-cursor").addEventListener("click",()=>{if(validAudioDraft()&&!audioSaving){pause();audioDraft.values.offset=roundTime(cursor);writeAudioFields();updateTime();}});
for(const edge of ["start","end"])$("#audio-trim-"+edge).addEventListener("click",()=>{const patch=audioTrimAtCursor(edge);if(!patch||audioSaving)return;pause();Object.assign(audioDraft.values,patch);writeAudioFields();updateTime();});
$("#audio-edit-play").addEventListener("click",()=>{if(!validAudioDraft()||audioSaving||audioDraftProblem())return;if(playing)pause();else{if(cursor>=project.duration)seekTo(Math.min(audioDraft.values.offset,Math.max(0,project.duration-.001)));play();}updateAudioControls();});
$("#audio-edit-dialog").addEventListener("cancel",e=>{if(audioSaving)e.preventDefault();});
$("#audio-edit-dialog").addEventListener("close",()=>{const original=audioDraft?.originalCursor;pause();audioDraft=null;if(original!==undefined)seekTo(original);else updateTime();});
$("#audio-edit-apply").addEventListener("click",async()=>{
  await queue;if(audioSaving||!validAudioDraft()||audioDraftProblem()||!audioEditChanged())return;
  const draft=audioDraft;audioSaving=true;pause();updateAudioControls();
  try{const ok=await mutate(draft.kind==="music"?"music_set":"narration_set",{...draft.values},"Áudio ajustado. Você pode desfazer pela linha do tempo.");if(ok){audioDraft=null;$("#audio-edit-dialog").close();}}
  finally{audioSaving=false;updateAudioControls();}
});

function seekAudioTime(){
  if(!audioDraft||audioSaving)return;const time=parseMontageTime($("#audio-seek-time").value);
  const error=$("#audio-seek-error");error.hidden=time!==null&&time>=0&&time<=project.duration;
  if(!error.hidden){error.textContent="Digite uma posição entre 0 e "+montageTime(project.duration)+".";return;}
  seekTo(time);
}
$("#audio-seek-go").addEventListener("click",seekAudioTime);
$("#audio-seek-time").addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();seekAudioTime();}});


// Subtitle text, timing and typography are one reversible edit, not autosaved keystrokes.
let captionDraft=null,captionSaving=false,captionPreviewEnd=null;
function validCaptionDraft(){
  return !!captionDraft&&project?.id===captionDraft.projectId&&project.revision===captionDraft.revision&&(captionDraft.isNew?!project.captions.some(c=>c.id===captionDraft.values.id):project.captions.some(c=>c.id===captionDraft.values.id));
}
function captionDraftProblem(values=captionDraft?.values){
  if(!validCaptionDraft())return "O projeto mudou. Cancele e abra a legenda novamente.";
  if(!values||!Number.isFinite(values.start)||!Number.isFinite(values.end)||values.start<0||values.end>1800||values.end-values.start<.09999)return "Use entrada e saída entre 0 e 30 minutos, com pelo menos 0,1 s de duração.";
  if(typeof values.text!=="string"||!values.text.trim()||values.text.length>160)return "Escreva a legenda com até 160 caracteres.";
  if(!["sans","serif","mono"].includes(values.title_font)||!["small","medium","large"].includes(values.title_size)||!["top","center","bottom"].includes(values.title_position))return "Escolha fonte, tamanho e posição disponíveis.";
  if((project.captions||[]).some(c=>c.id!==values.id&&values.start<c.end-.00001&&values.end>c.start+.00001))return "Este intervalo encontra outra legenda. Ajuste os tempos; a faixa não aceita sobreposição.";
  return "";
}
function captionPreviewItems(){
  const saved=project?.captions||[];
  if(!validCaptionDraft()||captionDraftProblem())return saved;
  const list=[...saved.filter(c=>c.id!==captionDraft.values.id),{...captionDraft.values,text:captionDraft.values.text.trim()}].sort((a,b)=>a.start-b.start);
  return captionDraft.styleAll?list.map(c=>({...c,...captionStyle(captionDraft.values)})):list;
}
function captionStyle(c){return {title_font:c.title_font||"sans",title_size:c.title_size||"medium",title_position:c.title_position||"bottom"};}
function captionHasChanges(){return validCaptionDraft()&&(captionDraft.isNew||Object.keys(captionDraft.values).some(k=>captionDraft.values[k]!==captionDraft.baseline[k])||captionDraft.styleAll&&(project.captions||[]).some(c=>Object.keys(captionStyle(c)).some(k=>captionStyle(c)[k]!==captionDraft.values[k])));}

function writeCaptionFields(){
  const d=captionDraft.values;for(const key of ["text","title_font","title_size","title_position"])$("#caption-edit-"+key).value=d[key];
  for(const key of ["start","end"])$("#caption-edit-"+key).value=Number.isFinite(d[key])?montageTime(d[key]):"";
}
function updateCaptionControls(){
  if(!captionDraft)return;const d=captionDraft.values,problem=captionDraftProblem(),canPreview=!problem&&d.start<project.duration&&project.timeline.length>0;
  $("#caption-style-all-label").textContent=`Usar este estilo em todas as legendas (${project.captions.length+(captionDraft.isNew?1:0)})`;
  $("#caption-edit-count").textContent=d.text.length+"/160";$("#caption-edit-error").hidden=!problem;$("#caption-edit-error").textContent=problem;
  $("#caption-edit-cursor").textContent=`Cursor ${montageTime(cursor)} · duração ${Number.isFinite(d.end-d.start)?precise(d.end-d.start):"—"}`;
  $("#caption-edit-status").textContent=captionSaving?"Salvando…":problem?"A prévia usa as legendas salvas até corrigir os valores.":d.end>project.duration?"A legenda ultrapassa a montagem. Só o trecho dentro do vídeo será exportado.":(captionDraft.styleAll?"Aplicar também padroniza o estilo de todas as legendas. ":"Prévia local. ")+"Texto, tempos e estilo são salvos de uma vez; Cancelar descarta.";
  for(const node of $("#caption-edit-dialog").querySelectorAll("input,textarea,select,button"))node.disabled=captionSaving;
  $("#caption-edit-apply").disabled=captionSaving||!!problem||!captionHasChanges();
  $("#caption-review").disabled=captionSaving||!canPreview;$("#caption-play").disabled=captionSaving||!canPreview||playerLoading;
  $("#caption-play").textContent=playing?"Pausar prévia":"Reproduzir legenda";
  $("#caption-edit-remove").hidden=captionDraft.isNew;$("#caption-edit-remove").disabled=captionSaving||!validCaptionDraft();
  for(const edge of ["start","end"])$("#caption-"+edge+"-here").disabled=captionSaving||!!captionDraftProblem({...d,[edge]:roundTime(cursor)});
  $("#caption-move-here").disabled=captionSaving||!!captionDraftProblem({...d,start:roundTime(cursor),end:roundTime(cursor+d.end-d.start)});
}
function changeCaptionDraft(patch,write=false){
  if(!validCaptionDraft()||captionSaving)return;pause();captionPreviewEnd=null;Object.assign(captionDraft.values,patch);if(write)writeCaptionFields();updateTime();
}
async function openCaptionEdit(id=null){
  await queue;if(!project||!editorFeatures.subtitles||captionSaving)return;
  let saved=id&&(project.captions||[]).find(c=>c.id===id),start=clamp(cursor,0,Math.max(0,project.duration-.1));
  if(id&&!saved)return;
  if(!saved)saved=(project.captions||[]).find(c=>c.start<=start&&start<c.end);
  let values;
  if(saved)values={title_font:"sans",title_size:"medium",title_position:"bottom",...saved};else{
    if(project.duration<.1||(project.captions||[]).length>=500){toast("A montagem precisa de espaço e aceita até 500 legendas.",true);return;}
    const next=(project.captions||[]).filter(c=>c.start>=start).sort((a,b)=>a.start-b.start)[0];
    const end=Math.min(project.duration,start+2,next?.start??1800);
    if(end-start<.09999){toast("Não cabe outra legenda neste instante. Mova o cursor para um espaço livre.",true);return;}
    values={id:crypto.randomUUID().replaceAll("-",""),start:roundTime(start),end:roundTime(end),text:"",title_font:"sans",title_size:"medium",title_position:"bottom"};
  }
  pause();closeSheet();captionPreviewEnd=null;captionDraft={projectId:project.id,revision:project.revision,originalCursor:cursor,isNew:!saved,styleAll:false,baseline:{...values},values};
  selectedCaption=values.id;$("#caption-edit-title").textContent=saved?"Editar legenda":"Nova legenda";$("#caption-edit-note").textContent=saved?"Ajuste esta legenda sem gravar experiências no projeto.":"Comece pelo texto. A legenda só entra no projeto quando você aplicar.";
  $("#caption-style-all").checked=false;writeCaptionFields();$("#caption-edit-dialog").showModal();updateTime();
}
$("#caption-style-all").addEventListener("change",e=>{if(!validCaptionDraft()||captionSaving)return;pause();captionPreviewEnd=null;captionDraft.styleAll=e.target.checked;updateTime();});
for(const key of ["text","start","end"])$("#caption-edit-"+key).addEventListener("input",e=>changeCaptionDraft({[key]:key==="text"?e.target.value:parseMontageTime(e.target.value)??NaN}));
for(const key of ["title_font","title_size","title_position"])$("#caption-edit-"+key).addEventListener("change",e=>changeCaptionDraft({[key]:e.target.value}));
for(const edge of ["start","end"])$("#caption-"+edge+"-here").addEventListener("click",()=>{if(!captionDraft||captionSaving)return;const patch={[edge]:roundTime(cursor)};if(!captionDraftProblem({...captionDraft.values,...patch}))changeCaptionDraft(patch,true);});
$("#caption-move-here").addEventListener("click",()=>{if(!captionDraft||captionSaving)return;const d=captionDraft.values,patch={start:roundTime(cursor),end:roundTime(cursor+d.end-d.start)};if(!captionDraftProblem({...d,...patch}))changeCaptionDraft(patch,true);});
for(const [key,direction] of [["back",-1],["forward",1]])$("#caption-cursor-"+key).addEventListener("click",()=>{if(captionDraft&&!captionSaving){captionPreviewEnd=null;seekTo(frameStep(cursor,direction,project.duration));}});
$("#caption-review").addEventListener("click",()=>{if(!validCaptionDraft()||captionSaving||captionDraftProblem()||captionDraft.values.start>=project.duration)return;captionPreviewEnd=null;const d=captionDraft.values;seekTo((d.start+Math.min(d.end,project.duration))/2);$("#expand-preview").click();});
$("#caption-play").addEventListener("click",()=>{
  if(!validCaptionDraft()||captionSaving||captionDraftProblem()||captionDraft.values.start>=project.duration)return;
  if(playing){captionPreviewEnd=null;pause();updateCaptionControls();return;}
  seekTo(captionDraft.values.start);captionPreviewEnd=Math.min(captionDraft.values.end,project.duration);play();updateCaptionControls();
});
function stopCaptionPlayback(){
  if(captionPreviewEnd===null||cursor<captionPreviewEnd-1/30)return false;
  const end=captionPreviewEnd,start=captionDraft?.values.start??0;captionPreviewEnd=null;pause();seekTo(Math.max(start,end-1/30));return true;
}
$("#caption-edit-dialog").addEventListener("cancel",e=>{if(captionSaving)e.preventDefault();});
$("#caption-edit-dialog").addEventListener("close",()=>{const original=captionDraft?.originalCursor;pause();captionPreviewEnd=null;captionDraft=null;if(original!==undefined)seekTo(original);else updateTime();});
async function saveCaptionDraft(remove=false){
  await queue;if(captionSaving||!validCaptionDraft()||(remove?captionDraft.isNew:captionDraftProblem()||!captionHasChanges()))return;
  const draft=captionDraft;captionSaving=true;pause();captionPreviewEnd=null;updateCaptionControls();
  const args=remove?{caption_id:draft.values.id}:draft.styleAll?{captions:captionPreviewItems()}:draft.isNew?{...draft.values}:{caption_id:draft.values.id,...Object.fromEntries(Object.entries(draft.values).filter(([key])=>key!=="id"))};
  try{const ok=await mutate(remove?"caption_remove":draft.styleAll?"captions_replace":draft.isNew?"caption_add":"caption_update",args,remove?"Legenda removida. Você pode desfazer.":"Legenda salva. Você pode desfazer pela linha do tempo.");if(ok){captionDraft=null;$("#caption-edit-dialog").close();}}
  finally{captionSaving=false;updateCaptionControls();}
}
$("#caption-edit-apply").addEventListener("click",()=>saveCaptionDraft());
$("#caption-edit-remove").addEventListener("click",()=>saveCaptionDraft(true));

$("#audio-reset-range").addEventListener("click",()=>{
  if(!validAudioDraft()||audioSaving||(audioDraft.kind!=="music"&&!editorFeatures.narration_trim))return;
  pause();audioDraft.values.start=0;audioDraft.values.end=audioDraft.asset.duration;writeAudioFields();updateTime();
});
