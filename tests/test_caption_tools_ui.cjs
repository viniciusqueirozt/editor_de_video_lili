const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),crypto=require("node:crypto");
const model=require("../web/caption-tools.js"),nodes=new Map(),commands=[],toasts=[];
let changed=false,fail=false;
function element(id=""){
 return {id,listeners:{},children:[],hidden:false,disabled:false,value:"",textContent:"",selectionStart:0,open:false,
 addEventListener(k,f){this.listeners[k]=f;},replaceChildren(){this.children=[];},append(...items){this.children.push(...items);},
 querySelectorAll(){return[];},showModal(){this.open=true;},close(){this.open=false;this.listeners.close?.();}};
}
const $=id=>{if(!nodes.has(id))nodes.set(id,element(id));return nodes.get(id);};
const a={id:"a".repeat(32),start:.2,end:1.2,text:"Olá Cora",title_font:"serif",title_size:"medium",title_position:"bottom"};
const b={...a,id:"b".repeat(32),start:1.5,end:2.5,text:"Outro passeio"};
const original={id:"p",revision:1,duration:5,captions:[a,b],timeline:[{id:"clip",start:0,end:5}],narration:{offset:0},music:{offset:1}};
const clone=x=>JSON.parse(JSON.stringify(x));
const c=vm.createContext({$: $,crypto,LiliCaptionTools:model,project:clone(original),captionDraft:{isNew:false,values:a},cursor:.7,queue:Promise.resolve(),
 document:{createElement:()=>element()},validCaptionDraft(){return !!c.captionDraft&&c.captionDraft.values.id===a.id;},captionHasChanges(){return changed;},pause(){},
 toast(msg){toasts.push(msg);},openInspector(){},seekTo(t){c.cursor=t;},montageTime:n=>Number(n).toFixed(3),parseMontageTime:n=>n.trim()&&!isNaN(Number(n))?Number(n):null,
 async mutate(op,args,msg,expected){commands.push({op,args,expected});if(fail)return false;assert.deepEqual(clone(expected),{projectId:"p",revision:c.project.revision});c.project.captions=clone(args.captions);c.project.revision++;return true;}
});
$("#caption-edit-dialog").addEventListener("close",()=>{c.captionDraft=null;});
vm.runInContext(fs.readFileSync("web/caption-tools-ui.js","utf8"),c);
const run=code=>vm.runInContext(code,c),click=key=>$("#caption-tools-"+key).listeners.click();
const reopen=async()=>{c.captionDraft={isNew:false,values:a};await c.openCaptionTools();};
(async()=>{
 await reopen();assert.equal($("#caption-tools-dialog").open,true);assert.equal(commands.length,0);assert.equal($("#caption-tools-apply").disabled,false);
 $("#caption-tools-first").value="<b>Olá</b>";c.updateCaptionTools();assert.equal($("#caption-tools-preview").children[0].children[1].textContent,"<b>Olá</b>");
 $("#caption-tools-dialog").close();assert.deepEqual(c.project,original,"cancel never changes saved project");
 changed=true;await reopen();assert.equal($("#caption-tools-dialog").open,false);assert.match(toasts.at(-1),/Aplique ou cancele/);changed=false;
 await reopen();$("#caption-tools-at").value=".21";c.updateCaptionTools();assert.equal($("#caption-tools-apply").disabled,true);await click("apply");assert.equal(commands.length,0);
 $("#caption-tools-middle").listeners.click();await Promise.all([click("apply"),click("apply")]);assert.equal(commands.length,1);assert.equal(commands[0].op,"captions_replace");assert.equal(c.project.captions.length,3);
 assert.deepEqual(c.project.timeline,original.timeline);assert.deepEqual(c.project.music,original.music);assert.deepEqual(c.project.narration,original.narration);
 c.project=clone(original);await reopen();$("#caption-tools-action").value="merge";c.updateCaptionTools();await click("apply");assert.equal(c.project.captions[0].text,"Olá Cora Outro passeio");assert.equal(c.project.captions[0].title_font,"serif");
 c.project=clone(original);await reopen();$("#caption-tools-action").value="shift";$("#caption-tools-offset").value=".3";$("#caption-tools-direction").value="before";c.updateCaptionTools();assert.equal($("#caption-tools-apply").disabled,true);
 $("#caption-tools-direction").value="after";fail=true;await click("apply");assert.equal($("#caption-tools-dialog").open,true);assert.deepEqual(c.project,original);assert.equal(run("captionToolsSaving"),false);fail=false;
 const count=commands.length;c.project.revision++;await click("apply");assert.equal(commands.length,count);assert.match($("#caption-tools-error").textContent,/projeto mudou/);
 $("#caption-tools-dialog").close();c.project=clone(original);await reopen();c.project={...c.project,id:"other"};await click("apply");assert.equal(commands.length,count,"project switch must not submit");
 $("#caption-tools-dialog").close();c.project=clone(original);await reopen();$("#caption-tools-action").value="shift";$("#caption-tools-offset").value=".25";await click("apply");
 assert.equal(c.project.captions[0].start,.45);assert.equal(c.project.captions[1].end,2.75);
 console.log("Caption UI: proposals, cancel, literal text, unsaved guard, atomic apply, double-click, failure and stale/project guards passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
