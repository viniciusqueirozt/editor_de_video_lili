const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),ctx=vm.createContext({});
vm.runInContext(source.slice(source.indexOf("function exportProfile("),source.indexOf("function configureExportControls(")),ctx);
for(const [width,height,quality,w,h] of [[1080,1920,"preview",540,960],[1920,1080,"balanced",1280,720],[1080,1080,"preview",540,540],[1080,1920,"high",1080,1920]]){
const size=ctx.exportProfile({width,height},quality);assert.equal(size.width,w);assert.equal(size.height,h);}
console.log("Export dimension preview profiles passed");
