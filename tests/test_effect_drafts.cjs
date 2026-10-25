const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('web/timeline.js','utf8'),app=fs.readFileSync('web/app.js','utf8');
const nodes=new Map(),commands=[];let failSave=false;
function node(id){if(!nodes.has(id))nodes.set(id,{style:{},listeners:{},attributes:{},open:false,disabled:false,
 addEventListener(type,fn){this.listeners[type]=fn;},setAttribute(k,v){this.attributes[k]=String(v);},querySelectorAll(){return[];},
 showModal(){this.open=true;},close(){this.open=false;this.listeners.close?.();}});return nodes.get(id);}
const saved={id:'a',media_id:'one',start:1,end:4,speed:1.25,brightness:.8,contrast:1.2,saturation:.6,title:'Keep this',volume:.7,fade_in:.2,framing:'cover',locked:false};
const context=vm.createContext({$:node,esc:value=>String(value??""),project:{id:'p',revision:4,timeline:[{...saved},{id:'b',media_id:'two',start:0,end:2}],media:[]},selected:'a',cursor:1,playing:false,playerLoading:false,player:{seeking:false},editorFeatures:{color_adjustments:true},queue:Promise.resolve(),document:{addEventListener(){},querySelectorAll(){return[];}},ResizeObserver:class{observe(){}},requestAnimationFrame(){},cancelAnimationFrame(){},
 clipDuration:c=>(c.end-c.start)/(c.speed||1),currentClip:()=>context.project.timeline.find(c=>c.id===context.selected),
 before:(at=context.project.timeline.findIndex(c=>c.id===context.selected))=>context.project.timeline.slice(0,Math.max(0,at)).reduce((sum,c)=>sum+context.clipDuration(c),0),
 index:()=>context.project.timeline.findIndex(c=>c.id===context.selected),
 pause(){context.playing=false;},closeSheet(){},seekTo(time){context.cursor=time;},selectClip(id){context.selected=id;context.cursor=context.before();},
 updatePlayer(resume,time){context.cursor=time;context.updateTime();},updateTime(){context.updateEffectControls();},
 async mutate(op,args){commands.push({op,args});if(failSave)return false;Object.assign(context.currentClip(),args);context.project.revision++;return true;},
 play(){context.playing=true;},toast(){}});
vm.runInContext(app.slice(app.indexOf('function gradeValues('),app.indexOf('function updatePreviewGrade(')),context);
vm.runInContext(source,context);
vm.runInContext('renderEffectCatalog=function(){};',context);
const evaluate=code=>vm.runInContext(code,context),copy=value=>JSON.parse(JSON.stringify(value));
(async()=>{
 assert.equal(context.effectFrameAt({start:0,end:2},1.999,0,2),1.96);
 assert.ok(context.effectFrameAt({start:0,end:1.9996},1.999,0,1.9996)<=1.9596);
 assert.equal(context.effectFrameAt({start:0,end:.03,speed:.25},.1,0,.03),0);
 await context.openEffects();assert.equal(node('#effects-dialog').open,true);assert.equal(node('#effects-apply').disabled,true);
 assert.equal(evaluate('EFFECT_PRESETS.length'),7);
 for(const preset of evaluate('EFFECT_PRESETS')){
  for(const strength of [0,25,50,100]){
   const values=context.mixEffectGrade(context.effectGrade(saved),preset,strength);
   assert.ok(values.brightness>=.5&&values.brightness<=1.5);assert.ok(values.contrast>=.5&&values.contrast<=1.5);assert.ok(values.saturation>=0&&values.saturation<=2);
  }
 }
 context.chooseEffectPreset('mono');assert.deepEqual(copy(context.effectDraftGrade()),{brightness:1,contrast:1.06,saturation:0});
 assert.deepEqual(context.project.timeline[0],saved,'choosing a look cannot edit the project');
 node('#effects-strength').listeners.input({target:{value:'50'}});
 assert.deepEqual(copy(context.effectDraftGrade()),{brightness:.9,contrast:1.13,saturation:.3});
 for(let i=0;i<10;i++)node('#effects-strength').listeners.input({target:{value:'50'}});
 assert.deepEqual(copy(context.effectDraftGrade()),{brightness:.9,contrast:1.13,saturation:.3},'slider never accumulates grading');
 const adjusted=context.effectPreviewClip(context.currentClip());assert.equal(adjusted.title,saved.title);assert.equal(adjusted.speed,saved.speed);assert.equal(adjusted.volume,saved.volume);
 node('#effects-compare').listeners.click();assert.equal(node('#effects-apply').disabled,true);assert.deepEqual(copy(context.effectPreviewClip(context.currentClip())),saved);
 await node('#effects-apply').listeners.click();assert.equal(commands.length,0,'cannot apply while looking at Before');
 node('#effects-compare').listeners.click();assert.equal(node('#effects-apply').disabled,false);
 await node('#effects-apply').listeners.click();assert.equal(commands.length,1);assert.equal(commands[0].op,'clip_update');
 assert.deepEqual(Object.keys(commands[0].args).sort(),['brightness','clip_id','contrast','saturation']);assert.equal(node('#effects-dialog').open,false);
 assert.equal(context.project.timeline[0].title,saved.title);assert.equal(context.project.timeline[0].speed,saved.speed);
 await context.openEffects();context.chooseEffectPreset('vivid');node('#effects-dialog').close();assert.equal(commands.length,1,'Cancel sends no command');
 assert.equal(context.cursor,1);
 await context.openEffects();context.chooseEffectPreset('light');context.project.revision++;context.updateEffectControls();assert.equal(node('#effects-apply').disabled,true);
 assert.equal(context.effectPreviewClip(context.currentClip()),context.currentClip(),'a stale draft cannot cover new server state');node('#effects-dialog').close();
 await context.openEffects();context.chooseEffectPreset('soft');context.currentClip().locked=true;context.updateEffectControls();await node('#effects-apply').listeners.click();assert.equal(commands.length,1);context.currentClip().locked=false;node('#effects-dialog').close();
 await context.openEffects();context.chooseEffectPreset('mono');const beforeFailure=copy(context.project);failSave=true;await node('#effects-apply').listeners.click();assert.deepEqual(context.project,beforeFailure);assert.equal(node('#effects-dialog').open,true);assert.equal(evaluate('effectSaving'),false);failSave=false;
 context.chooseEffectScene('b');assert.equal(evaluate('effectDraft.preset'),'current');assert.equal(context.selected,'b');assert.equal(context.effectChanges(),null);
 node('#effects-center').listeners.click();assert.equal(context.cursor,3.4);
 context.chooseEffectPreset('mono');assert.equal(context.effectPreviewClip(context.project.timeline[0]),context.project.timeline[0],'look targets only its scene');
 node('#effects-play').listeners.click();assert.equal(context.playing,true);assert.equal(evaluate('effectPreviewEnd'),4.4);
 node('#effects-compare').listeners.click();assert.equal(context.playing,false);assert.equal(evaluate('effectPreviewEnd'),null);
 node('#effects-play').listeners.click();assert.equal(context.stopEffectPlayback(),true);assert.equal(context.playing,false);assert.equal(context.selected,'b');assert.ok(context.cursor<4.4);assert.equal(context.stopEffectPlayback(),false);
 console.log('Appearance drafts: 7 real looks, strength, nonaccumulation, comparison, one-command save, cancel, locks, stale revision, failure and bounded preview passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
