/* Deterministic local retrieval. The corpus is complete; model context is deliberately scoped. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.BookCorpus=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const STOP=new Set(['如果','怎样','什么','如何','可以','一个','一些','这个','是否','我们','为什么','请问','一下','时候','时候','可能','帮助','问题','自己','需要','探索','进行','以及','不能','开始','不是']);
 function terms(s){const out=new Set();for(const run of String(s||'').toLowerCase().match(/[\u3400-\u9fff]+|[a-z0-9]+/g)||[]){if(/^[a-z0-9]+$/.test(run)){if(run.length>1)out.add(run);continue;}if(run.length===1)out.add(run);for(let n=2;n<=3;n++)for(let i=0;i+n<=run.length;i++){const t=run.slice(i,i+n);if(!STOP.has(t))out.add(t);}}return [...out].slice(0,240);}
 function create(corpus,points){const units=new Map(corpus.units.map(u=>[u.id,u]));const summaries=new Map(points.units.map(u=>[u.id,u]));const indexed=corpus.chunks.map(c=>{const u=units.get(c.unitId);return {...c,unit:u,text:u.rawMarkdown.slice(c.start,c.end),titleText:u.title.toLowerCase(),headingText:c.heading.toLowerCase()};});
  function rank(q,selected){const ts=terms(q);const freqs=new Map(ts.map(t=>[t,indexed.reduce((n,c)=>n+(c.text.toLowerCase().includes(t)?1:0),0)]));return indexed.map(c=>{let score=0;const tx=c.text.toLowerCase();for(const t of ts){const idf=1+Math.log((indexed.length+1)/(1+freqs.get(t)));score+=idf*(c.titleText.includes(t)?4.5:0)+idf*(c.headingText.includes(t)?3:0)+idf*(tx.includes(t)?1:0);}if(selected&&c.unitId===selected)score+=1000;return {...c,score};}).filter(c=>c.score>0||(!ts.length&&(!selected||c.unitId===selected))).sort((a,b)=>b.score-a.score||a.unit.order-b.unit.order||a.start-b.start);}
  function context(q,selected,maxChars=48000){const ranked=rank(q,selected);const sources=[];const seen=new Set();let used=0;const add=(c)=>{if(seen.has(c.id)||used+c.text.length>maxChars)return false;seen.add(c.id);sources.push(c);used+=c.text.length;return true;};
   if(selected&&units.has(selected)){const u=units.get(selected);add({id:selected+'-full',unitId:selected,unit:u,heading:'本单元完整原文',text:u.rawMarkdown,start:0,end:u.rawMarkdown.length,complete:true});}
   const unitUse=new Map();for(const c of ranked){if(selected&&c.unitId===selected)continue;if(sources.length>=13)break;const n=unitUse.get(c.unitId)||0;if(n>=3)continue;if(add(c))unitUse.set(c.unitId,n+1);}
   if(!sources.length){const c=indexed.find(c=>c.unitId==='intro');if(c)add(c);}
   const header='【本轮来源范围】以下是《人性发生学导论》本轮选定的章节原文，并非全书。每个[源N]后均注明单元与范围；没有给出的章节只有编辑摘要时，不得声称读过其正文。来源列表表明提供了哪些材料，不代表某个结论已经被这些材料证明。\n\n';
   const docText=header+sources.map((c,i)=>'[源'+(i+1)+'] '+c.unit.title+' / '+c.heading+'\n来源：https://sdeuniverses.com'+c.unit.url+'\n范围：'+(c.complete?'本单元完整原文':'原文字符区间 '+c.start+'–'+c.end)+'\n'+c.text).join('\n\n');
   return {sources,docText,rawChars:used,selectedUnit:selected||null};
  }
  return {units,summaries,indexed,rank,context};
 }
 return {terms,create};
});
