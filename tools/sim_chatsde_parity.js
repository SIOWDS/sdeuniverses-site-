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
 * 【二】限流器降级（2026-08-22 补）：全站十九处限流调用点必须统一过 limitRead()。
 *   病灶是站内挂了最久的一条硬伤——`_do()` 绑定缺失时回 {ok:false,error:"binding_missing"}
 *   并自陈「按降级处理」，而调用点只看 !lr.ok 就拒 ⇒ 一次绑定没跟上的部署
 *   ＝ **全站对话入口集体假报「太快啦」**。最坏的一种错：它长得像正常工作。
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

// ══ 二、限流器降级：绑定不见了要放行，不要假报「太快啦」 ══
ok("装了 limitRead 这个解释器", W.indexOf("function limitRead(j)")>0);
/* 要害是**一处不漏**：漏掉的那一处在绑定缺失的那天照样把人挡在门外，
   而它挡的还偏偏是最常走的那条路——没人会想到去查限流器。 */
const RAW=(W.match(/(?<!limitRead\()await \(await lim\.fetch\(/g)||[]).length;
const WRAPPED=(W.match(/limitRead\(await \(await lim\.fetch\(/g)||[]).length;
ok("十九处限流调用点全部过了解释器（未包装处 "+RAW+"）", RAW===0 && WRAPPED===19);
const LR=(()=>{const a=W.indexOf("function limitRead(");return new Function(W.slice(a,W.indexOf("\n}",a)+2)+"; return limitRead;")();})();
ok("绑定缺失→放行并标 degraded", (()=>{const r=LR({ok:false,error:"binding_missing"});return r.ok===true&&r.degraded===true;})());
ok("真限流（按分钟）照旧拦", LR({ok:false,reason:"min"}).ok===false);
ok("真限流（按天）照旧拦，且 inDay 不丢", (()=>{const r=LR({ok:false,reason:"day",inDay:7});return r.ok===false&&r.inDay===7;})());
ok("正常放行原样透传", LR({ok:true,inDay:3}).inDay===3);
ok("读不出 JSON 时也放行（限流是保护，不是正确性）", LR(null).ok===true);
/* ⚠ 这个解释器只许给限流器用：别的 DO 上 fail open ＝ 把没存上的东西报成存上了。 */
ok("limitRead 只出现在限流那一条路上", (W.match(/limitRead\(/g)||[]).length===WRAPPED+1);
ok("注释里写明了别的 DO 不许套", /别的 DO（记忆、索引、配置）绝不许套这个/.test(W));

console.log((f?"✗ ":"✓ ")+p+" passed, "+f+" failed"); process.exit(f?1:0);
