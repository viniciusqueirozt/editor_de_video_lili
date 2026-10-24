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
  if(!timelineGesture)$("#timeline-hint").textContent="Clique na régua para posicionar o cursor. Arraste as bordas do clipe para aparar.";
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
trackCanvas.addEventListener("pointerdown",e=>{
  if(e.button!==0||!project?.timeline.length||e.target.closest("button")) return;
  pause();timelineGesture={type:"seek",pointerId:e.pointerId};
  trackCanvas.setPointerCapture(e.pointerId);seekTo(pointerTime(e));
});
trackCanvas.addEventListener("pointermove",e=>{
  if(timelineGesture?.type==="seek"&&e.pointerId===timelineGesture.pointerId)seekTo(pointerTime(e));
});
function endScrub(e){if(timelineGesture?.type==="seek"&&e.pointerId===timelineGesture.pointerId){timelineGesture=null;if(trackCanvas.hasPointerCapture(e.pointerId))trackCanvas.releasePointerCapture(e.pointerId);}}
trackCanvas.addEventListener("pointerup",endScrub);trackCanvas.addEventListener("pointercancel",endScrub);

function beginTrim(e){
  if(e.button!==0||timelineGesture)return;
  e.preventDefault();e.stopPropagation();pause();
  const handle=e.currentTarget,node=handle.closest("[data-clip]"),c=project.timeline.find(c=>c.id===node.dataset.clip);
  if(c.locked)return;
  selected=c.id;markSelection();updatePlayer(false,before());
  timelineGesture={type:"trim",clip:{...c},edge:handle.dataset.edge,x:e.clientX,pointerId:e.pointerId,node,revision:project.revision,changed:null};
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
  const minimum=Math.max(.1,(c.fade_in||0)+(c.fade_out||0))*speed;
  const asset=assetFor(c), value=roundTime(edge==="start"?clamp(c.start+delta,0,c.end-minimum):clamp(c.end+delta,c.start+minimum,asset.duration));
  gesture.changed={[edge]:value};
  const start=edge==="start"?value:c.start, end=edge==="end"?value:c.end;
  const width=(end-start)/speed*timelineScale;
  gesture.node.style.width=`${width}px`;
  // In trim preview, reveal the moving source edge; ripple settles on save.
  gesture.node.style.left=`${(before()+(edge==="start"?(start-c.start)/speed:0))*timelineScale}px`;
  $("#clip-start").value=start;$("#clip-end").value=end;
  $("#timeline-hint").textContent=`Entrada ${precise(start)} → saída ${precise(end)} · duração ${precise((end-start)/speed)}`;
  if(player.readyState>=1&&loadedSource===assetUrl(asset))player.currentTime=edge==="start"?start:Math.max(start,end-.033);
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
    cursor=before();mutate("clip_update",{clip_id:gesture.clip.id,...gesture.changed},"Corte ajustado e salvo.");
  }else{renderTimeline();seekTo(cursor);}
}
function cancelTrim(e){clearTrim(e.currentTarget);timelineGesture=null;renderTimeline();seekTo(cursor);}

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
  if(e.key==="ArrowLeft"||e.key==="ArrowRight"){
    e.preventDefault();seekTo(cursor+(e.key==="ArrowLeft"?-1:1)*(e.shiftKey?1:1/30));
  }else if(e.key==="Home"){e.preventDefault();seekTo(0);}
  else if(e.key==="End"){e.preventDefault();seekTo(project.duration);}
});
document.addEventListener("keydown",e=>{
  if(/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)||document.querySelector("dialog[open]"))return;
  if(e.key.toLowerCase()==="s"&&!e.ctrlKey&&!e.metaKey){e.preventDefault();$("#split-button").click();}
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="z"){e.preventDefault();if(project?.undo_available)mutate("undo",{},"Última alteração desfeita.");}
});
let resizeFrame=0;
new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(project&&!timelineGesture)renderTimeline();});}).observe(trackScroll);
