const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const home=fs.readFileSync('web/home.js','utf8'),app=fs.readFileSync('web/app.js','utf8'),nodes=new Map(),opened=[];
function node(id){if(!nodes.has(id))nodes.set(id,{hidden:false,innerHTML:'',textContent:'',listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},click(){opened.push(id);}});return nodes.get(id);}
const first={id:'a'.repeat(32),name:'Vídeo <script>'},second={id:'b'.repeat(32),name:'Outro trabalho'};
const ctx=vm.createContext({$:node,active:[first,second],readPref:()=>second.id,esc:s=>String(s).replaceAll('<','&lt;').replaceAll('>','&gt;'),editorUrl:p=>'/editor?project='+p.id});
vm.runInContext(home.slice(home.indexOf('const QUICK_ACTIONS='),home.indexOf('function renderProjects(')),ctx);
ctx.renderQuickActions();assert.equal(node('#quick-actions').hidden,false);assert.match(node('#quick-action-grid').innerHTML,new RegExp(second.id));assert.equal((node('#quick-action-grid').innerHTML.match(/class="quick-action"/g)||[]).length,4);assert.match(node('#quick-project').innerHTML,/&lt;script&gt;/);assert.doesNotMatch(node('#quick-action-grid').innerHTML,/fetch|onclick/);
node('#quick-project').listeners.change({target:{value:first.id}});assert.match(node('#quick-action-grid').innerHTML,new RegExp(first.id));assert.match(node('#quick-project-note').textContent,/não altera/);ctx.active=[second];ctx.renderQuickActions();assert.doesNotMatch(node('#quick-action-grid').innerHTML,new RegExp(first.id));ctx.active=[];ctx.renderQuickActions();assert.equal(node('#quick-actions').hidden,true);assert.equal(node('#quick-action-grid').innerHTML,'');
Object.assign(ctx,{project:{id:'p',timeline:[{},{}]},queue:Promise.resolve(),editorFeatures:{pair_transitions:true},pause(){},async openAIEditor(){opened.push('ai');},openLibraryTab(p){opened.push(p);},openInspector(p){opened.push(p);},async openTransition(){opened.push('transitions');},toast(s){opened.push(s);}});
vm.runInContext(app.slice(app.indexOf('async function openEditorPanel('),app.indexOf('if("serviceWorker"')),ctx);
(async()=>{
 for(const panel of ['ai','media','transitions','captions','export'])assert.equal(await ctx.openEditorPanel(panel),true);
 assert.deepEqual(opened,['ai','media','transitions','captions','#export-button']);assert.equal(await ctx.openEditorPanel('javascript:bad'),false);assert.equal(opened.length,5);
 ctx.project.timeline=[];await ctx.openEditorPanel('transitions');assert.equal(opened.at(-2),'media');assert.match(opened.at(-1),/duas cenas/);await ctx.openEditorPanel('export');assert.equal(opened.at(-2),'media');assert.match(opened.at(-1),/Adicione cenas/);
 let release;ctx.queue=new Promise(r=>release=r);const old=ctx.openEditorPanel('ai');ctx.project={id:'other',timeline:[]};release();assert.equal(await old,false);
 console.log('Quick action navigation: chosen/empty/deleted projects, escaped labels, four safe links, existing editor panels, unknown intents, missing scenes and queued project switching passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
