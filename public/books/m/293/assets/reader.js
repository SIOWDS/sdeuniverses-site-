
(function(){'use strict';
var root=document.documentElement, key='m293-web-reader', size=18;
function save(k,v){try{localStorage.setItem(key+'-'+k,String(v));}catch(e){}}
function get(k){try{return localStorage.getItem(key+'-'+k);}catch(e){return null;}}
size=parseInt(get('size'),10)||18;size=Math.max(16,Math.min(28,size));root.style.setProperty('--size',size+'px');root.dataset.theme=get('theme')||'day';
var small=document.getElementById('font-small'),large=document.getElementById('font-large'),theme=document.getElementById('theme'),panel=document.getElementById('toc-panel');
function setSize(delta){size=Math.max(16,Math.min(28,size+delta));root.style.setProperty('--size',size+'px');save('size',size);update();}
if(small)small.onclick=function(){setSize(-2);};if(large)large.onclick=function(){setSize(2);};
function themeLabel(){if(theme)theme.textContent=root.dataset.theme==='night'?'日间':'夜间';}themeLabel();if(theme)theme.onclick=function(){root.dataset.theme=root.dataset.theme==='night'?'day':'night';save('theme',root.dataset.theme);themeLabel();};
var open=document.getElementById('toc-open'),close=document.getElementById('toc-close');if(open)open.onclick=function(){panel.hidden=!panel.hidden;open.setAttribute('aria-expanded',String(!panel.hidden));};if(close)close.onclick=function(){panel.hidden=true;if(open)open.setAttribute('aria-expanded','false');};document.addEventListener('keydown',function(e){if(e.key==='Escape'&&panel){panel.hidden=true;if(open)open.setAttribute('aria-expanded','false');}});if(panel)panel.addEventListener('click',function(e){if(e.target.closest('a'))panel.hidden=true;});
var pageKey=key+'-position-'+location.pathname,restore=null;try{restore=JSON.parse(localStorage.getItem(pageKey)||'null');}catch(e){}
if(!location.hash&&restore&&restore.y>0){requestAnimationFrame(function(){window.scrollTo(0,restore.y);});}
var timer=null;function update(){var extent=document.documentElement.scrollHeight-innerHeight,r=extent>0?Math.max(0,Math.min(1,scrollY/extent)):1;var bar=document.getElementById('progress'),label=document.getElementById('progress-label');if(bar)bar.style.width=(r*100)+'%';if(label)label.textContent=Math.round(r*100)+'%';clearTimeout(timer);timer=setTimeout(function(){try{localStorage.setItem(pageKey,JSON.stringify({y:scrollY}));}catch(e){}},180);}
addEventListener('scroll',update,{passive:true});addEventListener('resize',update);update();
})();
