/* Book 398: append-only local learning records. No credentials enter this module. */
(function(root){'use strict';
const BOOK='m-398', VERSION='1.0', NAME='sde-publication-m398-v1';
const uid=()=>crypto.randomUUID(), now=()=>new Date().toISOString();
const stable=x=>Array.isArray(x)?'['+x.map(stable).join(',')+']':x&&typeof x==='object'?'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}':JSON.stringify(x);
let dbp;
function db(){return dbp||(dbp=new Promise((resolve,reject)=>{let r=indexedDB.open(NAME,1);r.onupgradeneeded=()=>{let d=r.result;let s=d.createObjectStore('events',{keyPath:'id'});s.createIndex('lesson','lesson');d.createObjectStore('drafts',{keyPath:'id'});d.createObjectStore('meta',{keyPath:'id'});};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);r.onblocked=()=>reject(Error('档案被另一页占用，请关闭旧页面后重试；未清空任何记录。'));}));}
function read(store){return db().then(d=>new Promise((yes,no)=>{let t=d.transaction(store,'readonly'),r=t.objectStore(store).getAll();r.onsuccess=()=>yes(r.result);r.onerror=()=>no(r.error)}));}
function write(store,value){return db().then(d=>new Promise((yes,no)=>{let t=d.transaction(store,'readwrite');t.objectStore(store).put(value);t.oncomplete=()=>yes(value);t.onerror=()=>no(t.error);t.onabort=()=>no(t.error||Error('保存未完成'));}));}
function valid(e){if(!e||e.book!==BOOK||!e.id||!Number.isInteger(e.lesson)||e.lesson<1||e.lesson>40||typeof e.type!=='string')throw Error('档案书号、题号或记录结构不符；没有导入。');}
async function append(e){valid(e);const d=await db();return new Promise((yes,no)=>{let t=d.transaction('events','readwrite'),s=t.objectStore('events'),r=s.get(e.id),reason;
r.onsuccess=()=>{if(r.result){if(stable(r.result)!==stable(e)){reason=Error('相同记录ID对应不同内容，已停止保存。');t.abort();}return;}
if(e.type==='initial'){let c=s.index('lesson').getAll(e.lesson);c.onsuccess=()=>{if(c.result.some(x=>x.type==='initial')){reason=Error('本题初答已经封存。请写复答，不覆盖初答。');t.abort();}else s.add(e);};}else s.add(e);};t.oncomplete=()=>yes(e);t.onerror=()=>no(reason||t.error);t.onabort=()=>no(reason||t.error||Error('保存失败'));});}
function event(lesson,type,data,source){return {id:uid(),book:BOOK,lesson,type,createdAt:now(),schemaVersion:VERSION,sourceSnapshot:source||null,data};}
async function archive(){return {schemaVersion:VERSION,book:BOOK,exportedAt:now(),events:await read('events'),drafts:await read('drafts'),extensions:await read('meta')};}
async function importArchive(a){if(!a||a.book!==BOOK||a.schemaVersion!==VERSION||!Array.isArray(a.events)||!Array.isArray(a.drafts||[])||!Array.isArray(a.extensions||[]))throw Error('不是本书受支持的v1档案；没有改动旧档案。');a.events.forEach(valid);for(const d of a.drafts||[]){if(d.book&&d.book!==BOOK)throw Error('草稿书号不符；没有导入。');if(d.lesson!==undefined&&(!Number.isInteger(d.lesson)||d.lesson<1||d.lesson>40))throw Error('草稿题号不符；没有导入。');}const ids=new Map;for(const e of a.events){if(ids.has(e.id)&&stable(ids.get(e.id))!==stable(e))throw Error('导入文件内部有冲突ID。');ids.set(e.id,e);}
const d=await db();return new Promise((yes,no)=>{let t=d.transaction(['events','drafts','meta'],'readwrite'),s=t.objectStore('events'),r=s.getAll(),reason;r.onsuccess=()=>{try{const map=new Map(r.result.map(e=>[e.id,e])), initial=new Map;for(const e of r.result)if(e.type==='initial')initial.set(e.lesson,e.id);for(const e of ids.values()){const old=map.get(e.id);if(old&&stable(old)!==stable(e))throw Error('导入与现有记录有冲突；整个导入取消。');if(e.type==='initial'&&initial.has(e.lesson)&&initial.get(e.lesson)!==e.id)throw Error('本题已有不同初答；拒绝覆盖，请保留两个导出档案另行核对。');if(e.type==='initial')initial.set(e.lesson,e.id);if(!old)s.add(e);}
// Draft conflicts are retained under independent import IDs, never overwrite active drafts.
for(const x of a.drafts||[])t.objectStore('drafts').put({...x,id:'import:'+uid(),importedFromId:x.id});
for(const x of a.extensions||[])t.objectStore('meta').put({...x,id:'import:'+uid(),importedFromId:x.id});
const extras={...a};delete extras.events;delete extras.drafts;delete extras.extensions;t.objectStore('meta').put({id:'archive:'+uid(),originalEnvelope:extras});
}catch(e){reason=e;t.abort();}};t.oncomplete=()=>yes(true);t.onerror=()=>no(reason||t.error);t.onabort=()=>no(reason||t.error||Error('导入失败，旧档案未覆盖'));});}
async function removeDraft(id){const d=await db();return new Promise((yes,no)=>{let t=d.transaction('drafts','readwrite');t.objectStore('drafts').delete(id);t.oncomplete=yes;t.onerror=()=>no(t.error)});}
async function parseSSE(response,on,signal){if(!response.ok||!response.body)throw Error('HTTP '+response.status);let reader=response.body.getReader(),decoder=new TextDecoder(),buffer='',end=false,done=false,serverError=false,interrupted=false;
function line(s){s=s.trim();if(!s.startsWith('data:'))return;let v=s.slice(5).trim();if(v==='[DONE]'){done=true;return;}let j;try{j=JSON.parse(v)}catch(e){interrupted=true;return;}
if(j.t==='end')end=true;if(j.t==='error')serverError=true;if(j.t==='note'&&/断在半路|中断|截断|incomplete|interrupt/i.test(String(j.v)))interrupted=true;on(j);}
while(true){if(signal&&signal.aborted)throw new DOMException('Aborted','AbortError');const r=await reader.read();if(r.done)break;buffer+=decoder.decode(r.value,{stream:true});let i;while((i=buffer.indexOf('\n'))>=0){line(buffer.slice(0,i));buffer=buffer.slice(i+1);}}
buffer+=decoder.decode();if(buffer.trim())line(buffer);
return serverError?'error':interrupted||!end||!done?'interrupted':'received-unverified';}
root.M398Core={BOOK,VERSION,uid,now,stable,read,write,append,event,archive,importArchive,removeDraft,parseSSE};
})(window);
