(function(){'use strict';
const C=window.M271Core,$=id=>document.getElementById(id),B='/books/m/271/';
const FIELDS=['initial','reanswer','position','question','modelnote','revision','plan','observation','based-on','material'];
const LABELS={initial:'初答 · 已封存',reanswer:'复答版本',position:'理解与异议',modelnote:'讨论建议 · 待核对',revision:'本人确认修订',plan:'迁移计划',observation:'实际观察 · 读者自报',material:'同题材料预览 · 可修改'};
let manifest,current=1,events=[],drafts=[],ready=false,switching=false,storageOK=true,channel,draftTimer;
const memory=new Map(),pending=[],dirty=new Set();
const text=(id,value)=>{$(id).textContent=value==null?'':String(value);};
const el=(tag,value,cls)=>{const e=document.createElement(tag);if(value!==undefined)e.textContent=String(value);if(cls)e.className=cls;return e;};
function say(message,error=false){text('status',message);$('status').classList.toggle('error',error);}
function guarded(fn){return async(...args)=>{try{return await fn(...args);}catch(err){say(err.message||String(err),true);}};}
function card(){return manifest.chapters.find(x=>x.chapter===current);}
function own(){return events.filter(x=>x.chapter===current);}
function snapshot(){const t=card();return {edition:manifest.sourceEdition,revision:manifest.revision,chapter:current,title:t.title,url:t.sourceUrl,sha256:t.sourceHash};}
function capture(){const fields={};FIELDS.forEach(k=>fields[k]=$(k).value);return {id:'fields:'+current,book:C.BOOK,chapter:current,updatedAt:C.now(),sourceSnapshot:snapshot(),fields};}
function describe(value){if(typeof value==='string')return value;if(value&&typeof value==='object')return value.label||value.title||value.reference||value.text||JSON.stringify(value);return String(value??'');}
function list(id,values){$(id).replaceChildren();(Array.isArray(values)?values:values?[values]:[]).forEach(v=>$(id).append(el('li',describe(v))));}
function validateManifest(m){
 if(!m||m.unitId!==C.BOOK||!Array.isArray(m.chapters)||m.chapters.length!==40)throw Error('四十章学习材料尚未完整载入，请稍后重试。');
 const ns=new Set();for(const t of m.chapters){if(!C.chapter(t.chapter)||ns.has(t.chapter)||typeof t.title!=='string'||typeof t.beforeQuestion!=='string')throw Error('学习任务章号或内容不完整。');ns.add(t.chapter);}
 return m;
}
function sourceURL(value){const u=new URL(value,location.href);if(![location.origin,'https://sdeuniverses.com','https://www.sdeuniverses.com'].includes(u.origin)||!u.pathname.startsWith(B))throw Error('本章原文链接与本书不符。');return u.href;}
function agentURL(t){const params=new URLSearchParams({chapter:String(t.chapter),prompt:t.agentPrompt||'请围绕《耶稣之善》第'+t.chapter+'章，与我讨论：'+t.beforeQuestion});return B+'agent/?'+params.toString();}
async function persistDraft(){if(!ready)return;clearTimeout(draftTimer);const draft=capture();memory.set(current,draft);try{await C.saveDraft(draft);storageOK=true;if(current===draft.chapter&&C.stable(capture().fields)===C.stable(draft.fields))dirty.delete(draft.chapter);}catch(err){dirty.add(draft.chapter);storageOK=false;say('当前文字仍保留在页面内，但尚未保存到浏览器。请先“导出备份”带走文字。',true);}}
async function loadRecords(){try{const all=await Promise.all([C.read('events'),C.read('drafts')]);events=all[0].sort((a,b)=>a.createdAt.localeCompare(b.createdAt)||a.id.localeCompare(b.id));drafts=all[1];storageOK=true;}catch(err){storageOK=false;say('本地保存暂不可用，仍可阅读任务和填写；离开前请导出备份。',true);}}
function renderProgress(){const total=new Set(events.filter(e=>e.type==='initial').map(e=>e.chapter)).size;text('progress','已留下初答 '+total+' / 40 章');document.querySelectorAll('[data-chapter]').forEach(a=>{a.setAttribute('aria-current',Number(a.dataset.chapter)===current?'page':'false');});}
function renderHistory(){
 const box=$('history');box.replaceChildren();const records=own();if(!records.length)box.append(el('p','本章还没有已保存的记录。','muted small'));
 for(const e of records){const d=el('details'),when=new Date(e.createdAt).toLocaleString('zh-CN',{hour12:false});d.append(el('summary',(LABELS[e.type]||e.type)+' · '+when,'record-summary'));d.append(el('div',e.data.text,'preserved'));if(e.type==='revision'&&e.data.basedOnId)d.append(el('p','参照讨论建议：'+e.data.basedOnId.slice(0,8),'small muted'));d.append(el('p','记录时原文：'+(e.sourceSnapshot?.edition||'未记载'),'small muted'));box.append(d);}
 const selected=$('based-on').value;$('based-on').replaceChildren(new Option('独立修订／未采纳建议',''));records.filter(e=>e.type==='modelnote').forEach(e=>$('based-on').add(new Option('讨论建议 · '+new Date(e.createdAt).toLocaleString('zh-CN'),e.id)));$('based-on').value=selected;
 const initial=records.find(e=>e.type==='initial');$('initial').disabled=!!initial;$('save-initial').disabled=!!initial;if(initial){$('initial').value=initial.data.text;text('initial-state','初答已封存。请在复答中继续，不覆盖起点。');}else text('initial-state','封存后保留原样，后续另写复答。');
 const imported=drafts.filter(d=>d.chapter===current&&d.id.startsWith('import:'));$('imported-box').hidden=!imported.length;$('imported-drafts').replaceChildren();
 imported.forEach(d=>{const div=el('div',undefined,'imported-draft'),preview=el('details');preview.append(el('summary',d.pendingEvent?'找回未保存版本 · '+new Date(d.pendingEvent.createdAt).toLocaleString('zh-CN'):'查看这份草稿'));if(d.pendingEvent)preview.append(el('p','这是尚未写入历史的版本。恢复后仍需保存；修订需由本人重新确认。','small muted'));for(const [key,value] of Object.entries(d.fields))if(value)preview.append(el('div',(d.pendingEvent&&key==='initial'?'初答 · 未保存':LABELS[key]||{'question':'追问','based-on':'参照记录'}[key]||key)+'\n'+value,'preserved'));div.append(preview);const b=el('button','恢复到当前输入区');b.type='button';b.onclick=guarded(async()=>{
  if(!confirm('现有输入也会保留为另一份草稿。恢复这份导入草稿？'))return;
  const old=capture();await C.saveDraft({...old,id:'import:'+C.uid(),importedFromId:old.id});for(const k of FIELDS)if(k!=='initial'||!own().some(e=>e.type==='initial'))$(k).value=d.fields[k]||'';
  $('confirm-revision').checked=false;$('include-personal').checked=false;$('material-box').hidden=!$('material').value.trim();await persistDraft();await loadRecords();renderHistory();say('已恢复草稿。旧输入仍保留在“其他草稿”中。');
 });div.append(b);$('imported-drafts').append(div);});renderProgress();
}
async function showChapter(n,save=true){
 if(!C.chapter(n)||switching)return;switching=true;
 try{if(save&&ready)await persistDraft();current=n;const t=card();history.replaceState(null,'','?chapter='+n);$('chapter-select').value=String(n);text('chapter-number','第 '+n+' 章 · '+(t.partTitle||'第 '+Math.ceil(n/5)+' 编'));text('chapter-title',t.title);text('focus',t.focus);text('before-question',t.beforeQuestion);text('evidence-task',describe(t.evidenceTask));text('dialogue-task',describe(t.dialogueTask));text('sde-task',describe(t.sdeTask));text('transfer-task',describe(t.transferTask));text('pitfall',describe(t.pitfall));list('scriptures',t.scriptures);list('source-sections',t.sourceSections);list('checklist',t.checklist);text('source-text',t.sourceText||'请通过原文链接阅读本章。');$('source-link').href=sourceURL(t.sourceUrl||B+'chapters.html');
 const url=agentURL(t);['agent-nav','agent-link','agent-discuss'].forEach(id=>{$(id).href=url;});
 text('source-version','原文版本：'+(manifest.sourceEdition||'出版版')+' · 本章任务与原文相互参照');
 $('include-personal').checked=false;$('confirm-revision').checked=false;
 const stored=memory.get(n)||drafts.find(d=>d.id==='fields:'+n);FIELDS.forEach(k=>$(k).value=stored?.fields[k]||'');
 $('material-box').hidden=!$('material').value.trim();
 renderHistory();if(stored?.fields['based-on'])$('based-on').value=stored.fields['based-on'];
 $('previous').disabled=n===1;$('next').disabled=n===40;document.querySelectorAll('.part').forEach(d=>{if(d.querySelector('[data-chapter="'+n+'"]'))d.open=true;});
 }finally{switching=false;}
}
async function saveEvent(type){
 if(switching)throw Error('正在切换章节，请稍后。');const value=$(type).value.trim();if(!value)throw Error(type==='initial'?'可以写“不知道”，但请先留下自己的起点。':'请先填写内容。');
 const data={text:value};if(type==='revision'){if(!$('confirm-revision').checked)throw Error('请核对修订，并勾选本人确认。');data.confirmedBy='reader';data.confirmedAt=C.now();data.basedOnId=$('based-on').value||null;}if(type==='observation')data.evidenceType='reader-self-report';if(type==='plan')data.evidenceType='plan-not-result';if(type==='modelnote')data.evidenceType='discussion-not-verified';
 const e=C.event(current,type,data,snapshot());try{await C.append(e);}catch(err){pending.push(e);throw Error('本次记录未保存，文字仍在输入区。请导出备份。'+err.message);}
 await persistDraft();await loadRecords();renderHistory();if(type==='revision')$('confirm-revision').checked=false;if(channel)channel.postMessage('changed');say(type==='initial'?'初答已封存。阅读后可另存复答版本。':'已保存新版本，旧记录仍完整保留。');
}
function buildMaterial(){const t=card();let content='《耶稣之善》第'+current+'章：'+t.title+'\n原文：'+t.sourceUrl+'\n版本：'+manifest.sourceEdition+'\n\n【同题任务】\n'+(t.agentPrompt||t.beforeQuestion)+'\n\n【经文线索】\n'+(t.scriptures||[]).map(describe).join('；')+'\n\n【待核对的小节】\n'+(t.sourceSections||[]).map(describe).join('；');
 if($('question').value.trim())content+='\n\n【我当前的追问】\n'+$('question').value.trim();
 if($('include-personal').checked){content+='\n\n【读者本章材料；个人判断与草稿，不是作者原文】';for(const k of ['initial','reanswer','position','modelnote','revision','plan','observation']){const value=$(k).value.trim();if(value)content+='\n\n'+LABELS[k]+(k==='revision'?'（当前输入；是否确认请以档案为准）':'')+'\n'+value;}}
 content+='\n\n请区分经文陈述、历史事实、神学解释与模型推论；不以认同作者作为学习评价。若原文或证据不足，请明确指出。';$('material').value=content;$('material-box').hidden=false;say('材料已在下方生成，尚未发送。可检查、修改后复制或下载。');
}
function download(value,name,type='application/json;charset=utf-8'){const content=typeof value==='string'?value:JSON.stringify(value,null,2),u=URL.createObjectURL(new Blob([content],{type})),a=el('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),10000);}
async function exportArchive(rescue=false){await persistDraft();let a;try{a=await C.archive();}catch(err){if(!rescue)throw Error('本地档案暂不可读，请使用页面末尾“导出备份”。');a={schemaVersion:C.VERSION,unitId:C.BOOK,exportedAt:C.now(),events:[...events],drafts:[],extensions:[]};}
 const map=new Map(a.drafts.map(d=>[d.id,d]));for(const draft of memory.values())map.set(draft.id,draft);a.drafts=[...map.values()];if(pending.length)a.pendingUnstored=pending.slice();if(rescue)a.rescue=true;download(a,'耶稣之善-第271卷-'+(rescue?'学习备份':'学习档案')+'-'+new Date().toISOString().slice(0,10)+'.json');say('已生成下载文件，请保存。它包含个人学习文字。');}
function buildNavigation(){const select=$('chapter-select'),box=$('lessons');for(let p=0;p<8;p++){const group=manifest.chapters.filter(t=>Math.ceil(t.chapter/5)===p+1),details=el('details',undefined,'part');details.append(el('summary','第'+(p+1)+'编 · '+(group[0]?.partTitle||(p*5+1)+'—'+(p*5+5)+'章')));group.forEach(t=>{select.add(new Option(String(t.chapter).padStart(2,'0')+' · '+t.title,t.chapter));const a=el('a',String(t.chapter).padStart(2,'0')+' '+t.title,'lesson-link');a.href='?chapter='+t.chapter;a.dataset.chapter=t.chapter;a.onclick=guarded(async e=>{e.preventDefault();await showChapter(t.chapter);});details.append(a);});box.append(details);}}
function bind(){
 $('chapter-select').onchange=guarded(()=>showChapter(Number($('chapter-select').value)));
 $('previous').onclick=guarded(async()=>{await showChapter(current-1);$('workspace').scrollIntoView({block:'start'});});$('next').onclick=guarded(async()=>{await showChapter(current+1);$('workspace').scrollIntoView({block:'start'});});
 FIELDS.forEach(k=>$(k).addEventListener(k==='based-on'?'change':'input',()=>{dirty.add(current);if(k==='revision')$('confirm-revision').checked=false;clearTimeout(draftTimer);draftTimer=setTimeout(guarded(persistDraft),400);}));
 ['initial','reanswer','position','modelnote','revision','plan','observation'].forEach(k=>{$('save-'+k).onclick=guarded(async()=>{if(k==='initial'&&!confirm('封存后保留这份初答，后续另写复答。现在封存？'))return;await saveEvent(k);});});
 $('prepare-material').onclick=guarded(async()=>{await persistDraft();buildMaterial();dirty.add(current);await persistDraft();});$('copy-material').onclick=guarded(async()=>{if(!$('material').value.trim())throw Error('请先准备材料。');try{await navigator.clipboard.writeText($('material').value);say('材料已复制，可自行粘贴到善问。');}catch(err){$('material').focus();$('material').select();say('请按 Ctrl+C（手机长按）复制已选中的材料。');}});
 $('download-material').onclick=()=>download($('material').value,'耶稣之善-第'+current+'章-同题材料.txt','text/plain;charset=utf-8');
 $('export').onclick=guarded(()=>exportArchive());$('rescue').onclick=guarded(()=>exportArchive(true));
 $('import').onchange=guarded(async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>25*1024*1024)throw Error('文件超过25MB，请保留原文件；此次没有导入或删减。');const a=JSON.parse(await f.text());C.validateArchive(a);if(!confirm('合并本书档案，保留所有已封存记录与其他草稿。继续？'))return;await persistDraft();const result=await C.importArchive(a);memory.delete(current);await loadRecords();await showChapter(current,false);say('已合并'+result.added+'条记录。'+(result.recoveredPending?'另找回'+result.recoveredPending+'份未保存版本。':'')+'其他草稿可在本章记录下方查看和恢复。');if(channel)channel.postMessage('changed');}finally{e.target.value='';}});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')persistDraft();});window.addEventListener('pagehide',()=>{persistDraft();});
 window.addEventListener('beforeunload',e=>{if(!storageOK||pending.length||dirty.size){e.preventDefault();e.returnValue='';}});
 try{channel=new BroadcastChannel('sde-m271-learning');channel.onmessage=guarded(async()=>{await loadRecords();renderHistory();});}catch(err){}
}
async function boot(){
 const response=await fetch(B+'unit/learning.json',{cache:'no-cache'});if(!response.ok)throw Error('学习任务暂时无法载入，请稍后刷新或下载PDF。');manifest=validateManifest(await response.json());manifest.chapters.sort((a,b)=>a.chapter-b.chapter);buildNavigation();await loadRecords();bind();
 const params=new URLSearchParams(location.search),requested=Number(params.get('chapter')||params.get('lesson')||1);await showChapter(C.chapter(requested)?requested:1,false);ready=true;$('loading').hidden=true;$('workspace').hidden=false;
}
boot().catch(err=>{say(err.message,true);text('loading','仍可通过上方链接阅读本书和下载学习包。');});
})();
