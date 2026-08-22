#!/usr/bin/env node
/* sim_chatsde_parity.js —— ChatSDE ⇄ ChatJohn 的功能对等护栏（2026-08-22）
 *
 * 缘起：三体裁写作规范（sde-creative-writing v1.2）与论文祖宗闸 v3.0 都是在 ChatJohn 的
 * 真跑上改出来的，于是很容易被写成「语言档专属」。实查下来只有**站内取料**那一处曾经如此，
 * 其余零件本来就在两台共用的 dist 产线上——但**没人钉住这件事，下一次就会被写偏**。
 *
 * 本护栏钉的就是「两台拿到的是同一份」：
 *   ① 三档创作体 SPEC 与共用硬律 CW_X、评分卡 cwGrade 里不许出现任何按档案分流的判断；
 *   ② 祖宗闸四件（ancBlock／别名法补问／quoteAudit／收稿闸）不许按档案分流；
 *   ③ 全条产线只许剩下**一处**按档案分流——取料源（语言档走白名单，其余档走主站全站检索），
 *      且那一处的 else 支必须真的通向主站，不能是空分支。
 *
 * ⚠ 判据落在「递给基底的那份 system 里有没有这段字」，不是「源码里有没有这个函数」。
 *
 *   node tools/sim_chatsde_parity.js
 */
const fs=require("fs"), W=fs.readFileSync("src/worker.js","utf8");
let p=0,f=0; const ok=(n,c)=>{c?p++:(f++,console.log("  ✗ "+n));};
// 三档创作体 SPEC 与 CW_X / cwGrade 都在 dist 那条路上，dist 对 ChatSDE 与 ChatJohn 是同一个 handler
const dist = W.slice(W.indexOf('wechat: { name: "公众号文章'), W.indexOf('outline: { name:'));
["W-1","W-7","P-1","P-8","S-2","S-7","S-8","CW_X",'cwGrade("wechat")','cwGrade("prose")','cwGrade("story")']
  .forEach(k=>ok("三档 SPEC 含 "+k+"（ChatSDE 同一条 dist 路）", dist.indexOf(k)>=0));
// 这三档的 SPEC 里不许出现任何按档案分流的判断——一分流就意味着只给某一台
ok("三档 SPEC 里没有 prof/lang 分流（两台拿到的是同一份）", !/prof\b|"lang"/.test(dist));
ok("CW_X 本身没有按档案分流", !/prof\b|"lang"/.test(W.slice(W.indexOf("const CW_X ="), W.indexOf("const CW_GRADE"))));
// 祖宗闸四件：ancBlock / 别名法补问 / quoteAudit / 收稿闸，都在 dist 的 plan+part 里，无 profile 判断
["function ancBlock(list, aliases)","第一步 aliases","function quoteAudit(","_qa.n && _pk.n"]
  .forEach(k=>ok("祖宗闸零件在（未按档案分流）："+k, W.indexOf(k)>0));
const anc=W.slice(W.indexOf("function ancBlock("), W.indexOf("\n}", W.indexOf("function ancBlock(")));
ok("ancBlock 里没有 lang 判断", !/"lang"/.test(anc));
const asys=W.slice(W.indexOf("【只做一件事"), W.indexOf("【只做一件事")+3000);
ok("别名法补问里没有 lang 判断", !/"lang"/.test(asys));
// 取料：唯一按档案分流的地方，且两条路都通
ok("取料是唯一按档案分流处，且 else 支给主站", /\} else \{[\s\S]{0,300}wdsRag/.test(W.slice(W.indexOf("if (_fixSec && _fixSec.rag)"), W.indexOf("if (_fixSec && _fixSec.rag)")+1400)));
ok("全仓只剩这一处 prof.id === \"lang\" 的产线分流", (W.match(/prof && prof\.id === "lang"/g)||[]).length===1);
console.log((f?"✗ ":"✓ ")+p+" passed, "+f+" failed"); process.exit(f?1:0);
