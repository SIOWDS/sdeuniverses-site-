(function(){
  var PB=[
{id:1,zh:"SIO哲学导论",en:"An Introduction to SIO Philosophy",d:"core"},
{id:2,zh:"SIO本体论",en:"SIO Ontology",d:"core"},
{id:3,zh:"SIO三大公理",en:"The Three Axioms of SIO",d:"core"},
{id:4,zh:"SDE发生学",en:"SDE Genealogics",d:"core"},
{id:5,zh:"特征纠缠解码",en:"Decoding Feature Entanglement",d:"core"},
{id:6,zh:"西方哲学史",en:"A History of Western Philosophy",d:"civ"},
{id:7,zh:"中华文化导论",en:"Introduction to Chinese Culture",d:"civ"},
{id:8,zh:"中华文明之气",en:"The Qi of Chinese Civilization",d:"civ"},
{id:9,zh:"论艺术",en:"On Art",d:"civ"},
{id:10,zh:"论自由",en:"On Freedom",d:"civ"},
{id:11,zh:"三律治理",en:"Three-Law Governance",d:"gov"},
{id:12,zh:"意义管理学",en:"Meaning Management",d:"gov"},
{id:13,zh:"三元法学",en:"Triadic Law",d:"gov"},
{id:14,zh:"SIO逻辑学导论",en:"An Introduction to SIO Logic",d:"gov"},
{id:15,zh:"生成认识论",en:"Generative Epistemology",d:"gov"},
{id:16,zh:"SIO心理学",en:"SIO Psychology",d:"gov"},
{id:17,zh:"SIO经济学导论",en:"An Introduction to SIO Economics",d:"gov"},
{id:18,zh:"基于GPT的中国教育改革",en:"Educational Reform in China Based on GPT",d:"edu"},
{id:20,zh:"GPT时代的大学革命",en:"The University Revolution in the GPT Era",d:"edu"},
{id:21,zh:"AI时代的数学教育转型",en:"The Transformation of Mathematics Education in the Age of AI",d:"edu"},
{id:22,zh:"学习发生学导论",en:"Introduction to Learning Generativics",d:"edu"},
{id:23,zh:"GPT时代的SDE批判性思维",en:"SDE Critical Thinking in the GPT Era",d:"edu"},
{id:24,zh:"SDE交互医学",en:"SDE Interactive Medicine",d:"life"},
{id:25,zh:"心血管健康的发生学重建",en:"The Generative Reconstruction of Cardiovascular Health",d:"life"},
{id:26,zh:"逆转糖尿病",en:"Reversing Diabetes",d:"life"},
{id:27,zh:"逆转高血压之路",en:"The Path to Reversing Hypertension",d:"life"},
{id:28,zh:"穿越抑郁",en:"Crossing Depression",d:"life"},
{id:29,zh:"返青",en:"Rejuvenation",d:"life"},
{id:30,zh:"跑步与健康",en:"Running and Health",d:"life"},
{id:31,zh:"创造力发生机制解码",en:"Decoding the Generative Mechanisms of Creativity",d:"cre"},
{id:32,zh:"原创力动力学解码",en:"Decoding Originality Dynamics",d:"cre"},
{id:33,zh:"突破抵达原创",en:"Breakthrough to Originality",d:"cre"},
{id:35,zh:"AGI：人工智能的巴别塔",en:"AGI: the Babel Tower of Artificial Intelligence",d:"ai"},
{id:36,zh:"人—GPT超级复合智能",en:"Human-GPT Super Composite Intelligence",d:"ai"},
{id:37,zh:"未来人类做什么？",en:"What Will Future Humans Do?",d:"ai"},
{id:38,zh:"内卷与突围",en:"Involution and the Way Out",d:"ai"},
{id:39,zh:"人生的真谛",en:"The True Meaning of Life",d:"core"},
{id:40,zh:"在突变中发生",en:"In Mutation, Becoming",d:"cre"},
{id:41,zh:"语言发生学",en:"Language Occurrence",d:"civ"},
{id:42,zh:"大学的终结与重生",en:"The End and Rebirth of the University",d:"edu"},
{id:49,zh:"互动医学入门",en:"An Introduction to Interactive Medicine",d:"life"},
{id:51,zh:"SDE三方程导论",en:"Introduction to the Three SDE Equations",d:"core"},
{id:52,zh:"六路径方法论入门",en:"Introduction to the Six-Path Methodology",d:"core"}
  ];
  var DM={core:{zh:"本体论核心",en:"Ontology Core"},civ:{zh:"文明与人文",en:"Civilization"},gov:{zh:"治理与社科",en:"Governance"},edu:{zh:"教育革命",en:"Education"},life:{zh:"健康与生命",en:"Health & Life"},cre:{zh:"创造力",en:"Creativity"},ai:{zh:"AI 时代前沿",en:"AI Frontier"}};
  var ORDER=["core","civ","gov","edu","life","cre","ai"];
  function isZh(){return document.body.className!=="en";}
  var active="all";
  function render(){
    var zh=isZh();
    var grid=document.getElementById("pressGrid");
    if(!grid)return;
    var list=active==="all"?PB:PB.filter(function(b){return b.d===active;});
    grid.innerHTML=list.map(function(b){
      var name=zh?b.zh:b.en;
      var dm=DM[b.d]||{zh:b.d,en:b.d};
      return '<a href="/books/m/'+b.id+'/" style="display:block;text-decoration:none;transition:transform .16s">'
        +'<div style="width:100%;aspect-ratio:2/3;border-radius:3px;overflow:hidden;box-shadow:0 8px 22px rgba(0,0,0,0.5);border:1px solid rgba(212,178,94,0.18)">'
        +'<img src="/books/covers/'+b.id+'.jpg" alt="'+name.replace(/"/g,"")+'" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block">'
        +'</div>'
        +'<div style="color:#D6C9A8;font-size:12.5px;font-weight:700;margin-top:8px;line-height:1.4">'+name+'</div>'
        +'<div style="color:#8A7A54;font-size:11px;margin-top:3px">'+(zh?dm.zh:dm.en)+'</div>'
        +'</a>';
    }).join("");
  }
  function renderFilter(){
    var zh=isZh();
    var fb=document.getElementById("pressFilter");
    if(!fb)return;
    var btns=[["all",zh?"全部":"All"]];
    ORDER.forEach(function(k){btns.push([k,zh?DM[k].zh:DM[k].en]);});
    fb.innerHTML=btns.map(function(x){
      var on=x[0]===active;
      return '<button data-k="'+x[0]+'" style="margin:4px 5px;padding:6px 15px;border-radius:20px;font-size:12.5px;letter-spacing:0.03em;cursor:pointer;border:1px solid '+(on?"#D4B25E":"rgba(212,178,94,0.3)")+';background:'+(on?"#D4B25E":"transparent")+';color:'+(on?"#12100C":"#B4A780")+';font-weight:'+(on?"700":"400")+'">'+x[1]+'</button>';
    }).join("");
    Array.prototype.forEach.call(fb.querySelectorAll("button"),function(btn){
      btn.onclick=function(){active=btn.getAttribute("data-k");renderFilter();render();};
    });
  }
  renderFilter();render();
  window.__renderPress=function(){renderFilter();render();};
})();


/* 睡眠专栏 · 首页入口（2026-08-09） */
;(function(){
  function mountSleepColumn(){
    /* 2026-08-17：子导航已并成两排各 5 条（.nbs-grid），再往末尾 append 一条就会破坏对称。
       睡眠专栏改挂在「健康专栏」页的子导航里（静态 HTML），此处不再动顶栏。 */
    if(document.getElementById('sleep-column-home')) return;
    var hero=document.getElementById('hero'); if(!hero)return;
    var section=document.createElement('section');section.id='sleep-column-home';
    section.style.cssText='position:relative;overflow:hidden;background:radial-gradient(circle at 72% 18%,rgba(111,87,174,.28),transparent 28%),linear-gradient(145deg,#090D18 0%,#12182B 52%,#080B13 100%);border-bottom:1px solid rgba(196,167,231,.25);padding:76px 24px;color:#EEF3FB';
    section.innerHTML=''
      +'<div aria-hidden="true" style="position:absolute;inset:0;opacity:.28;background-image:radial-gradient(circle,#fff 0 1px,transparent 1.5px);background-size:88px 88px;transform:rotate(6deg)"></div>'
      +'<div style="position:relative;z-index:1;max-width:1120px;margin:auto">'
      +'<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:28px;flex-wrap:wrap;margin-bottom:34px">'
      +'<div style="max-width:760px"><div style="font-size:12px;letter-spacing:.34em;color:#C4A7E7;margin-bottom:14px">首页新专栏 · SLEEP · CARE · THOUGHT</div>'
      +'<h2 style="font-family:Georgia,\'Noto Serif SC\',serif;font-size:clamp(38px,7vw,72px);line-height:1.05;margin:0;color:#F7F1FF;letter-spacing:.06em">睡眠专栏</h2>'
      +'<p style="font-family:\'Noto Serif SC\',serif;font-size:clamp(17px,2.4vw,23px);line-height:1.9;color:#C8D1E3;margin:22px 0 0">给那些在夜里受苦、无法轻易入睡、又不愿被一句“放松点”打发的人。这里不要求你立刻睡着，先让你不再独自承担这一夜。</p>'
      +'<div style="margin-top:16px;color:#9DA9BF;font-size:14px">作者 · 王德生</div></div>'
      +'<a href="/sleep/" style="display:inline-block;text-decoration:none;background:linear-gradient(120deg,#E8D8FF,#C4A7E7);color:#171221;font-weight:800;padding:13px 24px;border-radius:999px;white-space:nowrap;box-shadow:0 10px 34px rgba(196,167,231,.24)">进入睡眠专栏 →</a></div>'
      +'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:13px">'
      +'<a href="/sleep/entrusted-beat/" style="text-decoration:none;color:inherit;border:1px solid rgba(142,202,230,.35);background:rgba(16,24,41,.78);border-radius:14px;padding:22px"><div style="font-size:11px;letter-spacing:.18em;color:#8ECAE6">01 · 托拍事件</div><h3 style="font-size:21px;margin:12px 0 8px;color:#F4F7FC">谁替睡者接住下一拍？</h3><p style="color:#AEBBD0;line-height:1.75;margin:0;font-size:14px">当你躺下以后，是否仍是所有事情的最后接口。</p></a>'
      +'<a href="/sleep/living-on-the-line/" style="text-decoration:none;color:inherit;border:1px solid rgba(196,167,231,.35);background:rgba(16,24,41,.78);border-radius:14px;padding:22px"><div style="font-size:11px;letter-spacing:.18em;color:#C4A7E7">02 · 界带</div><h3 style="font-size:21px;margin:12px 0 8px;color:#F4F7FC">住在线上</h3><p style="color:#AEBBD0;line-height:1.75;margin:0;font-size:14px">入睡不是跨过一条线，而是穿过一片地带。</p></a>'
      +'<a href="/sleep/half-minute-passage/" style="text-decoration:none;color:inherit;border:1px solid rgba(242,204,143,.35);background:rgba(16,24,41,.78);border-radius:14px;padding:22px"><div style="font-size:11px;letter-spacing:.18em;color:#F2CC8F">03 · 追认</div><h3 style="font-size:21px;margin:12px 0 8px;color:#F4F7FC">那三十秒算不算一段</h3><p style="color:#AEBBD0;line-height:1.75;margin:0;font-size:14px">一个短暂片段，不应替整夜作出判决。</p></a>'
      +'<a href="/sleep/never-in-doubt/" style="text-decoration:none;color:inherit;border:1px solid rgba(144,190,109,.35);background:rgba(16,24,41,.78);border-radius:14px;padding:22px"><div style="font-size:11px;letter-spacing:.18em;color:#90BE6D">04 · 判余</div><h3 style="font-size:21px;margin:12px 0 8px;color:#F4F7FC">必须回答，所以从不犹豫</h3><p style="color:#AEBBD0;line-height:1.75;margin:0;font-size:14px">一个确定标签，并不等于一个毫无分歧的夜晚。</p></a>'
      +'</div></div>';
    hero.insertAdjacentElement('afterend',section);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mountSleepColumn);else mountSleepColumn();
})();