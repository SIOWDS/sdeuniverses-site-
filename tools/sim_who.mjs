/* 成员面（v-who）的护栏 —— 抠页面真代码跑。
 * 六组：①接线四处 ②纪律：不出现任何可排序成等级的数字 ③距离用真 Jaccard 且与中位数对照
 *      ④没指纹时如实说、不编数 ⑤两处空态写明出路 ⑥静态索引失败不拦路
 */
import fs from "node:fs";
import vm from "node:vm";

const P = new URL("../public/sde-wechat/index.html", import.meta.url).pathname;
const H = fs.readFileSync(P, "utf8");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) pass++; else { fail++; console.log("  \u2717 " + n); } };

console.log("\u2460 \u63a5\u7ebf\u56db\u5904");
ok('show() 白名单含 who', /\["gate","who","home"/.test(H));
ok('视图 v-who 与容器 wh-body 都在', /id="v-who"[\s\S]{0,120}id="wh-body"/.test(H));
ok('who 是二级页：返回键会显示', /v==="who"\)\?"block"/.test(H) || /\|\|v==="who"\|\|/.test(H));
ok('标题分支用被看的人的名字', /v==="who"\)el\("t-ttl"\)\.textContent=whoName/.test(H));
ok('「我」页有入口且接了线', /id="b-who"/.test(H) && /el\("b-who"\)[\s\S]{0,60}whoMe/.test(H));
ok('社区首页的作者名可点进成员面', /hm-who[\s\S]{0,200}whoGo\(/.test(H));

const A = H.indexOf("/* \u2500\u2500 \u6210\u5458\u9762");
const B = H.indexOf("/* \u2500\u2500 \u5168\u6743\u7ba1\u7406 \u2500\u2500 */");
if (A < 0 || B < 0) { console.log("\u2717 \u62a0\u4e0d\u51fa\u6210\u5458\u9762\u4ee3\u7801"); process.exit(1); }
const SRC = H.slice(A, B);

function mk(id){ return { id, innerHTML:"", _a:{}, setAttribute(k,v){this._a[k]=v;}, getAttribute(k){return this._a[k]||null;}, textContent:"" }; }
function run(idx, pubs, cards, me, uid, name){
  const nodes = { "wh-body": mk("wh-body") };
  const ctx = {
    el:(i)=>nodes[i]||(nodes[i]=mk(i)),
    esc:(s)=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"),
    ME: me, CD_STATE:{open:["\u9876\u56de\u671f",""],alive:["\u5df2\u4ea4\u624b",""],dead:["\u6b7b\u683c",""],untouched:["\u672a\u4ea4\u624b",""]},
    show:()=>{}, cdOne:()=>{}, cdGo:()=>{}, openDm:()=>{}, cdApi:()=>Promise.resolve({ok:true,cards}),
    fetch:(u)=>Promise.resolve({ json:()=>Promise.resolve(u.indexOf("props")>0?idx:pubs) }),
    Promise, console, document:{querySelectorAll:()=>[]}, window:{},
    _nodes:nodes,
  };
  vm.createContext(ctx); vm.runInContext(SRC, ctx);
  ctx.whoUid = uid; ctx.whoName = name;
  return ctx;
}
const FPA = Array.from({length:100},(_,i)=>"a"+i);
const FPB = Array.from({length:100},(_,i)=>(i<10?"a"+i:"b"+i));   // 交 10 / 并 190 ⇒ j≈0.0526
const IDX = { calib:{ j_median:0.03378, j_max:0.10043 }, people:[
  { slug:"me", name:"\u6211", n:5, fields:["\u6559\u80b2\u5b66"], fp:FPA },
  { slug:"him", name:"\u4ed6", n:9, fields:["\u533b\u5b66"], fp:FPB },
  { slug:"non", name:"\u65b0\u4eba", n:1, fields:[], fp:null },
]};
const PUBS = { students:[{ name:"\u4ed6", items:[{title:"\u7bc7\u4e00",url:"/students/x/a/",kind:"\u7cfb\u5217"}] }] };
const CARDS = [
  { id:"1", state:"alive", prop:"\u547d\u98981", pid:"p_a_1" },
  { id:"2", state:"open",  prop:"\u547d\u98982" },
];
const ME = { uid:"u-me", name:"\u6211" };

const c1 = run(IDX, PUBS, CARDS, ME, "u-him", "\u4ed6");
await c1.whoLoad(); await new Promise(r=>setTimeout(r,30));
const O = c1._nodes["wh-body"].innerHTML;

console.log("\u2461 \u7eaa\u5f8b\uff1a\u6ca1\u6709\u53ef\u6392\u5e8f\u6210\u7b49\u7ea7\u7684\u6570\u5b57");
const BODY = O.replace(/<div class="wh-say">[\s\S]*?<\/div>/g, "");
for (const w of ["\u7c89\u4e1d","\u9605\u8bfb\u91cf","\u70b9\u8d5e","\u6392\u540d","\u6392\u884c","\u5f97\u5206","\u699c"])
  ok("\u9875\u4e0a\u4e0d\u51fa\u73b0\u300c"+w+"\u300d", BODY.indexOf(w) < 0);
ok("\u6e90\u7801\u628a\u8fd9\u6761\u7eaa\u5f8b\u5199\u8fdb\u4e86\u6ce8\u91ca", /\u4e0d\u51fa\u73b0\u4efb\u4f55\u53ef\u6392\u5e8f\u6210\u7b49\u7ea7\u7684\u6570\u5b57/.test(SRC));
ok("\u9875\u4e0a\u660e\u8bf4\u8fd9\u4e0d\u662f\u8bc4\u5206\u4e5f\u4e0d\u6392\u540d", /\u8fd9\u4e0d\u662f\u8bc4\u5206\uff0c\u4e5f\u4e0d\u6392\u540d/.test(O));

console.log("\u2462 \u8ddd\u79bb\u662f\u7b97\u51fa\u6765\u7684");
ok("Jaccard \u7b97\u5bf9\uff080.0526\uff09", O.indexOf("0.0526") > 0);
ok("\u4e0e\u5168\u7ad9\u4e2d\u4f4d\u5bf9\u7167", O.indexOf("0.034") > 0);
ok("\u91cd\u53e0\u9ad8\u4e8e\u4e2d\u4f4d\u65f6\u8bf4\u7684\u662f\u300c\u5bb9\u6613\u5f7c\u6b64\u9644\u548c\u300d", /\u5bb9\u6613\u53ea\u662f\u5f7c\u6b64\u9644\u548c/.test(O));
ok("\u660e\u5199\u91cd\u53e0\u4f4e\u2260\u4ed6\u66f4\u597d", /\u91cd\u53e0\u7387\u4f4e\u4e0d\u7b49\u4e8e\u4ed6\u66f4\u597d/.test(O));

console.log("\u2463 \u6ca1\u6307\u7eb9\u5c31\u4e0d\u7f16\u6570");
const c2 = run(IDX, PUBS, CARDS, ME, "u-non", "\u65b0\u4eba");
await c2.whoLoad(); await new Promise(r=>setTimeout(r,30));
const O2 = c2._nodes["wh-body"].innerHTML;
ok("\u5982\u5b9e\u8bf4\u7b97\u4e0d\u51fa\u8ddd\u79bb", /\u8fd8\u7b97\u4e0d\u51fa\u4f60\u4eec\u4e4b\u95f4\u7684\u8ddd\u79bb/.test(O2));
ok("\u4e0d\u7ed9\u4e00\u4e2a\u5047\u6570", !/wh-j">0\./.test(O2));
ok("\u8bf4\u6e05\u695a\u4e3a\u4ec0\u4e48\u7b97\u4e0d\u51fa", /800 \u4e2a\u8bed\u6c47\u4e8c\u5143\u7ec4/.test(O2));

console.log("\u2464 \u7a7a\u6001\u5199\u660e\u51fa\u8def");
const c3 = run(IDX, { students: [] }, [], ME, "u-him", "\u4ed6");
await c3.whoLoad(); await new Promise(r=>setTimeout(r,30));
const O3 = c3._nodes["wh-body"].innerHTML;
ok("\u6ca1\u547d\u9898\u65f6\u8bb2\u6e05\u695a\u600e\u6837\u624d\u4f1a\u7559\u5728\u8d26\u672c\u4e0a", /\u88ab\u4e00\u6761\u5206\u79bb\u7ebf\u6551\u56de\u6765/.test(O3));
ok("\u4e0d\u662f\u4e00\u53e5\u300c\u6682\u65e0\u5185\u5bb9\u300d", O3.indexOf("\u6682\u65e0\u5185\u5bb9") < 0);

console.log("\u2465 \u9759\u6001\u7d22\u5f15\u5931\u8d25\u4e0d\u62e6\u8def");
const c4 = run(null, null, CARDS, ME, "u-him", "\u4ed6");
await c4.whoLoad(); await new Promise(r=>setTimeout(r,30));
const O4 = c4._nodes["wh-body"].innerHTML;
ok("\u4e24\u4efd\u7d22\u5f15\u90fd\u6ca1\u4e86\uff0c\u4ed6\u7684\u547d\u9898\u7167\u6837\u6446\u51fa\u6765", O4.indexOf("\u547d\u98981") > 0);
ok("\u4e0d\u62a5\u300c\u52a0\u8f7d\u5931\u8d25\u300d", O4.indexOf("\u52a0\u8f7d\u5931\u8d25") < 0);

console.log("\u2466 el() \u65e0\u60ac\u7a7a\u5f15\u7528");
const ids = new Set([...H.matchAll(/id="([A-Za-z0-9_-]+)"/g)].map(m=>m[1]));
const refs = [...SRC.matchAll(/\bel\("([A-Za-z0-9_-]+)"\)/g)].map(m=>m[1]).filter(x=>x!=="wh-dm"&&x!=="wh-cd");
const miss = refs.filter(r=>!ids.has(r));
ok("\u65e0\u60ac\u7a7a\u5f15\u7528" + (miss.length?"\uff1a"+miss.join(","):""), miss.length===0);

console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
process.exit(fail ? 1 : 0);
