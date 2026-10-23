const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8");
const code=source.slice(source.indexOf("async function uploadFiles("),source.indexOf("async function openAIEditor("));
function fixture(options={}){
  const elements=new Map(),calls=[],chunks=[],messages=[];
  const $=key=>{if(!elements.has(key))elements.set(key,{hidden:true,disabled:false,textContent:"",value:""});return elements.get(key);};
  let context,started=0,completed=0,cancelFails=Boolean(options.cancelFails);
  const project={id:"project",media:[],trash:[]};
  async function api(path){
    calls.push(path);
    if(path==="/api/health")return options.legacy?{}:{features:{upload_cancel:true}};
    if(path.endsWith("/uploads")){
      started++;
      if(options.cancelAtStart)context.requestUploadCancel();
      return {upload_id:"upload"+started,chunk_size:3};
    }
    if(path.endsWith("/complete")){
      if(options.cancelAtComplete)context.requestUploadCancel();
      if(options.failComplete)throw new Error("response lost");
      completed++;return {media_id:"media"+completed};
    }
    if(path.endsWith("/cancel")){
      if(cancelFails)throw new Error("offline");
      if(options.cancelMissing)throw Object.assign(new Error("not found"),{status:404});
      return {cancelled:true};
    }
    return project;
  }
  class XHR{
    constructor(){this.handlers={};this.upload={addEventListener(){}};}
    open(method,url){this.url=url;}
    addEventListener(event,handler){this.handlers[event]=handler;}
    send(){
      chunks.push(this.url);
      queueMicrotask(()=>{
        if(options.cancelBlock&&(!options.afterFirstComplete||completed===1))context.requestUploadCancel();
        if(options.failBlock){this.handlers.error();return;}
        this.status=200;this.responseText="{}";this.handlers.load();
      });
    }
  }
  context=vm.createContext({$,project,uploadRunning:false,uploadState:{pending:null,cancel:false,completing:false,available:false},
    importBatch:null,api,XMLHttpRequest:XHR,toast:(message,error)=>messages.push({message,error}),render(){},updateImportStatus(){},location:{assign(){}}});
  vm.runInContext(code,context);
  const file={name:"synthetic.mp4",size:6,slice(){return "synthetic-block";}};
  return {context,elements,calls,chunks,messages,file,setCancelFailure:value=>{cancelFails=value;},getStarted:()=>started,getCompleted:()=>completed};
}
(async()=>{
  {
    const f=fixture({cancelBlock:true});await f.context.uploadFiles([f.file]);
    assert.equal(f.chunks.length,1);assert.equal(f.getCompleted(),0);
    assert.equal(f.calls.filter(p=>p.endsWith("/cancel")).length,1);
    assert.equal(f.context.uploadState.pending,null);assert.equal(f.context.uploadRunning,false);
    assert.match(f.context.importBatch.error,/cancelado/);
  }
  {
    const f=fixture({cancelBlock:true,afterFirstComplete:true});await f.context.uploadFiles([f.file,f.file,f.file]);
    assert.equal(f.getStarted(),2);assert.equal(f.getCompleted(),1);
    assert.equal(f.context.importBatch.mediaIds.join(","),"media1");
    assert.ok(f.calls.some(p=>p.endsWith("/upload2/cancel")));
    assert.ok(!f.calls.some(p=>p.endsWith("/upload1/cancel")));
  }
  {
    const f=fixture({cancelBlock:true,cancelFails:true});await f.context.uploadFiles([f.file]);
    assert.ok(f.context.uploadState.pending);assert.equal(f.elements.get("#cancel-upload").hidden,false);
    assert.equal(f.elements.get("#cancel-upload").disabled,false);
    const before=f.calls.length;await f.context.uploadFiles([f.file]);assert.equal(f.calls.length,before);
    f.setCancelFailure(false);await f.context.requestUploadCancel();assert.equal(f.context.uploadState.pending,null);
  }
  {
    const f=fixture({cancelAtComplete:true});await f.context.uploadFiles([f.file]);
    assert.equal(f.getCompleted(),1);assert.equal(f.calls.some(p=>p.endsWith("/cancel")),false);
    assert.equal(f.context.uploadState.pending,null);
  }
  {
    const f=fixture({failComplete:true,cancelMissing:true});await f.context.uploadFiles([f.file]);
    assert.ok(f.context.uploadState.pending);await f.context.requestUploadCancel();
    assert.equal(f.context.uploadState.pending,null);assert.match(f.context.importBatch.error,/não está mais pendente/);
    assert.doesNotMatch(f.context.importBatch.error,/espaço liberado|Envio cancelado/);
  }
  {
    const f=fixture({legacy:true});await f.context.uploadFiles([f.file]);
    assert.equal(f.getCompleted(),1);assert.equal(f.elements.get("#cancel-upload").hidden,true);
    assert.equal(f.context.uploadState.pending,null);
  }
  {
    const f=fixture({failBlock:true});await f.context.uploadFiles([f.file]);
    assert.equal(f.chunks.length,2);assert.ok(f.context.uploadState.pending);
    assert.equal(f.calls.some(p=>p.endsWith("/cancel")),false);
    await f.context.requestUploadCancel();assert.equal(f.context.uploadState.pending,null);
  }
  {
    const f=fixture({cancelAtStart:true});await f.context.uploadFiles([f.file]);
    assert.equal(f.chunks.length,0);assert.equal(f.getCompleted(),0);
    assert.equal(f.calls.filter(p=>p.endsWith("/cancel")).length,1);
  }
  console.log("8 upload cancellation scenarios passed (actual application functions)");
})().catch(error=>{console.error(error);process.exitCode=1;});
