"use strict";
const $=s=>document.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const bin='<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/></svg>';
let active=[],trashed=[],inTrash=location.hash==="#trash",pendingDelete=null,pendingPurge=null,messageTimer;
function readPref(key,fallback){try{return localStorage.getItem(key)||fallback;}catch{return fallback;}}
function savePref(key,value){try{localStorage.setItem(key,value);return true;}catch{message("O navegador não permitiu salvar a preferência.",true);return false;}}
let view=readPref("lili-home-view","grid"),sort=readPref("lili-home-sort","recent");
if(!["grid","list"].includes(view))view="grid";if(!["recent","name"].includes(sort))sort="recent";
async function api(path,options={}){
 const r=await fetch(path,{...options,headers:{"Content-Type":"application/json",...options.headers}});
 if(r.status===401){location.assign("/auth/login");throw new Error("Entre novamente para continuar.");}
 const data=await r.json().catch(()=>({error:"O estúdio não respondeu. Verifique a conexão do notebook."}));
 if(!r.ok)throw new Error(data.error||"Não foi possível concluir.");return data;
}
function message(text,error=false){clearTimeout(messageTimer);$("#home-message").textContent=text;$("#home-message").className=error?"error":"";$("#home-message").hidden=false;messageTimer=setTimeout(()=>$("#home-message").hidden=true,error?8500:4500);}
function editorUrl(p,ai=false){return `/editor?project=${encodeURIComponent(p.id)}${ai?"&panel=ai":""}`;}
function stamp(p){return new Date(p.updated_at).toLocaleDateString("pt-BR",{day:"2-digit",month:"short"});}
function length(seconds){return `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,"0")}`;}
const QUICK_ACTIONS=[
 {panel:"media",title:"Importar arquivos",description:"Traga vídeos, fotos e sons para a biblioteca.",symbol:"+"},
 {panel:"transitions",title:"Ajustar transições",description:"Escolha o corte e experimente o encontro das cenas.",symbol:"⋈"},
 {panel:"captions",title:"Revisar legendas",description:"Ajuste textos e tempos ou importe um arquivo SRT.",symbol:"T"},
 {panel:"export",title:"Preparar entrega",description:"Confira qualidade, avisos e vídeos já exportados.",symbol:"↗"}
];
let quickProjectId="";
function renderQuickActions(fallback=null){
 const target=active.find(p=>p.id===quickProjectId)||fallback||active.find(p=>p.id===readPref("lili-project",""))||active[0];
 const section=$("#quick-actions");section.hidden=!target;
 if(!target){quickProjectId="";$("#quick-action-grid").innerHTML="";$("#quick-project").innerHTML="";return;}
 quickProjectId=target.id;
 $("#quick-project").innerHTML=active.map(p=>`<option value="${esc(p.id)}" ${p.id===target.id?"selected":""}>${esc(p.name)}</option>`).join("");
 $("#quick-project-note").textContent=`Ferramentas para ${target.name}. Abrir um atalho não altera a montagem.`;
 $("#quick-action-grid").innerHTML=QUICK_ACTIONS.map(action=>`<a class="quick-action" href="${editorUrl(target)}&panel=${action.panel}"><span aria-hidden="true">${action.symbol}</span><strong>${action.title}</strong><small>${action.description}</small></a>`).join("");
}
$("#quick-project").addEventListener("change",e=>{quickProjectId=e.target.value;renderQuickActions();});
function renderProjects(){
 $("#project-total").textContent=active.length;
 $("#project-trash-count").textContent=trashed.length?`(${trashed.length})`:"";
 $("#show-active").setAttribute("aria-pressed",String(!inTrash));$("#show-trash").setAttribute("aria-pressed",String(inTrash));$("#trash-explanation").hidden=!inTrash;
 const search=$("#project-search").value.trim().toLocaleLowerCase("pt-BR");
 const source=inTrash?trashed:active;
 const items=source.filter(p=>p.name.toLocaleLowerCase("pt-BR").includes(search)).sort((a,b)=>sort==="name"?a.name.localeCompare(b.name,"pt-BR"):b.updated_at.localeCompare(a.updated_at));
 $("#project-grid").className=`project-grid ${view==="list"?"list":""}`;
 $("#project-grid").innerHTML=items.map(p=>{
  const picture=!inTrash&&p.thumbnail_id?`<img src="/api/projects/${p.id}/media/${p.thumbnail_id}/thumbnail" alt="" loading="lazy">`:'<span aria-hidden="true">l.</span>';
  const preview=`${picture}<small>${length(p.duration||0)} · ${p.media_count||0} arquivo(s)</small>`;
  return `<article class="project-card">${inTrash?`<div class="project-preview">${preview}</div>`:`<a class="project-preview" href="${editorUrl(p)}" aria-label="Abrir projeto ${esc(p.name)}">${preview}</a>`}<div class="project-info"><div><h3>${inTrash?esc(p.name):`<a href="${editorUrl(p)}">${esc(p.name)}</a>`}</h3><p>${inTrash?"Na Lixeira":"Editado"} · ${stamp(p)}</p></div>${inTrash?"":`<button class="card-delete" data-delete="${p.id}" aria-label="Excluir projeto ${esc(p.name)}" title="Excluir projeto">${bin}</button>`}</div>${inTrash?`<div class="trash-actions"><button class="button secondary restore" data-restore="${p.id}">Restaurar</button><button class="button danger purge" data-purge="${p.id}">Excluir permanentemente</button></div>`:""}</article>`;
 }).join("")||`<div class="empty"><strong>${search?"Nenhum projeto encontrado.":inTrash?"A Lixeira está vazia.":"Sua próxima história começa aqui."}</strong>${search?"Tente outro nome.":inTrash?"Projetos excluídos aparecerão aqui para restauração.":"Toque em Novo projeto para trazer suas gravações."}</div>`;
 $("#project-grid").querySelectorAll("[data-delete]").forEach(b=>b.addEventListener("click",()=>{
  const p=active.find(p=>p.id===b.dataset.delete);if(!p)return;
  pendingDelete={id:p.id,revision:p.revision};$("#remove-project-name").textContent=p.name;$("#remove-project-dialog").showModal();
 }));
 $("#project-grid").querySelectorAll("[data-restore]").forEach(b=>b.addEventListener("click",async()=>{
  const p=trashed.find(p=>p.id===b.dataset.restore);if(!p)return;b.disabled=true;
  try{await api(`/api/projects/${p.id}/restore`,{method:"POST",body:JSON.stringify({expected_revision:p.revision})});await loadProjects();message("Projeto restaurado com a montagem e os arquivos.");}catch(e){message(e.message,true);b.disabled=false;}
 }));
 $("#project-grid").querySelectorAll("[data-purge]").forEach(b=>b.addEventListener("click",()=>{
  const p=trashed.find(p=>p.id===b.dataset.purge);if(!p)return;
  pendingPurge={id:p.id,revision:p.revision};$("#purge-project-name").textContent=p.name;
  $("#purge-confirmation").value="";$("#purge-project-submit").disabled=true;$("#purge-project-dialog").showModal();
 }));
 const saved=readPref("lili-project","");const last=active.find(p=>p.id===saved)||active[0];
 renderQuickActions(last);
 for(const id of ["continue-project","ai-last-project"]){const a=$("#"+id);a.hidden=!last;if(last)a.href=editorUrl(last,id==="ai-last-project");}
}
async function loadProjects(){[active,trashed]=await Promise.all([api("/api/projects"),api("/api/projects?trash=1")]);renderProjects();}
async function health(){try{await api("/api/health");$("#connection-dot").className="online";$("#connection-label").textContent="Estúdio conectado";}catch{$("#connection-dot").className="";$("#connection-label").textContent="Notebook desconectado";}}
function showPage(name,updateHash=true){
 if(!["projects","ai","connection","settings"].includes(name))name="projects";
 for(const page of document.querySelectorAll(".page"))page.hidden=page.id!=="page-"+name;
 for(const b of document.querySelectorAll("[data-page]")){if(b.dataset.page===name)b.setAttribute("aria-current","page");else b.removeAttribute("aria-current");}
 $("#breadcrumb").textContent="Estúdio / "+({projects:"Projetos",ai:"Edição com IA",connection:"Conexão",settings:"Preferências"}[name]);
 if(updateHash)history.replaceState(null,"",name==="projects"?(inTrash?"#trash":"#projects"):"#"+name);
 window.scrollTo(0,0);
 if(name==="ai")api("/api/ai/status").then(s=>$("#ai-status").textContent=s.available?"Codex encontrado no notebook. Login e limites serão conferidos ao editar.":"Codex não encontrado. A edição manual continua disponível.").catch(e=>$("#ai-status").textContent=e.message);
}
document.querySelectorAll("[data-page]").forEach(b=>b.addEventListener("click",()=>showPage(b.dataset.page)));
document.querySelectorAll("[data-new]").forEach(b=>b.addEventListener("click",()=>$("#create-dialog").showModal()));
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>b.closest("dialog").close()));
$("#project-search").addEventListener("input",renderProjects);
$("#refresh-projects").addEventListener("click",async()=>{try{await loadProjects();message("Projetos atualizados.");}catch(e){message(e.message,true);}});
function changeTrash(value){inTrash=value;history.replaceState(null,"",value?"#trash":"#projects");renderProjects();}
$("#show-active").addEventListener("click",()=>changeTrash(false));$("#show-trash").addEventListener("click",()=>changeTrash(true));
$("#settings-trash").addEventListener("click",()=>{inTrash=true;renderProjects();showPage("projects");});
$("#create-form").addEventListener("submit",async e=>{
 e.preventDefault();$("#create-submit").disabled=true;
 try{const name=$("#create-name").value.trim();if(!name)throw new Error("Dê um nome ao projeto.");const p=await api("/api/projects",{method:"POST",body:JSON.stringify({name,script:$("#create-script").value})});location.assign(editorUrl(p));}catch(error){message(error.message,true);$("#create-submit").disabled=false;}
});
$("#remove-project-form").addEventListener("submit",async e=>{
 e.preventDefault();if(!pendingDelete)return;$("#remove-project-submit").disabled=true;
 try{const p=pendingDelete;await api(`/api/projects/${p.id}/trash`,{method:"POST",body:JSON.stringify({expected_revision:p.revision})});$("#remove-project-dialog").close();await loadProjects();message("Projeto movido para a Lixeira. Você pode restaurá-lo.");}
 catch(error){$("#remove-project-dialog").close();message(error.message+" Atualize a lista antes de confirmar novamente.",true);await loadProjects().catch(()=>{});}
 finally{$("#remove-project-submit").disabled=false;pendingDelete=null;}
});
$("#project-view").value=view;$("#project-sort").value=sort;
function preferencesChanged(){view=$("#project-view").value;sort=$("#project-sort").value;const saved=savePref("lili-home-view",view)&&savePref("lili-home-sort",sort);renderProjects();$("#preferences-saved").textContent=saved?"Preferências salvas neste navegador.":"Não foi possível salvar neste navegador.";}
$("#project-view").addEventListener("change",preferencesChanged);$("#project-sort").addEventListener("change",preferencesChanged);$("#reset-preferences").addEventListener("click",()=>{$("#project-view").value="grid";$("#project-sort").value="recent";preferencesChanged();});
$("#connection-type").textContent=location.protocol==="https:"?"Acesso remoto protegido por HTTPS":"Acesso local no notebook";$("#current-address").textContent=location.origin;
window.addEventListener("hashchange",()=>{inTrash=location.hash==="#trash";showPage(location.hash.slice(1),false);renderProjects();});
showPage(inTrash?"projects":location.hash.slice(1)||"projects",false);
loadProjects().catch(e=>{$("#project-grid").innerHTML='<div class="empty"><strong>Não foi possível carregar os projetos.</strong>Confira a conexão e toque em Atualizar projetos.</div>';message(e.message,true);});health();setInterval(()=>{if(!document.hidden)health();},15000);
api("/auth/status").then(s=>$("#home-logout").hidden=!s.authenticated).catch(()=>{});
if("serviceWorker" in navigator&&window.isSecureContext)navigator.serviceWorker.register("/sw.js").catch(()=>{});

$("#purge-confirmation").addEventListener("input",()=>{$("#purge-project-submit").disabled=$("#purge-confirmation").value!=="EXCLUIR";});
$("#purge-project-form").addEventListener("submit",async e=>{
 e.preventDefault();if(!pendingPurge||$("#purge-confirmation").value!=="EXCLUIR")return;
 $("#purge-project-submit").disabled=true;
 try{const p=pendingPurge;await api(`/api/projects/${p.id}/purge`,{method:"POST",body:JSON.stringify({expected_revision:p.revision,confirmation:$("#purge-confirmation").value})});$("#purge-project-dialog").close();await loadProjects();message("Projeto excluído permanentemente. Arquivos locais removidos.");}
 catch(error){$("#purge-project-dialog").close();message(error.message+" Atualize e revise antes de tentar novamente.",true);await loadProjects().catch(()=>{});}
 finally{pendingPurge=null;}
});
