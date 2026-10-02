const $=id=>document.getElementById(id);
const BASE=new URL('../',import.meta.url), KEY='sde-book11-complete-v1.0';
let pdf,outline=[],pages=null,cur=1,zoom=1,wantSpread=innerWidth>=900,busy=false,requested=null,theme=0,turn=false;
const state=window.book11State={ready:false,rendered:[],total:677,cur:1,error:null};
const clamp=p=>Math.max(1,Math.min(pdf?.numPages||677,Math.round(Number(p)||1)));
function status(s){$('status').hidden=!s;if(s)$('status').textContent=s;}
function fail(e){state.error=String(e);$('status').hidden=false;$('status').replaceChildren(document.createTextNode('书页未能载入。请重试，或 '));const a=document.createElement('a');a.href=new URL('text/',BASE);a.textContent='改读完整长文';$('status').append(a);}
function spread(){return wantSpread&&innerWidth>=800;}
function openMenu(on){$('drawer').classList.toggle('open',on);$('drawer').inert=!on;$('menu').setAttribute('aria-expanded',String(on));if(on)$('q').focus();else $('menu').focus();}
function sync(){state.cur=cur;state.total=pdf.numPages;state.spread=spread();$('pageNo').value=cur;$('range').value=cur;$('range').max=pdf.numPages;$('pageNo').max=pdf.numPages;$('total').textContent=pdf.numPages;$('prev').disabled=cur<=1;$('next').disabled=cur>=pdf.numPages;$('spread').textContent=spread()?'双页':'单页';try{localStorage.setItem(KEY,String(cur));}catch{}const u=new URL(location.href);u.hash='page='+cur;history.replaceState(null,'',u);}
async function render(){
 if(busy)return;busy=true;
 while(requested!==null){
  const target=requested;requested=null;cur=target;state.ready=false;
  try{
   $('book').classList.add('loading');
   const ps=spread()?(cur===1?[1]:[cur%2===0?cur:cur-1,(cur%2===0?cur:cur-1)+1].filter(x=>x<=pdf.numPages)):[cur];
   const first=await pdf.getPage(ps[0]);const v=first.getViewport({scale:1});
   const W=$('stage').clientWidth-(innerWidth<800?16:32),H=$('stage').clientHeight-(innerWidth<800?16:32);
   const scale=Math.min(W/(v.width*ps.length),H/v.height)*zoom;
   const frag=document.createDocumentFragment(),txt=[];
   for(const pn of ps){
    const p=await pdf.getPage(pn),vp=p.getViewport({scale});
    const leaf=document.createElement('div');leaf.className='leaf';leaf.dataset.page=pn;
    leaf.style.width=Math.floor(vp.width)+'px';leaf.style.height=Math.floor(vp.height)+'px';
    const c=document.createElement('canvas');c.setAttribute('aria-label','第'+pn+'页');
    const ratio=Math.min(devicePixelRatio||1,2.5);c.width=Math.floor(vp.width*ratio);c.height=Math.floor(vp.height*ratio);c.style.width=Math.floor(vp.width)+'px';c.style.height=Math.floor(vp.height)+'px';
    leaf.append(c);frag.append(leaf);
    await p.render({canvasContext:c.getContext('2d',{alpha:false}),viewport:vp,transform:ratio===1?null:[ratio,0,0,ratio,0,0]}).promise;
    const tc=await p.getTextContent();txt.push('【第'+pn+'页】\n'+tc.items.map(x=>x.str).join(''));
   }
   $('book').replaceChildren(frag);$('pageText').textContent=txt.join('\n');state.rendered=ps;state.text=txt.join('\n');state.error=null;sync();status('');state.ready=true;
   $('book').classList.remove('loading');if(turn){$('book').classList.remove('turn');void $('book').offsetWidth;$('book').classList.add('turn');turn=false;}
  }catch(e){fail(e);$('book').classList.remove('loading');}
 }
 busy=false;
}
function go(p,animate=false){if(!pdf)return;requested=clamp(p);turn=animate;render();}
window.book11Go=go;
function step(dir){let p;if(!spread())p=cur+dir;else if(dir>0)p=cur===1?2:(cur%2===0?cur:cur-1)+2;else p=(cur%2===0?cur:cur-1)-2;go(p,true);}
function addToc(entries){const f=document.createDocumentFragment();for(const e of entries){const a=document.createElement('a');a.href='#page='+e.page;a.dataset.level=e.level;const t=document.createElement('span');t.textContent=e.title;a.append(t);const n=document.createElement('small');n.textContent=e.page;a.append(n);a.addEventListener('click',ev=>{ev.preventDefault();go(e.page);openMenu(false);});f.append(a);}$('toc').replaceChildren(f);}
function showToc(){const q=$('q').value.trim().toLocaleLowerCase();addToc(q?outline.filter(e=>e.title.toLocaleLowerCase().includes(q)):outline);$('drawerTitle').textContent='全书目录';$('searchHelp').textContent='筛选目录；按回车在全书677页中查找。';}
async function search(e){e.preventDefault();const q=$('q').value.trim();if(!q){showToc();return;}$('searchHelp').textContent='正在查找…';try{if(!pages)pages=await fetch(new URL('pages.json',BASE)).then(r=>{if(!r.ok)throw Error('Page text unavailable');return r.json();});const hits=[];for(let i=0;i<pages.length;i++){const text=pages[i].replace(/\s+/g,'');const at=text.toLocaleLowerCase().indexOf(q.toLocaleLowerCase().replace(/\s+/g,''));if(at>=0)hits.push({level:2,page:i+1,title:text.slice(Math.max(0,at-24),at+q.length+60)});}addToc(hits);$('drawerTitle').textContent='全文查找';$('searchHelp').textContent='“'+q+'”：'+hits.length+'页匹配。';if(!hits.length){const p=document.createElement('p');p.className='empty';p.textContent='本书没有找到此关键词。';$('toc').append(p);}}catch(e){$('searchHelp').textContent='查找暂不可用，请使用长文页面的浏览器查找功能。';}}
$('menu').onclick=()=>openMenu(!$('drawer').classList.contains('open'));$('closeMenu').onclick=()=>openMenu(false);$('resetToc').onclick=()=>{$('q').value='';showToc();};$('q').oninput=showToc;$('searchForm').onsubmit=search;
$('prev').onclick=()=>step(-1);$('next').onclick=()=>step(1);$('pageNo').onchange=e=>go(e.target.value);$('pageNo').onkeydown=e=>{if(e.key==='Enter')go(e.target.value);};$('range').onchange=e=>go(e.target.value);$('plus').onclick=()=>{zoom=Math.min(3,zoom+.2);go(cur);};$('minus').onclick=()=>{zoom=Math.max(.6,zoom-.2);go(cur);};$('spread').onclick=()=>{wantSpread=!wantSpread;go(cur);};
$('theme').onclick=()=>{theme=(theme+1)%3;document.documentElement.classList.toggle('day',theme===1);document.documentElement.classList.toggle('paper',theme===2);$('theme').textContent=['夜','日','纸'][theme];};$('full').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen?.();else document.documentElement.requestFullscreen?.();};
let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(()=>go(cur),180);});addEventListener('hashchange',()=>{const p=new URLSearchParams(location.hash.slice(1)).get('page');if(p)go(p);});addEventListener('keydown',e=>{if(['INPUT','TEXTAREA'].includes(e.target.tagName))return;if(e.key==='ArrowRight'){e.preventDefault();step(1);}if(e.key==='ArrowLeft'){e.preventDefault();step(-1);}if(e.key==='Escape')openMenu(false);if(e.key==='t')openMenu(true);});
let touchX=null;$('stage').addEventListener('touchstart',e=>{if(e.touches.length===1&&zoom===1)touchX=e.touches[0].clientX;},{passive:true});$('stage').addEventListener('touchend',e=>{if(touchX!==null){const dx=e.changedTouches[0].clientX-touchX;if(Math.abs(dx)>65)step(dx<0?1:-1);}touchX=null;},{passive:true});
window.WDS_READ={title:'三律治理学',bodyEl:()=>$('book'),docTextFn:()=>state.text||''};
try{
 const lib=await import('./pdf.min.mjs');lib.GlobalWorkerOptions.workerSrc=new URL('pdf.worker.min.mjs',import.meta.url).href;
 const loader=lib.getDocument({url:new URL('downloads/book-v1.0.pdf',BASE).href,isEvalSupported:false,useSystemFonts:true});
 loader.onProgress=p=>{if(!pdf&&p.total)status('正在载入完整书稿… '+Math.min(100,Math.round(p.loaded/p.total*100))+'%');};
 [pdf,outline]=await Promise.all([loader.promise,fetch(new URL('toc.json',BASE)).then(r=>{if(!r.ok)throw Error('目录载入失败');return r.json();})]);
 if(pdf.numPages!==677)throw Error('版本页数不符，请打开长文版核对。');
 showToc();let initial=new URLSearchParams(location.hash.slice(1)).get('page');if(!initial)try{initial=localStorage.getItem(KEY);}catch{}
 go(initial||1);
}catch(e){fail(e);}
