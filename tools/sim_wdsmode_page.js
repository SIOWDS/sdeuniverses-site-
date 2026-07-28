// DOM 桩：验证 wds-mode.js 三种场景
function makeEnv(hasNav, page, ls){
  const store = Object.assign({}, ls);
  const mkEl = (tag)=>{
    const e = {tag, className:'', textContent:'', innerHTML:'', style:{cssText:''}, dataset:{}, children:[], attrs:{},
      classList:{ _s:new Set(), add(c){this._s.add(c)}, remove(c){this._s.delete(c)}, contains(c){return this._s.has(c)} },
      appendChild(c){this.children.push(c); c.parent=this; return c},
      insertBefore(c,ref){this.children.push(c); return c},
      querySelector(sel){ return findSel(e, sel); },
      querySelectorAll(sel){ return findAll(e, sel); },
      addEventListener(){}, focus(){}, set href(v){this.attrs.href=v}, get href(){return this.attrs.href},
      // 桩补：页面后来给模式按钮加了 data-k（标准/深度/联网），paintModes 会 getAttribute 读它
      getAttribute(n){ if(n&&n.indexOf('data-')===0){ const k=n.slice(5); return (this.dataset&&this.dataset[k]!==undefined)?this.dataset[k]:null; } return this.attrs[n]!==undefined?this.attrs[n]:null; },
      setAttribute(n,v){ if(n&&n.indexOf('data-')===0){ this.dataset[n.slice(5)]=v; } else { this.attrs[n]=v; } },
      set onclick(f){this._onclick=f}, get onclick(){return this._onclick}
    };
    return e;
  };
  function classMatch(e, cls){ return (e.className||'').split(/\s+/).includes(cls) || e.classList._s.has(cls); }
  function walk(root, fn){ const st=[...root.children]; while(st.length){const n=st.shift(); if(fn(n))return n; st.push(...(n.children||[]));} return null; }
  function walkAll(root, fn){ const out=[]; const st=[...root.children]; while(st.length){const n=st.shift(); if(fn(n))out.push(n); st.push(...(n.children||[]));} return out; }
  function parseInner(e){ // 极简：为 layer.innerHTML 生成可查询的假子节点
    const html=e.innerHTML||'';
    const classes=[...html.matchAll(/class='([^']+)'/g)].map(m=>m[1].split(/\s+/)).flat();
    e.children = classes.map(cs=>{const c=mkEl('div'); c.className=cs; 
      const dm=html.match(new RegExp("class='[^']*"+cs+"[^']*'[^>]*data-m='([a-z]+)'")); if(dm)c.dataset.m=dm[1];
      return c;});
  }
  function findSel(root, sel){
    // 桩补：页面用上了 ".cls[data-x='v']" 这种选择器（两个页签靠 data-m 区分）
    const am = sel.match(/^\.([\w-]+)\[([\w-]+)='([^']*)'\]$/);
    if(am){ return walk(root, n=>classMatch(n, am[1]) && n.getAttribute && n.getAttribute(am[2])===am[3]); }
    if(sel[0]==='.'){ return walk(root, n=>classMatch(n, sel.slice(1))); }
    if(sel.startsWith("a[href=")){ const want=sel.match(/'([^']+)'/)[1]; return walk(root,n=>n.tag==='a'&&n.attrs.href===want); }
    return null;
  }
  function findAll(root, sel){ if(sel[0]==='.') return walkAll(root, n=>classMatch(n, sel.slice(1))); return []; }
  const body=mkEl('body'), head=mkEl('head'), docEl=mkEl('html');
  const nav = hasNav ? mkEl('nav') : null; if(nav){ nav.className='nav-links'; body.appendChild(nav); }
  const doc = { head, body, documentElement:docEl,
    createElement:(t)=>{const e=mkEl(t); const desc=Object.getOwnPropertyDescriptor(e,'innerHTML'); 
      let _ih=''; Object.defineProperty(e,'innerHTML',{get:()=>_ih,set:(v)=>{_ih=v;e._rawHTML=v;parseInnerFor(e,v);}}); return e;},
    querySelector:(sel)=>findSel({children:body.children}, sel) };
  // 桩补：按"每个标签一次"扫描，而不是按 class 去 html 里回查——
  // 同名 class 有多个（三个 .wdsm-mode 各带不同 data-k）时，回查只会拿到第一个，全部串成同一个值。
  function parseInnerFor(e,html){
    const out=[];
    const re=/<(\w+)([^>]*)>/g; let m;
    while((m=re.exec(html))){
      const tag=m[1], attrs=m[2]||'';
      const cm=attrs.match(/class='([^']*)'/); if(!cm) continue;
      const c=mkEl(tag); c.className=cm[1];
      const dm=attrs.match(/data-m='([^']*)'/); if(dm)c.dataset.m=dm[1];
      const dk=attrs.match(/data-k='([^']*)'/); if(dk)c.dataset.k=dk[1];
      out.push(c);
    }
    e.children=out;
  }
  let navigated=null;
  const win = { WDSM_PAGE: page?1:undefined,
    localStorage:{ getItem:k=>store[k]??null, setItem:(k,v)=>{store[k]=v}, removeItem:k=>{delete store[k]} },
    history:{length:2, back(){navigated='BACK'}},
    location:{ get href(){return navigated}, set href(v){navigated=v} } };
  return {doc,win,body,nav,store,get navigated(){return navigated}};
}
const fs=require('fs');
let src=fs.readFileSync('public/wds-mode.js','utf8');
function run(env){
  const sandbox = `(function(window,document,localStorage,setTimeout){ var history=window.history; ${src} })`;
  eval(sandbox)(env.win, env.doc, env.win.localStorage, (f)=>f());
}
let pass=0, fail=0; const T=(name,c)=>{ if(c){pass++;console.log('PASS',name)}else{fail++;console.log('FAIL',name)} };

// 场景1：普通页有导航 + 旧 LS=1（历史上会自动弹出）
let e1=makeEnv(true,false,{sdeuniverses_wds_mode:'1'});
run(e1);
const pill = e1.nav.children.find(c=>(c.className||'').includes('wdsm-navbtn'));
T('导航药丸=真实链接指向独立页', pill && pill.attrs.href==='/taste/wds-chat/');
T('药丸无 preventDefault 开浮层的 onclick', !pill._onclick);
const layer1 = e1.body.children.find(c=>c.className==='wdsm-layer');
T('旧 LS=1 也不再自动弹出浮层', layer1 && !layer1.classList.contains('on'));
T('旧 LS 记忆已清除', !('sdeuniverses_wds_mode' in e1.store));

// 场景2：普通页无导航 → 浮钮=跳转
let e2=makeEnv(false,false,{});
run(e2);
const fab = e2.body.children.find(c=>c.className==='wdsm-fab');
T('无导航页挂浮钮', !!fab);
fab._onclick && fab._onclick();
T('浮钮点击=跳转独立页而非开浮层', e2.navigated==='/taste/wds-chat/');

// 场景3：独立页模式
let e3=makeEnv(false,true,{});
run(e3);
const layer3 = e3.body.children.find(c=>c.className==='wdsm-layer');
T('独立页载入即整页打开', layer3 && layer3.classList.contains('on'));
T('独立页不再挂浮钮', !e3.body.children.find(c=>c.className==='wdsm-fab'));
const tabs3 = layer3.children.filter(c=>(c.className||'').includes('wdsm-tab')&&!(c.className||'').includes('wdsm-tabs'));
const normal3 = tabs3.find(t=>t.dataset.m==='normal');
// 桩里没有站点语言标记，t() 会落到英文档——断言按两种语言都认（设计后来加了中英双语）
T('常规页签改名为返回浏览', normal3 && /返回|Back/.test(normal3.textContent));
normal3.onclick && normal3.onclick();
T('返回浏览=history.back', e3.navigated==='BACK');

// —— 07-20 配额显示修复（静态核对 public/wds-mode.js）——
{
  const S = require("fs").readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
  const dec = S.replace(/\\u([0-9a-fA-F]{4})/g, (m, h) => String.fromCharCode(parseInt(h, 16)));
  // 文案后来搬进 TXT/t()，断言随设计改写：中文档词条仍是「本场剩余」，拼装处走 t("left")+sessionLeft
  T("顶栏计数改称「本场剩余」，不再冒充今日额度", dec.includes("本场剩余 100 次") && dec.includes('left: "本场剩余 "') && dec.includes('t("left") + sessionLeft'));
  T("服务端 quota 事件被消费并写入 dayLeft", dec.includes('j.t === "quota"') && dec.includes("dayLeft = j.v.left"));
  T("今日额度为 0 时锁输入并说明另两个入口不受影响", dec.includes("dayLeft === 0") && dec.includes("今日本机额度已用完"));
  T("＋新对话只复位本场，不把今日额度画回满格", dec.includes("dayLeft 不复位"));
  T("计数带 title 说明本场与今日两义", dec.includes("turnsEl.title"));
}

// —— 07-28 站内文献延后 + Claude/GPT 式滚动留白（静态核对 + 行为核对）——
{
  const S = require("fs").readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
  const dec = S.replace(/\\u([0-9a-fA-F]{4})/g, (m, hx) => String.fromCharCode(parseInt(hx, 16)));
  T("来源事件只入暂存，不在流里当场渲染", /j\.t === "sources"[^\n]*pendSite = j\.v/.test(dec) && !/j\.t === "sources"[^\n]*renderSources/.test(dec));
  T("站外来源同样入暂存", /j\.t === "web"[^\n]*pendWeb = j\.v/.test(dec) && !/j\.t === "web"[^\n]*renderSources\(/.test(dec));
  T("正文写完才 flushSrcs（排在 mountActs 之前）", dec.indexOf("flushSrcs();") > 0 && dec.indexOf("flushSrcs();") < dec.indexOf("mountActs(cell, answer)"));
  T("出错/中途停下的路径也会补上来源", (dec.match(/flushSrcs\(\);/g) || []).length >= 2);
  T("来源块默认收起、点头部展开", dec.includes(".wdsm-src-l{display:none") && dec.includes('box.classList.toggle("on")'));
  T("点正文里的 [W] 引用会先把来源展开", dec.includes('box.classList.add("on")'));
  T("来源插在追问建议之前", dec.includes("cell.turn.insertBefore(box, cell.follows)"));
  T("只在贴底时跟随滚动，不再无条件拽到底", dec.includes("if (stick) scrollBottom()") && !dec.includes("bodyEl.scrollTop = bodyEl.scrollHeight;\n      cell.a"));
  T("手动上翻即松手（scroll 监听改 stick）", dec.includes('bodyEl.addEventListener("scroll"') && dec.includes("setStick(atBottom())"));
  T("有回到最新按钮且默认隐藏", dec.includes("wdsm-tobot") && dec.includes("style='display:none'>↓"));
  T("新一问下方留一屏白（末轮 minHeight）", dec.includes('turn.style.minHeight = Math.max(0, bodyEl.clientHeight - 88)') && dec.includes('all[ti].style.minHeight = ""'));
  T("留白只给最后一轮，前面几轮会被清掉", /for \(var ti = 0; ti < all\.length - 1; ti\+\+\)/.test(dec));
  T("正文列宽与上下留白已放宽", dec.includes("max-width:768px") && dec.includes("padding:34px 24px 56px") && dec.includes(".wdsm-turn{margin-bottom:46px"));
  // ── 成文：存到用户自选目录（File System Access API）──
  T("成文面板多了「存到目录」按钮", dec.includes("wdsm-tbtn ddir") && dec.includes('dirBtn.textContent = t("dDir")'));
  T("下拉菜单里能选/换目录，并显示当前目录", dec.includes('t("dDirPick")') && dec.includes("dirPick(function (hd)") && dec.includes('dirName() ? (t("dDirSaved") + dirName())'));
  T("目录句柄存进 IndexedDB（localStorage 存不了句柄）", dec.includes('DIRDB = "wds-fs"') && dec.includes("objectStore(DIRSTORE).put(hd, DIRKEY)"));
  T("开页就把句柄读进内存（否则点击那一下要不到权限）", /dirLoad\(function \(hd\) \{ if \(hd\) DIRH = hd; \}\)/.test(dec));
  T("复用目录时先查权限、不行再当场要一次", dec.includes("queryPermission(opt)") && dec.includes("requestPermission(opt)"));
  T("不支持的浏览器回退成普通下载，不让读者空手", dec.includes('say(t("dDirNoApi")); download(name, text)'));
  T("同名不覆盖，撞名自动加序号", dec.includes("getFileHandle(nm, { create: false })") && dec.includes('base + "-" + n + ext'));
  T("文件名里的非法字符被清掉", /function safeName/.test(dec) && dec.includes('replace(/\\s+/g, " ")'));
  T("中英两套文案都齐（dDir/dDirPick/dDirNoApi/dDirDenied）", ["dDir:", "dDirPick:", "dDirNoApi:", "dDirDenied:", "dDirSaved:"].every(function (k) { return (dec.split(k).length - 1) >= 2; }));
}

console.log(pass+' PASS / '+fail+' FAIL'); process.exit(fail?1:0);
