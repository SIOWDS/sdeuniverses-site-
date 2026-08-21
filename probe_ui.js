const fs=require("fs"); const {JSDOM}=require("jsdom");
const SRC=fs.readFileSync("public/wds-mode.js","utf8");
function boot(prof){
  const dom=new JSDOM("<!doctype html><html><body></body></html>",
    {runScripts:"outside-only",url:"https://lang.sdeuniverses.com/chatjohn/",pretendToBeVisual:true});
  const w=dom.window;
  const mem={sde_wds_key:"sk-abcdefghijklmnop"};
  Object.defineProperty(w,"localStorage",{value:{getItem:k=>(k in mem?mem[k]:null),setItem:(k,v)=>{mem[k]=String(v);},removeItem:k=>{delete mem[k];}},configurable:true});
  w.WDSM_PAGE=1; if(prof) w.WDSM_PROFILE=prof;
  w.fetch=()=>new Promise(()=>{});
  w.TextDecoder=w.TextDecoder||require("util").TextDecoder;
  try{ w.eval(SRC); }catch(e){ console.log("eval err:",e.message); }
  return w;
}
function look(w,tag){
  const d=w.document;
  const g=s=>{const e=d.querySelector(s);return e?(e.textContent||e.placeholder||"").trim():"(无)";};
  console.log("\n===== "+tag+" =====");
  console.log("侧栏抬头 :", g(".wdsm-sbrand"));
  console.log("开屏标题 :", g(".wdsm-h1"));
  console.log("开屏副题 :", g(".wdsm-sub").slice(0,60));
  console.log("种子问题 :", d.querySelectorAll(".wdsm-eg").length+" 条 ｜ "+g(".wdsm-eg").slice(0,34));
  const inp=d.querySelector(".wdsm-in,textarea");
  console.log("输入框   :", inp?(inp.placeholder||"(空)").slice(0,42):"(无)");
  console.log("工序按钮 :", g(".wdsm-toolbtn"));
  console.log("底注     :", g(".wdsm-note").slice(0,44));
}
look(boot("lang"),"挂 lang 档案");
look(boot(null),"不挂档案（ChatSDE 本身）");
