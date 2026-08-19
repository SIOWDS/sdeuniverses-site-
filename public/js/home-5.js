(function(){
  const d=new Date();
  const box=document.getElementById('dq-cards');
  var trio;
  try{ trio=window.DQ_pickForDate(d.getFullYear(),d.getMonth()+1,d.getDate()); }
  catch(err){
    trio=[
      {t:"你越用力地抓它，它越不是它。",u:"/column/self-discipline-genesis/"},
      {t:"有一个教育在发生，有一个教育在证明发生。",u:"/column/what-is-education/"},
      {t:"情越真的人，输得越尽。",u:"/column/redology-intro/"}
    ];
    if(box){var e=document.createElement('div');e.style.cssText='color:#ff9c9c;font-size:12px;margin-bottom:10px';e.textContent='[dq-fallback] '+(err&&err.message||err);box.parentNode.insertBefore(e,box);}
  }
  if(box){
    function cstars(){
      var s='';
      for(var i=0;i<7;i++){
        var x=(Math.random()*96+2).toFixed(1), y=(Math.random()*90+4).toFixed(1);
        var sz=(Math.random()*1.4+0.9).toFixed(1), du=(Math.random()*2.6+2).toFixed(1);
        var dl=(Math.random()*4).toFixed(1), mo=(Math.random()*0.35+0.4).toFixed(2);
        s+='<span class="ll-star" style="left:'+x+'%;top:'+y+'%;width:'+sz+'px;height:'+sz+'px;--d:'+du+'s;--dl:'+dl+'s;--mo:'+mo+'"></span>';
      }
      return s;
    }
    box.innerHTML=trio.map(function(q){
      return '<a class="dq-card" href="'+q.u+'"><span class="cstars">'+cstars()+'</span><div class="dq-text">'+q.t+'</div><div class="dq-go">读全文 →</div></a>';}).join('');
    var dt=document.getElementById('dq-date');
    if(dt) dt.textContent=(d.getMonth()+1)+'月'+d.getDate()+'日';
  }
  /* 星场 */
  var sf=document.getElementById('dq-stars');
  if(sf){
    var html='';
    for(var i=0;i<64;i++){
      var x=(Math.random()*100).toFixed(2), y=(Math.random()*100).toFixed(2);
      var size=(Math.random()*2.2+0.8).toFixed(1), dur=(Math.random()*3+2.2).toFixed(1);
      var dl=(Math.random()*5).toFixed(1), mo=(Math.random()*0.5+0.45).toFixed(2);
      html+='<span class="ll-star" style="left:'+x+'%;top:'+y+'%;width:'+size+'px;height:'+size+'px;--d:'+dur+'s;--dl:'+dl+'s;--mo:'+mo+'"></span>';
    }
    html+='<span class="ll-shoot" style="left:12%;top:16%;animation-delay:2s"></span>';
    html+='<span class="ll-shoot" style="left:58%;top:8%;animation-delay:9s"></span>';
    sf.innerHTML=html;
  }
  /* 指针3D倾斜 */
  if(window.matchMedia && window.matchMedia('(pointer:fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    document.querySelectorAll('.dq-card').forEach(function(card){
      card.addEventListener('pointermove',function(e){
        var r=card.getBoundingClientRect();
        var px=(e.clientX-r.left)/r.width-0.5, py=(e.clientY-r.top)/r.height-0.5;
        card.style.transform='perspective(700px) rotateX('+(-py*7).toFixed(2)+'deg) rotateY('+(px*9).toFixed(2)+'deg) translateY(-6px)';
        card.style.animationPlayState='paused,paused';
      });
      card.addEventListener('pointerleave',function(){
        card.style.transform=''; card.style.animationPlayState='';
      });
    });
  }
})();
