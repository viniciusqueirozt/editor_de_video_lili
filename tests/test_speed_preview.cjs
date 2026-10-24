const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),ctx=vm.createContext({project:{timeline:[{start:1,end:5,speed:2},{start:0,end:2,speed:.5}]},index:()=>1});
vm.runInContext(source.slice(source.indexOf("function clipDuration("),source.indexOf("function elapsed(")),ctx);
assert.equal(ctx.clipDuration(ctx.project.timeline[0]),2);assert.equal(ctx.clipDuration(ctx.project.timeline[1]),4);assert.equal(ctx.before(),2);assert.equal(ctx.before(2),6);
console.log("Speed-aware montage timing passed");
