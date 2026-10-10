/* Local, append-only learning records for Jesus' Goodness, volume 271. */
(function(root){'use strict';
const BOOK='m-271',VERSION='1.0',DB_NAME='sde-publication-m271-v1';
const TYPES=new Set(['initial','reanswer','position','revision','plan','observation','modelnote']);
const uid=()=>root.crypto.randomUUID(),now=()=>new Date().toISOString();
const stable=x=>Array.isArray(x)?'['+x.map(stable).join(',')+']':x&&typeof x==='object'?'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}':JSON.stringify(x);
const chapter=n=>Number.isInteger(n)&&n>=1&&n<=40;
function validateEvent(e){
 if(!e||e.book!==BOOK||e.schemaVersion!==VERSION||typeof e.id!=='string'||!e.id||!chapter(e.chapter)||!TYPES.has(e.type)||typeof e.createdAt!=='string'||!Number.isFinite(Date.parse(e.createdAt))||!e.data||typeof e.data.text!=='string'||!e.data.text.trim())throw Error('记录格式或书号不符，未改动现有档案。');
 if(e.type==='revision'&&(e.data.confirmedBy!=='reader'||!Number.isFinite(Date.parse(e.data.confirmedAt))))throw Error('修订必须由读者本人确认。');
 return e;
}
function validateDraft(d){if(!d||d.book!==BOOK||typeof d.id!=='string'||!chapter(d.chapter)||!d.fields||typeof d.fields!=='object'||Array.isArray(d.fields)||Object.values(d.fields).some(x=>typeof x!=='string'))throw Error('草稿格式或书号不符，未导入。');if(d.pendingEvent){validateEvent(d.pendingEvent);if(d.pendingEvent.chapter!==d.chapter)throw Error('待恢复记录与草稿章号不符，未导入。');}return d;}
function event(n,type,data,sourceSnapshot){return validateEvent({id:uid(),book:BOOK,schemaVersion:VERSION,chapter:n,type,createdAt:now(),sourceSnapshot:sourceSnapshot||null,data});}
function mergeEvents(existing,incoming){
 const map=new Map(),initial=new Map(),added=[];
 for(const e of [...existing,...incoming]){
  validateEvent(e);const old=map.get(e.id);
  if(old){if(stable(old)!==stable(e))throw Error('相同记录编号存在不同内容，整个导入取消。');continue;}
  if(e.type==='initial'&&initial.has(e.chapter))throw Error('第'+e.chapter+'章已有不同的封存初答；未覆盖，请分别保留两份档案。');
  map.set(e.id,e);if(e.type==='initial')initial.set(e.chapter,e.id);
  if(!existing.some(x=>x.id===e.id))added.push(e);
 }
 return added;
}
function validateArchive(a){
 if(!a||(a.unitId||a.book)!==BOOK||a.schemaVersion!==VERSION||!Array.isArray(a.events)||!Array.isArray(a.drafts))throw Error('请选择第271卷的学习档案（v1.0）。');
 a.events.forEach(validateEvent);a.drafts.forEach(validateDraft);mergeEvents([],a.events);recoveryDrafts(a);return a;
}
function recoveryDrafts(a){
 const queue=[a],seen=new Set(),records=new Map();
 while(queue.length){const item=queue.pop();if(!item||typeof item!=='object'||seen.has(item))continue;seen.add(item);
  if(item.pendingUnstored!==undefined){if(!Array.isArray(item.pendingUnstored))throw Error('待恢复记录格式不符，未导入。');for(const e of item.pendingUnstored){validateEvent(e);const old=records.get(e.id);if(old&&stable(old)!==stable(e))throw Error('待恢复记录编号存在不同内容，未导入。');records.set(e.id,e);}}
  if(Array.isArray(item.extensions))queue.push(...item.extensions);if(item.envelope&&typeof item.envelope==='object')queue.push(item.envelope);
 }
 return [...records.values()].map(e=>({id:'import:pending:'+e.id,book:BOOK,chapter:e.chapter,updatedAt:e.createdAt,sourceSnapshot:e.sourceSnapshot||null,fields:{[e.type]:e.data.text,...(typeof e.data.basedOnId==='string'?{'based-on':e.data.basedOnId}:{})},pendingEvent:e}));
}
let dbp;
function db(){return dbp||(dbp=new Promise((yes,no)=>{
 if(!root.indexedDB){no(Error('本浏览器暂不支持保存，请先导出当前记录。'));return;}
 const r=root.indexedDB.open(DB_NAME,1);
 r.onupgradeneeded=()=>{const d=r.result,s=d.createObjectStore('events',{keyPath:'id'});s.createIndex('chapter','chapter');d.createObjectStore('drafts',{keyPath:'id'});d.createObjectStore('meta',{keyPath:'id'});};
 r.onsuccess=()=>{r.result.onversionchange=()=>r.result.close();yes(r.result);};
 r.onerror=()=>{dbp=null;no(r.error||Error('本地档案无法打开。'));};r.onblocked=()=>{dbp=null;no(Error('请关闭本书旧标签页后重试，原记录未清空。'));};
}));}
async function read(store){const d=await db();return new Promise((yes,no)=>{const t=d.transaction(store,'readonly'),r=t.objectStore(store).getAll();r.onsuccess=()=>yes(r.result);r.onerror=()=>no(r.error);});}
async function saveDraft(value){validateDraft(value);const d=await db();return new Promise((yes,no)=>{const t=d.transaction('drafts','readwrite');t.objectStore('drafts').put(value);t.oncomplete=()=>yes(value);t.onerror=()=>no(t.error);t.onabort=()=>no(t.error||Error('草稿保存未完成。'));});}
async function append(e){validateEvent(e);const d=await db();return new Promise((yes,no)=>{
 const t=d.transaction('events','readwrite'),s=t.objectStore('events'),r=s.getAll();let reason;
 r.onsuccess=()=>{try{for(const x of mergeEvents(r.result,[e]))s.add(x);}catch(err){reason=err;t.abort();}};
 t.oncomplete=()=>yes(e);t.onerror=()=>no(reason||t.error);t.onabort=()=>no(reason||t.error||Error('记录保存未完成。'));
});}
async function archive(){return {schemaVersion:VERSION,unitId:BOOK,exportedAt:now(),events:await read('events'),drafts:await read('drafts'),extensions:await read('meta')};}
async function importArchive(a){
 validateArchive(a);const d=await db();return new Promise((yes,no)=>{
 const t=d.transaction(['events','drafts','meta'],'readwrite'),s=t.objectStore('events'),ds=t.objectStore('drafts'),ms=t.objectStore('meta'),r=s.getAll(),dr=ds.getAll(),mr=ms.getAll();let reason,done=0,added=0,importedDrafts=0,recoveredPending=0;
 function merge(){if(++done<3)return;try{
  const additions=mergeEvents(r.result,a.events);added=additions.length;additions.forEach(e=>s.add(e));
  const current=new Map(dr.result.map(x=>[x.id,x]));
  for(const draft of [...a.drafts,...recoveryDrafts(a)]){
   const values=[...current.values()],active='fields:'+draft.chapter,old=current.get(active);
   if(draft.pendingEvent&&values.some(x=>x.pendingEvent?.id===draft.pendingEvent.id&&stable(x.pendingEvent)!==stable(draft.pendingEvent)))throw Error('待恢复记录编号存在不同内容，整个导入取消。');
   if(draft.pendingEvent?values.some(x=>x.pendingEvent&&stable(x.pendingEvent)===stable(draft.pendingEvent)):values.some(x=>!x.pendingEvent&&stable(x.fields)===stable(draft.fields)&&x.chapter===draft.chapter))continue;
   const saved=!old&&draft.id===active?draft:{...draft,id:'import:'+uid(),importedFromId:draft.id,importedAt:now()};ds.put(saved);current.set(saved.id,saved);importedDrafts++;if(draft.pendingEvent)recoveredPending++;
  }
  const metadata={...a};delete metadata.events;delete metadata.drafts;
  const known=new Map(mr.result.map(x=>[x.id,x]));
  if(Array.isArray(metadata.extensions)){for(const item of metadata.extensions){let record=item&&typeof item==='object'&&!Array.isArray(item)&&typeof item.id==='string'?item:{id:'import:'+uid(),envelope:{extension:item}};const old=known.get(record.id);if(old&&stable(old)===stable(record))continue;if(old)record={...record,id:'import:'+uid(),importedFromId:record.id};ms.put(record);known.set(record.id,record);}delete metadata.extensions;}
  if(![...known.values()].some(x=>stable(x.envelope)===stable(metadata)))ms.put({id:'import:'+uid(),importedAt:now(),envelope:metadata});
 }catch(err){reason=err;t.abort();}}
 r.onsuccess=merge;dr.onsuccess=merge;mr.onsuccess=merge;t.oncomplete=()=>yes({added,importedDrafts,recoveredPending});t.onerror=()=>no(reason||t.error);t.onabort=()=>no(reason||t.error||Error('导入未完成，原档案未覆盖。'));
 });
}
const api={BOOK,VERSION,uid,now,stable,chapter,validateEvent,validateDraft,validateArchive,recoveryDrafts,event,mergeEvents,read,saveDraft,append,archive,importArchive};root.M271Core=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
