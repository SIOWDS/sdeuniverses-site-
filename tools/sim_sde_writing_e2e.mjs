/* sim_sde_writing_e2e.mjs —— 「SDE 作文共创」的端到端干跑
 *
 * 静态断言只能证明"写了"，证明不了"跑得通"。这一份把**整页真装进假浏览器**，
 * 喂脚本化的 SSE，把一条真实路径走完：
 *   说一句话 → 共创问 → 它判出路径（回执）→ 写 → WDS 修改 → WDS 编辑
 *   → 版本链 / 比对 / 导出，外加几条只有跑起来才暴露的失败路径。
 *
 * 用法：npm i jsdom && node tools/sim_sde_writing_e2e.mjs
 */
import fs from "fs";
import path from "path";
import { JSDOM } from "jsdom";

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), "..");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");
const read = p => fs.readFileSync(path.join(ROOT, p), "utf8");

const HTML = read("public/taste/sde-writing/index.html");
const RTE = read("public/assets/wds-rte.js");
const DIFF = read("public/assets/wds-diff.js");

/* SSE 编成一次 fetch 的返回。默认一条普通回话。 */
function sse(lines) {
  return lines.map(l => "data: " + (typeof l === "string" ? l : JSON.stringify(l))).join("\n") + "\n";
}
const tok = t => ({ t: "token", v: t });

async function mount(opts = {}) {
  opts.queue = opts.queue || [];
  const posts = [];
  const store = {};
  const errs = [];
  const dom = new JSDOM(HTML, {
    runScripts: "dangerously",
    url: "https://sdeuniverses.com/taste/sde-writing/",
    beforeParse(w) {
      /* ⚠ jsdom 不取 <script src>，页面引的三个模块不会自己进来。
         不注进去的话，富文本与 diff 全走降级分支，测出来的是另一台机器。 */
      w.eval(RTE); w.eval(DIFF);
      w.SDEVault = opts.noVault ? undefined : {
        cred: () => (opts.cred === false ? "" : "fake-cred"),
        kb: (o, box) => { posts.push({ kb: o }); if (box) box.innerHTML = "已存进知识库。"; return Promise.resolve({ ok: true }); }
      };
      /* 默认喂一把 Key —— **键名照 wds-mode.js 的 VENDORS[].ks**，不许自己拼
         （第一版就是拼错了，页面对配好 Key 的读者一律说"还没配"）。
         要测"没配 Key"的用例传 noKey: true。 */
      if (!opts.noKey) { store["sde_wds_vendor"] = "ds"; store["sde_ds_key"] = "sk-testtesttesttest"; }
      Object.keys(opts.ls || {}).forEach(k => { store[k] = opts.ls[k]; });
      Object.defineProperty(w, "localStorage", {
        value: {
          getItem: k => (k in store ? store[k] : null),
          setItem: (k, v) => { store[k] = String(v); },
          removeItem: k => { delete store[k]; }
        }, configurable: true
      });
      w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
      w.fetch = (u, init) => {
        const body = JSON.parse(init.body);
        posts.push({ u, body });
        const next = opts.queue.length ? opts.queue.shift() : [tok("好的。")];
        if (next === "reject") return Promise.reject(new Error("net down"));
        const text = sse(next.concat(next.__noDone ? [] : ["[DONE]"]));
        const bytes = new TextEncoder().encode(text);
        let served = false;
        return Promise.resolve({
          ok: true, status: 200,
          body: { getReader: () => ({ read: () => served ? Promise.resolve({ done: true })
            : (served = true, Promise.resolve({ done: false, value: bytes })) }) }
        });
      };
      w.onerror = e => errs.push(String(e));
      w.alert = () => {};
      w.confirm = () => true;
      w.prompt = () => "";
    }
  });
  await new Promise(r => setTimeout(r, 80));
  const w = dom.window, d = w.document;
  return {
    w, d, posts, store, errs,
    $: id => d.getElementById(id),
    wait: (ms = 80) => new Promise(r => setTimeout(r, ms)),
    lastPost: () => posts.filter(p => p.body).pop()
  };
}

/* ══ ① 装得起来吗 ═══════════════════════════════ */
sec("① 真装载");
{
  const A = await mount();
  ok(A.errs.length === 0, "装载期异常：" + A.errs.join(";"));
  ok(!!A.$("seed") && !!A.$("seedgo"), "首屏没有开场入口");
  ok(A.$("start").style.display !== "none", "一进来就把开场框藏了");
  ok(A.$("fruit").style.display === "none", "还没定路径就亮出了「这一篇的活儿」");
  ok(A.d.querySelectorAll(".ags button").length === 3, "不是三台智能体");
  ok(A.d.querySelectorAll(".rtb button").length >= 12, "排版工具条按钮太少");
  ok(A.d.querySelectorAll(".quick button").length >= 4, "没有快捷问");
  /* 弹层里才有路径选单，首屏没有 */
  ok(A.d.querySelectorAll("#sbd .pchip").length === 6, "弹层里不是六条路径");
  ok(A.$("mask").className.indexOf("on") === -1, "弹层一进来就是开的");
}

/* ══ ② 从一句话开始：共创引导并判出路径 ═════════ */
sec("② 说一句话 → 共创问 → 判出路径");
{
  const A = await mount({ queue: [
    [tok("先问你两句：这件事发生在哪一年？你希望读的人读完之后，心里有什么变化？")],
    [tok("那这一篇的活儿是让人看见。第一段就从你说的那个画面写起：\n\n"), tok("〔SDE路径：EDS〕")]
  ] });
  A.$("seed").value = "我想写写我爸退休以后的样子";
  A.$("seedgo").click();
  await A.wait(120);

  const p1 = A.lastPost();
  ok(!!p1, "开场没有发出请求");
  ok(p1.body.q.indexOf("我想写的是：我想写写我爸退休以后的样子") > -1, "没把那句话送进去");
  ok(p1.body.q.indexOf("也不懂那些方法") > -1, "没告诉它这人不懂理论");
  ok(p1.body.q.indexOf("与 WDS 共创") > -1, "没走共创那台的 system");
  ok(p1.body.q.indexOf("绝不对他讲 S/D/E") > -1, "共创的规矩没带过去");
  ok(A.$("start").style.display === "none", "开场之后没把输入框收起来");

  /* 第一轮只是问，不该判路径 */
  ok(A.$("fruit").style.display === "none", "第一轮就把路径定了（它还没判）");
  const store1 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(!store1.path, "第一轮就落了路径");

  /* 第二轮带回执 */
  A.$("in").value = "1998 年，我希望他们读完觉得亏欠。";
  A.$("go").click();
  await A.wait(140);
  const st2 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(st2.path === "EDS", "回执没被采纳，路径仍是 " + JSON.stringify(st2.path));
  ok(A.$("fruit").style.display !== "none", "定了路径却没亮出「这一篇的活儿」");
  // EDS＝牵动→行动→见证，**落点是 S（让人看见）**，不是 E —— 第一版我把它记反了
  ok(A.$("fruit").textContent.indexOf("让人看见") > -1, "亮出来的落点不对：" + A.$("fruit").textContent);

  /* 回执那一行**绝不许露在脸上** */
  const ms = A.$("ms").textContent;
  ok(ms.indexOf("SDE路径") === -1, "回执露在了对话里（读者会当成乱码）：" + ms.slice(-60));
  ok(ms.indexOf("第一段就从你说的那个画面写起") > -1, "回话正文被抹掉了");
}

/* ══ ③ 写：编辑器与版本链 ═══════════════════════ */
sec("③ 写 → 修改 → 编辑：版本链与归属");
{
  const A = await mount({ queue: [
    [tok("# 我爸的下午\n\n改好的整篇正文。他坐在阳台上，剪指甲，一片一片，剪得很慢。窗外的树在动，他没有抬头。")],
    [tok("# 我爸的下午\n\n编校后的整篇正文。他坐在阳台上剪指甲，一片一片，剪得很慢；窗外的树在动，他没有抬头。")]
  ] });
  /* 直接在富文本里写 */
  A.$("ed").innerHTML = "<h1>我爸的下午</h1><p>他坐在阳台上。</p>";
  A.$("ed").dispatchEvent(new A.w.Event("input"));
  await A.wait(40);
  ok(A.$("wc").textContent.indexOf("字") > -1, "字数没更新");
  const st0 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(String(st0.vers[st0.vi]).indexOf("# 我爸的下午") > -1,
    "富文本没序列化回 markdown：" + JSON.stringify(st0.vers[st0.vi]));

  /* 切到 WDS 修改 */
  /* ⚠ .ags 每次 paintAgs 都整块重绘，旧引用是**脱离文档的节点**，点了没反应。
     每次都现查（这也是页面把委托挂在容器上的原因）。 */
  const agBtn = (kw) => [...A.d.querySelectorAll(".ags button")].find(b => b.textContent.indexOf(kw) > -1);
  agBtn("修改").click();
  await A.wait(30);
  ok(A.$("agdesc").textContent.indexOf("内容") > -1, "切台之后说明没跟上");
  A.$("in").value = "按落点改一遍";
  A.$("go").click();
  await A.wait(140);
  const p = A.lastPost();
  ok(p.body.q.indexOf("你是【WDS 修改】") > -1, "没走修改那台的 system");
  ok(p.body.q.indexOf("只输出改好的整篇") > -1, "修改的硬规矩没带过去");
  ok(p.body.q.indexOf("他坐在阳台上") > -1, "没把当前正文带过去");
  const st1 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(st1.vers.length === 2, "修改交回整篇却没落成新版本：" + st1.vers.length);
  ok(String(st1.vers[1]).indexOf("剪指甲") > -1, "落的版本不是它交回的那一篇");
  ok(st1.vi === 1, "没切到新版");
  ok(A.$("verTag").textContent === "2/2", "版本号不对：" + A.$("verTag").textContent);

  /* 切到 WDS 编辑 */
  agBtn("编辑").click();
  await A.wait(30);
  A.$("in").value = "通篇编校";
  A.$("go").click();
  await A.wait(140);
  const p2 = A.lastPost();
  ok(p2.body.q.indexOf("你是【WDS 编辑】") > -1, "没走编辑那台的 system");
  ok(p2.body.q.indexOf("一个判断都不许改") > -1, "编辑的硬规矩没带过去");
  const st2 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(st2.vers.length === 3, "编辑没落成第三版：" + st2.vers.length);

  /* 退回去看得见 */
  A.$("verPrev").click(); await A.wait(30);
  ok(A.$("verTag").textContent === "2/3", "退不回去：" + A.$("verTag").textContent);
  ok(A.$("ed").innerHTML.indexOf("剪指甲") > -1, "退回去看到的不是那一版");
  /* 比对 */
  A.$("verDiff").click(); await A.wait(30);
  ok(A.$("ed").innerHTML.indexOf("wdsd") > -1, "比对没渲染出来");
  A.$("verDiff").click(); await A.wait(30);

  /* 三台各自的对话是分开的 */
  const st3 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok((st3.chat.rev || []).length === 2 && (st3.chat.ed || []).length === 2 && (st3.chat.co || []).length === 0,
    "三台的对话没有分开记：" + JSON.stringify(Object.keys(st3.chat).map(k => k + ":" + st3.chat[k].length)));
}

/* ══ ④ 共创绝不自动落版；修改/编辑的正文不许被当回执 ═ */
sec("④ 分工：谁会落版、谁不会");
{
  const A = await mount({ queue: [[tok("我建议你把第一段挪到后面去。这一段可以这样写：他坐在阳台上，剪指甲。")]] });
  A.$("ed").innerHTML = "<p>原文一句。</p>";
  A.$("ed").dispatchEvent(new A.w.Event("input"));
  A.$("in").value = "接下去怎么写";
  A.$("go").click();
  await A.wait(140);
  const st = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(st.vers.length === 1, "共创的回话竟然落成了新版本 —— 那会让人不敢开口问");
  /* 按一下才插入 */
  const ins = [...A.d.querySelectorAll('.row .acts button')].find(b => b.textContent.indexOf("插入正文") > -1);
  ok(!!ins, "回话下面没有「插入正文」");
  ins.click(); await A.wait(40);
  const st2 = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(String(st2.vers[st2.vi]).indexOf("剪指甲") > -1, "插不进去");
  ok(String(st2.vers[st2.vi]).indexOf("原文一句") > -1, "插入把原文冲掉了");
  ok(st2.vers.length === 1, "插入不该直接落成版本");

  /* 修改/编辑的整篇正文里若出现回执字样，**不许**被当成指令 */
  const B = await mount({ queue: [[tok("# 稿\n\n正文里提到了〔SDE路径：SDE〕这几个字，那只是引用。")]] });
  [...B.d.querySelectorAll(".ags button")].find(b => b.textContent.indexOf("修改") > -1).click();
  B.$("in").value = "改一遍"; B.$("go").click();
  await B.wait(140);
  const sb = JSON.parse(B.store["sde_writing_v1"] || "{}");
  ok(!sb.path, "修改交回的正文被当成了回执，把路径设歪了：" + sb.path);
  ok(String(sb.vers[sb.vi]).indexOf("SDE路径") > -1, "正文里那几个字被当回执抹掉了");
}

/* ══ ④b 太短的回话不落版，但要说一声 ═══════════ */
sec("④b 修改说「改不动」时不许静默");
{
  const A = await mount({ queue: [[tok("改不动。")]] });
  A.$("ed").innerHTML = "<p>原文一句。</p>";
  A.$("ed").dispatchEvent(new A.w.Event("input"));
  [...A.d.querySelectorAll(".ags button")].find(b => b.textContent.indexOf("修改") > -1).click();
  A.$("in").value = "改一遍"; A.$("go").click();
  await A.wait(140);
  const st = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(st.vers.length === 1, "「改不动」也被落成了一版");
  ok(A.$("note").textContent.indexOf("没有落成新版本") > -1,
    "没落版却一声不吭 —— 读者只会以为功能坏了：" + A.$("note").textContent);
}

/* ══ ⑤ 失败路径 ════════════════════════════════ */
sec("⑤ 失败路径：空流自动重问、乱写的回执、没配 Key");
{
  /* 空流 → 自动重问一次；两次都空才落到那句话 */
  const A = await mount({ queue: [[{ t: "beat", v: { sec: 1 } }], [{ t: "beat", v: { sec: 1 } }]] });
  A.$("ed").innerHTML = "<p>写了一些。</p>";
  A.$("ed").dispatchEvent(new A.w.Event("input"));
  A.$("in").value = "接下去怎么写"; A.$("go").click();
  await A.wait(900);
  const asks = A.posts.filter(p => p.body).length;
  ok(asks === 2, "空正文没有自动重问一次（实发 " + asks + " 次）");
  const txt = A.$("ms").textContent;
  ok(txt.indexOf("两次都没吐出字") > -1, "两次都空却没说清：" + txt.slice(-80));
  ok(/HTTP 200/.test(txt) && /块/.test(txt) && /(done|DONE)/.test(txt), "回执三读数不全：" + txt.slice(-120));

  /* 乱写的路径 id 一律不认 */
  const B = await mount({ queue: [[tok("定了。〔SDE路径：XYZ〕")]] });
  B.$("in").value = "判一下"; B.$("go").click();
  await B.wait(140);
  const sb = JSON.parse(B.store["sde_writing_v1"] || "{}");
  ok(!sb.path, "基底瞎写的路径 id 竟被采纳：" + sb.path);
  ok(B.$("ms").textContent.indexOf("SDE路径") === -1, "不合法的回执也该从显示里抹掉");

  /* 没配 Key：如实说，不发请求 */
  const C = await mount({ noKey: true });
  C.$("in").value = "问一句"; C.$("go").click();
  await C.wait(80);
  ok(C.posts.filter(p => p.body).length === 0, "没配 Key 还发了请求");
  ok(C.$("note").textContent.indexOf("Key") > -1, "没配 Key 却不吭声");

  /* 网络挂了：回执带异常 */
  const D = await mount({ queue: ["reject"] });
  D.$("in").value = "问一句"; D.$("go").click();
  await D.wait(140);
  ok(D.$("ms").textContent.indexOf("诊断回执") > -1, "网络挂了没有回执");
  ok(D.$("ms").textContent.indexOf("net down") > -1, "回执没带上异常本身");
}

/* ══ ⑥ 出口与留存 ══════════════════════════════ */
sec("⑥ 出口与留存");
{
  const A = await mount();
  A.$("ed").innerHTML = "<h1>我爸的下午</h1><p>正文。</p>";
  A.$("ed").dispatchEvent(new A.w.Event("input"));
  await A.wait(40);
  A.$("oKb").click(); await A.wait(40);
  const kb = A.posts.filter(p => p.kb).pop();
  ok(!!kb, "存进知识库没被调起来");
  ok(kb.kb.title === "我爸的下午", "标题没取正文的一级标题：" + (kb && kb.kb.title));
  ok(String(kb.kb.text).indexOf("# 我爸的下午") > -1, "存进去的不是 markdown");

  /* 刷新之后接着写，且不再被问一遍「你想说什么」 */
  const saved = A.store["sde_writing_v1"];
  const B = await mount({ ls: { sde_writing_v1: saved } });
  ok(B.$("ed").innerHTML.indexOf("我爸的下午") > -1, "刷新之后稿子没回来");
  ok(B.$("start").style.display === "none", "回头再进又被问了一遍「你想说什么」");
}

/* ══ ⑦ 何谓作文：弹层与手动换路径 ═══════════════ */
sec("⑦ 弹层与手动换路径");
{
  const A = await mount();
  A.$("whatb").click(); await A.wait(30);
  ok(A.$("mask").className.indexOf("on") > -1, "弹层开不了");
  const sbd = A.$("sbd").textContent;
  ok(sbd.indexOf("用文本（文）来建造（作）一个具体的 SDE") > -1, "弹层里没有那句总纲");
  ok(sbd.indexOf("中项") > -1 && sbd.indexOf("落点") > -1, "弹层里三分说明不全");
  ok(A.d.querySelectorAll("#sbd table").length >= 2, "弹层里少了表（六路径／三台）");

  /* 在弹层里手动换一条 */
  const chip = [...A.d.querySelectorAll("#sbd .pchip")].find(b => b.textContent.indexOf("征象") > -1);   // 「处境」两条都有，用唯一的词
  ok(!!chip, "弹层里找不到那一条");
  chip.click(); await A.wait(40);
  const st = JSON.parse(A.store["sde_writing_v1"] || "{}");
  ok(st.path === "ESD", "手动换路径没生效：" + st.path);
  ok(A.$("fruit").textContent.indexOf("让人会做") > -1, "换完落点没跟着变：" + A.$("fruit").textContent);

  /* 关得掉 */
  A.$("mx").click(); await A.wait(20);
  ok(A.$("mask").className.indexOf("on") === -1, "关不掉弹层");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
