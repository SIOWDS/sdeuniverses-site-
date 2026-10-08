(async function(){
'use strict';
const $=id=>document.getElementById(id),B='/books/m/7/',C=M7;
let rules,data,sources,cross=[],q,events=[],fp='',gate='read',prepared=null,busy=false,sending=false,controller,focus=null;
const labels={initial:'封存初答',reanswer:'读后复答',objection:'异议或错题',plan:'行动计划',observation:'实践观察',review:'延后回看',revision:'本人修订',request:'已确认发送',receipt:'模型答复',draft:'流式草稿'};
function esc(t){return String(t??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function status(id,t,bad=false){$(id).textContent=t;$(id).className='status'+(bad?' error':'')}
function error(e){status('globalStatus',e.message||String(e),true)}
function invalidate(){prepared=null;$('preview').hidden=true;$('confirmSend').checked=false}
async function j(u){const r=await fetch(u);if(!r.ok)throw Error('资料未载入：'+u);return r.json()}
function nav(){const qs='?problem='+q.id;$('navRead').href=sources.find(s=>s.id===q.sourceIds[0]).url.replace('#',qs+'#');$('navLearn').href=B+'agent/learning.html'+qs;$('navAgent').href=B+'agent/'+qs}
function list(){const f=$('filter').value.trim().toLowerCase();$('questionList').innerHTML=data.parts.map(p=>'<h3>第'+p.part+'篇 · '+esc(p.title)+'</h3>'+data.questions.filter(x=>x.part===p.part&&(!f||(x.title+x.task+p.title).toLowerCase().includes(f))).map(x=>'<button data-q="'+x.id+'" class="'+(q?.id===x.id?'active':'')+'">'+esc(x.title)+'</button>').join('')).join('');document.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>choose(b.dataset.q))}
async function choose(id){if(busy){status('globalStatus','请先等待或停止当前问对。');return}if(($('recordText').value||$('revision').value)&&q&&q.id!==id&&!confirm('当前未保存的文字仍在输入框；切换问题前请先保存。仍要切换吗？'))return;
 q=data.questions.find(x=>x.id===id)||data.questions[0];history.replaceState(null,'','?problem='+q.id);invalidate();focus=null;
 try{const f=JSON.parse(sessionStorage.getItem('m7-focus')||'null');if(f&&f.problemId===q.id){focus=f;$('focusInfo').innerHTML='<p class="status">从阅读现场带来：'+esc(f.label)+'。选句将在材料预览中单列。</p>'}else $('focusInfo').textContent=''}catch(e){}
 $('partTitle').textContent='第'+q.part+'篇 · '+q.id+' · 原文v1.0';$('questionTitle').textContent=q.title;$('why').textContent=q.why;$('task').textContent=q.task;$('check').textContent='检验：'+q.check;$('quote').textContent=q.quote;
 $('ask').value='请就“'+q.title+'”给我一个关键提示。';$('recordText').value='';$('revision').value='';$('sourceLinks').innerHTML=q.sourceIds.map(id=>{const s=sources.find(x=>x.id===id);return '<a class="button" href="'+s.url.replace('#','?problem='+q.id+'#')+'">带问读原文</a><a class="button" href="'+B+'read.html?problem='+q.id+'&page='+s.pdfPage+'">翻到第'+s.pdfPage+'页</a>'}).join('');
 $('sourceChoices').innerHTML=[...new Set(q.sourceIds.concat(focus?.sourceId?[focus.sourceId]:[]))].map(id=>{const s=sources.find(x=>x.id===id);return '<label class="row"><input type="checkbox" data-source="'+id+'" checked>原文：'+esc(s.title)+'（'+s.text.length+'字符）</label>'}).join('');
 $('crossChoices').innerHTML='<details><summary>跨书对读 · '+cross.length+'份已核原段</summary>'+cross.map(s=>'<label class="row"><input type="checkbox" data-cross="'+s.id+'">'+esc(s.title)+'</label><details><summary>查看段落与出处</summary><p class="source">'+esc(s.text)+'</p><a href="'+s.url+'" target="_blank" rel="noopener">原文出处</a></details>').join('')+'</details>';
 list();nav();await refresh();$('workspace').hidden=false;status('globalStatus','本题档案已打开。先写初答，或直接带问阅读。');
 if(location.pathname.endsWith('/agent/')||location.pathname.endsWith('/agent/index.html'))$('dialogue').scrollIntoView({block:'start'});
}
async function refresh(){events=(await C.all()).filter(e=>e.problemId===q.id).sort((a,b)=>a.at.localeCompare(b.at)||a.id.localeCompare(b.id));fp=C.fingerprint(events);renderHistory();invalidate()}
function renderHistory(){
 const has=events.some(e=>e.type==='initial');$('recordType').options[0].disabled=has;if(has&&$('recordType').value==='initial')$('recordType').value='reanswer';
 const privateEvents=events.filter(e=>['initial','reanswer','objection','plan','observation','review','revision','receipt'].includes(e.type));
 $('recordChoices').innerHTML='<p class="muted">本题个人记录（默认不发送）</p>'+privateEvents.map(e=>'<label class="row"><input type="checkbox" data-record="'+e.id+'">'+esc(labels[e.type])+' · '+esc(e.at)+' · '+esc((e.text||'').slice(0,60))+'</label>').join('');
 $('receiptSelect').innerHTML='<option value="">独立修订 · 不依赖某条模型答复</option>'+events.filter(e=>e.type==='receipt'&&e.status==='complete').map(e=>'<option value="'+e.id+'">完整建议 · '+esc(e.at)+'</option>').join('');
 $('history').innerHTML=events.map(e=>'<details class="record" '+(['initial','receipt','revision'].includes(e.type)?'open':'')+'><summary>'+esc(labels[e.type]||e.type)+' <span class="badge">'+esc(e.status||(e.type==='receipt'?'未核对建议':'本人记录'))+'</span> · '+esc(e.at)+'</summary><p>'+esc(e.text||e.question||'')+'</p>'+(e.type==='receipt'?'<p class="muted">'+esc(e.status==='complete'?'完整答复 · 尚未由本人核对':'未完成答复 · 不可作为完整建议采纳')+'</p>':'')+(e.sourceIds?e.sourceIds.map(id=>{const s=sources.find(x=>x.id===id)||cross.find(x=>x.id===id);return s?'<a class="step-link" href="'+s.url+'">复核：'+esc(s.title)+'</a>':''}).join(''):'')+'<details><summary>记录身份与回执</summary><pre>'+esc(JSON.stringify(e,null,2))+'</pre></details></details>').join('')||'<p class="muted">还没有记录。你的第一份理解将保存在这里。</p>';
}
async function save(type,text,extra={}){if(!text.trim())throw Error('先写一点内容，也可以明确写不知道或暂不判断。');await C.append(q.id,type,{text,sourceIds:q.sourceIds,sourceHash:q.sourceHash,questionVersion:q.questionVersion,...extra},fp);await refresh()}
const gates={read:'读懂',apply:'用上',cut:'拆开',clash:'对撞',write:'写出'};
$('gates').innerHTML=Object.entries(gates).map(([k,t])=>'<button data-gate="'+k+'" aria-pressed="'+(k===gate)+'">'+t+'</button>').join('');document.querySelectorAll('[data-gate]').forEach(b=>b.onclick=()=>{gate=b.dataset.gate;document.querySelectorAll('[data-gate]').forEach(x=>x.setAttribute('aria-pressed',x===b));invalidate()});
$('filter').oninput=list;$('theme').onclick=()=>document.body.classList.toggle('dark');
$('saveRecord').onclick=async()=>{try{await save($('recordType').value,$('recordText').value);$('recordText').value='';status('recordsStatus','已追加保存。初答与旧记录仍保留。')}catch(e){status('recordsStatus',e.message,true)}};
$('refreshRecords').onclick=async()=>{try{await refresh();status('recordsStatus','已更新档案，输入仍保留。')}catch(e){error(e)}};
$('saveRevision').onclick=async()=>{try{if(!$('confirmRevision').checked)throw Error('请由本人勾选确认。');const rid=$('receiptSelect').value,decision=$('decision').value;if(decision!=='independent'&&!rid)throw Error('请选择一条完整建议，或改为独立修订。');await save('revision',$('revision').value,{receiptId:rid||null,decision,confirmedBy:'reader',confirmedAt:new Date().toISOString()});$('revision').value='';$('confirmRevision').checked=false;status('recordsStatus','本人修订已另行保存，模型建议未覆盖初答。')}catch(e){error(e)}};
$('export').onclick=()=>C.backup().catch(error);
$('import').onchange=async()=>{try{const f=$('import').files[0];if(!f)return;const packet=JSON.parse(await f.text());if(packet.events?.some(e=>!data.questions.some(q=>q.id===e.problemId)))throw Error('含未知问题ID，未导入');await C.backup();await C.merge(packet);await refresh();status('globalStatus','已先导出旧档案，再合并导入；旧记录保留。')}catch(e){error(e)}finally{$('import').value=''}};
$('publicDraft').onclick=()=>{const revisions=events.filter(e=>e.type==='revision');if(!revisions.length){error(Error('先登记本人修订，再导出草案。'));return}const selected=prompt('输入愿意单独整理的本人修订编号（1—'+revisions.length+'）。导出后请自行脱敏；不会自动投稿。',String(revisions.length));if(!selected)return;const e=revisions[Number(selected)-1];if(!e){error(Error('编号不符'));return}C.download('中华文化导论_待审核增补草案.json',{unitId:'m-7',status:'本人待脱敏检查，未投稿、未审定',problemId:q.id,title:q.title,text:e.text,sourceIds:e.sourceIds})};
function selections(){return{sourceIds:[...document.querySelectorAll('[data-source]:checked')].map(x=>x.dataset.source),recordIds:[...document.querySelectorAll('[data-record]:checked')].map(x=>x.dataset.record),crossIds:[...document.querySelectorAll('[data-cross]:checked')].map(x=>x.dataset.cross)}}
function uiSignature(){return C.canon({q:$('ask').value,gate,task:$('route').value,vendor:$('vendor').value,selection:selections(),problem:q.id,fp,focus})}
document.querySelectorAll('#dialogue input:not(#key):not(#confirmSend),#dialogue select,#ask').forEach(x=>x.addEventListener('input',invalidate));$('sourceChoices').onchange=$('recordChoices').onchange=$('crossChoices').onchange=invalidate;
$('prepare').onclick=async()=>{try{if(busy)return;const question=$('ask').value.trim();if(!question)throw Error('请先写下这一问。');const signature=uiSignature(),sel=selections();if(!sel.sourceIds.length)throw Error('请至少选择一处本书原文。');const current=(await C.all()).filter(e=>e.problemId===q.id);if(C.fingerprint(current)!==fp)throw Error('本题档案已变化，请先刷新记录后重新预览。');
 const records=events.filter(e=>sel.recordIds.includes(e.id));
 const payload={unitId:'m-7',problemId:q.id,requestId:C.uid(),sourceEdition:'v1.0',questionVersion:q.questionVersion,rulesVersion:'m7-1.0.0',gate,task:$('route').value,vendor:$('vendor').value,question,problem:{title:q.title,task:q.task,check:q.check},sources:sel.sourceIds.map(id=>sources.find(x=>x.id===id)),cross:sel.crossIds.map(id=>cross.find(x=>x.id===id)),records,focus:focus||null};
 if(C.canon(payload).length>90000)throw Error('选入材料超过9万字符；请减少本次选择。完整档案不会裁剪。');
 const payloadHash=await C.hash(payload);if(signature!==uiSignature())throw Error('材料在准备时发生变化，请重新预览。');prepared={payload,payloadHash,signature};$('previewMeta').textContent=records.length+'条个人记录 · '+payload.sources.length+'处原文 · '+payload.cross.length+'份对读材料 · '+C.canon(payload).length+'字符 · 请求 '+payload.requestId;$('previewText').textContent='【固定问对规则】\n'+rules.rules+'\n'+rules.gates[gate]+'\n本轮任务：'+rules.tasks[payload.task]+'\n\n【所选材料】\n'+JSON.stringify(payload,null,2);$('confirmSend').checked=false;$('preview').hidden=false;
 }catch(e){error(e)}};
try{$('key').value=sessionStorage.getItem('m7-key')||localStorage.getItem('m7-key')||'';$('vendor').value=localStorage.getItem('m7-vendor')||'ds'}catch(e){}
$('clearKey').onclick=()=>{try{localStorage.removeItem('m7-key');sessionStorage.removeItem('m7-key')}catch(e){}$('key').value='';status('answerStatus','本页保存的Key已清除。')};
$('cancel').onclick=()=>controller?.abort();
$('send').onclick=async()=>{
 if(busy||sending)return;sending=true;
 let sent,answer='',completion='interrupted',receiptMeta=null,lastSaved=0,sendEvent;
 try{
  if(!prepared||!$('confirmSend').checked)throw Error('请先预览并确认本次材料。');if(uiSignature()!==prepared.signature)throw Error('材料已变化，请重新预览。');
  const key=$('key').value.trim();if(key.length<8)throw Error('请填写自己的模型Key；尚未调用模型。');
  sent=prepared;const pid=sent.payload.problemId;
  sendEvent=await C.append(pid,'request',{requestId:sent.payload.requestId,payloadHash:sent.payloadHash,payload:sent.payload,question:sent.payload.question,status:'sent'},fp);
  if($('rememberKey').checked){try{localStorage.setItem('m7-key',key);localStorage.setItem('m7-vendor',sent.payload.vendor)}catch(e){}}
  busy=true;$('send').disabled=true;$('cancel').disabled=false;$('prepare').disabled=true;$('liveAnswer').hidden=false;$('liveAnswer').textContent='';controller=new AbortController();status('answerStatus','请求已登记；等待模型。');
  const r=await fetch('/api/wds/read',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({unitId:'m-7',bookagent:1,q:sent.payload.question,docTitle:'中华文化导论',vendor:sent.payload.vendor,key,payload:sent.payload,payloadHash:sent.payloadHash}),signal:controller.signal});
  if(!r.ok){let j={};try{j=await r.json()}catch(e){}throw Error(j.error||'接口返回 HTTP '+r.status)}if(!r.body)throw Error('接口未返回数据流');
  const rd=r.body.getReader(),dec=new TextDecoder();let buf='',ended=false;
  async function line(v){if(!v.startsWith('data:'))return;const z=v.slice(5).trim();if(!z||z==='[DONE]')return;let x;try{x=JSON.parse(z)}catch(e){throw Error('响应数据未能解析')}
   if(x.requestId&&x.requestId!==sent.payload.requestId)throw Error('响应请求身份不匹配');if(x.problemId&&x.problemId!==pid)throw Error('响应题号不匹配');
   if(x.t==='token'){answer+=x.v;$('liveAnswer').textContent=answer;if(answer.length-lastSaved>5000){await C.append(pid,'draft',{requestId:sent.payload.requestId,text:answer,status:'streaming'});lastSaved=answer.length}}
   if(x.t==='error')throw Error(x.v||'模型未完成');
   if(x.t==='end'){ended=true;receiptMeta=x.v;if(x.v?.status==='complete'&&x.v?.finishReason==='stop'&&answer.trim()&&x.v?.payloadHash===sent.payloadHash)completion='complete';else completion=x.v?.status||'interrupted'}
  }
  while(true){const z=await rd.read();if(z.done)break;buf+=dec.decode(z.value,{stream:true});let i;while((i=buf.indexOf('\n'))>=0){await line(buf.slice(0,i).trim());buf=buf.slice(i+1)}}if(buf.trim())await line(buf.trim());if(!ended)completion='interrupted';if(completion==='complete'&&await C.hash(answer)!==receiptMeta.responseHash)throw Error('回答内容校验不符，保留为未完成记录');
 }catch(e){if(!busy){error(e);return}completion=e.name==='AbortError'?'cancelled':'error';status('answerStatus',e.name==='AbortError'?'已停止，已有文字保留为未完成草稿。':e.message,true)}
 finally{sending=false;if(busy&&sent){try{await C.append(sent.payload.problemId,'receipt',{requestId:sent.payload.requestId,payloadHash:sent.payloadHash,text:answer,status:completion,meta:receiptMeta,sourceIds:sent.payload.sources.map(s=>s.id),crossIds:sent.payload.cross.map(s=>s.id),modelAdvice:true,verifiedByReader:false});status('answerStatus',completion==='complete'?'完整建议已回到本题档案，等你复核与确认。':'本次答复未完成，已按实际状态保存；重试需重新预览。',completion!=='complete');await refresh()}catch(e){error(Error('回执保存失败，请复制当前回答并导出旧档案：'+e.message))}busy=false;$('send').disabled=false;$('cancel').disabled=true;$('prepare').disabled=false;prepared=null;}}
};
try{[data,sources,cross,rules]=await Promise.all([j(B+'agent/learning.json'),j(B+'agent/sources.json'),j(B+'agent/cross.json'),j(B+'agent/rules.json')]);sources=sources.sources;cross=cross.sources||[];await choose(new URLSearchParams(location.search).get('problem')||data.questions[0].id)}catch(e){error(e)}
})();
