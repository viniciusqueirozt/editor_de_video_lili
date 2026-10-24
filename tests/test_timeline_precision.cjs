const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const timeline=fs.readFileSync('web/timeline.js','utf8'),app=fs.readFileSync('web/app.js','utf8');
const helpers=vm.createContext({clamp:(x,a,b)=>Math.max(a,Math.min(b,x)),roundTime:x=>Math.round(x*1000)/1000});
vm.runInContext(timeline.slice(timeline.indexOf('function frameStep('),timeline.indexOf('let precisionSaving=')),helpers);
assert.equal(helpers.parseMontageTime('1,5'),1.5);
assert.equal(helpers.parseMontageTime('02:01.050'),121.05);
for(const value of ['', '-1','1e3','0:60','1:2','Infinity','1.0001','1,2,3','1:00junk'])assert.equal(helpers.parseMontageTime(value),null,value);
assert.equal(helpers.montageTime(59.9996),'01:00.000');
assert.equal(helpers.montageTime(3601.125),'60:01.125');
let time=0;for(let i=0;i<30;i++)time=helpers.frameStep(time,1,10);assert.equal(time,1);
assert.equal(helpers.frameStep(1.01,1,10),31/30);assert.equal(helpers.frameStep(1.01,-1,10),1);
assert.equal(helpers.frameStep(0,-1,10),0);assert.equal(helpers.frameStep(9.99,1,10),10);
const clip={start:1,end:5,speed:2};
assert.equal(helpers.cursorTrim(clip,'start',3,2).start,3);
assert.equal(helpers.cursorTrim(clip,'end',3,2).end,3);
assert.equal(helpers.cursorTrim({...clip,locked:true},'end',3,2),null);
assert.equal(helpers.cursorTrim(clip,'end',2.01,2),null);
assert.equal(helpers.cursorTrim(clip,'start',1.5,2),null);
assert.equal(helpers.cursorTrim(clip,'end',6,2),null);
assert.equal(helpers.cursorTrim({...clip,audio_fade_in:.6,audio_fade_out:.5},'end',3,2),null);
assert.equal(helpers.cursorTrim({...clip,fade_in:.6,fade_out:.5},'end',3,2),null);
assert.equal(helpers.trimmedCursor(clip,'end',3,2),2.999);
assert.equal(helpers.trimmedCursor(clip,'start',3,2),2);

// Test the real seek implementation with a decoder that finishes asynchronously.
const writes=[],elements=new Map();let sourceTime=0;
const player={readyState:4,seeking:false,playbackRate:1,preservesPitch:true,
 get currentTime(){return sourceTime;},set currentTime(t){writes.push(t);this.seeking=true;},
 getAttribute(){return null;},hasAttribute(){return false;},load(){this.readyState=0;this.seeking=false;},removeAttribute(){}};
const ctx=vm.createContext({project:{duration:8,timeline:[{id:'a',media_id:'x',start:0,end:4,volume:1},{id:'b',media_id:'x',start:0,end:4,volume:1}],media:[{id:'x'}]},selected:'a',cursor:0,loadedSource:'/x',previewSeek:null,playerLoading:false,playing:false,player,
 $:id=>{if(!elements.has(id))elements.set(id,{});return elements.get(id);},
 currentClip(){return ctx.project.timeline.find(c=>c.id===ctx.selected);},assetFor:()=>({id:'x'}),assetUrl:m=>'/'+m.id,frameUrl:()=>'/frame',before:()=>ctx.selected==='a'?0:4,index:()=>0,
 renderPreviewCaption(){},renderPreviewFraming(){},updateTime(){},voice:{pause(){},hasAttribute(){return false;}},musicPlayer:{pause(){},hasAttribute(){return false;}},play(){ctx.plays=(ctx.plays||0)+1;}});
vm.runInContext(app.slice(app.indexOf('function flushPreviewSeek('),app.indexOf('function voiceGain(')),ctx);
ctx.updatePlayer(false,1);ctx.updatePlayer(false,2);ctx.updatePlayer(false,3);
assert.deepEqual(writes,[1]);assert.equal(ctx.playerLoading,true);
sourceTime=1;player.seeking=false;ctx.flushPreviewSeek();assert.deepEqual(writes,[1,3]);assert.equal(ctx.playerLoading,true);
sourceTime=3;player.seeking=false;ctx.flushPreviewSeek();assert.equal(ctx.previewSeek,null);assert.equal(ctx.playerLoading,false);
ctx.updatePlayer(false,2);ctx.selected='b';ctx.updatePlayer(false,6.5);
sourceTime=2;player.seeking=false;ctx.flushPreviewSeek();assert.equal(writes.at(-1),2.5);
sourceTime=2.5;player.seeking=false;ctx.flushPreviewSeek();assert.equal(ctx.playerLoading,false);
ctx.project.timeline[1].media_id='y';ctx.assetFor=()=>({id:'y'});ctx.updatePlayer(false,7);
assert.equal(player.readyState,0);ctx.flushPreviewSeek();assert.equal(ctx.playerLoading,true);
player.readyState=1;sourceTime=0;player.onloadedmetadata();assert.equal(writes.at(-1),3);
sourceTime=3;player.seeking=false;player.readyState=1;ctx.flushPreviewSeek();assert.equal(ctx.playerLoading,true);
player.readyState=2;ctx.flushPreviewSeek();assert.equal(ctx.playerLoading,false);
ctx.playing=true;ctx.updatePlayer(true,7);assert.equal(ctx.plays,1);ctx.flushPreviewSeek();assert.equal(ctx.plays,1);
// Paused seeks must not replay a stale auto-advance request.
ctx.updatePlayer(true,6);ctx.playing=false;ctx.updatePlayer(false,5);
sourceTime=2;player.seeking=false;ctx.flushPreviewSeek();sourceTime=1;player.seeking=false;ctx.flushPreviewSeek();assert.equal(ctx.plays,1);

// Seeking within a scene preserves inspector inputs; crossing a scene refreshes once.
ctx.pause=()=>{};ctx.clipDuration=c=>(c.end-c.start)/(c.speed||1);ctx.markSelection=()=>ctx.marks=(ctx.marks||0)+1;ctx.updatePlayer=()=>{};
vm.runInContext(app.slice(app.indexOf('function seekTo('),app.indexOf('// Serialize media seeks')),ctx);
ctx.selected='a';ctx.seekTo(1);ctx.seekTo(2);assert.equal(ctx.marks,undefined);
ctx.seekTo(5);assert.equal(ctx.selected,'b');assert.equal(ctx.marks,1);
ctx.seekTo(6,true);assert.equal(ctx.marks,2);
console.log('Timeline precision: parsing, frame grid, speed/fade/lock-safe cuts, latest seek and stable inspector passed');

// Use the installed pointer handlers, not a second implementation of the gesture.
const nodes=new Map(),frames=new Map();let frameId=0;
function node(id){if(!nodes.has(id))nodes.set(id,{listeners:{},style:{},clientWidth:300,scrollLeft:0,
 addEventListener(type,fn){this.listeners[type]=fn;},setPointerCapture(id){this.capture??=new Set();this.capture.add(id);},
 hasPointerCapture(id){return this.capture?.has(id)||false;},releasePointerCapture(id){this.capture.delete(id);},
 getBoundingClientRect(){return {left:id==='#timeline'?50-node('#timeline-scroll').scrollLeft:50};}});return nodes.get(id);}
const gestureContext=vm.createContext({$:node,Map,project:{duration:20,timeline:[{id:'a',start:0,end:20}]},cursor:.5,playing:false,editorFeatures:{},document:{addEventListener(){}},ResizeObserver:class{observe(){}},
 requestAnimationFrame(fn){frames.set(++frameId,fn);return frameId;},cancelAnimationFrame(id){frames.delete(id);},pause(){},seekTo(time){gestureContext.cursor=time;}});
vm.runInContext(timeline,gestureContext);
vm.runInContext('renderTimeline=function(){timelineScale=30*timelineZoom;}',gestureContext);
const canvas=node('#timeline'),ruler={closest:selector=>selector==='#time-ruler'?true:null};
const event=(pointerId,clientX)=>({pointerId,clientX,button:0,pointerType:'touch',target:ruler});
canvas.listeners.pointerdown(event(1,80));assert.equal(gestureContext.cursor,1);
canvas.listeners.pointerdown(event(2,140));assert.equal(gestureContext.cursor,.5,'pinch restores pre-scrub cursor');
canvas.listeners.pointermove(event(2,200));for(const [id,fn]of frames){frames.delete(id);fn();}
assert.equal(vm.runInContext('timelineZoom',gestureContext),2);
assert.equal(node('#timeline-scroll').scrollLeft,30,'same time remains under pinch midpoint');
canvas.listeners.pointerup(event(2,200));canvas.listeners.pointermove(event(1,150));assert.equal(gestureContext.cursor,.5,'one remaining finger cannot become a seek');
canvas.listeners.pointerdown(event(3,180));assert.equal(vm.runInContext('timelineGesture.type',gestureContext),'drain');
canvas.listeners.pointercancel(event(1,150));assert.equal(vm.runInContext('timelineGesture',gestureContext),null);
assert.equal(canvas.capture.size,0);
canvas.listeners.pointerdown(event(4,110));canvas.listeners.pointercancel(event(4,110));assert.equal(vm.runInContext('timelineGesture',gestureContext),null);
assert.equal(canvas.capture.size,0);
console.log('Ruler pinch preserves cursor/anchor and drains cancelled pointers without accidental seeks');
