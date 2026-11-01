const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync('web/app.js','utf8'),nodes=new Map(),calls=[],messages=[],rendered=[];let postGate=null,jobGate=null,failJobs=false,failPost=false;
function node(id){if(!nodes.has(id))nodes.set(id,{value:'full',disabled:false,textContent:'',innerHTML:'',querySelectorAll(){return[];}});return nodes.get(id);}
const navigation=[];
const original={id:'a',revision:7,duration:4,timeline:[{media_id:'v',volume:1}],media:[{id:'v',status:'ready',has_audio:true,duration:4}],captions:[]};
const ctx=vm.createContext({project:structuredClone(original),$:node,precise:n=>n.toFixed(2)+' s',esc:s=>String(s).replaceAll('<','&lt;'),queue:Promise.resolve(),toast:(s)=>messages.push(s),pause(){navigation.push('pause');},openInspector:name=>navigation.push(name),openLibraryTab:name=>navigation.push(name),renderAIJobs(){},renderExportJobs:j=>rendered.push(j),
 async api(path,opt){calls.push({path,opt});if(opt){if(failPost)throw new Error('request failed');if(postGate)await postGate;return{id:'job'};}if(jobGate)return await jobGate;if(failJobs)throw new Error('offline');return[];}});
vm.runInContext(fs.readFileSync('web/app.js','utf8').slice(fs.readFileSync('web/app.js','utf8').indexOf('function audioRange('),fs.readFileSync('web/app.js','utf8').indexOf('function syncVoice(')),ctx);
vm.runInContext(app.slice(app.indexOf('let exportSubmitting='),app.indexOf('function exportProfile(')),ctx);vm.runInContext(app.slice(app.indexOf('async function refreshJobs('),app.indexOf('setInterval(',app.indexOf('async function refreshJobs('))),ctx);
const copy=structuredClone,ev=s=>vm.runInContext(s,ctx),tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 const review=[{dataset:{exportReview:'library'},addEventListener(type,fn){this.click=fn;}},{dataset:{exportReview:'voice'},addEventListener(type,fn){this.click=fn;}}];node('#export-readiness').querySelectorAll=()=>review;node('#export-dialog').close=()=>navigation.push('close');ctx.renderExportReadiness();review[0].click();review[1].click();assert.deepEqual(navigation,['pause','close','media','pause','close','voice']);
 assert.deepEqual(copy(ctx.exportReadiness(original)),[]);
 let p=copy(original);p.narration={media_id:'n',offset:3,volume:1};p.media.push({id:'n',status:'ready',duration:2});assert.match(ctx.exportReadiness(p)[0].text,/Parte da fala/);p.narration.offset=4;assert.match(ctx.exportReadiness(p)[0].text,/não será ouvida/);
 p=copy(original);p.narration={media_id:'n',offset:3,start:2,end:2.5,volume:1};p.media.push({id:'n',status:'ready',duration:6});assert.equal(ctx.exportReadiness(p).length,0,'voice warning uses trimmed duration');
 p=copy(original);p.music={media_id:'v',start:0,end:5,offset:0,volume:1,fade_out:1};p.captions=[{start:3,end:5}];assert.equal(ctx.exportReadiness(p).filter(n=>n.level==='warning').length,2);
 p=copy(original);p.timeline[0].volume=0;assert.match(ctx.exportReadiness(p)[0].text,/não tem áudio audível/);p.media[0].status='processing';assert.ok(ctx.exportReadiness(p).some(n=>n.level==='error'));assert.deepEqual(copy(p),p);
 let releaseQueue;ctx.queue=new Promise(r=>releaseQueue=r);const first=ctx.submitExport();await ctx.submitExport();assert.equal(calls.length,0);ctx.project.revision=8;node('#export-quality').value='preview';releaseQueue();await first;
 assert.equal(calls.filter(c=>c.opt).length,1);assert.deepEqual(JSON.parse(calls[0].opt.body),{expected_revision:8,quality:'full'});assert.equal(node('#start-export').disabled,false);
 calls.length=0;ctx.queue=new Promise(r=>releaseQueue=r);const switched=ctx.submitExport();ctx.project={...copy(original),id:'b'};releaseQueue();await switched;assert.equal(calls.length,0);assert.match(messages.at(-1),/selecionado mudou/);
 ctx.project=copy(original);ctx.queue=Promise.resolve();failJobs=true;await ctx.submitExport();assert.equal(ev('exportBusyProject'),'a');assert.equal(node('#start-export').disabled,true);const count=calls.length;await ctx.submitExport();assert.equal(calls.length,count,'uncertain queue keeps submission blocked');failJobs=false;await ctx.refreshJobs();assert.equal(node('#start-export').disabled,false);
 let releaseJobs;jobGate=new Promise(r=>releaseJobs=r);const old=ctx.refreshJobs(),before=rendered.length;ctx.project={...copy(original),id:'b'};releaseJobs([{kind:'export',status:'running',id:'old'}]);await old;assert.equal(rendered.length,before,'late queue response cannot render on another project');assert.equal(ev('exportJobRunning'),false);jobGate=null;
 ctx.project=copy(original);ctx.project.media[0].deleted_at='yes';calls.length=0;await ctx.submitExport();assert.equal(calls.filter(c=>c.opt).length,0,'unavailable used media blocks POST');
 ctx.project=copy(original);failPost=true;await ctx.submitExport();assert.ok(messages.some(m=>m.includes('Confira a fila')));assert.equal(ev('exportSubmitting'),false);failPost=false;
 console.log('Export readiness and actual submission handlers: concrete warnings, missing media, double click, queued revision/quality, project switching, uncertain response and late queue results passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
