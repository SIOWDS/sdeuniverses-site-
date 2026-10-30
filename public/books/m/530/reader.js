'use strict';
const BASE='/books/m/530/';
const EXPECTED='5b6903dfad8ffdd64e0252717741ca781cab4cee6bf2aea178e21f1a668c8c7f';
let archivePromise, pdfURL, chapters=[];
const $=id=>document.getElementById(id);
function notify(t){$('status').textContent=t;}
async function archive(){
 if(!archivePromise)archivePromise=(async()=>{
  const r=await fetch(BASE+'downloads/manuscript-source-v1.1.zip');
  if(!r.ok)throw new Error('原稿档案尚不可用（'+r.status+'）');
  const b=await r.arrayBuffer();
  if(b.byteLength>8000000)throw new Error('档案大小异常');
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),x=>x.toString(16).padStart(2,'0')).join('');
  if(hash!==EXPECTED)throw new Error('原稿校验失败，已停止读取');
  const v=new DataView(b);let e=b.byteLength-22;
  for(;e>=Math.max(0,b.byteLength-65557)&&v.getUint32(e,true)!==0x06054b50;e--);
  if(e<0||v.getUint32(e,true)!==0x06054b50)throw new Error('档案目录无效');
  const count=v.getUint16(e+10,true);let p=v.getUint32(e+16,true);const entries=new Map();
  if(count>100)throw new Error('档案条目异常');
  for(let i=0;i<count;i++){
   if(v.getUint32(p,true)!==0x02014b50)throw new Error('档案目录损坏');
   const n=v.getUint16(p+28,true),x=v.getUint16(p+30,true),c=v.getUint16(p+32,true);
   const name=new TextDecoder().decode(new Uint8Array(b,p+46,n));
   entries.set(name,{method:v.getUint16(p+10,true),packed:v.getUint32(p+20,true),size:v.getUint32(p+24,true),at:v.getUint32(p+42,true)});
   p+=46+n+x+c;
  }
  return {b,v,entries};
 })();
 return archivePromise;
}
async function extract(name){
 const {b,v,entries}=await archive();const f=entries.get(name);
 if(!f||f.size>10000000)throw new Error('文件不存在或大小异常');
 if(v.getUint32(f.at,true)!==0x04034b50)throw new Error('文件头无效');
 const offset=f.at+30+v.getUint16(f.at+26,true)+v.getUint16(f.at+28,true);
 let data=b.slice(offset,offset+f.packed);
 if(f.method===8)data=await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer();
 else if(f.method!==0)throw new Error('浏览器不支持此压缩格式，请下载原稿档案');
 if(data.byteLength!==f.size)throw new Error('文件长度校验失败');
 return data;
}
function render(text){
 const area=$('text');area.replaceChildren();let paragraph=[];
 function flush(){if(paragraph.length){const p=document.createElement('p');p.textContent=paragraph.join('\n');area.append(p);paragraph=[];}}
 for(const line of text.split(/\r?\n/)){
  const m=line.match(/^(#{1,6})\s+(.+)$/);
  if(m){flush();const h=document.createElement('h'+Math.min(m[1].length+1,4));h.textContent=m[2];area.append(h);}
  else if(!line.trim())flush();else paragraph.push(line);
 }
 flush();
}
async function choose(){
 const c=chapters[Number($('chapter').value)];if(!c)return;
 $('pdf').hidden=true;$('text').hidden=false;
 render(new TextDecoder().decode(await extract(c.name)));
 history.replaceState(null,'','#chapter-'+c.number);
 notify('已校验原稿 · '+c.title+' · 理论研究稿，非实证结论');
}
async function download(name,mime){
 const u=URL.createObjectURL(new Blob([await extract(name)],{type:mime}));
 const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),60000);
}
async function openPDF(){
 if(!pdfURL)pdfURL=URL.createObjectURL(new Blob([await extract('manuscript.pdf')],{type:'application/pdf'}));
 $('text').hidden=true;$('pdf').hidden=false;$('pdf').src=pdfURL;
 notify('350页统稿三审原稿v1.1；内页版本说明保持原样。浏览器不显示时请下载PDF。');
}
function run(fn){return ()=>Promise.resolve().then(fn).catch(e=>notify('未能完成：'+e.message+'。可直接下载完整原稿档案。'));}
async function start(){
 const {entries}=await archive();
 const names=[...entries.keys()].filter(n=>/^chapters\/\d\d_[^/]+\.md$/.test(n)).sort();
 if(names.length!==49)throw new Error('正文单元数不是49，已停止读取');
 for(const name of names){const text=new TextDecoder().decode(await extract(name));chapters.push({name,number:name.slice(9,11),title:text.split(/\r?\n/)[0].replace(/^#+\s*/, '')});}
 chapters.forEach((c,i)=>{$('chapter').add(new Option(c.title,String(i)));});
 const match=location.hash.match(/^#chapter-(\d\d)$/);if(match){const i=chapters.findIndex(c=>c.number===match[1]);if(i>=0)$('chapter').value=String(i);}
 $('chapter').onchange=run(choose);$('open-pdf').onclick=run(openPDF);
 $('get-pdf').onclick=run(()=>download('manuscript.pdf','application/pdf'));
 $('get-word').onclick=run(()=>download('manuscript.docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document'));
 await choose();
}
if(typeof document!=='undefined')run(start)();
