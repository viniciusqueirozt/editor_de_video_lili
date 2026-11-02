const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),start=source.indexOf("async function initializeEditor(){"),end=source.indexOf("\n",source.indexOf('else document.addEventListener("DOMContentLoaded"',start));
assert.ok(start>=0&&end>start);const boot=source.slice(start,end);
async function scenario(state){
 let handler=null,opened=0,ready=state==="complete",panel=null,finish;const completed=new Promise(resolve=>{finish=resolve;});
 const ctx=vm.createContext({document:{readyState:state,addEventListener(event,fn,options){assert.equal(event,"DOMContentLoaded");assert.equal(options.once,true);handler=fn;},body:{classList:{toggle(){}}}},
  editorFeatures:{},projects:[{id:"p"}],location:{search:"?project=p&panel=captions",replace(){throw Error("unexpected redirect");}},
  localStorage:{getItem(){return null;}},URLSearchParams,$(){return{accept:""};},api:async()=>({features:{subtitles:true}}),listProjects:async()=>{},toast(msg){throw Error(msg);},
  openProject:async id=>{assert.ok(ready,"no project render before deferred timeline module is ready");assert.equal(id,"p");opened++;},openEditorPanel:async name=>{panel=name;finish();}});
 vm.runInContext(boot,ctx);
 if(state!=="complete"){await Promise.resolve();await Promise.resolve();assert.equal(opened,0);assert.equal(typeof handler,"function");ready=true;await handler();}
 else await completed;
 assert.equal(opened,1);assert.equal(panel,"captions");
}
(async()=>{await scenario("loading");await scenario("interactive");await scenario("complete");console.log("Editor startup: deferred modules finish before initial project render; direct project and panel preserved");})().catch(e=>{console.error(e);process.exitCode=1;});
