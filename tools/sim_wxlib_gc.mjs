/* SDE 微信库 7 天清理的定向模拟：假 R2（带 uploaded 时间与分页），跑真 wxSweep 逻辑 */
import { readFileSync } from "node:fs";
let ok=0,bad=0; const t=(n,c)=>{ if(c){ok++;console.log("  ✓ "+n);} else {bad++;console.log("  ✗ "+n);} };
// worker.js 里 wxSweep 不是导出的，按源码同构复刻它的判据来跑（改了源码这里要跟着改）
const src=readFileSync("src/worker.js","utf8");
t("源码里 TTL 就是 7 天", /WX_TTL_MS\s*=\s*7\s*\*\s*24\s*\*\s*3600\s*\*\s*1000/.test(src));
t("新库前缀是 sde-wechat/lib/", /WX_LIB\s*=\s*"sde-wechat\/lib\/"/.test(src));
t("旧前缀仍在扫描名单里", /WX_LIB_OLD\s*=\s*"moments\/doc\//.test(src));
t("扫描有分页上限，不会扫穿", /round\s*<\s*50/.test(src));
t("上传落到新库", /PDFS\.put\(WX_LIB \+ k/.test(src));
t("读取先新库再回落旧前缀", /for \(const pre of \[WX_LIB, WX_LIB_OLD\]\)[\s\S]{0,200}PDFS\.get\(pre/.test(src));
t("删帖时两个前缀都删", /for \(const pre of \[WX_LIB, WX_LIB_OLD\]\) \{ try \{ await env\.PDFS\.delete\(pre/.test(src));
t("过期 404 有中文说明而不是裸 not found", /已超过 7 天保留期/.test(src));
t("scheduled 入口存在", /async scheduled\(event, env, ctx\)/.test(src));
t("cron 写进了 wrangler", /"crons":\s*\[\s*"17 4 \* \* \*"\s*\]/.test(readFileSync("wrangler.jsonc","utf8")));
t("手动清库挂在管理员门里", /if \(op === "admin"\)[\s\S]*?a === "gc"/.test(src));

// 把 wxSweep 抠出来单独跑（同一份源码，不是另写一份）
const body=src.slice(src.indexOf("async function wxSweep"), src.indexOf("export default {"));
const wxSweep=new Function("WX_LIB","WX_LIB_OLD","WX_TTL_MS", body+"; return wxSweep;")("sde-wechat/lib/","moments/doc/",7*24*3600*1000);
const DAY=86400000, NOW=Date.UTC(2026,6,31,10,0,0);
const mkR2=(objs)=>({ _o:objs.slice(),
  async list({prefix,limit=1000,cursor}){ const all=this._o.filter(o=>o.key.startsWith(prefix)).sort((a,b)=>a.key<b.key?-1:1);
    const st=cursor?all.findIndex(o=>o.key===cursor)+1:0; const page=all.slice(st,st+limit);
    return {objects:page, truncated: st+limit<all.length, cursor: page.length?page[page.length-1].key:null}; },
  async delete(k){ this._o=this._o.filter(o=>o.key!==k); } });

console.log("场景1 · 过 7 天的清掉，没过的留下");
{const r2=mkR2([
  {key:"sde-wechat/lib/aa.pdf", uploaded:new Date(NOW-8*DAY)},
  {key:"sde-wechat/lib/bb.pdf", uploaded:new Date(NOW-6*DAY)},
  {key:"sde-wechat/lib/cc.docx",uploaded:new Date(NOW-30*DAY)},
  {key:"sde-wechat/lib/dd.docx",uploaded:new Date(NOW-1*3600000)}]);
 const r=await wxSweep({PDFS:r2}, NOW);
 t("扫到 4 件", r.scanned===4);
 t("清掉 2 件", r.removed===2);
 t("留下 2 件", r.kept===2);
 t("留下的正是没过期那两件", r2._o.map(o=>o.key).sort().join()==="sde-wechat/lib/bb.pdf,sde-wechat/lib/dd.docx");}

console.log("场景2 · 首版落点 moments/doc/ 也要被扫到");
{const r2=mkR2([{key:"moments/doc/old.pdf", uploaded:new Date(NOW-9*DAY)},
                {key:"moments/doc/new.pdf", uploaded:new Date(NOW-2*DAY)}]);
 const r=await wxSweep({PDFS:r2}, NOW);
 t("旧前缀被清了 1 件", r.removed===1&&r2._o.length===1);}

console.log("场景3 · 绝不误伤别的东西（学员 PDF、检索索引都在同一个桶里）");
{const r2=mkR2([
  {key:"students/liu-yanyan/quiet-doing.pdf", uploaded:new Date(NOW-400*DAY)},
  {key:"search/manifest.json",                uploaded:new Date(NOW-400*DAY)},
  {key:"moments/abc123.jpg",                  uploaded:new Date(NOW-400*DAY)},
  {key:"sde-wechat/lib/x.pdf",                uploaded:new Date(NOW-400*DAY)}]);
 const r=await wxSweep({PDFS:r2}, NOW);
 t("只动微信库那一件", r.removed===1);
 t("学员PDF/检索索引/朋友圈图片都还在", r2._o.length===3&&!r2._o.some(o=>o.key.startsWith("sde-wechat/lib/")));}

console.log("场景4 · 分页：超过 1000 件也要扫全");
{const many=[]; for(let i=0;i<2500;i++) many.push({key:"sde-wechat/lib/"+String(i).padStart(5,"0")+".pdf",uploaded:new Date(NOW-10*DAY)});
 const r2=mkR2(many); const r=await wxSweep({PDFS:r2}, NOW);
 t("2500 件全扫到", r.scanned===2500);
 t("2500 件全清掉", r.removed===2500&&r2._o.length===0);}

console.log("场景5 · 桶没绑定时不炸");
{const r=await wxSweep({}, NOW); t("无 R2 时返回 ok:false 而不抛异常", r.ok===false);}

console.log("场景6 · 边界：正好 7 天算过期");
{const r2=mkR2([{key:"sde-wechat/lib/edge.pdf", uploaded:new Date(NOW-7*DAY)}]);
 const r=await wxSweep({PDFS:r2}, NOW); t("整 7 天判为过期", r.removed===1);}

console.log("\n通过 "+ok+" / 失败 "+bad); process.exit(bad?1:0);
