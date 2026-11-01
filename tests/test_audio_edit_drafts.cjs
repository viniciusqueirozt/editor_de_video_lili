const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('web/timeline.js','utf8'),app=fs.readFileSync('web/app.js','utf8'),nodes=new Map(),commands=[];let failSave=false;
function node(id){if(!nodes.has(id))nodes.set(id,{style:{},listeners:{},attributes:{},open:false,disabled:false,value:'',
 addEventListener(type,fn){this.listeners[type]=fn;},setAttribute(k,v){this.attributes[k]=String(v);},querySelectorAll(){return[];},
 showModal(){this.open=true;},close(){this.open=false;this.listeners.close?.();}});return nodes.get(id);}
function media(){return {paused:true,currentTime:0,readyState:1,volume:1,pause(){this.paused=true;},play(){this.paused=false;return Promise.resolve();}};}
const context=vm.createContext({$:node,project:{id:'p',revision:1,duration:6,timeline:[{id:'clip',media_id:'video',start:0,end:6}],media:[{id:'voice',name:'Voice',duration:4},{id:'music',name:'Music',duration:6}],narration:{media_id:'voice',offset:0,volume:1,fade_in:0,fade_out:0},music:{media_id:'music',offset:.5,start:1,end:5,volume:.8,fade_in:.2,fade_out:.2,duck:true}},editorFeatures:{narration_trim:false},cursor:1.5,queue:Promise.resolve(),playing:false,playerLoading:false,player:{paused:false,seeking:false},voice:media(),musicPlayer:media(),
 document:{addEventListener(){},querySelectorAll(){return[];}},ResizeObserver:class{observe(){}},requestAnimationFrame(){},cancelAnimationFrame(){},
 pause(){context.playing=false;context.voice.pause();context.musicPlayer.pause();},closeSheet(){},
 seekTo(t){context.pause();context.cursor=t;context.updateTime();},updateTime(){context.updateAudioControls();},
 play(){context.playing=true;context.syncVoice();context.syncMusic();},
 async mutate(op,args){commands.push({op,args});if(failSave)return false;context.project[op==='music_set'?'music':'narration']={...args};context.project.revision++;return true;},precise:n=>n.toFixed(3)});
vm.runInContext(app.slice(app.indexOf('function voiceGain('),app.indexOf('function renderMusicInspector(')),context);
vm.runInContext(source,context);vm.runInContext('getAudioWaveform=()=>Promise.resolve({duration:6,peaks:[0,.2,.8,1,.3,.1]});',context);
const evaluate=code=>vm.runInContext(code,context),copy=v=>JSON.parse(JSON.stringify(v));
const input=(id,value)=>node('#audio-edit-'+id).listeners.input({target:{value}}),click=id=>node('#audio-'+id).listeners.click();
(async()=>{
 const original=copy(context.project);await context.openAudioEdit('music');assert.equal(node('#audio-edit-dialog').open,true);assert.equal(node('#audio-edit-apply').disabled,true);
 node('#audio-seek-time').value='00:02.200';click('seek-go');assert.equal(context.cursor,2.2);node('#audio-seek-time').value='bad';click('seek-go');assert.equal(context.cursor,2.2);assert.equal(node('#audio-seek-error').hidden,false);context.cursor=1.5;
 input('offset','00:01.200');assert.equal(context.audioPreviewTrack('music').offset,1.2);assert.deepEqual(context.project,original);
 context.cursor=2;context.play();assert.ok(Math.abs(context.musicPlayer.currentTime-1.8)<1e-9);assert.equal(context.musicPlayer.volume,.2,'duck uses active narration');
 node('#audio-edit-duck').listeners.change({target:{checked:false}});context.play();assert.equal(context.musicPlayer.volume,.8);
 node('#audio-edit-dialog').close();assert.deepEqual(context.project,original);assert.equal(context.cursor,1.5);assert.equal(commands.length,0);assert.equal(context.audioPreviewTrack('music'),context.project.music);
 await context.openAudioEdit('music');click('trim-start');assert.deepEqual(copy(evaluate('audioDraft.values')),{...original.music,start:2,offset:1.5});
 context.cursor=2.5;click('trim-end');assert.equal(evaluate('audioDraft.values.end'),3);assert.equal(evaluate('audioDraft.values.offset+audioDraft.values.end-audioDraft.values.start'),2.5);
 input('fade_in','.8');input('fade_out','.8');assert.equal(node('#audio-edit-apply').disabled,true);assert.match(context.audioDraftProblem(),/suaves/);assert.equal(context.audioPreviewTrack('music'),context.project.music);
 await click('edit-apply');assert.equal(commands.length,0);input('fade_in','.1');input('fade_out','.1');input('offset','oops');assert.equal(node('#audio-edit-apply').disabled,true);input('offset','00:01.500');
 await click('edit-apply');assert.equal(commands.length,1);assert.equal(commands[0].op,'music_set');assert.equal(commands[0].args.start,2);assert.equal(commands[0].args.end,3);assert.equal(commands[0].args.offset,1.5);assert.deepEqual(context.project.timeline,original.timeline);assert.deepEqual(context.project.narration,original.narration);
 await context.openAudioEdit('narration');context.cursor=2;click('align-cursor');assert.equal(evaluate('audioDraft.values.offset'),2);assert.equal(context.audioTrimAtCursor('start'),null);assert.equal(node('#audio-music-trim').hidden,true);
 context.cursor=1;context.play();assert.equal(context.voice.paused,true);context.cursor=2.5;context.play();assert.equal(context.voice.currentTime,.5);assert.equal(context.voice.paused,false);
 click('offset-forward');assert.ok(Math.abs(evaluate('audioDraft.values.offset')-61/30)<1e-9);click('offset-back');assert.equal(evaluate('audioDraft.values.offset'),2);
 input('offset','3600');assert.equal(context.audioDraftProblem(),'');input('offset','3601');assert.notEqual(context.audioDraftProblem(),'');input('offset','2');
 failSave=true;const before=copy(context.project);await click('edit-apply');assert.deepEqual(context.project,before);assert.equal(node('#audio-edit-dialog').open,true);assert.equal(evaluate('audioSaving'),false);failSave=false;
 context.project.revision++;context.updateAudioControls();await click('edit-apply');assert.equal(commands.length,2,'stale draft cannot submit');assert.equal(context.audioPreviewTrack('narration'),context.project.narration);node('#audio-edit-dialog').close();
 await context.openAudioEdit('music');input('start','0');input('end','0.09');assert.notEqual(context.audioDraftProblem(),'');input('end','0.5');input('fade_in','0');input('fade_out','0');assert.equal(context.audioDraftProblem(),'');input('end','6.001');assert.notEqual(context.audioDraftProblem(),'');node('#audio-edit-dialog').close();
 context.drawAudioWaveform(node('wave'),{duration:4,peaks:[0,0,1,1]},2,2);assert.ok(node('wave').innerHTML.includes('v32'),'waveform samples the trimmed source region');
 context.editorFeatures.narration_trim=true;context.cursor=1;await context.openAudioEdit('narration');assert.equal(node('#audio-music-trim').hidden,false);assert.equal(evaluate('audioDraft.values.end'),4);click('trim-start');assert.equal(evaluate('audioDraft.values.start'),1);assert.equal(evaluate('audioDraft.values.offset'),1);context.cursor=2;click('trim-end');assert.equal(evaluate('audioDraft.values.end'),2);
 context.cursor=1.5;context.play();assert.equal(context.voice.currentTime,1.5);assert.equal(context.voice.paused,false);context.cursor=2.01;context.play();assert.equal(context.voice.paused,true,'trimmed voice must stop before the source file ends');assert.equal(context.musicPlayer.volume,context.project.music.volume,'duck ends with trimmed narration');
 const originalVoice=copy(context.project.narration);node('#audio-edit-dialog').close();assert.deepEqual(context.project.narration,originalVoice);await context.openAudioEdit('narration');input('start','1');input('end','2');await click('edit-apply');assert.equal(commands.at(-1).op,'narration_set');assert.equal(commands.at(-1).args.start,1);assert.equal(commands.at(-1).args.end,2);
 await context.openAudioEdit('narration');click('reset-range');assert.equal(evaluate('audioDraft.values.start'),0);assert.equal(evaluate('audioDraft.values.end'),4);node('#audio-edit-dialog').close();
 console.log('Audio draft handlers: offset, frame steps, sync-preserving music trim, real preview/duck, fades, invalid/stale state, cancel, one command and save failure passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
