const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync('web/app.js','utf8'),source=fs.readFileSync('web/timeline.js','utf8');
const nodes=new Map(),documentEvents=new Map(),windowEvents=new Map(),calls=[],messages=[],opened=[];
let failPost=false,failGet=false,postGate=null,fresh=null,renders=0;
class Node {
 constructor(id){this.id=id;this.style={};this.listeners=new Map();this.attributes={};this.captures=new Set();this.classes=new Set();this.disabled=false;this.scrollLeft=0;this.clientWidth=500;this.tagName='BUTTON';this.isConnected=true;this.classList={add:k=>this.classes.add(k),remove:k=>this.classes.delete(k)};}
 addEventListener(k,fn){if(!this.listeners.has(k))this.listeners.set(k,[]);this.listeners.get(k).push(fn);}
 removeEventListener(k,fn){this.listeners.set(k,(this.listeners.get(k)||[]).filter(f=>f!==fn));}
 setAttribute(k,v){this.attributes[k]=String(v);}
 setPointerCapture(id){if(this.captureFails)throw Error('capture unavailable');this.captures.add(id);}
 hasPointerCapture(id){return this.captures.has(id);}
 releasePointerCapture(id){this.captures.delete(id);this.emit('lostpointercapture',{pointerId:id});}
 focus(){ctx.document.activeElement=this;}
 getBoundingClientRect(){return{left:0};}
 set innerHTML(html){this.html=html;for(const [tag,id]of html.matchAll(/<[^>]*id="([^"]+)"[^>]*>/g)){const child=new Node('#'+id),style=tag.match(/style="([^"]*)"/);if(style)for(const declaration of style[1].split(';')){const [key,value]=declaration.split(':');if(key)child.style[key]=value;}nodes.set('#'+id,child);}}
 get innerHTML(){return this.html||'';}
 querySelector(selector){if(selector==='button')return node(this.id==='#music-track'?'#music-move-placeholder':'#narration-move-placeholder',true);return node(this.id+' '+selector);}
 querySelectorAll(){return[];}
 async emit(type,props={}){const e={button:0,pointerId:1,clientX:0,clientY:0,currentTarget:this,target:this,preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;},...props};for(const fn of this.listeners.get(type)||[])await fn(e);return e;}
}
function node(id,placeholder=false){if(placeholder){const real=id.includes('music')?'#music-region':'#narration-region';if(nodes.has(real))return nodes.get(real);}if(!nodes.has(id))nodes.set(id,new Node(id));return nodes.get(id);}
const baseline={id:'p',revision:1,duration:6,timeline:[{id:'c1',media_id:'v',start:0,end:2},{id:'c2',media_id:'v',start:0,end:4}],media:[{id:'v',duration:6},{id:'voice',duration:5,name:'Voice'},{id:'song',duration:5,name:'Song'}],narration:{media_id:'voice',start:1,end:3,offset:.5,volume:.7,fade_in:.2,fade_out:.3},music:{media_id:'song',start:1,end:3,offset:1,volume:.8,fade_in:.1,fade_out:.2,duck:true},captions:[{id:'title',start:3.5,end:4.5,text:'Example'}]};
const ctx=vm.createContext({$:node,project:structuredClone(baseline),queue:Promise.resolve(),cursor:1,playing:false,editorFeatures:{narration_trim:false},localStorage:{getItem(){return'off';}},document:{activeElement:{tagName:'BODY'},hidden:false,querySelector(){return null;},querySelectorAll(){return[];},addEventListener(k,fn){if(!documentEvents.has(k))documentEvents.set(k,[]);documentEvents.get(k).push(fn);}},addEventListener(k,fn){windowEvents.set(k,fn);},ResizeObserver:class{observe(){}},requestAnimationFrame(){},cancelAnimationFrame(){},setTimeout,clearTimeout,precise:n=>n.toFixed(3),esc:s=>String(s),icon:()=>'',pause(){ctx.playing=false;},toast:(s)=>messages.push(s),
 async api(path,opt){if(opt){calls.push({path,body:JSON.parse(opt.body)});if(postGate)await postGate;if(failPost)throw Error('Conflict or offline');const p=structuredClone(ctx.project),{operation,args}=JSON.parse(opt.body);p[operation==='music_set'?'music':'narration']={...p[operation==='music_set'?'music':'narration'],...args};p.revision++;return p;}if(failGet)throw Error('Offline');return structuredClone(fresh||ctx.project);},
 render(){renders++;ctx.renderTimeline();}});
vm.runInContext(app.slice(app.indexOf('function audioRange('),app.indexOf('function syncVoice(')),ctx);
vm.runInContext(app.slice(app.indexOf('function mutate('),app.indexOf('async function listProjects(')),ctx);
vm.runInContext(source,ctx);ctx.renderWholeTimeline=ctx.renderTimeline;
const ev=s=>vm.runInContext(s,ctx),tick=()=>new Promise(r=>setImmediate(r));
ev('getAudioWaveform=()=>Promise.resolve({duration:5,peaks:[0,.2,.8,.1,.3,0]});openAudioEdit=kind=>recordOpen(kind);renderTimeline=()=>{renderAudioTrack();renderSoundTrack("music",$("#music-track"));};');ctx.recordOpen=k=>opened.push(k);
function reset(){ctx.project=structuredClone(baseline);ctx.queue=Promise.resolve();ctx.cursor=1;node('#timeline-scroll').scrollLeft=0;failPost=false;failGet=false;postGate=null;fresh=null;calls.length=0;messages.length=0;opened.length=0;ev('timelineScale=100;timelineSnapEnabled=false;timelineGesture=null;audioMoveSaving=false;suppressAudioClick=false;');ctx.renderTimeline();}
const event=(handle,x=0,id=1)=>({button:0,pointerId:id,clientX:x,currentTarget:handle,preventDefault(){},stopPropagation(){}});
function begin(kind='music',x=0){const h=node('#'+kind+'-move');h.emit('pointerdown',{clientX:x});return h;}
async function move(h,x,id=1,extra={}){return h.emit('pointermove',{clientX:x,pointerId:id,...extra});}
async function release(h,x,id=1){await h.emit('pointerup',{clientX:x,pointerId:id});await ctx.queue;await tick();}
async function doc(type,event){for(const fn of documentEvents.get(type)||[])await fn(event);}
(async()=>{
 reset();const untouched=structuredClone(ctx.project);const targets=ctx.timelineSnapTargets(ctx.project,'music');assert.ok(!targets.some(t=>t.label.startsWith('Música')));assert.ok(targets.some(t=>t.label==='Narração · fim'));
 assert.equal(ctx.snappedAudioOffset(1.43,2,5.9,[{time:3.5,label:'end'}],100,true).offset,1.5,'audio end can align with a caption');
 assert.equal(ctx.snappedAudioOffset(1.43,2,5.9,[{time:3.5,label:'end'}],100,true,true).offset,1.43,'Shift bypasses');
 assert.equal(ctx.snappedAudioOffset(1.43,2,5.9,[{time:3.5,label:'end'}],400,true).target,null,'pixel threshold');
 assert.equal(ctx.snappedAudioOffset(.9,2,1,[{time:3.05,label:'outside'}],100,true).target,null,'snap cannot exceed maximum');
 assert.equal(ctx.snappedAudioOffset(-1,2,5.9,[],100,false).offset,0);
 let h=begin();await move(h,4);assert.equal(ev('timelineGesture.moved'),false);await release(h,4);assert.equal(calls.length,0);await h.emit('click');assert.deepEqual(opened,['music'],'tap remains access to precise panel');
 reset();h=begin();await move(h,50);assert.deepEqual(ctx.project,untouched,'drag never mutates project');assert.equal(node('#music-region').style.left,'150px');assert.equal(node('#music-region').style.width,'200px');assert.equal(ctx.cursor,1,'moving audio does not seek the video');await release(h,50);assert.equal(calls.length,1);assert.deepEqual(calls[0].body,{operation:'music_set',args:{media_id:'song',offset:1.5},expected_revision:1,actor:'editor'});assert.equal(ctx.project.music.start,1);assert.equal(ctx.project.music.fade_out,.2);assert.deepEqual(ctx.project.narration,baseline.narration);assert.deepEqual(ctx.project.timeline,baseline.timeline);assert.deepEqual(ctx.project.captions,baseline.captions);assert.equal(ctx.project.music.offset,1.5);
 reset();h=begin('narration');await release(h,100);assert.equal(calls[0].body.operation,'narration_set');assert.deepEqual(calls[0].body.args,{media_id:'voice',offset:1.5},'old server compatible partial command');assert.equal(ctx.project.narration.start,1);assert.equal(ctx.project.narration.end,3);
 reset();h=begin();await move(h,-999);assert.equal(ev('timelineGesture.offset'),0);await release(h,-999);assert.equal(ctx.project.music.offset,0);
 reset();h=begin();await move(h,9999);assert.equal(ev('timelineGesture.offset'),5.9);assert.equal(node('#music-region').style.width,`${(6-5.9)*100}px`);assert.match(node('#timeline-hint').textContent,/ultrapassa/);await release(h,9999);assert.equal(ctx.project.music.end,3,'overrun never trims source');
 reset();ev('timelineSnapEnabled=true');h=begin();await move(h,94);assert.equal(ev('timelineGesture.offset'),2);assert.equal(node('#timeline-snap-guide').hidden,false);await move(h,94,1,{shiftKey:true});assert.equal(ev('timelineGesture.offset'),1.94);assert.equal(node('#timeline-snap-guide').hidden,true);await release(h,94);assert.equal(ctx.project.music.offset,2);
 reset();h=begin();node('#timeline-scroll').scrollLeft=40;await move(h,10);assert.equal(ev('timelineGesture.offset'),1.5,'scroll displacement participates in position');await release(h,10);
 for(const type of ['pointercancel','lostpointercapture']){reset();h=begin();await move(h,80);await h.emit(type);await tick();assert.equal(ev('timelineGesture'),null);assert.equal(calls.length,0,type+' never saves');assert.equal(ctx.project.music.offset,1);assert.equal(node('#music-move').style.left,'100px');}
 reset();h=begin();await move(h,50,2);await release(h,50,2);assert.equal(calls.length,0);assert.equal(ev('timelineGesture.moved'),false);await h.emit('pointercancel');
 reset();h=begin();await move(h,80);await doc('keydown',{key:'Escape',preventDefault(){}});assert.equal(ev('timelineGesture'),null);assert.equal(calls.length,0);
 reset();h=begin();await move(h,80);await doc('pointerdown',{pointerId:2});assert.equal(ev('timelineGesture'),null);assert.equal(calls.length,0,'second touch cancels rather than conflicting with pinch');
 for(const cause of ['hidden','blur']){reset();h=begin();await move(h,80);if(cause==='hidden'){ctx.document.hidden=true;await doc('visibilitychange',{});ctx.document.hidden=false;}else windowEvents.get('blur')();assert.equal(ev('timelineGesture'),null);assert.equal(calls.length,0);}
 reset();h=begin();await move(h,80);ctx.project.revision++;await release(h,80);assert.equal(calls.length,0,'changed revision cancels');
 reset();h=begin();await move(h,80);ctx.project={...ctx.project,id:'other'};await release(h,80);assert.equal(calls.length,0,'other project cannot receive a prior gesture');
 reset();h=begin();await move(h,80);ctx.project.music.media_id='voice';await release(h,80);assert.equal(calls.length,0,'replaced source cancels');
 reset();let gate;ctx.queue=new Promise(r=>gate=r);h=begin();await move(h,50);const pending=h.emit('pointerup',{clientX:50});ctx.project.revision++;gate();await pending;assert.equal(calls.length,0,'queue guard catches an intervening revision');assert.match(messages.at(-1),/projeto mudou/);
 reset();ctx.queue=new Promise(r=>gate=r);h=begin();await move(h,50);const changed=h.emit('pointerup',{clientX:50});ctx.project={...ctx.project,id:'other'};gate();await changed;assert.equal(calls.length,0,'queue guard checks project as well');
 reset();let finishPost;postGate=new Promise(r=>finishPost=r);h=begin();await move(h,50);const saving=h.emit('pointerup',{clientX:50});await tick();assert.equal(ev('audioMoveSaving'),true);ctx.beginAudioMove(event(node('#narration-move')),'narration');assert.equal(ev('timelineGesture'),null,'no second drag while saving');finishPost();await saving;assert.equal(calls.length,1);assert.equal(ev('audioMoveSaving'),false);
 reset();failPost=true;fresh={...structuredClone(baseline),revision:2,music:{...baseline.music,offset:4}};h=begin();await release(h,50);assert.equal(ctx.project.music.offset,4,'conflict redraws server truth');assert.equal(node('#music-region').style.left,'400px');assert.equal(ev('audioMoveSaving'),false);
 reset();failPost=true;failGet=true;h=begin();await release(h,50);assert.equal(ctx.project.music.offset,1,'unconfirmed failure does not change local metadata');assert.equal(node('#music-region').style.left,'100px');assert.ok(messages.includes('Offline'));assert.equal(ev('audioMoveSaving'),false);
 reset();h=begin();await move(h,80);await move(h,0);await release(h,0);assert.equal(calls.length,0,'returning to original offset creates no history entry');
 reset();h=node('#music-move');h.captureFails=true;await h.emit('pointerdown');assert.equal(ev('timelineGesture'),null);assert.equal(calls.length,0,'capture failure is canceled safely');
 reset();h=node('#music-move');h.isConnected=false;await h.emit('pointerdown');assert.equal(ev('timelineGesture'),null,'detached handle cannot begin a second gesture after redraw');
 reset();h=begin();await move(h,80);ctx.selected='c1';ctx.clock=n=>String(n);ctx.clipDuration=c=>c.end-c.start;ctx.assetFor=c=>ctx.project.media.find(a=>a.id===c.media_id);ctx.assetUrl=()=>'/synthetic';ev('renderTransitionJoins=()=>{};updatePlayhead=()=>{};');ctx.renderWholeTimeline();assert.equal(ev('timelineGesture'),null,'actual timeline redraw cancels capture');assert.equal(calls.length,0);assert.equal(node('#narration-region').style.left,`${baseline.narration.offset*ev('timelineScale')}px`);
 console.log('Audio movement: real handlers and real command queue passed; source-preserving single save, both-edge snap, tap/pan separation, release position, clipping, cancellation, concurrent edits/projects, duplicate save, conflicts and offline recovery.');
})().catch(e=>{console.error(e);process.exitCode=1;});
