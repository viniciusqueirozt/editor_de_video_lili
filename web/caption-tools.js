/* Caption split/merge/shift adapted to Lili's seconds, IDs and styles.
 * Reference: geovanejunior92-debug/edvid, helpers/caption_edit.py
 * revision 230316f2a860f2b67e02440fc6e0bd77afdaaf61, MIT, Creator Factory (2026).
 * See third_party/edvid/LICENSE. No dependency on its runtime or models.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  root.LiliCaptionTools=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const stamp=n=>Math.round(n*1e9)/1e9;
  function validate(rows,limit=1800){
    if(!Array.isArray(rows)||rows.length>500)throw Error("Use até 500 legendas por projeto.");
    if(!Number.isFinite(limit)||limit<0||limit>1800)throw Error("Duração da montagem inválida.");
    const seen=new Set(),copy=rows.map(c=>{
      if(!c||typeof c.id!=="string"||!/^[a-f0-9]{32}$/.test(c.id)||seen.has(c.id))throw Error("Identificador de legenda inválido ou repetido.");
      seen.add(c.id);
      if(!Number.isFinite(c.start)||!Number.isFinite(c.end)||c.start<0||c.end>limit||c.end-c.start<.09999)throw Error("As legendas precisam caber no vídeo e durar pelo menos 0,1 s.");
      if(typeof c.text!=="string"||!c.text.trim()||[...c.text].length>160)throw Error("Escreva cada legenda com até 160 caracteres.");
      if([...c.text].some(ch=>{const n=ch.codePointAt(0);return n>=0xd800&&n<=0xdfff;}))throw Error("Confira os caracteres do texto antes de aplicar.");
      return {...c,text:c.text.trim()};
    }).sort((a,b)=>a.start-b.start||a.end-b.end);
    if(copy.some((c,i)=>i&&c.start<copy[i-1].end-.00001))throw Error("As legendas não podem se sobrepor.");
    return copy;
  }
  function find(rows,id){
    const index=rows.findIndex(c=>c.id===id);
    if(index<0)throw Error("A legenda não está mais neste projeto.");
    return index;
  }
  function split(rows,id,at,first,second,newId,limit=1800){
    const list=validate(rows),i=find(list,id),c=list[i];
    if(!Number.isFinite(at)||at<c.start+.1-.00001||at>c.end-.1+.00001)throw Error("Divida dentro da legenda, deixando pelo menos 0,1 s em cada parte.");
    list.splice(i,1,{...c,end:stamp(at),text:first},{...c,id:newId,start:stamp(at),text:second});
    return validate(list,limit);
  }
  function merge(rows,id,limit=1800){
    const list=validate(rows),i=find(list,id),a=list[i],b=list[i+1];
    if(!b)throw Error("Não há uma próxima legenda para juntar.");
    list.splice(i,2,{...a,end:b.end,text:a.text+" "+b.text});
    return validate(list,limit);
  }
  function shift(rows,delta,limit=1800){
    if(!Number.isFinite(delta)||Math.abs(delta)>1800||Math.abs(delta)<.00001)throw Error("Escolha um deslocamento maior que zero, até 30 minutos.");
    if(!rows.length)throw Error("Adicione legendas antes de sincronizar.");
    return validate(validate(rows).map(c=>({...c,start:stamp(c.start+delta),end:stamp(c.end+delta)})),limit);
  }
  function splitText(text,caret=null){
    const value=text.trim();
    if(Number.isInteger(caret)&&caret>0&&caret<text.length){
      const first=text.slice(0,caret).trim(),second=text.slice(caret).trim();
      if(first&&second)return [first,second];
    }
    const words=value.split(/\s+/u);
    if(words.length<2)return [value,""];
    const middle=Math.ceil(words.length/2);
    return [words.slice(0,middle).join(" "),words.slice(middle).join(" ")];
  }
  return {validate,split,merge,shift,splitText};
});
