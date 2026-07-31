/* sim_sde_art_e2e.js —— SDE 艺术绘画智能体·端到端干跑
 *
 * 与 sim_sde_art.js 的分工：那个查**源码契约**（谁在场、纪律写没写），
 * 这个把整条产线**真跑一遍**——真 DOM(jsdom)、打桩基底(可编程剧本)、打桩 fetch，
 * 并捕获每一次 payload 反查「客户端 → 上游」的字段契约。
 *
 * 桩数据证明不了画好不好看，但能证明：
 *   调用序列对不对、图有没有真传给看图那一步、单路挂了另两路还跑不跑、
 *   全挂了会不会污染交付、评分卡解析崩了会不会打崩流程、三档差异有没有真生效。
 *
 * 跑法：node tools/sim_sde_art_e2e.js
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const PAGE = path.join(__dirname, "..", "public", "taste", "sde-art", "index.html");
const html = fs.readFileSync(PAGE, "utf8");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra ? "  → " + extra : "")); }
}
function group(n) { console.log("\n【" + n + "】"); }

/* ═══════════ 打桩：一段像样的基底产出 ═══════════ */
const TINY_JPG_B64 =
  "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a" +
  "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAA" +
  "AAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==";

function triReply(n) {
  const one = (i, dir) =>
    "观点" + "一二三"[i - 1] + "：\n" +
    "D：把「" + dir + "」和它的反面分开\n" +
    "E：材质是粗麻，光是侧逆光，观看惯例是展墙平视\n" +
    "S：一道横贯画面的接缝，两侧密度相反\n" +
    "压缩：一道把两种密度分开的接缝，缝本身不发光\n" +
    "最易被推翻处：如果两侧密度差看不出来，这一刀就没落下。";
  return [1, 2, 3].slice(0, n).map((i) => one(i, ["沉降", "上浮", "悬停"][i - 1])).join("\n\n");
}
const GATE_REPLY =
  "条1｜判定：〔通过〕\n条1｜撞上：无\n条1｜分离线：地层剖面在【层界是水平堆叠】上是 A，本条是非 A（缝是竖的且两侧同质），读法是看缝的走向。\n" +
  "条2｜判定：〔占位失败〕\n条2｜撞上：群鸟成形\n条2｜分离线：—\n" +
  "条3｜判定：〔库未命中·不放行〕\n条3｜撞上：无\n条3｜分离线：—";
function paraReply(tag) {
  return "一、典范名：缝不是边界，是两种密度的交班处（" + tag + "）\n" +
    "二、承重命题：这幅画要显露的不是分隔也不是过渡，而是交班\n" +
    "三、它切开的辨别面：把「两侧不同」和「两侧正在互相交出」分开\n" +
    "四、沉淀层：\n材质：粗麻与打磨石\n光源：低角度侧逆光\n观看距离：一臂\n" +
    "五、可见形状：一道贯穿画面的接缝，左侧纤维松散、右侧致密\n" +
    "六、分离线：与地层剖面的分别在于层界走向；与拼图缺块的分别在于本画没有缺口\n" +
    "七、绘图指令：a taut horizontal seam across the frame, loose coarse fibre on the left meeting dense polished stone on the right, " +
    "low raking side-backlight grazing the junction, matte surface, viewed at arm's length, seam sitting slightly below centre, " +
    "weight gathered low, generous empty field above, muted earth palette, " +
    "no text, no letters, no numbers, no watermark, no recognizable real person, no logo, no brand, not in the style of any named artist";
}
const B9_REPLY = [
  "统一｜82｜同一材质逻辑贯穿", "多样｜71｜三张构图有别", "和谐｜78｜重量偏低但稳",
  "完全｜66｜那一刀读得出但不够狠", "活力｜58｜偏静", "纯一｜85｜只讲一件事",
  "爱｜74｜有可辨认的具体物", "自由｜80｜上方留白足", "平安｜88｜不推搡"
].join("\n");
const GATEOUT_REPLY =
  "图1｜判定：〔通过〕\n图1｜撞上：无\n图1｜分离线：与地层剖面在层界走向上分开。\n" +
  "图2｜判定：〔占位失败〕\n图2｜撞上：蒙德里安红黄蓝方格\n图2｜分离线：—\n最干净的是第 1 张。";
const SYNTH_REPLY = "一、这幅画要显露的那一刀\n……\n二、它是怎么撞出来的\n……\n三、落选典范的可回收零件\n……\n" +
  "四、分离线\n……\n五、评分卡开出的作业\n……\n六、明确不画什么\n……";

/* ═══════════ 干跑环境 ═══════════ */
async function boot(script) {
  const calls = [];                     // 捕获每一次 fetch 的 payload
  const dom = new JSDOM(html, {
    runScripts: "dangerously",
    url: "https://sdeuniverses.com/taste/sde-art/",
    beforeParse(w) {
      w.localStorage.clear();
      w.fetch = async function (url, opt) {
        opt = opt || {};
        const target = (opt.headers && opt.headers["x-target-url"]) || String(url);
        let body = null;
        try { body = opt.body ? JSON.parse(opt.body) : null; } catch (e) { body = "(unparsable)"; }
        const rec = { url: String(url), target, body, auth: (opt.headers || {})["authorization"] || "" };
        calls.push(rec);
        const r = await script(rec, calls.length);
        return {
          ok: r.ok !== false, status: r.status || 200,
          text: async () => r.text != null ? r.text : JSON.stringify(r.json || {}),
          json: async () => r.json || {},
        };
      };
    },
  });
  const w = dom.window;
  // 静态资源（内功/总原则）也走同一个桩，所以 script 里要认这两条
  await new Promise((res) => { if (w.document.readyState === "complete") res(); else w.addEventListener("load", res); });
  return { w, calls, dom };
}
function chatOK(text) { return { json: { choices: [{ message: { content: text } }] } }; }
function imgOK(n) { return { json: { data: { image_base64: Array(n).fill(TINY_JPG_B64) } } }; }

/* 一份「一切正常」的剧本 */
function happyScript(opts) {
  opts = opts || {};
  let collideSeen = 0, drawSeen = 0, auditSeen = 0;
  return async function (rec) {
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "（内功正文桩）".repeat(200) };
    if (/\/api\/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [{ n: 1, text: "桩原则" }] } };
    if (/image_generation$/.test(rec.target)) {
      drawSeen++;
      if (opts.drawFailAt === drawSeen) return { ok: false, status: 500, text: "boom" };
      return imgOK((rec.body && rec.body.n) || 1);
    }
    const u = rec.body && rec.body.messages && rec.body.messages[1];
    const uText = typeof u.content === "string" ? u.content : (u.content[0] && u.content[0].text) || "";
    const sys = (rec.body.messages[0] && rec.body.messages[0].content) || "";
    if (/彼此不相容\*{0,2}的视觉进路|三条\*{0,2}彼此不相容/.test(uText) || /观点一：/.test(uText) === false && /要你做的/.test(uText))
      return chatOK(triReply(opts.triCount == null ? 3 : opts.triCount));
    if (/图像占位核查员/.test(sys) && !/看着\*{0,2}成品图/.test(sys)) return chatOK(GATE_REPLY);
    if (/图像占位核查员/.test(sys)) return chatOK(GATEOUT_REPLY);
    if (/画面审看者/.test(sys)) {
      auditSeen++;
      if (opts.auditGarbageAt === auditSeen) return chatOK("完全乱写，没有任何格名与分数");
      return chatOK(B9_REPLY);
    }
    if (/本轮碰撞方式/.test(uText)) {
      collideSeen++;
      if (opts.collideFailAt === collideSeen) return { ok: false, status: 500, text: "upstream down" };
      if (opts.collideNoPromptAt === collideSeen) return chatOK("一、典范名：残缺\n二、承重命题：无\n（没有第七节）");
      if (opts.collideAllFail) return { ok: false, status: 500, text: "upstream down" };
      return chatOK(paraReply("路" + collideSeen));
    }
    if (/要你写/.test(uText)) return chatOK(SYNTH_REPLY);
    return chatOK("（未识别的调用）");
  };
}
async function drive(w, mode, opts) {
  w.document.getElementById("mmKey").value = "sk-stub";
  w.document.getElementById("topic").value =
    "制度不是被设计出来的，而是在反复的失败里沉淀成形的——每一条规则背后都躺着一次没人再想经历的事故。";
  w.__sdeArt.setMode(mode);
  w.__sdeArt.resetWays();
  await w.__sdeArt.run(false);
}

(async function main() {

  /* ═════ 一、B 档全套顺跑：调用序列与字段契约 ═════ */
  group("一、B 档全套顺跑（3 路）");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    const api = calls.filter((c) => /minimaxi?\.(com|io)/.test(c.target));
    const chats = api.filter((c) => /chat\/completions$/.test(c.target));
    const draws = api.filter((c) => /image_generation$/.test(c.target));

    ok("内功与 100 条总原则各取一次", calls.filter((c) => /sde-neigong/.test(c.url)).length === 1
      && calls.filter((c) => /kb\/principles/.test(c.url)).length === 1);
    ok("基底调用 10 次（三观点1＋进闸1＋碰撞3＋看图3＋出闸1＋提炼1）", chats.length === 10, "实测 " + chats.length);
    ok("出图 3 次（每路一次）", draws.length === 3, "实测 " + draws.length);
    ok("全部走 /api/llm-proxy，无浏览器直连", api.every((c) => /\/api\/llm-proxy$/.test(c.url)));
    ok("每一次都带 Bearer，且 Key 不出现在 body 里",
      api.every((c) => /^Bearer sk-stub$/.test(c.auth) && JSON.stringify(c.body).indexOf("sk-stub") < 0));
    ok("聊天一律用 MiniMax-M3（M2.x 看不了图）", chats.every((c) => c.body.model === "MiniMax-M3"));
    ok("出图一律用 image-01", draws.every((c) => c.body.model === "image-01"));
    ok("出图关掉 prompt_optimizer", draws.every((c) => c.body.prompt_optimizer === false));
    ok("出图取 base64（URL 24 小时会失效）", draws.every((c) => c.body.response_format === "base64"));
    ok("送出的 prompt 每条都 ≤1500 字符", draws.every((c) => c.body.prompt.length <= 1500));
    ok("送出的 prompt 都带满英文禁令串",
      draws.every((c) => /no text, no letters, no numbers, no watermark, no recognizable real person, no logo, no brand, not in the style of any named artist/.test(c.body.prompt)));

    // ★ 最要紧的一条：看图那两步必须真把图传上去
    const vis = chats.filter((c) => Array.isArray(c.body.messages[1].content));
    ok("看图调用共 4 次（三路评分 ＋ 一次出闸门）", vis.length === 4, "实测 " + vis.length);
    ok("看图调用真的带了 image_url 块，不是只传文字",
      vis.every((c) => c.body.messages[1].content.some((b) => b.type === "image_url" && /^data:image\//.test(b.image_url.url))));
    ok("图排在文字之后（先说看什么再给看）",
      vis.every((c) => c.body.messages[1].content[0].type === "text"));
    ok("出闸门是拿成品图去查，不是拿 prompt 去查",
      vis[vis.length - 1].body.messages[0].content.indexOf("看着**成品图**") >= 0
      || /看着\*\*成品图\*\*|看着成品图/.test(vis[vis.length - 1].body.messages[0].content));

    // 装内功 / 不装内功的分工
    const withCore = chats.filter((c) => /SDE 内功·完整先验/.test(c.body.messages[0].content));
    const noCore = chats.filter((c) => !/SDE 内功·完整先验/.test(c.body.messages[0].content));
    ok("装内功的是：三观点＋三路碰撞＋综合提炼＝5 次", withCore.length === 5, "实测 " + withCore.length);
    ok("不装内功的是：进闸门＋三次看图＋出闸门＝5 次（防评分通胀）", noCore.length === 5, "实测 " + noCore.length);
    ok("装内功的每一次也都装了 100 条总原则", withCore.every((c) => /长期总原则 100 条/.test(c.body.messages[0].content)));
    ok("装内功的每一次都带术语纪律", withCore.every((c) => /S＝显露\(Show\)/.test(c.body.messages[0].content)));
    ok("三观点提示里明令写完就停、不许调和", /写完就停/.test(chats[0].body.messages[1].content));

    // 碰撞方式无放回
    const wayNos = chats.filter((c) => /本轮碰撞方式/.test(String(c.body.messages[1].content)))
      .map((c) => (String(c.body.messages[1].content).match(/本轮碰撞方式 (\d)/) || [])[1]);
    ok("三路用的是三种不同碰撞方式（无放回）", new Set(wayNos).size === 3, wayNos.join(","));

    ok("产线跑完有产出", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("胜出者带着分数", w.__sdeArt.last().winner.score != null);
    ok("综合提炼落到页面上", /评分卡开出的作业/.test(w.document.getElementById("synthOut").textContent));
    ok("草稿已落 localStorage（第 0 层保底）", !!w.localStorage.getItem("sde_art_draft"));
    ok("九个格子都渲染出来了", w.document.querySelectorAll("#drawOut .b9 .g").length === 27, // 3 路 × 9 格
      "实测 " + w.document.querySelectorAll("#drawOut .b9 .g").length);
    ok("三路共 9 张图渲染出来", w.document.querySelectorAll("#drawOut .shot img").length === 9,
      "实测 " + w.document.querySelectorAll("#drawOut .shot img").length);
  }

  /* ═════ 二、三档差异真生效 ═════ */
  group("二、三档差异");
  for (const [m, wantChats, wantDraws] of [["A", 6, 1], ["C", 6, 1], ["B", 10, 3]]) {
    const { w, calls } = await boot(happyScript());
    await drive(w, m, {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    const draws = calls.filter((c) => /image_generation$/.test(c.target));
    ok(m + " 档＝" + wantChats + " 次基底 ＋ " + wantDraws + " 次出图",
      chats.length === wantChats && draws.length === wantDraws,
      "实测 " + chats.length + "/" + draws.length);
    const b9sys = chats.filter((c) => /画面审看者/.test(c.body.messages[0].content))[0];
    const acc = { A: ["连接", "完全"], B: ["影响", "活力"], C: ["连接", "共存"] }[m];
    ok(m + " 档把侧重格「" + acc.join("／") + "」点名写进看图提示",
      b9sys && acc.every((n) => b9sys.body.messages[0].content.indexOf("「" + n + "」") >= 0));
    ok(m + " 档明写侧重格打分加倍、其余七格救不回来",
      b9sys && /加倍/.test(b9sys.body.messages[0].content) && /救不回来/.test(b9sys.body.messages[0].content));
  }

  /* ═════ 三、故障路径 ═════ */
  group("三、故障路径（本组是干跑的真正价值）");
  {
    // ① 单路碰撞失败
    const { w, calls } = await boot(happyScript({ collideFailAt: 2 }));
    await drive(w, "B", {});
    const draws = calls.filter((c) => /image_generation$/.test(c.target));
    ok("单路碰撞失败 → 另外两路照跑（出图 2 次不是 0 次）", draws.length === 2, "实测 " + draws.length);
    ok("单路失败仍能走到综合提炼", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("失败那一路在页面上明说作废，不静默吞掉", /碰撞失败，本路作废/.test(w.document.getElementById("drawOut").innerHTML));
    ok("失败步骤标红（不是标成完成）", w.document.querySelectorAll("#steps .step.fail").length >= 1);
  }
  {
    // ② 三路全挂
    const { w, calls } = await boot(happyScript({ collideAllFail: true }));
    await drive(w, "B", {});
    ok("三路全挂 → 一张图都不出（不污染交付）",
      calls.filter((c) => /image_generation$/.test(c.target)).length === 0);
    ok("三路全挂 → 不写综合提炼", !w.document.getElementById("synthOut").textContent);
    ok("三路全挂 → 显式报错给读者", /全挂了/.test(w.document.getElementById("err").textContent));
  }
  {
    // ③ 碰撞回来了但第七节缺失（解析器：宽容但绝不猜）
    const { w, calls } = await boot(happyScript({ collideNoPromptAt: 1 }));
    await drive(w, "B", {});
    ok("缺绘图指令的那一路被判失败，不拿半截 prompt 去出图",
      calls.filter((c) => /image_generation$/.test(c.target)).length === 2);
    ok("另外两路不受影响、仍出提炼", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
  }
  {
    // ④ 出图挂了
    const { w, calls } = await boot(happyScript({ drawFailAt: 1 }));
    await drive(w, "B", {});
    const vis = calls.filter((c) => /chat\/completions$/.test(c.target) && Array.isArray(c.body.messages[1].content));
    ok("某路出图失败 → 该路跳过看图评分（看图 2 次 ＋ 出闸门 1 次）", vis.length === 3, "实测 " + vis.length);
    ok("出图失败不打断整条产线", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
  }
  {
    // ⑤ 评分卡解析不出来
    const { w } = await boot(happyScript({ auditGarbageAt: 1 }));
    await drive(w, "B", {});
    const ps = w.__sdeArt.last().paras.filter(Boolean);
    ok("评分卡解析失败记 null，不打崩流程", ps.some((p) => p.score === null) && ps.some((p) => p.score != null));
    ok("胜出的是真评上分的那个，不是记 null 的",
      w.__sdeArt.last().winner.score != null);
  }
  {
    // ⑥ 基底只给两条观点
    const { w } = await boot(happyScript({ triCount: 2 }));
    await drive(w, "B", {});
    ok("只给两条观点 → 仍继续（≥2 条可跑），不假装有三条",
      w.document.getElementById("triOut").querySelectorAll(".card").length === 3); // 2 观点卡 + 1 闸门卡
  }
  {
    // ⑦ 没填 Key / 入题太短
    const { w, calls } = await boot(happyScript());
    w.document.getElementById("mmKey").value = "";
    w.document.getElementById("topic").value = "画个画";
    await w.__sdeArt.run(false);
    ok("没填 Key 直接挡回，零调用", calls.length === 0 && /API Key/.test(w.document.getElementById("err").textContent));
    w.document.getElementById("mmKey").value = "sk-stub";
    await w.__sdeArt.run(false);
    ok("入题太短挡回，仍零调用", calls.length === 0 && /太短/.test(w.document.getElementById("err").textContent));
  }

  /* ═════ 四、闸门的话真的送到了 ═════ */
  group("四、闸门契约");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    const gateIn = chats.filter((c) => /图像占位核查员/.test(c.body.messages[0].content))[0];
    ok("进闸门带上了完整禁区表（SDE 七词 ＋ 陈词 ＋ 画派）",
      /涌现 → /.test(gateIn.body.messages[0].content) && /天平=公平/.test(gateIn.body.messages[0].content)
      && /埃舍尔/.test(gateIn.body.messages[0].content));
    ok("进闸门写死「库里没有 ≠ 没被占位」且不得据此放行",
      /库里没有\s*≠\s*没被占位/.test(gateIn.body.messages[0].content)
      && /不得据此判定通过/.test(gateIn.body.messages[0].content));
    ok("进闸门要求通过必须写满分离线那一行", /必须写满这一行/.test(gateIn.body.messages[1].content));
    const collide = chats.filter((c) => /本轮碰撞方式/.test(String(c.body.messages[1].content)))[0];
    ok("闸门结论被喂进了碰撞那一步（不是评完就完）",
      collide.body.messages[1].content.indexOf("近邻闸门的核查结论") >= 0
      && collide.body.messages[1].content.indexOf("占位失败") >= 0);
    const synth = chats[chats.length - 1];
    ok("综合提炼吃到了胜出典范＋评分卡＋落选典范三样",
      /胜出典范/.test(synth.body.messages[1].content) && /九宫格评分卡/.test(synth.body.messages[1].content)
      && /落选典范/.test(synth.body.messages[1].content));
  }

  /* ═════ 五、确定性 ═════ */
  group("五、确定性");
  {
    const a = await boot(happyScript()); await drive(a.w, "B", {});
    const b = await boot(happyScript()); await drive(b.w, "B", {});
    const seq = (c) => c.filter((x) => /chat\/completions$|image_generation$/.test(x.target))
      .map((x) => /image_generation$/.test(x.target) ? "IMG" : "CHAT").join(">");
    ok("同一份输入两次跑，调用序列完全一致", seq(a.calls) === seq(b.calls), seq(a.calls));
    ok("碰撞方式是随机抽的（这一项本就该随机，只验它不越界 1–6）",
      a.calls.filter((c) => /本轮碰撞方式/.test(String(c.body && c.body.messages && c.body.messages[1] && c.body.messages[1].content)))
        .every((c) => /本轮碰撞方式 [1-6]·/.test(String(c.body.messages[1].content))));
  }

  /* ═════ 六、基底不听话时，渲染端有没有回收路径 ═════ */
  /* 这一组是照 PPT 线那条教训写的：「凡是靠形状驱动的设计，都要在渲染端
     为『形状写错位置』留一条回收路径，光靠提示禁止不够。」 */
  group("六、基底不听话时的回收路径");
  {
    // ① 基底漏掉了英文禁令串
    const { w, calls } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u))
        return chatOK("一、典范名：甲\n二、承重命题：不是A也不是B而是C\n七、绘图指令：a taut horizontal seam across the whole frame, loose fibre meeting dense stone, low raking side light, matte surface, weight gathered low");
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    const draw = calls.filter((c) => /image_generation$/.test(c.target))[0];
    ok("基底漏写禁令串时，渲染端补上（不指望它听话）",
      draw && /no text, no letters, no numbers, no watermark, no recognizable real person, no logo, no brand, not in the style of any named artist/.test(draw.body.prompt),
      draw ? draw.body.prompt.slice(-80) : "没出图");
  }
  {
    // ② 基底把艺术家人名写进了 prompt（禁令①被违反）
    const { w, calls } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u))
        return chatOK("一、典范名：甲\n二、承重命题：不是A也不是B而是C\n七、绘图指令：a swirling night field in the manner of Van Gogh, Escher-like impossible stair, thick impasto, no text");
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    const draw = calls.filter((c) => /image_generation$/.test(c.target))[0];
    ok("基底把艺术家人名写进 prompt 时，本路作废或人名被摘掉（禁令①不能只靠提示）",
      !draw || !/van gogh|escher|mondrian|dali|magritte|rothko|kandinsky/i.test(draw.body.prompt),
      draw ? draw.body.prompt.slice(0, 90) : "（没出图＝已作废，也算过）");
  }

  /* ═════ 七、连跑两次不串场 ═════ */
  group("七、连跑两次不串场");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    const n1 = calls.length;
    const firstWays = calls.filter((c) => /本轮碰撞方式/.test(String(c.body && c.body.messages && c.body.messages[1] && c.body.messages[1].content)))
      .map((c) => String(c.body.messages[1].content).match(/本轮碰撞方式 (\d)/)[1]);
    await w.__sdeArt.run(true);   // 「🎲 换碰撞方式重来一次」
    const allWays = calls.filter((c) => /本轮碰撞方式/.test(String(c.body && c.body.messages && c.body.messages[1] && c.body.messages[1].content)))
      .map((c) => String(c.body.messages[1].content).match(/本轮碰撞方式 (\d)/)[1]);
    const secondWays = allWays.slice(3);
    ok("重来一次真的换了碰撞方式（六种无放回，第二轮是剩下三种）",
      new Set(secondWays).size === 3 && secondWays.every((x) => firstWays.indexOf(x) < 0),
      "第一轮 " + firstWays.join(",") + " 第二轮 " + secondWays.join(","));
    ok("重来一次不会把上一轮的图留在页面上（渲染是重画不是追加）",
      w.document.querySelectorAll("#drawOut .shot img").length === 9,
      "实测 " + w.document.querySelectorAll("#drawOut .shot img").length);
    ok("重来一次不会把上一轮的观点卡留下",
      w.document.getElementById("triOut").querySelectorAll(".card").length === 4,
      "实测 " + w.document.getElementById("triOut").querySelectorAll(".card").length);
    ok("重来一次的调用数与第一轮相同（没有多烧也没有少跑）", calls.length - n1 === n1 - 2,
      "第一轮 " + (n1 - 2) + "(不含内功/原则) 第二轮 " + (calls.length - n1));
  }

  /* ═════ 八、再往刁钻处挖 ═════ */
  group("八、再往刁钻处挖");
  {
    // ① 单字格名「爱」出现在别的格的理由里 —— 会不会串行取错分？
    const { w } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/画面审看者/.test(sys))
        return chatOK([
          "关系｜90｜稳", "影响｜10｜后段没有回写前段，结构与连接都被拖累，活力也差", "共存｜90｜稳",
          "连接｜90｜稳", "次序｜90｜稳", "结构｜90｜稳",
          "完全｜90｜稳", "纯一｜90｜稳", "活力｜90｜稳"
        ].join("\n"));
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "C", {});   // C 档侧重「连接」「共存」
    const p = w.__sdeArt.last().paras.filter(Boolean)[0];
    // 正确答案：八格 90、多样 10，C 档「爱／平安」加倍 → (90*7 + 10 + 90*2)/11 ≈ 84
    ok("项名出现在别项的理由文字里，不会抢走分数（结构/连接/活力都被「影响」那行提到）", p.score >= 80,
      "实测 " + p.score + "（若取错会明显偏低）");
  }
  {
    // ② 基底把第七节写在中间，后面还有第八节
    const { w, calls } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u))
        return chatOK("一、典范名：甲\n七、绘图指令：a taut horizontal seam across the whole frame, loose fibre meeting dense stone, low raking side light, matte\n八、附注：本条为自选补充，不属于绘图指令\n九、备注：随手写的");
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    const draw = calls.filter((c) => /image_generation$/.test(c.target))[0];
    ok("第七节后面还有别的节时，不会把后面几节一起当 prompt 送出去",
      draw && !/附注|备注|自选补充/.test(draw.body.prompt),
      draw ? draw.body.prompt.slice(0, 120) : "没出图");
  }
  {
    // ③ 上游 200 但 content 为空（四次空产出的同族）
    const { w } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return { json: { choices: [{ message: { content: "" } }] } };
    });
    await drive(w, "B", {});
    const err = w.document.getElementById("err").textContent;
    ok("上游 200 但正文为空 → 显式报「空产出」，不是「什么也没发生」", /空产出/.test(err), err.slice(0, 80));
    ok("空产出时给出可执行的下一步", /可缩短入题再试/.test(err));
  }
  {
    // ④ 上游返回的不是 JSON（Cloudflare 错误页那一类）
    const { w } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return { ok: false, status: 503, text: "<!DOCTYPE html><html>Cloudflare</html>" };
    });
    await drive(w, "B", {});
    ok("上游回 HTML 错误页 → 报出状态码与前缀，不吞掉", /503/.test(w.document.getElementById("err").textContent));
  }
  {
    // ⑤ 内功与总原则都取不到（静态资源挂了）
    const { w, calls } = await boot(async function (rec) {
      if (/sde-neigong\.txt$/.test(rec.url) || /kb\/principles$/.test(rec.url)) return { ok: false, status: 404, text: "nope" };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    ok("内功取不到时不阻断开工（退化跑，不是崩）", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("内功缺了要在进度条上如实说，不假装装上了",
      /内功缺/.test(w.document.getElementById("steps").textContent),
      w.document.getElementById("st0") ? w.document.getElementById("st0").textContent : "");
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    ok("内功缺了，术语纪律与承重纪律仍然在场（那是写死的不是取来的）",
      chats.every((c) => !/本轮碰撞方式/.test(String(c.body.messages[1].content))
        || /S＝显露\(Show\)/.test(c.body.messages[0].content)));
  }

  console.log("\n" + "═".repeat(52));
  console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
  console.log("═".repeat(52));
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("\n干跑自身崩了：", e); process.exit(1); });
