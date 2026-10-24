const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("web/app.js","utf8"),ctx=vm.createContext({});
vm.runInContext(source.slice(source.indexOf("function gradeValues("),source.indexOf("function updatePreviewGrade(")),ctx);
const grade=ctx.gradeValues({brightness:.8,contrast:1.2,saturation:0});
assert.ok(Math.abs(grade.slope-.96)<1e-8);assert.ok(Math.abs(grade.offset+.08)<1e-8);
assert.equal(grade.matrix[0],grade.matrix[5]);assert.equal(grade.matrix[5],grade.matrix[10]);
assert.equal(ctx.gradeValues({}).active,false);console.log("RGB grading preview coefficients passed");
