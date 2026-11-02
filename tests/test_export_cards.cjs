const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),root={querySelector:()=>({open:true}),querySelectorAll:()=>[]};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ctx=vm.createContext({project:{id:"a".repeat(32),revision:10},$:()=>root,esc,precise:t=>t+" s",icon:()=>"↓"});
vm.runInContext(source.slice(source.indexOf("function exportJobCard("),source.indexOf("async function refreshJobs(")),ctx);
const done={id:"b".repeat(32),status:"done",result:{revision:10,width:1080,height:1920,duration:2,quality:"high",bytes:1048576,url:"javascript:bad"}};
let html=ctx.exportJobCard(done);assert.match(html,/Versão atual/);assert.match(html,/Alta qualidade/);assert.match(html,/1.0 MB/);assert.doesNotMatch(html,/javascript:/);
html=ctx.exportJobCard({...done,result:{...done.result,revision:9}});assert.match(html,/Versão anterior/);
html=ctx.exportJobCard({id:"x",status:"error",error:"<script>"});assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>/);
html=ctx.exportJobCard({id:"x",status:"running",progress:200});assert.match(html,/value="100"/);
ctx.renderExportJobs([done,done]);assert.match(root.innerHTML,/details class="export-history" open/);
ctx.renderExportJobs([]);assert.match(root.innerHTML,/Seu vídeo final/);console.log("Export cards, safe links, history and status passed");

html=ctx.exportJobCard({...done,result:{...done.result,download_name:'Ágata-<script>".mp4',download_available:false,artifact_state:'missing'}});assert.match(html,/Arquivo indisponível/);assert.doesNotMatch(html,/export-download/);assert.match(html,/data-export-again="high"/);assert.match(html,/não restaura uma versão antiga/);assert.doesNotMatch(html,/<script>/);assert.match(html,/&lt;script&gt;/);
html=ctx.exportJobCard({...done,result:{...done.result,quality:'preview',download_name:'Sample-v10-previa.mp4'}});assert.match(html,/Prévia pronta/);assert.match(html,/download="Sample-v10-previa.mp4"/);
let prepared=0,focused=0;ctx.$=id=>id==='#export-quality'?{set value(v){assert.equal(v,'high');}}:id==='#start-export'?{focus(){focused++;}}:root;ctx.updateExportPreview=()=>prepared++;ctx.renderExportReadiness=()=>prepared++;ctx.toast=()=>{};ctx.prepareExportAgain('high',ctx.project.id);assert.equal(prepared,2);assert.equal(focused,1);ctx.prepareExportAgain('high','other');ctx.prepareExportAgain('bad',ctx.project.id);assert.equal(prepared,2);

const recovery={dataset:{exportAgain:'high'},addEventListener(type,fn){this.click=fn;}};root.querySelectorAll=()=>[recovery];ctx.renderExportJobs([{...done,result:{...done.result,download_available:false}}]);recovery.click();assert.equal(prepared,4);ctx.project.id='other';recovery.click();assert.equal(prepared,4,'old recovery button cannot target another project');

html=ctx.exportJobCard({...done,result:{download_name:"legacy.mp4",download_available:true}});assert.match(html,/Exportação salva/);assert.doesNotMatch(html,/undefined/);assert.match(html,/export-download/);
