const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),node={style:{}},player={style:{}};
const ctx=vm.createContext({$:()=>node,player,project:{settings:{watermark:{text:"@Lili",position:"top_left",opacity:.5}}}});
vm.runInContext(source.slice(source.indexOf("function renderPreviewFraming("),source.indexOf("function captionLines(")),ctx);
ctx.renderPreviewFraming({framing:"cover",pan_x:1,pan_y:0,mirror:true});
assert.equal(player.style.objectFit,"cover");assert.equal(player.style.objectPosition,"100% 0%");assert.equal(player.style.transform,"scaleX(-1)");
assert.equal(node.textContent,"@Lili");assert.equal(node.style.left,"4%");assert.equal(node.style.top,"4%");
ctx.renderPreviewFraming(null);assert.equal(node.hidden,true);console.log("Framing and watermark preview passed");
