/* Explicit, reversible subtitle proposals using the existing captions_replace API. */
let captionToolsDraft=null,captionToolsSaving=false;
function captionToolsProblem(){
  if(!captionToolsDraft||!project||project.id!==captionToolsDraft.projectId||project.revision!==captionToolsDraft.revision)return "O projeto mudou. Feche este painel e abra novamente.";
  return "";
}
function captionToolsProposal(){
  const problem=captionToolsProblem();if(problem)throw Error(problem);
  const d=captionToolsDraft,rows=d.captions,limit=Math.min(1800,project.duration),op=$("#caption-tools-action").value;
  if(op==="split"){
    const at=parseMontageTime($("#caption-tools-at").value);
    return LiliCaptionTools.split(rows,d.captionId,at,$("#caption-tools-first").value,$("#caption-tools-second").value,d.newId,limit);
  }
  if(op==="merge")return LiliCaptionTools.merge(rows,d.captionId,limit);
  if(op!=="shift")throw Error("Escolha uma ação disponível.");
  const value=parseMontageTime($("#caption-tools-offset").value);
  if(!Number.isFinite(value)||value<=0)throw Error("Informe quanto as legendas devem se deslocar.");
  return LiliCaptionTools.shift(rows,value*($("#caption-tools-direction").value==="before"?-1:1),limit);
}
function updateCaptionTools(){
  if(!captionToolsDraft)return;
  const op=$("#caption-tools-action").value;
  for(const kind of ["split","merge","shift"])$("#caption-tools-"+kind).hidden=kind!==op;
  let error="",rows=[];
  try{rows=captionToolsProposal();}catch(e){error=e.message;}
  $("#caption-tools-error").textContent=error;$("#caption-tools-error").hidden=!error;
  const changed=rows.filter(c=>{const old=captionToolsDraft.captions.find(x=>x.id===c.id);return !old||old.start!==c.start||old.end!==c.end||old.text!==c.text;});
  $("#caption-tools-summary").textContent=error?"Ajuste os valores para ver a proposta.":op==="shift"?rows.length+" legenda(s) serão deslocadas. Vídeo, voz e música permanecem nas suas posições.":op==="merge"?"Mantém a entrada da primeira, a saída da próxima e o estilo da primeira. O intervalo entre elas também ficará legendado.":"Cada parte mantém o estilo. Confira o texto e o instante da divisão.";
  const preview=$("#caption-tools-preview");preview.replaceChildren();
  for(const c of changed.slice(0,8)){
    const item=document.createElement("li"),time=document.createElement("span"),text=document.createElement("p");
    time.textContent=montageTime(c.start)+" → "+montageTime(c.end);text.textContent=c.text;item.append(time,text);preview.append(item);
  }
  if(changed.length>8){const more=document.createElement("li");more.textContent="E mais "+(changed.length-8)+" legenda(s).";preview.append(more);}
  for(const node of $("#caption-tools-dialog").querySelectorAll("input,textarea,select,button"))node.disabled=captionToolsSaving;
  $("#caption-tools-apply").disabled=captionToolsSaving||!!error;
  $("#caption-tools-status").textContent=captionToolsSaving?"Salvando…":"Aplicar grava uma única alteração. Você pode desfazer pela linha do tempo.";
}
async function openCaptionTools(){
  await queue;
  if(captionToolsSaving||!project||!validCaptionDraft()||captionDraft.isNew)return;
  if(captionHasChanges()){toast("Aplique ou cancele os ajustes da legenda antes de organizar os blocos.",true);return;}
  const c=project.captions.find(x=>x.id===captionDraft.values.id),position=cursor,caret=$("#caption-edit-text").selectionStart;
  if(!c)return;
  const firstPosition=position>=c.start+.1&&position<=c.end-.1?position:(c.start+c.end)/2;
  const [first,second]=LiliCaptionTools.splitText(c.text,caret);
  const draft={projectId:project.id,revision:project.revision,captionId:c.id,newId:crypto.randomUUID().replaceAll("-",""),captions:project.captions.map(c=>({...c})),originalCursor:position};
  pause();$("#caption-edit-dialog").close();captionToolsDraft=draft;
  $("#caption-tools-action").value="split";$("#caption-tools-at").value=montageTime(firstPosition);
  $("#caption-tools-first").value=first;$("#caption-tools-second").value=second;
  $("#caption-tools-offset").value="0.5";$("#caption-tools-direction").value="after";
  $("#caption-tools-dialog").showModal();updateCaptionTools();
}
$("#caption-organize").addEventListener("click",()=>openCaptionTools());
for(const id of ["action","at","first","second","offset","direction"])$("#caption-tools-"+id).addEventListener(["action","direction"].includes(id)?"change":"input",updateCaptionTools);
$("#caption-tools-middle").addEventListener("click",()=>{
  if(captionToolsSaving||captionToolsProblem())return;
  const c=captionToolsDraft.captions.find(c=>c.id===captionToolsDraft.captionId);
  $("#caption-tools-at").value=montageTime((c.start+c.end)/2);updateCaptionTools();
});
$("#caption-tools-cursor").addEventListener("click",()=>{
  if(captionToolsSaving||captionToolsProblem())return;
  $("#caption-tools-at").value=montageTime(captionToolsDraft.originalCursor);updateCaptionTools();
});
$("#caption-tools-dialog").addEventListener("cancel",e=>{if(captionToolsSaving)e.preventDefault();});
$("#caption-tools-dialog").addEventListener("close",()=>{
  const d=captionToolsDraft;captionToolsDraft=null;
  if(d&&project?.id===d.projectId)seekTo(Math.min(d.originalCursor,project.duration));
});
$("#caption-tools-apply").addEventListener("click",async()=>{
  if(captionToolsSaving||!captionToolsDraft)return;
  const draft=captionToolsDraft;
  await queue;
  if(captionToolsSaving||captionToolsDraft!==draft||captionToolsProblem()){updateCaptionTools();return;}
  let captions;try{captions=captionToolsProposal();}catch(e){updateCaptionTools();return;}
  captionToolsSaving=true;pause();updateCaptionTools();
  try{
    const ok=await mutate("captions_replace",{captions},"Legendas ajustadas. Você pode desfazer.",{projectId:draft.projectId,revision:draft.revision});
    if(ok){$("#caption-tools-dialog").close();openInspector("captions");}
  }finally{captionToolsSaving=false;updateCaptionTools();}
});
