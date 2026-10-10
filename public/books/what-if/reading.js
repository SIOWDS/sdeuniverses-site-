(() => {
  const root=document.documentElement, fontKey='what-if-font-size', themeKey='what-if-theme';
  const sizes=[16,17,18,20,22,24]; let size=window.innerWidth<760?17:18;
  const get=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
  const set=(k,v)=>{try{localStorage.setItem(k,String(v))}catch(e){}};
  const saved=Number(get(fontKey));if(sizes.includes(saved))size=saved;
  const smaller=document.getElementById('smaller'),larger=document.getElementById('larger'),night=document.getElementById('night');
  function font(){root.style.setProperty('--reader-size',size+'px');if(smaller)smaller.disabled=size===sizes[0];if(larger)larger.disabled=size===sizes[sizes.length-1];const out=document.getElementById('font-status');if(out)out.textContent='正文字号 '+size+' 像素';}
  function theme(){const dark=root.classList.contains('dark');if(night){night.textContent=dark?'日间':'夜间';night.setAttribute('aria-pressed',String(dark));night.setAttribute('aria-label',dark?'切换日间阅读':'切换夜间阅读');}}
  if(get(themeKey)==='dark')root.classList.add('dark');font();theme();
  if(smaller)smaller.addEventListener('click',()=>{size=sizes[Math.max(0,sizes.indexOf(size)-1)];font();set(fontKey,size)});
  if(larger)larger.addEventListener('click',()=>{size=sizes[Math.min(sizes.length-1,sizes.indexOf(size)+1)];font();set(fontKey,size)});
  if(night)night.addEventListener('click',()=>{root.classList.toggle('dark');theme();set(themeKey,root.classList.contains('dark')?'dark':'light')});
  const prog=document.getElementById('prog');let queued=false;
  function progress(){const h=document.documentElement,total=h.scrollHeight-h.clientHeight;if(prog)prog.style.width=(total>0?Math.min(100,Math.max(0,h.scrollTop/total*100)):100)+'%';queued=false;}
  addEventListener('scroll',()=>{if(!queued){queued=true;requestAnimationFrame(progress)}},{passive:true});addEventListener('resize',progress);progress();
})();
