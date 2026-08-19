(function(){
  const root=document.documentElement;
  let storedTheme=null,storedSize=19;
  try{storedTheme=localStorage.getItem('sleep-theme');storedSize=parseInt(localStorage.getItem('sleep-font')||'19',10)}catch(_e){}
  if(storedTheme) root.dataset.theme=storedTheme;
  if(storedSize>=17&&storedSize<=24) root.style.setProperty('--reader-size',storedSize+'px');
  document.addEventListener('click',function(e){
    const b=e.target.closest('[data-action]'); if(!b)return;
    const action=b.dataset.action;
    if(action==='theme'){
      const next=root.dataset.theme==='paper'?'night':'paper';root.dataset.theme=next;try{localStorage.setItem('sleep-theme',next)}catch(_e){}
    }
    if(action==='font-up'||action==='font-down'){
      const cur=parseInt(getComputedStyle(root).getPropertyValue('--reader-size'),10)||19;
      const next=Math.max(17,Math.min(24,cur+(action==='font-up'?1:-1)));
      root.style.setProperty('--reader-size',next+'px');try{localStorage.setItem('sleep-font',String(next))}catch(_e){}
    }
    if(action==='toc'){
      const toc=b.closest('.paper-toc'); if(!toc)return; toc.classList.toggle('collapsed');
      const open=!toc.classList.contains('collapsed');b.setAttribute('aria-expanded',String(open));b.textContent=open?'收起':'展开';
    }
  });
  const bar=document.querySelector('.reading-progress span');
  if(bar){
    const update=()=>{const d=document.documentElement;const max=d.scrollHeight-d.clientHeight;bar.style.width=(max?Math.min(100,d.scrollTop/max*100):0)+'%'};
    addEventListener('scroll',update,{passive:true});update();
  }
})();