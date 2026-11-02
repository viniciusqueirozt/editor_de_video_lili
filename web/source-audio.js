"use strict";
// Legacy audio stays attached until an explicit edit. New insertions detach atomically.
function sourceAudioTracks(p){
  const result=(p.audio_clips||[]).map(a=>({...a}));let offset=0;
  for(const clip of p.timeline){
    const asset=p.media.find(a=>a.id===clip.media_id);
    if(!clip.audio_detached&&asset?.has_audio)result.push({id:"linked-"+clip.id,source_clip_id:clip.id,linked:true,media_id:clip.media_id,start:clip.start,end:clip.end,speed:clip.speed||1,offset,volume:clip.volume,fade_in:clip.audio_fade_in||0,fade_out:clip.audio_fade_out||0,label:clip.label,locked:!!clip.locked});
    offset+=clipDuration(clip);
  }
  return result;
}
function findSourceAudio(p,id){return sourceAudioTracks(p).find(a=>a.id===id);}
const sourcePlayers=new Map();
function pauseSourceAudio(){for(const sound of sourcePlayers.values())sound.pause();}
function sourceDraftMutesVideo(id){return typeof audioDraft!=="undefined"&&audioDraft?.kind==="source"&&audioDraft.baseline.linked&&audioDraft.baseline.source_clip_id===id&&validAudioDraft()&&!audioDraftProblem();}
function sourceAudioForPlayback(){
  const tracks=sourceAudioTracks(project),draft=typeof audioDraft!=="undefined"&&audioDraft?.kind==="source"&&validAudioDraft()&&!audioDraftProblem()?audioDraft:null;
  return tracks.map(a=>draft?.baseline.id===a.id?draft.values:a).filter(a=>!a.linked||draft?.baseline.id===a.id);
}
function syncSourceAudio(){
  if(!project||!playing||playerLoading||player.seeking||player.paused){pauseSourceAudio();return;}
  const active=new Set();
  for(const track of sourceAudioForPlayback()){
    const range=audioRange(track,0),local=cursor-track.offset;
    if(local<0||local>=range.length)continue;
    const key=project.id+"/"+track.id,asset=project.media.find(a=>a.id===track.media_id);if(!asset)continue;
    active.add(key);let sound=sourcePlayers.get(key);
    if(!sound){sound=new Audio();sound.preload="metadata";sound.src=assetUrl(asset);sourcePlayers.set(key,sound);}
    sound.volume=voiceGain(track,local,range.length);sound.playbackRate=track.speed||1;sound.preservesPitch=true;
    if(sound.readyState<1){sound.onloadedmetadata=()=>{sound.onloadedmetadata=null;if(playing)syncSourceAudio();};continue;}
    const time=range.start+local*(track.speed||1);
    if(sound.readyState>=1&&Math.abs(sound.currentTime-time)>.12)sound.currentTime=time;
    if(sound.paused)sound.play().catch(()=>{});
  }
  for(const [key,sound]of sourcePlayers)if(!active.has(key))sound.pause();
}
function renderSourceAudioTrack(){
  const track=$("#source-audio-track"),label=$("#source-audio-label"),supported=!!editorFeatures.source_audio_clips;
  track.hidden=label.hidden=!supported;if(!supported)return;
  const sounds=sourceAudioTracks(project),allowed=new Set(sounds.map(a=>project.id+"/"+a.id)),lanes=[],visible=[];
  for(const [key,sound]of sourcePlayers)if(!allowed.has(key)){sound.pause();sound.onloadedmetadata=null;sound.removeAttribute("src");sound.load();sourcePlayers.delete(key);}
  for(const sound of [...sounds].sort((a,b)=>a.offset-b.offset)){
    const length=Math.max(0,Math.min(audioRange(sound,0).length,project.duration-sound.offset));if(!length)continue;
    let row=lanes.findIndex(end=>end<=sound.offset+.00001);if(row<0)row=lanes.length;
    lanes[row]=sound.offset+length;visible.push({sound,length,row});
  }
  const height=Math.max(50,lanes.length*50),viewport=Math.min(200,height);
  track.style.height=label.style.height=viewport+"px";
  track.innerHTML=`<div class="source-audio-content" style="height:${height}px">`+visible.map(({sound,length,row})=>`<button type="button" class="audio-region source-region has-move ${sound.linked?"linked":""}" id="source-region-${sound.id}" data-source-edit="${sound.id}" style="left:${sound.offset*timelineScale}px;top:${row*50+3}px;width:${length*timelineScale}px" aria-label="Editar som original: ${esc(sound.label)}"><svg id="source-wave-${sound.id}" preserveAspectRatio="none" aria-hidden="true"></svg><span>${sound.locked?icon("lock"):icon("mic")}${esc(sound.label)}</span></button><button type="button" class="audio-move-handle source-move-handle" data-source-move="${sound.id}" id="source-move-${sound.id}" style="left:${sound.offset*timelineScale}px;top:${row*50+3}px" aria-label="Mover som original: ${esc(sound.label)}" ${sound.locked||audioMoveSaving?"disabled":""}>↔</button>`).join("")+(visible.length?"":`<button type="button" class="add-voice-track" id="source-audio-empty">${sounds.length?"Som fora do vídeo · ajustar":"O som dos vídeos aparece aqui ao adicionar uma cena."}</button>`)+"</div>";
  for(const button of track.querySelectorAll("[data-source-edit]"))button.addEventListener("click",()=>{if(!suppressAudioClick&&!audioMoveSaving&&!timelineGesture)openAudioEdit("source",button.dataset.sourceEdit);});
  for(const handle of track.querySelectorAll("[data-source-move]")){
    handle.addEventListener("click",()=>{if(!suppressAudioClick&&!audioMoveSaving&&!timelineGesture)openAudioEdit("source",handle.dataset.sourceMove);});
    handle.addEventListener("pointerdown",e=>beginAudioMove(e,"source",handle.dataset.sourceMove));handle.addEventListener("pointermove",moveAudio);handle.addEventListener("pointerup",finishAudioMove);handle.addEventListener("pointercancel",cancelAudioMove);handle.addEventListener("lostpointercapture",cancelAudioMove);
  }
  $("#source-audio-empty")?.addEventListener("click",()=>{if(sounds.length)openAudioEdit("source",sounds[0].id);});
  const pid=project.id,revision=project.revision;
  for(const {sound,length}of visible){const asset=project.media.find(a=>a.id===sound.media_id);if(!asset)continue;getAudioWaveform(asset).then(data=>{const node=$("#source-wave-"+sound.id);if(project?.id===pid&&project.revision===revision&&node)drawAudioWaveform(node,data,sound.start,length*(sound.speed||1));}).catch(()=>{});}
}
async function sourceAudioAction(action){
  await queue;if(audioSaving||!validAudioDraft()||audioDraft.kind!=="source"||audioDraft.baseline.locked)return;
  if(action!=="remove"&&(audioEditChanged()||audioDraftProblem()))return;
  const draft=audioDraft,track=draft.baseline,args=track.linked?{clip_id:track.source_clip_id,then:action}:{audio_id:track.id};
  if(action==="split")args.at=roundTime(track.start+(cursor-track.offset)*(track.speed||1));
  audioSaving=true;pause();updateAudioControls();
  try{const ok=await mutate(track.linked?"audio_detach":"audio_clip_"+action,args,"Áudio ajustado. A imagem foi preservada.",{projectId:draft.projectId,revision:draft.revision});if(ok){audioDraft=null;$("#audio-edit-dialog").close();}}
  finally{audioSaving=false;updateAudioControls();}
}
for(const action of ["split","duplicate","remove"])$("#source-audio-"+action).addEventListener("click",()=>sourceAudioAction(action));
$("#source-audio-speed").addEventListener("input",e=>{if(validAudioDraft()&&audioDraft.kind==="source"&&!audioSaving){pause();audioDraft.values.speed=Number(e.target.value);updateTime();}});
$("#source-audio-lock").addEventListener("change",e=>{if(validAudioDraft()&&audioDraft.kind==="source"&&!audioSaving){pause();audioDraft.values.locked=e.target.checked;updateTime();}});
$("#source-audio-picker").addEventListener("change",e=>{if(!audioDraft||audioSaving)return;if(audioEditChanged()){e.target.value=audioDraft.baseline.id;toast("Aplique ou cancele os ajustes antes de trocar de bloco.");return;}openAudioEdit("source",e.target.value);});
