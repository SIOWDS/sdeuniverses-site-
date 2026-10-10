/* All publication manifests: Node DOM simulation, not browser rendering QA. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert'),crypto=require('crypto');
const {parseHTML}=require('linkedom'),{indexedDB}=require('fake-indexeddb');
const root=path.resolve(__dirname,'../../public'),IDS=[266,330,347,401,272,276,278,281,282,386,399,400];
const core=fs.readFileSync(root+'/books/unit-runtime/core.js','utf8'),app=fs.readFileSync(root+'/books/unit-runtime/app.js','utf8');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function run(number){
 const base='/books/m/'+number+'/',manifest=JSON.parse(fs.readFileSync(root+base+'unit/learning.json'));
 const {window,document}=parseHTML(fs.readFileSync(root+base+'agent/index.html','utf8'));
 window.indexedDB=indexedDB;window.PUBLICATION_UNIT={manifest:base+'unit/learning.json',view:'agent'};
 window.HTMLElement.prototype.scrollIntoView=function(){};window.HTMLElement.prototype.showModal=function(){this.open=true;};window.HTMLElement.prototype.close=function(){this.open=false;};window.HTMLSelectElement.prototype.add=function(e){this.append(e);};Object.defineProperty(window.HTMLSelectElement.prototype,'value',{get(){return this._value??this.querySelector('option')?.value??'';},set(v){this._value=String(v);},configurable:true});
 function Option(label,value){const e=document.createElement('option');e.textContent=label;e.value=String(value);return e;}
 const location={origin:'http://localhost',href:'http://localhost'+base+'agent/',search:''},history={replaceState(a,b,u){location.search=u;}};let apiCalls=0;
 async function fetch(url,opts){const u=new URL(String(url),location.href);if(u.pathname.startsWith('/api/')){apiCalls++;throw Error('Unexpected model request in smoke test');}const f=root+u.pathname;if(!fs.existsSync(f))return new Response('',{status:404});return new Response(fs.readFileSync(f));}
 const ctx=vm.createContext({window,document,console,Option,location,history,crypto:crypto.webcrypto,fetch,Response,ReadableStream,TextDecoder,TextEncoder,Uint8Array,URL,URLSearchParams,Blob,AbortController,DOMException,setTimeout,clearTimeout,confirm:()=>true,navigator:{},BroadcastChannel:class{postMessage(){}},module:undefined});
 vm.runInContext(core,ctx);vm.runInContext(app,ctx);
 const $=id=>document.getElementById(id);async function wait(){for(let i=0;i<400;i++){if($('loading')?.hidden&&$('workspace')&&!$('workspace').hidden)return;await pause(5);}throw Error(number+' boot failed: '+$('status')?.textContent);}
 await wait();assert.equal($('chapter-select').children.length,manifest.tasks.length);assert.equal($('mode').value,'read');assert.equal($('agent-starts').children.length,5);assert.equal($('source-link').textContent,manifest.tasks[0].chapterTitle+' · 阅读原文 →');assert(!$('preview-btn').disabled);assert(document.querySelector('h1').textContent.includes(manifest.agent.name));
 const last=manifest.tasks.length;$('chapter-select').value=String(last);await $('chapter-select').onchange();assert.equal($('lesson-title').textContent,manifest.tasks[last-1].title||manifest.tasks[last-1].chapterTitle);assert.equal($('source-link').textContent,manifest.tasks[last-1].chapterTitle+' · 阅读原文 →');assert(!$('preview-btn').disabled);assert($('next').disabled);
 $('chapter-select').value='1';await $('chapter-select').onchange();assert($('previous').disabled);assert(!$('preview-btn').disabled);
 // Every starter, regardless of scalar or array form, is a prefill only.
 const modes=['read','apply','cut','clash','write'];for(let i=0;i<5;i++){await $('agent-starts').children[i].onclick();assert.equal($('mode').value,modes[i]);const raw=manifest.agent.starts[modes[i]],expected=Array.isArray(raw)?raw[0]:raw;assert.equal($('question').value,typeof expected==='string'?expected:'');assert(!$('preview-btn').disabled);}
 assert.equal(apiCalls,0);assert.equal(document.querySelectorAll('main main').length,0);
 return {number,title:manifest.title,tasks:manifest.tasks.length,parts:manifest.parts.length,firstSource:manifest.tasks[0].sourceData,lastSource:manifest.tasks.at(-1).sourceData,lastTitle:manifest.tasks.at(-1).chapterTitle,startsForms:[...new Set(Object.values(manifest.agent.starts).map(x=>Array.isArray(x)?'array':typeof x))],boot:true,firstLastNavigation:true,fiveGatesPrefillWithoutSending:true,sourceChecked:true,apiCalls};
}
(async()=>{const results=[];for(const no of IDS)results.push(await run(no));const report={passed:true,environment:'Node VM + linkedom + fake-indexeddb; source HTTP responses simulated from repository files',browserTested:false,realModelTested:false,books:results,totalTasks:results.reduce((n,b)=>n+b.tasks,0)};fs.writeFileSync(__dirname+'/manifest-smoke-result.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));process.exit(0);})().catch(e=>{console.error(e.stack);process.exit(1);});
