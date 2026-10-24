const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),node={style:{}};
const ctx=vm.createContext({$:()=>node,project:{settings:{width:1080,height:1920}}});vm.runInContext(source.slice(source.indexOf("function captionLines("),source.indexOf("function sceneFadeGain(")),ctx);
ctx.renderPreviewCaption({title:"Minha legenda",title_position:"bottom",title_font:"serif",title_size:"large"});
assert.equal(node.style.top,"82%");assert.equal(node.style.transform,"translateY(-100%)");assert.equal(node.style.fontSize,"6cqw");assert.equal(node.style.fontFamily,"Georgia, serif");
assert.equal(Array.from(ctx.captionLines({title:"x".repeat(55),title_size:"large"})).join("|"),"x".repeat(22)+"|"+"x".repeat(22)+"|"+"x".repeat(11));
assert.equal(Array.from(ctx.captionLines({title:"Linha 1\n\nLinha 3"})).join("|"),"Linha 1||Linha 3");
ctx.renderPreviewCaption({title:"Legado"});assert.equal(node.style.top,"32%");console.log("Caption typography, position and wrapping passed");
