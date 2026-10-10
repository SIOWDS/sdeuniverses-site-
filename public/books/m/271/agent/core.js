/* 本书局部原文选择与请求组装；无网络、凭证或自动发送行为。 */
(function(root){
'use strict';
var REV='20261010-m271-unit-v1';
function grams(s){var a={},t=String(s||'').replace(/[^\u4e00-\u9fff]/g,'');for(var i=0;i<t.length-1;i++)a[t.slice(i,i+2)]=1;return a}
function validate(corpus,rag,kp,spec){
 if(!corpus||!Array.isArray(corpus.units)||corpus.units.length!==51)throw new Error('原文包应包含51个阅读单元');
 [corpus,rag,kp,spec].forEach(function(x){if(!x||x.no!==271||x.revision!==REV)throw new Error('原文与问答规范版本不一致')});
 var ids=new Set(corpus.units.map(function(u){return u.id}));
 if(ids.size!==51||!ids.has('ch40')||!ids.has('references'))throw new Error('阅读单元不完整');
 if(!rag.items.length||new Set(rag.items.map(function(x){return x.unit})).size!==51||kp.items.length!==51)throw new Error('知识包覆盖不完整');
 return true;
}
function queryState(search,units){
 var p=new URLSearchParams(search),v=p.get('chapter'),id=v&&/^\d+$/.test(v)?'ch'+String(+v).padStart(2,'0'):v;
 var i=units.findIndex(function(u){return u.id===id}),q=p.get('prompt')||'';
 return{selected:i>=0?[i]:null,prompt:q,invalidChapter:!!v&&i<0};
}
function explicitUnits(q){var ids=[],m,re=/第\s*([0-9]{1,2})\s*章/g;while((m=re.exec(q)))if(+m[1]>=1&&+m[1]<=40)ids.push('ch'+String(+m[1]).padStart(2,'0'));
 var nums=['一','二','三','四','五','六','七','八','九'];q.replace(/第([一二三四五六七八九十]{1,3})章/g,function(_,s){var n=s==='十'?10:s.includes('十')?(s[0]==='十'?10:(nums.indexOf(s[0])+1)*10)+(s.endsWith('十')?0:nums.indexOf(s.slice(-1))+1):nums.indexOf(s)+1;if(n>0&&n<=40)ids.push('ch'+String(n).padStart(2,'0'))});
 if(/导论/.test(q))ids.push('intro');if(/结语/.test(q))ids.push('conclusion');if(/参考/.test(q))ids.push('references');q.replace(/附录\s*([a-h])/gi,function(_,c){ids.push('appendix-'+c.toLowerCase())});return ids;
}
function retrieve(q,act,rag,units,selected,k){
 var g=grams(q),explicit=explicitUnits(q),on=new Set((selected||[]).map(function(i){return units[i].id}));
 var scored=rag.items.map(function(it,index){var hit=0,h=grams(it.x+' '+it.ch);Object.keys(g).forEach(function(x){if(h[x])hit++});var score=hit+(explicit.includes(it.unit)?22:0)+(on.has(it.unit)?1.5:0);return{it:it,score:score,index:index}}).filter(function(x){return x.score>0}).sort(function(a,b){return b.score-a.score||a.index-b.index});
 var out=[],size=0,per={};scored.some(function(x){if((per[x.it.unit]||0)>=4)return false;var block='【本书原文 · '+x.it.t+' · '+x.it.ch+'】\n来源：'+x.it.u+'\n'+x.it.x;if(size+block.length>11000)return false;out.push(x.it);size+=block.length;per[x.it.unit]=(per[x.it.unit]||0)+1;return out.length>=(k||10)});
 return{text:'以下均为本书原文检索片段。段落含有作者对经文和传统的解释，不能把整段一概当作圣经原句或外部原典。表格行以制表符分列。\n\n'+out.map(function(it){return'【本书原文 · '+it.t+' · '+it.ch+'】\n来源：'+it.u+'\n'+it.x}).join('\n\n'),items:out};
}
function docText(units,selected,cap){
 cap=cap||110000;var keep=[],skipped=[],used=0,sel=Array.isArray(selected)?selected:[0,1];
 sel.forEach(function(i){var u=units[i];if(!u)return;var block='【本书原文 · '+u.t+'】\n来源：'+u.u+'\n'+u.x;if(used+block.length<=cap-5000){keep.push(block);used+=block.length}else skipped.push(u.t)});
 var included=new Set(sel.filter(function(i){return units[i]&&!skipped.includes(units[i].t)}));
 var toc='【阅读范围说明】只把下面明确标为“本书原文”的正文和bookRag片段当作已提供的原文。目录仅供定位，不是原文证据。\n【全书51单元目录】\n'+units.map(function(u,i){return(included.has(i)?'已提供正文：':'未提供正文：')+u.t+' '+u.u}).join('\n');
 return toc+'\n\n'+keep.join('\n\n')+(skipped.length?'\n【因长度未提供的所选单元】'+skipped.join('；'):'');
}
function policy(spec){return '【善问公开问答规范：不是本书原文】\n'+spec.publicPolicy.map(function(p,i){return(i+1)+'. '+p}).join('\n')}
function points(kp,spec){return policy(spec)+'\n\n【51单元原文节录：检索入口，不是完整章摘要】\n'+kp.items.map(function(it){return it.t+'：'+it.x+'\n来源：'+it.url}).join('\n')}
function meta(book,spec){return '德麦国际第271卷《耶稣之善》 · 王德生 著 · '+spec.sourceEdition+' · '+REV+'\n'+policy(spec)}
function payload(q,act,state){var rp=retrieve(q,act,state.rag,state.units,state.selected,10);return{request:{q:q,bookagent:1,bookNo:271,act:act,agentName:'善问',agentEpithet:state.spec.agent.epithet,bookRag:rp.text,bookPoints:points(state.kp,state.spec),bookMeta:meta(state.book,state.spec),docTitle:'耶稣之善',docText:docText(state.units,state.selected),history:state.history},sources:rp.items.map(function(it){return{t:it.t+' · '+it.ch,u:it.u,rel:'本书原文'}})}}
var api={revision:REV,validate:validate,queryState:queryState,explicitUnits:explicitUnits,retrieve:retrieve,docText:docText,policy:policy,points:points,meta:meta,payload:payload};
if(typeof module==='object'&&module.exports)module.exports=api;else root.ShanwenCore=api;
})(typeof window==='object'?window:globalThis);
