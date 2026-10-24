const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8");const ctx=vm.createContext({});
vm.runInContext(source.slice(source.indexOf("function sceneFadeGain("),source.indexOf("function updateSceneFade(")),ctx);
const c={start:2,end:4,fade_in:.4,fade_out:.5};
for(const [t,value] of [[0,0],[.2,.5],[1,1],[1.75,.5],[2,0]])assert.ok(Math.abs(ctx.sceneFadeGain(c,t)-value)<1e-8);
assert.equal(ctx.sceneFadeGain({start:0,end:1},.5),1);console.log("Visual fade preview curve passed");
