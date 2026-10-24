const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),node={style:{},hidden:false},renders=[];
const ctx=vm.createContext({project:{captions:[{start:.2,end:.8,text:"Legenda"}]},$:()=>node,currentClip:()=>null,renderPreviewCaption:(c,target)=>renders.push({c,target})});
vm.runInContext(source.slice(source.indexOf("function updatePreviewSubtitle("),source.indexOf("function renderRequests(")),ctx);
ctx.updatePreviewSubtitle(0);assert.equal(node.hidden,true);ctx.updatePreviewSubtitle(.5);assert.equal(node.hidden,false);assert.equal(renders[0].c.title,"Legenda");ctx.updatePreviewSubtitle(.8);assert.equal(node.hidden,true);console.log("Timed subtitle preview boundaries passed");
