/* Existing catalogue cards remain static. Volume 530 has a deduplicated display supplement pending canonical catalogue merge. */
(function(){
 'use strict';
 const grid=document.getElementById('book-grid'); if(!grid)return;
 // Remove this supplement after m-530 is merged into catalog.json and the static shelves are regenerated.
 if(!grid.querySelector('.book[data-number="530"]')){
  const c=document.createElement('article');c.className='book';
  Object.assign(c.dataset,{id:'m-530',number:'530',title:'SDE意义递归发生学',category:'core',reading:'full',authors:'["王德生"]',search:'SDE意义递归发生学 从人的全面发展到国家治理与文明升维 王德生 530 979-8-90690-530-7 创造 自由 幸福 教育 健康 事业 政治 经济 法律 递生',flip:'false',online:'2026-10-30',publicationUnit:'m-530',catalogSupplement:'true'});
  c.innerHTML='<div class="book-main"><a class="cover" href="/books/m/530/" tabindex="-1" aria-hidden="true"><span class="no-cover">SDE意义递归发生学</span></a><div class="book-copy"><p class="book-tag"><span>SDE理论</span><span class="ordinal">#530</span></p><h3><a href="/books/m/530/">SDE意义递归发生学</a></h3><p class="byline">王德生</p><p class="description">从人的全面发展到国家治理与文明升维。九编47章、350页原稿、47项学习任务与专属研读智能体“递生”。</p></div></div><div class="book-meta"><span class="reading-state full">全文可读</span><span class="format">网页／原稿PDF</span></div><div class="book-actions publication-unit-actions" role="group" aria-label="阅读、学习、智能问对"><p class="publication-unit-label">三位一体 · 网站版</p><a class="read-button" data-unit-action="read" href="/books/m/530/read.html">阅读 · 完整原稿</a><a class="learn-link" data-unit-action="learn" href="/books/m/530/agent/learning.html">学习包 · 47项任务</a><a class="agent-link" data-unit-action="agent" href="/books/m/530/agent/dialogue.html">递生 · 智能问对</a><div class="unit-secondary"><a class="detail-button" href="/books/m/530/">详情</a><a class="detail-button" href="/books/m/530/unit/handbook.html">学习手册</a></div></div>';
  grid.prepend(c);
  const total=document.querySelector('.shelf-total strong');if(total)total.textContent=String(grid.querySelectorAll('.book').length);
  for(const category of ['all','core']){const span=document.querySelector('[data-category-filter="'+category+'"] span');if(span&&/^\d+$/.test(span.textContent.trim()))span.textContent=String(Number(span.textContent)+1);}
 }
 const cards=Array.from(grid.querySelectorAll('.book'));
 const q=document.getElementById('book-search'),author=document.getElementById('author-filter'),availability=document.getElementById('reading-filter'),sort=document.getElementById('sort-books');
 const chips=Array.from(document.querySelectorAll('[data-category-filter]')),views=Array.from(document.querySelectorAll('[data-view]'));
 const count=document.getElementById('result-count'),heading=document.getElementById('result-title'),empty=document.getElementById('empty-state'),more=document.getElementById('load-more'),progress=document.getElementById('load-progress'),reset=document.getElementById('reset-filters'),clear=document.getElementById('clear-search');
 const initialOrder=new Map(cards.map((c,i)=>[c,i]));
 const normalize=s=>String(s||'').toLocaleLowerCase().replace(/[\s\-—–·：:，,（）()《》]/g,'');
 const searchIndex=new Map(cards.map(c=>[c,normalize(c.dataset.search)]));
 let category='all',view='grid',limit=24,matched=[];
 function setURL(){
  try{const u=new URL(location.href);['q','category','author','read','sort','view'].forEach(k=>u.searchParams.delete(k));
   const vals={q:q.value.trim(),category:category==='all'?'':category,author:author.value,read:availability.value,sort:sort.value==='latest'?'':sort.value,view:view==='grid'?'':view};
   Object.entries(vals).forEach(([k,v])=>{if(v)u.searchParams.set(k,v)});history.replaceState(null,'',u.pathname+u.search+u.hash);
  }catch(e){/* A file preview may not support history updates. */}
 }
 function restore(){
  const p=new URLSearchParams(location.search);q.value=p.get('q')||'';
  category=chips.some(c=>c.dataset.categoryFilter===p.get('category'))?p.get('category'):'all';
  [ [author,'author'],[availability,'read'],[sort,'sort'] ].forEach(([el,key])=>{const v=p.get(key);if(Array.from(el.options).some(o=>o.value===v))el.value=v;else el.selectedIndex=0;});
  view=p.get('view')==='list'?'list':'grid';limit=24;
 }
 function apply(resetLimit=true,updateURL=true){
  if(resetLimit)limit=24;
  const terms=q.value.trim().split(/\s+/).map(normalize).filter(Boolean);
  matched=cards.filter(c=>(category==='all'||c.dataset.category===category)&&(!author.value||JSON.parse(c.dataset.authors).includes(author.value))&&(!availability.value||(availability.value==='flip'?c.dataset.flip==='true':c.dataset.reading===availability.value))&&terms.every(t=>searchIndex.get(c).includes(t)));
  matched.sort((a,b)=>{
   if(sort.value==='number')return (Number(a.dataset.number)||9999)-(Number(b.dataset.number)||9999)||initialOrder.get(a)-initialOrder.get(b);
   if(sort.value==='title')return a.dataset.title.localeCompare(b.dataset.title,'zh-CN');
   if(sort.value==='online-new')return (b.dataset.online||'').localeCompare(a.dataset.online||'')||initialOrder.get(a)-initialOrder.get(b);
   if(sort.value==='online-old')return (a.dataset.online||'').localeCompare(b.dataset.online||'')||initialOrder.get(b)-initialOrder.get(a);
   if(sort.value==='numdesc')return (Number(b.dataset.number)||-1)-(Number(a.dataset.number)||-1)||initialOrder.get(a)-initialOrder.get(b);
   return (b.dataset.online||'').localeCompare(a.dataset.online||'')||(Number(b.dataset.number)||-1)-(Number(a.dataset.number)||-1)||initialOrder.get(a)-initialOrder.get(b);
  });
  cards.forEach(c=>{c.hidden=true;});
  matched.forEach((c,i)=>{grid.appendChild(c);c.hidden=i>=limit;});
  grid.classList.toggle('list-view',view==='list');
  chips.forEach(c=>c.setAttribute('aria-pressed',String(c.dataset.categoryFilter===category)));
  views.forEach(v=>v.setAttribute('aria-pressed',String(v.dataset.view===view)));
  const selected=chips.find(c=>c.dataset.categoryFilter===category);
  heading.textContent=selected?selected.dataset.label:'全部图书';count.textContent=matched.length+' 部';
  const shown=Math.min(limit,matched.length);progress.textContent=matched.length?'已显示 '+shown+' / '+matched.length+' 部':'';
  more.hidden=shown>=matched.length;more.textContent='再看 '+Math.min(24,matched.length-shown)+' 本';
  empty.hidden=matched.length!==0;clear.hidden=!q.value;
  reset.hidden=!(q.value||author.value||availability.value||category!=='all'||sort.value!=='latest');
  if(updateURL)setURL();
 }
 function resetAll(){q.value='';author.value='';availability.value='';sort.value='latest';category='all';apply();q.focus();}
 q.addEventListener('input',()=>apply());author.addEventListener('change',()=>apply());availability.addEventListener('change',()=>apply());sort.addEventListener('change',()=>apply());
 clear.addEventListener('click',()=>{q.value='';apply();q.focus();});
 chips.forEach(c=>c.addEventListener('click',()=>{category=c.dataset.categoryFilter;apply();}));
 views.forEach(v=>v.addEventListener('click',()=>{view=v.dataset.view;apply(false);}));
 more.addEventListener('click',()=>{const firstNew=matched[limit];limit+=24;apply(false,false);if(firstNew){const a=firstNew.querySelector('h3 a');if(a)a.focus({preventScroll:true});}});
 reset.addEventListener('click',resetAll);document.getElementById('empty-reset').addEventListener('click',resetAll);
 window.addEventListener('popstate',()=>{restore();apply(true,false);});
 grid.querySelectorAll('img').forEach(img=>{function fallback(){img.hidden=true;const f=img.nextElementSibling;if(f)f.hidden=false;}img.addEventListener('error',fallback);if(img.complete&&img.naturalWidth===0)fallback();});
 document.querySelectorAll('.js-tools').forEach(x=>x.hidden=false);
 restore();apply(true,false);
})();
