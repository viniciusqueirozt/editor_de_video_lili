const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("web/app.js", "utf8");
const functions = source.slice(source.indexOf("function voiceGain("), source.indexOf("function updateTime("));
const context = vm.createContext({
  project: {narration: {media_id:"voice", offset:.3, volume:.5, fade_in:.6, fade_out:.6}, media:[{id:"voice",duration:2.5}]},
  cursor:.6, playing:true, playerLoading:false, player:{seeking:false,paused:false},
  voice:{volume:1,currentTime:0,readyState:1,paused:true,pause(){this.paused=true},play(){this.paused=false;return Promise.resolve()}}
});
vm.runInContext(functions, context);
const near=(actual,expected)=>assert.ok(Math.abs(actual-expected)<1e-6, `${actual} != ${expected}`);
vm.runInContext("syncVoice()", context);
near(context.voice.volume,.25);
near(context.voice.currentTime,.3);
assert.equal(context.voice.paused,false);
context.cursor=2.5;
vm.runInContext("syncVoice()", context);
near(context.voice.volume,.25);
context.cursor=.1;
vm.runInContext("syncVoice()", context);
assert.equal(context.voice.paused,true);
near(context.voice.volume,0);
context.cursor=2.9;
vm.runInContext("syncVoice()", context);
assert.equal(context.voice.paused,true);
context.project.narration={media_id:"voice",offset:0,volume:.7};
context.cursor=1;
vm.runInContext("syncVoice()", context);
near(context.voice.volume,.7);
console.log("Prévia: fades, atraso, busca e projeto antigo passaram.");
