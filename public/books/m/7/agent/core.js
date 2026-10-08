(function(root,f){if(typeof module==='object')module.exports=f();else root.M7=f()})(typeof self!=='undefined'?self:this,function(){
'use strict';
const UNIT='m-7',DB='sde-m7-publication-v1';
const canon=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canon).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canon(x[k])).join(',')+'}';
const uid=()=>crypto.randomUUID();
async function hash(x){const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof x==='string'?x:canon(x)));return Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,'0')).join('')}
let dbPromise;
function open(){return dbPromise||(dbPromise=new Promise((resolve,reject)=>{const r=indexedDB.open(DB,1);r.onupgradeneeded=()=>{r.result.createObjectStore('events',{keyPath:'id'});r.result.createObjectStore('heads',{keyPath:'problemId'})};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)}))}
async function all(){const d=await open();return new Promise((yes,no)=>{const t=d.transaction('events'),r=t.objectStore('events').getAll();r.onsuccess=()=>yes(r.result);r.onerror=()=>no(r.error)})}
function fingerprint(es){return es.map(e=>e.id).sort().join('|')}
function validateMerge(old,rows){
 if(!Array.isArray(rows))throw Error('档案不是记录数组');
 const ids=new Map(old.map(e=>[e.id,e])),first=new Map();
 for(const e of old)if(e.type==='initial')first.set(e.problemId,e.id);
 for(const e of rows){
  if(!e||e.unitId!==UNIT||typeof e.id!=='string'||!/^m7-q\d\d$/.test(e.problemId)||!e.type||!e.at||!e.sourceEdition)throw Error('档案书目、题号或来源字段不符');
  if(ids.has(e.id)){if(canon(ids.get(e.id))!==canon(e))throw Error('相同记录ID内容冲突，整批未导入');continue}
  if(e.type==='initial'&&first.has(e.problemId))throw Error('同题出现两份初答，整批未导入');
  if(e.type==='initial')first.set(e.problemId,e.id);ids.set(e.id,e);
 }
 return [...ids.values()];
}
async function append(problemId,type,data,expected){
 const d=await open(),e={unitId:UNIT,problemId,id:uid(),type,at:new Date().toISOString(),sourceEdition:'v1.0',...data};
 return new Promise((yes,no)=>{const t=d.transaction(['events','heads'],'readwrite'),s=t.objectStore('events'),h=t.objectStore('heads');let failure;
  const r=s.getAll();r.onsuccess=()=>{try{const own=r.result.filter(x=>x.problemId===problemId);if(expected!==undefined&&fingerprint(own)!==expected)throw Error('另一页面已更新本题。输入仍在，请刷新记录后重新保存。');validateMerge(r.result,[e]);s.add(e);h.put({problemId,lastId:e.id})}catch(err){failure=err;t.abort()}};
  t.oncomplete=()=>yes(e);t.onerror=t.onabort=()=>no(failure||t.error||Error('本机保存失败；请导出备份，输入尚未清空。'));
 });
}
async function merge(packet){
 if(packet.unitId!==UNIT||packet.schemaVersion!==1)throw Error('不是第7号本版本档案');
 const d=await open();return new Promise((yes,no)=>{const t=d.transaction(['events','heads'],'readwrite'),s=t.objectStore('events');let err;const r=s.getAll();r.onsuccess=()=>{try{const rows=validateMerge(r.result,packet.events),ids=new Set(r.result.map(e=>e.id));rows.filter(e=>!ids.has(e.id)).forEach(e=>s.add(e))}catch(e){err=e;t.abort()}};t.oncomplete=()=>yes();t.onabort=t.onerror=()=>no(err||t.error)});
}
function download(name,data){const a=document.createElement('a'),u=URL.createObjectURL(new Blob([typeof data==='string'?data:JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'}));a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),3000)}
async function backup(){const p={schemaVersion:1,unitId:UNIT,exportedAt:new Date().toISOString(),events:await all()};download('中华文化导论_第7号_学习档案_'+Date.now()+'.json',p);return p}
return{UNIT,canon,uid,hash,all,append,merge,fingerprint,validateMerge,download,backup};
});
