/* Progressive enhancement: every book and reading link is present without JS. */
(function(){
 'use strict';
 const grid=document.getElementById('book-grid'); if(!grid)return;
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
   return initialOrder.get(a)-initialOrder.get(b);
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
