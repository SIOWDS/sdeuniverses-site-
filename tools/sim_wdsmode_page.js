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
  function parseInnerFor(e,html){ const classes=[...html.matchAll(/class='([^']+)'/g)].map(m=>m[1]);
    e.children = classes.map(cs=>{const c=mkEl('div'); c.className=cs;
      const dm=html.match(new RegExp("class='"+cs.replace(/ /g,' ')+"'[^>]*data-m='([a-z]+)'")); if(dm)c.dataset.m=dm[1];
      return c;}); }
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
T('常规页签改名为返回浏览', normal3 && /返回/.test(normal3.textContent));
normal3.onclick && normal3.onclick();
T('返回浏览=history.back', e3.navigated==='BACK');

// —— 07-20 配额显示修复（静态核对 public/wds-mode.js）——
{
  const S = require("fs").readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
  const dec = S.replace(/\\u([0-9a-fA-F]{4})/g, (m, h) => String.fromCharCode(parseInt(h, 16)));
  T("顶栏计数改称「本场剩余」，不再冒充今日额度", dec.includes("本场剩余 100 次") && dec.includes('"本场剩余 " + sessionLeft + " 次"'));
  T("服务端 quota 事件被消费并写入 dayLeft", dec.includes('j.t === "quota"') && dec.includes("dayLeft = j.v.left"));
  T("今日额度为 0 时锁输入并说明另两个入口不受影响", dec.includes("dayLeft === 0") && dec.includes("今日本机额度已用完"));
  T("＋新对话只复位本场，不把今日额度画回满格", dec.includes("dayLeft 不复位"));
  T("计数带 title 说明本场与今日两义", dec.includes("turnsEl.title"));
}

console.log(pass+' PASS / '+fail+' FAIL'); process.exit(fail?1:0);
