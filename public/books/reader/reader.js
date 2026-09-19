/* Real PDF paging, or lossless CSS-column paging of the existing full chapters. */
(function(){
 'use strict';
 const cfg=JSON.parse(document.getElementById('reader-config').textContent),$=id=>document.getElementById(id);
 const prev=$('prev'),next=$('next'),input=$('pageInput'),totalEl=$('totalPages'),select=$('chapter'),status=$('reader-status');
 const paper=$('html-paper'),flow=$('text-flow'),viewport=$('text-viewport'),pdfPaper=$('pdf-paper'),canvas=$('pdfCanvas'),layer=$('textLayer');
 const pdfMode=cfg.format==='pdf',cache=new Map(),storageKey='sde-book-page:'+cfg.id;
 let section=0,page=1,total=1,zoom=1,font=18,busy=false,token=0,doc=null,renderTask=null,textTask=null,stride=0,resizeTimer,htmlText='';
 const params=new URLSearchParams(location.hash.slice(1));
 let saved={};try{saved=JSON.parse(localStorage.getItem(storageKey)||'{}');}catch(e){}
 function bounded(n,max=1){return Math.max(1,Math.min(max,Number(n)||1));}
 const startSection=Math.max(0,Math.min(cfg.sources.length-1,Number(params.get('chapter')||saved.section||0)));
 const startPage=Math.max(1,Number(params.get('page')||saved.page||1));
 function persist(){try{localStorage.setItem(storageKey,JSON.stringify({section,page}));history.replaceState(null,'','#chapter='+section+'&page='+page);}catch(e){}}
 function paint(){
  input.value=page;input.max=total;input.disabled=busy;totalEl.textContent=busy?'…':total;
  prev.disabled=busy||(section===0&&page===1);next.disabled=busy||(section===cfg.sources.length-1&&page===total);
  select.value=section;select.disabled=busy;
  $('smaller').disabled=busy;$('larger').disabled=busy;
  status.textContent=busy?'正在载入书页…':(cfg.sources.length>1?'第 '+(section+1)+' / '+cfg.sources.length+' '+(pdfMode?'册':'章')+' · ':'')+'第 '+page+' / '+total+' 页 · '+cfg.sources[section].title;
  $('source-link').href=cfg.sources[section].url;
 }
 function fail(error){
  busy=false;paper.hidden=true;pdfPaper.hidden=true;$('reader-error').hidden=false;
  $('error-message').textContent='这一部分暂时未能载入，请重试，或打开原文继续阅读。';
  $('error-source').href=cfg.sources[section].url;paint();prev.disabled=true;next.disabled=true;
  status.textContent='载入失败';console.warn('Book reader:',error);
 }
 function safeURL(value,base){try{const u=new URL(value,base);return /^https?:$/.test(u.protocol)?u.href:null;}catch(e){return null;}}
 function cleanHTML(html,url){
  const parsed=new DOMParser().parseFromString(html,'text/html');
  const source=parsed.querySelector('main article')||parsed.querySelector('main .body')||parsed.querySelector('main')||parsed.querySelector('body > .wrap');
  if(!source||source.textContent.trim().length<30)throw Error('No readable chapter');
  const body=source.cloneNode(true);
  body.querySelectorAll('script,style,link,iframe,object,embed,form,button,input,select,textarea,nav,footer,.nav,.bar,.foot,.talk,.comments,.discussion,.grouplink,.sde-reader-entry').forEach(el=>el.remove());
  body.querySelectorAll('*').forEach(el=>{
   const href=el.getAttribute('href'),src=el.getAttribute('src');
   Array.from(el.attributes).forEach(a=>{if(/^on/i.test(a.name)||['style','srcdoc','id','srcset','hidden'].includes(a.name))el.removeAttribute(a.name);});
   if(href){const resolved=safeURL(href,url);if(resolved){el.setAttribute('href',resolved);el.setAttribute('rel','noopener');}else el.removeAttribute('href');}
   if(src){const resolved=safeURL(src,url);if(resolved)el.setAttribute('src',resolved);else el.removeAttribute('src');}
  });
  return body.innerHTML;
 }
 function layout(requested=page){
  const width=viewport.clientWidth;if(!width)return;
  flow.style.transform='none';flow.style.columnWidth=width+'px';flow.style.fontSize=font+'px';
  const gap=parseFloat(getComputedStyle(flow).columnGap)||0;stride=width+gap;
  total=Math.max(1,Math.ceil((flow.scrollWidth+gap-1)/stride));page=bounded(requested===-1?total:requested,total);
  flow.style.transform='translateX('+(-(page-1)*stride)+'px)';paint();persist();
 }
 async function renderPDF(requested=page){
  if(!doc)return;busy=true;paint();const current=++token;
  if(renderTask){try{renderTask.cancel();await renderTask.promise;}catch(e){}renderTask=null;}
  if(textTask){try{textTask.cancel();}catch(e){}textTask=null;}
  try{
   total=doc.numPages;page=bounded(requested===-1?total:requested,total);const pdfPage=await doc.getPage(page);if(current!==token)return;
   const natural=pdfPage.getViewport({scale:1});const available=Math.min(960,Math.max(240,$('stage').clientWidth-36));
   const scale=Math.min(1.55,available/natural.width)*zoom,vp=pdfPage.getViewport({scale});const ratio=Math.min(devicePixelRatio||1,2);
   canvas.width=Math.floor(vp.width*ratio);canvas.height=Math.floor(vp.height*ratio);canvas.style.width=vp.width+'px';canvas.style.height=vp.height+'px';
   pdfPaper.style.width=vp.width+'px';pdfPaper.style.height=vp.height+'px';layer.replaceChildren();layer.style.setProperty('--scale-factor',scale);
   const ctx=canvas.getContext('2d');renderTask=pdfPage.render({canvasContext:ctx,viewport:vp,transform:ratio===1?null:[ratio,0,0,ratio,0,0]});await renderTask.promise;if(current!==token)return;renderTask=null;
   const tc=await pdfPage.getTextContent();if(current!==token)return;
   htmlText=tc.items.map(x=>x.str).join(' ');textTask=pdfjsLib.renderTextLayer({textContentSource:tc,container:layer,viewport:vp,textDivs:[]});await textTask.promise;if(current!==token)return;
   busy=false;paint();persist();
  }catch(e){if(current===token&&e.name!=='RenderingCancelledException')fail(e);}
 }
 async function loadSection(index,requested=1){
  section=Math.max(0,Math.min(cfg.sources.length-1,index));busy=true;paper.hidden=true;pdfPaper.hidden=true;$('reader-error').hidden=true;paint();
  try{
   const source=cfg.sources[section];
   if(pdfMode){
    if(!window.pdfjsLib)throw Error('PDF library unavailable');
    pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    if(doc){await doc.destroy();doc=null;}
    doc=await pdfjsLib.getDocument(source.url).promise;pdfPaper.hidden=false;await renderPDF(requested);
   }else{
    let html=cache.get(source.url);if(!html){const response=await fetch(source.url);if(!response.ok)throw Error('HTTP '+response.status);html=cleanHTML(await response.text(),source.url);cache.set(source.url,html);}
    flow.innerHTML=html;htmlText=flow.textContent;paper.hidden=false;
    await Promise.all(Array.from(flow.querySelectorAll('img')).map(img=>img.decode?img.decode().catch(()=>{}):Promise.resolve()));
    if(document.fonts)await document.fonts.ready;busy=false;layout(requested);
   }
  }catch(e){fail(e);}
 }
 function go(target){
  if(busy)return;
  if(target<1){if(section>0)loadSection(section-1,-1);return;}
  if(target>total){if(section<cfg.sources.length-1)loadSection(section+1,1);return;}
  if(pdfMode)renderPDF(target);else layout(target);
  window.scrollTo({top:0});
 }
 prev.addEventListener('click',()=>go(page-1));next.addEventListener('click',()=>go(page+1));
 input.addEventListener('change',()=>go(bounded(parseInt(input.value,10),total)));
 input.addEventListener('keydown',e=>{if(e.key==='Enter'){go(bounded(parseInt(input.value,10),total));input.blur();}});
 select.addEventListener('change',()=>loadSection(Number(select.value),1));
 $('retry').addEventListener('click',()=>loadSection(section,page));
 $('smaller').addEventListener('click',()=>{if(pdfMode){zoom=Math.max(.65,zoom-.15);renderPDF(page);}else{const fraction=(page-1)/Math.max(1,total);font=Math.max(14,font-2);layout(1);layout(Math.floor(fraction*total)+1);}});
 $('larger').addEventListener('click',()=>{if(pdfMode){zoom=Math.min(2.2,zoom+.15);renderPDF(page);}else{const fraction=(page-1)/Math.max(1,total);font=Math.min(28,font+2);layout(1);layout(Math.floor(fraction*total)+1);}});
 document.addEventListener('keydown',e=>{if(e.altKey||e.ctrlKey||e.metaKey||e.shiftKey||/INPUT|TEXTAREA|SELECT|BUTTON/.test(e.target.tagName)||e.target.isContentEditable)return;if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();go(page+1);}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();go(page-1);}});
 let touch=null;viewport.addEventListener('touchstart',e=>{if(e.touches.length===1)touch={x:e.touches[0].clientX,y:e.touches[0].clientY};},{passive:true});viewport.addEventListener('touchend',e=>{if(!touch)return;const dx=e.changedTouches[0].clientX-touch.x,dy=e.changedTouches[0].clientY-touch.y;touch=null;if(Math.abs(dx)>65&&Math.abs(dx)>Math.abs(dy)*1.5&&!getSelection().toString())go(page+(dx<0?1:-1));},{passive:true});
 window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(!busy){if(pdfMode)renderPDF(page);else layout(page);}},180);});
 window.WDS_READ={title:cfg.title,bodyEl:()=>pdfMode?pdfPaper:flow,docTextFn:()=>('【'+cfg.sources[section].title+' · 第 '+page+' / '+total+' 页】\n'+htmlText)};
 $('stage').classList.toggle('pdf-stage',pdfMode);loadSection(startSection,startPage);
})();
