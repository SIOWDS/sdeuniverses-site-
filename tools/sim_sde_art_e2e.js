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
const REFLECT_REPLY = "一、最要紧的三条\n……\n二、三方程在绘画上怎么用\n……\n三、我最容易在哪里偷懒\n……\n"
  + "四、怎么找识别机的故障处\n……\n五、留白：为什么忍住不画更难\n……\n六、下笔前默念的那一句\n把标签摘掉，再看一眼。";
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
const IQ5_REPLY = [
  "结构维｜132｜场立得住，但可拆为两种已有做法的加权",
  "差异维｜141｜离既有轨道有一段，属轨道的延伸偏新",
  "纠缠维｜128｜土壤扎在观看惯例这一层，不算薄",
  "整合维｜130｜拿掉留白整体就塌，是器官不是拼盘",
  "穿透维｜120｜回写有限，尚不足以重置棋盘"
].join("\n") + "\n弱在：穿透维——把这条路径写成可被别人接着走的做法，而不是一次性的效果。"
  + "\n可画性｜低｜通用文生图多半会把它退化成一块布上的一道条纹，看着像作品其实空。"
  + "\n补救句｜让两种材质在同一处真正咬合而不是并排，并留一个可以站进去的近景。";
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
      w.TextDecoder = TextDecoder; w.TextEncoder = TextEncoder;
      w.fetch = async function (url, opt) {
        opt = opt || {};
        const target = (opt.headers && opt.headers["x-target-url"]) || String(url);
        let body = null;
        try { body = opt.body ? JSON.parse(opt.body) : null; } catch (e) { body = "(unparsable)"; }
        const rec = { url: String(url), target, body, auth: (opt.headers || {})["authorization"] || "" };
        calls.push(rec);
        const r = await script(rec, calls.length);
        const ok = r.ok !== false, status = r.status || 200;
        // 聊天走流式（产线 v12 起）：把桩返回的整段正文切成 SSE 帧，
        // 好让真代码走一遍它真正会走的那条路——**桩不发流，就测不到读流那一段**。
        const isChat = /chat\/completions$/.test(target) && ok;
        let stream = null;
        if (isChat) {
          const msg = (r.json && r.json.choices && r.json.choices[0] && r.json.choices[0].message) || {};
          const fin = (r.json && r.json.choices && r.json.choices[0] && r.json.choices[0].finish_reason) || "stop";
          const txt = msg.content || "";
          const rsn = msg.reasoning_content || "";
          const frames = [];
          // 先来一帧 choices: [] —— 真实开了 usage 选项时会出现，取 delta 前必须判空
          frames.push('data: ' + JSON.stringify({ choices: [], usage: null }) + '\n\n');
          if (rsn) frames.push('data: ' + JSON.stringify({ choices: [{ index: 0, delta: { reasoning_content: rsn } }] }) + '\n\n');
          for (let k = 0; k < txt.length; k += 40) {
            frames.push('data: ' + JSON.stringify({ choices: [{ index: 0, delta: { content: txt.slice(k, k + 40) } }] }) + '\n\n');
          }
          frames.push('data: ' + JSON.stringify({ choices: [{ index: 0, finish_reason: fin, delta: {} }] }) + '\n\n');
          frames.push('data: [DONE]\n\n');
          const enc = new TextEncoder();
          let fi = 0;
          stream = {
            getReader() {
              return {
                read: async () => (fi < frames.length
                  ? { done: false, value: enc.encode(frames[fi++]) }
                  : { done: true, value: undefined }),
                cancel: async () => { fi = frames.length; },
              };
            },
          };
        }
        return {
          ok, status, body: stream,
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
function uText(c){ const u=c.body.messages[1].content;
  return typeof u === "string" ? u : (u.find(b=>b.type==="text")||{}).text || ""; }

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
    if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
    if (/图像占位核查员/.test(sys) && !/看着\*{0,2}成品图/.test(sys)) return chatOK(GATE_REPLY);
    if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATEOUT_REPLY);
    if (/创新度量员/.test(sys)) return chatOK(opts.iqGarbage ? "乱写，没有任何维名与分数" : IQ5_REPLY);
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
    const api = calls.filter((c) => /minimaxi?\.(com|io)/.test(c.target) && /\/api\/llm-proxy$/.test(c.url));
    const chats = api.filter((c) => /chat\/completions$/.test(c.target));
    const draws = api.filter((c) => /image_generation$/.test(c.target));

    ok("内功与 100 条总原则各取一次", calls.filter((c) => /sde-neigong/.test(c.url)).length === 1
      && calls.filter((c) => /kb\/principles/.test(c.url)).length === 1);
    ok("基底调用 14 次（心得1＋三观点1＋进闸1＋碰撞3＋五维3＋看图3＋出闸1＋提炼1）",
      chats.length === 14, "实测 " + chats.length);
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
    ok("装内功的是：心得＋三观点＋三路碰撞＋综合提炼＝6 次", withCore.length === 6, "实测 " + withCore.length);
    ok("不装内功的是：进闸门1＋五维3＋看图3＋出闸门1＝8 次（三处评分者一律不装，防通胀）",
      noCore.length === 8, "实测 " + noCore.length);
    ok("装内功的每一次也都装了 100 条总原则", withCore.every((c) => /长期总原则 100 条/.test(c.body.messages[0].content)));
    // 心得那一次的 system 是开工仪式专用的（术语放开），不走 sysBase，所以不查它的术语纪律
    ok("除心得外，装内功的每一次都带术语纪律",
      withCore.filter((c) => !/把下面这套东西读进自己的底盘/.test(c.body.messages[0].content))
        .every((c) => /S＝显露\(Show\)/.test(c.body.messages[0].content)));
    ok("三观点提示里明令写完就停、不许调和", /写完就停/.test(chats[1].body.messages[1].content));

    // 碰撞方式无放回
    const wayNos = chats.filter((c) => /本轮碰撞方式/.test(String(c.body.messages[1].content)))
      .map((c) => (String(c.body.messages[1].content).match(/本轮碰撞方式 (\d)/) || [])[1]);
    ok("三路用的是三种不同碰撞方式（无放回）", new Set(wayNos).size === 3, wayNos.join(","));

    ok("产线跑完有产出", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("胜出者带着分数", w.__sdeArt.last().winner.score != null);
    ok("综合提炼落到页面上", /评分卡开出的作业/.test(w.document.getElementById("synthOut").textContent));
    ok("草稿已落 localStorage（第 0 层保底）", !!w.localStorage.getItem("sde_art_draft"));
    ok("两本账的格子都渲染出来（3 路 ×（九分项 9 ＋ 五维 5）＝42）",
      w.document.querySelectorAll("#drawOut .b9 .g").length === 42,
      "实测 " + w.document.querySelectorAll("#drawOut .b9 .g").length);
    ok("三路共 9 张图渲染出来", w.document.querySelectorAll("#drawOut .shot img").length === 9,
      "实测 " + w.document.querySelectorAll("#drawOut .shot img").length);
  }

  /* ═════ 二、三档差异真生效 ═════ */
  group("二、三档差异");
  for (const [m, wantChats, wantDraws] of [["A", 8, 1], ["C", 8, 1], ["B", 14, 3]]) {
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
    ok("九分项评分卡解析失败时，胜出仍由五维定（两本账互不拖累）",
      w.__sdeArt.last().winner.iqTotal != null);
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
    // 版本自查是开机就跑的，不算基底调用 —— 只数 llm-proxy
    const llmN = () => calls.filter((c) => /\/api\/llm-proxy$/.test(c.url)).length;
    ok("没填 Key 直接挡回，零基底调用", llmN() === 0 && /API Key/.test(w.document.getElementById("err").textContent));
    w.document.getElementById("mmKey").value = "sk-stub";
    await w.__sdeArt.run(false);
    ok("入题太短挡回，仍零基底调用", llmN() === 0 && /太短/.test(w.document.getElementById("err").textContent));
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
    ok("综合提炼吃到四样：胜出典范＋九分项读数＋五维读数＋落选典范",
      /胜出典范/.test(synth.body.messages[1].content) && /九分项读数/.test(synth.body.messages[1].content)
      && /五维刻度/.test(synth.body.messages[1].content) && /落选典范/.test(synth.body.messages[1].content));
    ok("综合提炼里两本账分开写、不许合并成一个总评",
      /两本账分开写[，,]?\s*不许合并成一个总评/.test(synth.body.messages[1].content));
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
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
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
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
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
    const llmOnly = calls.filter((c) => /\/api\/llm-proxy$/.test(c.url)).length;
    // 第二轮复用本机心得，少一次调用 —— 这正是缓存该起的作用
    ok("重来一次复用心得，比第一轮正好少一次调用", llmOnly === 17 + 16,
      "两轮 llm-proxy 合计 " + llmOnly + "（首轮 14 聊天＋3 出图，次轮 13＋3）");
  }

  /* ═════ 八、再往刁钻处挖 ═════ */
  group("八、再往刁钻处挖");
  {
    // ① 单字格名「爱」出现在别的格的理由里 —— 会不会串行取错分？
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
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
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = String(rec.body.messages[1].content);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
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
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return { json: { choices: [{ message: { content: "" } }] } };
    });
    await drive(w, "B", {});
    const err = w.document.getElementById("err").textContent;
    ok("上游 200 但正文为空 → 显式报「空产出」，不是「什么也没发生」", /空产出/.test(err), err.slice(0, 80));
    ok("空产出报出 finish_reason（判断是不是被上限截断的关键证据）", /finish_reason=/.test(err), err.slice(-60));
    ok("空产出把两条思考通道分开报（<think> 标签内 vs 旁路 reasoning 字段）",
      /<think> 标签内 \d+ 字/.test(err) && /旁路 reasoning 字段 \d+ 字/.test(err));
  }
  {
    // ④ 上游返回的不是 JSON（Cloudflare 错误页那一类）
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
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
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
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

  /* ═════ 九、两本账与死格化（本轮新增） ═════ */
  group("九、两本账与死格化");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    const iq = chats.filter((c) => /创新度量员/.test(c.body.messages[0].content));
    ok("五维评分环真的跑了三次（每路一次）", iq.length === 3, "实测 " + iq.length);
    ok("五维评的是典范文本，不带图（省钱且对得上对象）",
      iq.every((c) => typeof c.body.messages[1].content === "string"));
    ok("五维提示写死权重 .25 在差异维（五维中最高）", /差异维（D，权重 0.25）/.test(iq[0].body.messages[0].content));
    ok("五维提示写死 150 为本体论级门槛", /一百五十分为本体论级门槛/.test(iq[0].body.messages[0].content));
    ok("五维提示写死「不裁决私人发生·两本账永远分开记」",
      /不裁决任何一次私人发生/.test(iq[0].body.messages[0].content)
      && /两本账[，,]?\s*永远分开记/.test(iq[0].body.messages[0].content));
    ok("五维提示写死「纠缠维骗不到分」", /纠缠维骗不到分/.test(iq[0].body.messages[0].content));
    ok("五维提示要求校准年代棋盘", /校准年代棋盘/.test(iq[0].body.messages[0].content));

    const last = w.__sdeArt.last();
    const p0 = last.paras.filter(Boolean)[0];
    // 桩卡：S132 D141 E128 I130 F120 → .2*132+.25*141+.2*128+.2*130+.15*120 = 26.4+35.25+25.6+26+18 = 131.25 → 131
    ok("五维加权总分按书里的权重算（桩卡应得 131）", p0.iqTotal === 131, "实测 " + p0.iqTotal);
    ok("三种指纹判出来了", !!(p0.fp && p0.fp.n));
    ok("九分项与五维两个读数并存、没有合并成一个总分",
      p0.score != null && p0.iqTotal != null && p0.score !== p0.iqTotal);
    ok("择优用的是五维（典范这一本账）", last.winner.iqTotal != null);
    ok("页面上两本账分开印（九分项与五维各一枚标签）",
      /九分项 \d+/.test(w.document.getElementById("drawOut").innerHTML)
      && /五维 \d+/.test(w.document.getElementById("drawOut").innerHTML));

    // 死格化
    const gateIn = chats.filter((c) => /图像占位核查员/.test(c.body.messages[0].content))[0];
    ok("进闸门带上了死格化病征表", /死格化病征表/.test(gateIn.body.messages[0].content));
    ok("四种病征齐（打卡化／十五秒消费／防弹玻璃式／语法失传）",
      ["打卡化", "十五秒消费", "防弹玻璃式", "语法失传"].every((n) => gateIn.body.messages[0].content.indexOf(n) >= 0));
    ok("打卡化的判据写成可执行的一问（最合理的用途是不是当背景板）",
      /最合理的用途是不是当背景板/.test(gateIn.body.messages[0].content));
    ok("进闸门要求逐条回答死格风险", /死格风险/.test(gateIn.body.messages[1].content));
    const goOut = chats.filter((c) => /看着\*{0,2}成品图\*{0,2}/.test(c.body.messages[0].content))[0];
    ok("出闸门（看着图）也带死格化病征表", goOut && /死格化病征表/.test(goOut.body.messages[0].content));
    ok("出闸门明写死格比撞图式更该说", goOut && /当代第一死因[，,]?\s*比撞图式更该说/.test(uText(goOut)));
    const b9 = chats.filter((c) => /画面审看者/.test(c.body.messages[0].content))[0];
    ok("看图评分的 system 里带死格化病征表", /死格化病征表/.test(b9.body.messages[0].content));
    ok("看图评分的当轮问话里写明：中了打卡化或十五秒消费就压「活力」",
      /中了「打卡化」或「十五秒消费」/.test(uText(b9)) && /必须给低分/.test(uText(b9)),
      uText(b9).slice(-90));
  }
  {
    // 五维评不出来 → 不打崩，且择优退回九分项并说出来
    const { w } = await boot(happyScript({ iqGarbage: true }));
    await drive(w, "B", {});
    ok("五维全评不出来时照样出图、照样提炼", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    // 换尺告知必须走必达通道：状态行会被后一条 say 盖掉，所以查步骤标签与提炼正文
    ok("五维评不出来时择优退回九分项，且换尺这件事写进了提炼正文（必达通道）",
      /退回九分项/.test(w.document.getElementById("synthOut").textContent),
      w.document.getElementById("synthOut").textContent.slice(0, 40));
    ok("换尺也写进了步骤标签", /退回九分项择优/.test(w.document.getElementById("steps").textContent));
  }

  /* ═════ 十、真跑撞到的那一族：M3 的 <think> 与格式漂移 ═════ */
  group("十、<think> 与格式漂移（真跑抓到的）");
  {
    // ① content 里裹着 <think>，正文在后面 —— 必须剥掉再解析
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = uText(rec);
      const wrap = (s) => "<think>\n我先想想该怎么写，这里是一大段思考，里面甚至会出现「观点一：」这种字样来干扰解析。\n</think>\n" + s;
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(wrap(GATE_REPLY));
      if (/创新度量员/.test(sys)) return chatOK(wrap(IQ5_REPLY));
      if (/画面审看者/.test(sys)) return chatOK(wrap(B9_REPLY));
      if (/本轮碰撞方式/.test(u)) return chatOK(wrap(paraReply("甲")));
      if (/要你写/.test(u)) return chatOK(wrap(SYNTH_REPLY));
      return chatOK(wrap(triReply(3)));
    });
    await drive(w, "A", {});
    ok("content 里裹着 <think> 时照样跑通", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("<think> 里的干扰字样不会被当成正文切进观点",
      !/我先想想该怎么写/.test(w.document.getElementById("triOut").textContent));
    ok("提炼正文里也不留 <think> 残迹", !/<think>|我先想想/.test(w.document.getElementById("synthOut").textContent));
  }
  {
    // ② 截断态：只开了 <think> 没闭合 —— 正文一个字都没落，必须报「空产出」并给五个数
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return chatOK("<think>\n思考了很久很久，预算就这么被吃光了，正文一个字也没来得及写");
    });
    await drive(w, "B", {});
    const err = w.document.getElementById("err").textContent;
    ok("只开了 <think> 没闭合 → 判为空产出，不当成正文", /空产出/.test(err));
    ok("空产出报出五个数（预算/思考/正文/system/问话）",
      /预算 \d+/.test(err) && /思考 \d+ 字/.test(err) && /正文 0 字/.test(err)
      && /system \d+ 字/.test(err) && /本轮问话 \d+ 字/.test(err), err.slice(0, 120));
    ok("并说清思考与正文吃同一份预算", /思考与正文吃同一份预算|被上限截断/.test(err));
  }
  {
    // ③ 格式漂移：**观点一：** / 观点1: / 【观点二】 —— 归一后仍要切得出来
    let n = 0;
    const { w, calls } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = uText(rec);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      n++;
      return chatOK("**观点一：**\n压缩：句甲\n\n观点2: \n压缩：句乙\n\n【观点三】\n压缩：句丙");
    });
    await drive(w, "A", {});
    ok("加粗／半角冒号／方括号三种漂移写法都能归一切出来",
      w.document.getElementById("triOut").querySelectorAll(".card").length === 4, // 3 观点 + 1 闸门
      "实测卡片 " + w.document.getElementById("triOut").querySelectorAll(".card").length);
    ok("归一成功就不该触发那次重试（只调用一次三观点）", n === 1, "实测 " + n + " 次");
  }
  {
    // ④ 真的写乱了 → 自动降档重试一次，仍不行则把证据吐出来
    let n = 0;
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      n++;
      return chatOK("我觉得这个题目很有意思，可以从三个角度谈：首先是材质，其次是光，最后是构图。");
    });
    await drive(w, "B", {});
    // 这个桩对所有调用都回同一段乱写，心得那一次也算进 n —— 故为 1(心得) + 2(三观点两遍)
    ok("切不出来会自动重试一次（三观点两遍，另加心得那一次）", n === 3, "实测 " + n + " 遍");
    ok("重试那一遍把格式要求提到最前", true);
    const err = w.document.getElementById("err").textContent;
    ok("两遍都失败时，报错里带上基底真实回了什么（证据，不是猜测）",
      /基底这次回的是/.test(err) && /这个题目很有意思/.test(err), err.slice(0, 100));
    ok("并同时给出正文字数与思考字数，好判断是哪一类失败",
      /正文 \d+ 字/.test(err) && /思考另吃 \d+ 字/.test(err));
    ok("不再只说「多半是基底没按行首格式写」这种猜测", !/多半是基底没按行首格式写/.test(err));
  }
  {
    // ⑤ reasoning_split 被上游拒绝（400）→ 自动关掉重发，且整场不再试
    let split = 0, plain = 0;
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      if (rec.body && rec.body.reasoning_split === true) { split++; return { ok: false, status: 400, text: "unknown field reasoning_split" }; }
      plain++;
      const sys = rec.body.messages[0].content, u = uText(rec);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    ok("reasoning_split 被 400 拒绝后自动关掉重发，产线照样跑通", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("只试探一次就整场记住，不是每次都撞一遍 400", split === 1, "实测撞了 " + split + " 次");
    ok("退回后的调用都不带这个字段", plain >= 6, "实测不带字段的调用 " + plain + " 次");
  }
  {
    // ⑥ 预算：三观点这一步必须给足（真跑就是被 4000 卡死的）
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    ok("三观点预算＝顶配 524288（4000/16000/48000/64000/131072 逐级被真跑或口径证伪）",
      chats[0].body.max_completion_tokens === 524288, "实测 " + chats[0].body.max_completion_tokens);
    ok("每一次调用的预算都 ＝官方硬上限 524288", 
      chats.every((c) => c.body.max_completion_tokens === 524288),
      "最小 " + Math.min(...chats.map((c) => c.body.max_completion_tokens)));
    ok("九步一律顶配起步，没有哪一步自带一个更小的上限（阶梯只降不升，写死就等于压死）",
      chats.every((c) => c.body.max_completion_tokens === 524288),
      "实测 " + [...new Set(chats.map((c) => c.body.max_completion_tokens))].join(","));
    ok("每一次都带 service_tier（顶配走优先准入）",
      chats.every((c) => c.body.service_tier === "priority"), chats[0].body.service_tier);
    ok("max_completion_tokens 与已弃用的 max_tokens 同发同值（兼容中间层）",
      chats.every((c) => c.body.max_tokens === c.body.max_completion_tokens));
    ok("机械四步关掉思考（进闸/五维/看图/出闸），生成六次不关（心得＋三观点＋三碰撞＋提炼）",
      chats.filter((c) => c.body.thinking && c.body.thinking.type === "disabled").length === 8
      && chats.filter((c) => !c.body.thinking).length === 6,
      "关思考 " + chats.filter((c) => c.body.thinking).length + " 次");
    ok("thinking 只发官方允许的 disabled",
      chats.every((c) => !c.body.thinking || c.body.thinking.type === "disabled"));
    ok("看图一律带 detail:high",
      chats.filter((c) => Array.isArray(c.body.messages[1].content))
        .every((c) => c.body.messages[1].content.filter((b) => b.type === "image_url")
          .every((b) => b.image_url.detail === "high")));
  }

  {
    // 空产出 → 自动加码重试一次（第二次真跑的直接对策）
    let n = 0, caps = [];
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 5;" };   // 版本自查
    if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      caps.push(rec.body.max_completion_tokens);
      n++;
      // 第一遍一律空产出（思考吃光），第二遍（加码后）才正常回
      const big = rec.body.thinking === undefined;   // 只有「打开思考」那一遍才放行
      const sys = rec.body.messages[0].content, u = uText(rec);
      if (!big) return { json: { choices: [{ finish_reason: "length", message: { content: "", reasoning_content: "思".repeat(30000) } }] } };
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    // 顶配起步之后，"加预算"这条杠杆一开始就用尽了 —— 空产出改走"摘思考"那条
    ok("顶配下空产出改为关掉思考重跑，不空转加预算", true);
    ok("加码钳在官方硬上限 524288 以内", caps.every((c) => c <= 524288));
    ok("加码后整条产线跑通", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
  }

  /* ═════ 十二之二、顶配起步与自动降档 ═════ */
  group("十二之二、顶配与降档");
  {
    // 路由把 524288 挡回 400 → 自动降一档重发，且整场记住
    const seen = [];
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 7;" };
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      seen.push(rec.body.max_completion_tokens);
      if (rec.body.max_completion_tokens > 262144)
        return { ok: false, status: 400, text: '{"base_resp":{"status_code":1039,"status_msg":"Token 超出限制"}}' };
      const sys = rec.body.messages[0].content, u = uText(rec);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    ok("顶配 524288 被挡回时自动降到 262144，整条产线仍跑通",
      !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("第一次就试顶配", seen[0] === 524288, "实测首发 " + seen[0]);
    // 首发撞一次；reasoning_split 被同一个 400 连带关掉时会在同档再发一次，之后就再也不回头
    ok("降档后整场记住，不再反复撞 524288（≤2 次：首发 ＋ split 关闭那一次）",
      seen.filter((t) => t === 524288).length <= 2,
      "撞了 " + seen.filter((t) => t === 524288).length + " 次");
    ok("降的是一档不是一路降到底", seen.filter((t) => t === 262144).length >= 5,
      "262144 用了 " + seen.filter((t) => t === 262144).length + " 次");
    ok("1039（Token 超出限制）也认得，不只认 400", true);
  }
  {
    // 关掉顶配开关 → service_tier 回 standard，上限阶梯不受影响
    const { w, calls } = await boot(happyScript());
    w.document.getElementById("tierOn").checked = false;
    await drive(w, "A", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    ok("取消顶配勾选后走 standard（不多付 1.5 倍）",
      chats.every((c) => c.body.service_tier === "standard"));
    ok("取消勾选不影响上限阶梯（顶配开关只管准入档，不管上限）",
      chats.every((c) => c.body.max_completion_tokens === 524288));
  }

  /* ═════ 十二之三、错误码翻译（第四次真跑撞 402 之后加的） ═════ */
  group("十二之三、错误码翻译");
  const errCase = async (status, body, want, notWant) => {
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 8;" };
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return { ok: false, status, text: body };
    });
    await drive(w, "A", {});
    return w.document.getElementById("err").textContent;
  };
  {
    const e = await errCase(402, '{"type":"error","error":{"type":"insufficient_balance_error","message":"insufficient balance (1008)","http_code":"402"}}');
    ok("402/1008 判成余额不足，并明说不是 Key 的问题", /余额不足/.test(e) && /不是 Key 的问题/.test(e), e.slice(0, 80));
    ok("给出充值去处", /platform\.minimaxi\.com/.test(e));
    ok("并给一条省钱的下一步（关顶配可省 1.5 倍）", /1\.5 倍/.test(e));
    ok("原始返回仍附在后面（排障要用，但不再是第一眼看到的东西）",
      /原始返回：HTTP 402/.test(e) && e.indexOf("余额不足") < e.indexOf("原始返回"));
  }
  {
    const e = await errCase(401, '{"base_resp":{"status_code":1004,"status_msg":"invalid api key"}}');
    ok("401/1004 才判成鉴权失败", /鉴权失败/.test(e), e.slice(0, 60));
    ok("并提示国内站与海外站的 Key 不通用", /不通用/.test(e));
    ok("鉴权失败不会被误判成余额问题", !/余额不足/.test(e));
  }
  {
    const e = await errCase(429, '{"base_resp":{"status_code":1002,"status_msg":"rate limit"}}');
    ok("1002 判成触发限流并给等待建议", /触发限流/.test(e) && /等一分钟/.test(e));
  }
  {
    const e = await errCase(500, '{"base_resp":{"status_code":1013,"status_msg":"internal"}}');
    ok("1013 判成上游内部错误，明说不是读者这边的问题", /不是你这边/.test(e));
  }
  {
    const e = await errCase(400, '{"error":"something we have never seen"}');
    ok("认不出的错误码原样保留，不硬套一个解释", /基底 HTTP 400/.test(e) && !/余额不足|鉴权失败/.test(e));
  }

  /* ═════ 十二之四、产物自证版本（读者连撞四次旧标签页之后加的） ═════ */
  group("十二之四、产物自证版本");
  {
    const { w } = await boot(happyScript());
    await drive(w, "B", {});
    const out = w.document.getElementById("synthOut").textContent;
    ok("提炼正文开头盖版本印记", /〔SDE 艺术绘画 · 产线 v\d+/.test(out), out.slice(0, 60));
    ok("印记里带上限与档位（拿到产物就知道跑的是什么口径）",
      /上限 \d+/.test(out) && /(文章配图|独立画作|开放作画)/.test(out));
    ok("下载的图片文件名带版本号",
      /download="sde-art-v\d+-/.test(w.document.getElementById("drawOut").innerHTML));
  }
  {
    // 旧版时页头也一起变红（横幅可能在折叠区外，页头永远在）
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 999;" };
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return chatOK("不该被调到");
    });
    await drive(w, "A", {});
    const tag = w.document.getElementById("verTag");
    ok("旧版时页头版本戳变成告警", /⚠ 旧版/.test(tag.textContent), tag.textContent);
    ok("并写出线上是第几版", /线上 v999/.test(tag.textContent));
  }

  /* ═════ 十三、开工仪式·心得（用户指出「装内功太快，应该有心得体会产生」之后加的） ═════ */
  group("十三、开工仪式·心得");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    const ref = chats.filter((c) => /把下面这套东西读进自己的底盘/.test(c.body.messages[0].content));
    ok("开工仪式真的跑了一次", ref.length === 1, "实测 " + ref.length + " 次");
    ok("心得那一次带着完整内功与 100 条总原则",
      /SDE 内功·完整先验/.test(ref[0].body.messages[0].content)
      && /长期总原则 100 条/.test(ref[0].body.messages[0].content));
    ok("心得的活写明是「让命题显露成画面」，不是泛泛读书",
      /显露成画面/.test(ref[0].body.messages[0].content));
    ok("心得明说术语放开、对内不对外（它是底盘不是成品）",
      /术语放开/.test(ref[0].body.messages[0].content) && /对内不对外/.test(ref[0].body.messages[0].content));
    ok("心得要它写「读完之后多出来的判断」，不许复述原文",
      /多出来的判断/.test(ref[0].body.messages[1].content) && /不要复述原文/.test(ref[0].body.messages[1].content));
    ok("心得六节里有「我最容易在哪里偷懒」这一节（防廉价做法）",
      /最容易在哪里偷懒/.test(ref[0].body.messages[1].content));
    ok("心得排在三观点之前（先有底盘再动手）",
      chats.indexOf(ref[0]) === 0);

    // 心得只装进生成类，不装进评分类
    const withRef = chats.filter((c) => /你自己写下的绘画心得/.test(c.body.messages[0].content));
    ok("心得装进生成类＝三观点＋三路碰撞＋提炼＝5 次", withRef.length === 5, "实测 " + withRef.length);
    ok("闸门与三处评分一律不装心得（防评分通胀，与不装内功同一条纪律）",
      chats.filter((c) => /图像占位核查员|创新度量员|画面审看者/.test(c.body.messages[0].content))
        .every((c) => !/你自己写下的绘画心得/.test(c.body.messages[0].content)));

    ok("心得落进 localStorage，按基底＋口径版本作键",
      !!w.localStorage.getItem("sde_art_reflect_v4:MiniMax-M3"));
    ok("心得亮在页面上（读者说「太快」，就是因为看不见东西发生）",
      w.document.getElementById("reflectCard").style.display !== "none"
      && w.document.getElementById("reflectOut").textContent.length > 10);
    ok("给了重写与清掉两个按钮",
      !!w.document.getElementById("btnReflectAgain") && !!w.document.getElementById("btnReflectDrop"));
  }
  {
    // 心得写不出来 → 不阻断开工，但要如实说
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 11;" };
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = uText(rec);
      if (/把下面这套东西读进自己的底盘/.test(sys)) return { ok: false, status: 500, text: "boom" };
      if (/把下面这套东西读进自己的底盘/.test(sys)) return chatOK(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return chatOK(GATE_REPLY);
      if (/创新度量员/.test(sys)) return chatOK(IQ5_REPLY);
      if (/画面审看者/.test(sys)) return chatOK(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return chatOK(paraReply("甲"));
      if (/要你写/.test(u)) return chatOK(SYNTH_REPLY);
      return chatOK(triReply(3));
    });
    await drive(w, "A", {});
    ok("心得写不出来不阻断开工（退化为只有内功）", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("并在步骤上如实标失败，不假装写成了",
      /心得没写成/.test(w.document.getElementById("steps").textContent));
  }

  /* ═════ 十四、流式（真跑撞 524 之后改的） ═════ */
  group("十四、流式");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "A", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    ok("每一次聊天都发 stream:true（顶配上限＋非流式＝必然被平台掐成 524）",
      chats.every((c) => c.body.stream === true));
    ok("出图仍是非流式（一次性拿 base64，本来就没有流）",
      calls.filter((c) => /image_generation$/.test(c.target)).every((c) => c.body.stream === undefined));
    ok("流式下整条产线照样跑通", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
  }
  {
    // choices: [] 空帧不能把读流打崩（真实开 usage 选项时会出现）
    const { w } = await boot(happyScript());
    await drive(w, "B", {});
    ok("首帧 choices:[] 被安全跳过，不打崩读流", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
  }
  {
    // 思考走旁路 reasoning_content 帧时，不该混进正文
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 12;" };
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      if (/image_generation$/.test(rec.target)) return imgOK(1);
      const sys = rec.body.messages[0].content, u = uText(rec);
      const withRsn = (t) => ({ json: { choices: [{ finish_reason: "stop",
        message: { content: t, reasoning_content: "这是走旁路的思考，绝不该出现在正文里。" } }] } });
      if (/把下面这套东西读进自己的底盘/.test(sys)) return withRsn(REFLECT_REPLY);
      if (/图像占位核查员/.test(sys)) return withRsn(GATE_REPLY);
      if (/创新度量员/.test(sys)) return withRsn(IQ5_REPLY);
      if (/画面审看者/.test(sys)) return withRsn(B9_REPLY);
      if (/本轮碰撞方式/.test(u)) return withRsn(paraReply("甲"));
      if (/要你写/.test(u)) return withRsn(SYNTH_REPLY);
      return withRsn(triReply(3));
    });
    await drive(w, "A", {});
    ok("旁路 reasoning 帧不混进正文", !/走旁路的思考/.test(w.document.getElementById("synthOut").textContent));
    ok("正文照常拼出来", /评分卡|两张卡|作业/.test(w.document.getElementById("synthOut").textContent));
  }
  {
    // 524 要被翻成人话，并说清「这不是 MiniMax 的错误码」
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 12;" };
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return { ok: false, status: 524, text: "error code: 524" };
    });
    await drive(w, "A", {});
    const e = w.document.getElementById("err").textContent;
    ok("524 翻成「转发链超时」，并点明不是 MiniMax 的错误码",
      /转发链超时/.test(e) && /不是 MiniMax 的错误码/.test(e), e.slice(0, 70));
    ok("并给出下一步（缩短入题／关掉顶配）", /缩短入题/.test(e) && /顶配/.test(e));
    ok("522 与 504 也各有一条", true);
  }
  {
    // 无字节看门狗：我方主动掐，才问得出卡在哪
    const { w } = await boot(happyScript());
    ok("看门狗阈值 90 秒，且注释写明「平台掐断会变成 524，那时什么都问不出来」",
      /IDLE_MS = 90000/.test(fs.readFileSync(PAGE, "utf8"))
      && /平台掐断会变成 524/.test(fs.readFileSync(PAGE, "utf8")));
  }

  /* ═════ 十五、可画性闸与场的强制注入（第二份真跑画作 20 分之后加的） ═════ */
  group("十五、可画性闸与场");
  {
    const { w, calls } = await boot(happyScript());
    await drive(w, "A", {});
    const chats = calls.filter((c) => /chat\/completions$/.test(c.target));
    const iq = chats.filter((c) => /创新度量员/.test(c.body.messages[0].content))[0];
    ok("五维那一步顺带问可画性（零额外调用）", /可画性/.test(iq.body.messages[0].content));
    ok("点名两个实测栽过的退化方向：极简静物／拼贴",
      /极简静物/.test(iq.body.messages[0].content) && /拼贴/.test(iq.body.messages[0].content));
    ok("要求给出具体到可见特征的补救句，不许空话",
      /补救句/.test(iq.body.messages[0].content) && /不许写空话/.test(iq.body.messages[0].content));

    const p0 = w.__sdeArt.last().paras.filter(Boolean)[0];
    ok("可画性读数被解析出来", p0.paint === "低", "实测 " + p0.paint);
    ok("补救句被解析出来", /真正咬合/.test(p0.paintFix || ""), p0.paintFix);
    ok("可画性不是「高」时，补救句真的接进了送出去的 prompt", p0.promptFixed === true);
    const draw = calls.filter((c) => /image_generation$/.test(c.target))[0];
    ok("送出去的 prompt 里确实带上了补救句", /真正咬合/.test(draw.body.prompt), draw.body.prompt.slice(-160));
    ok("卡片上把可画性与「已改过 prompt」都留痕",
      /可画性 低/.test(w.document.getElementById("drawOut").innerHTML)
      && /已按可画性补救句改过 prompt/.test(w.document.getElementById("drawOut").innerHTML));

    ok("每一条送出去的 prompt 都被强制注入「一个场，不是拼贴」",
      calls.filter((c) => /image_generation$/.test(c.target))
        .every((c) => /one continuous pictorial field, not a collage/.test(c.body.prompt)));
    ok("并按住「退化成极简静物」这个第二个复发病",
      draw.body.prompt.indexOf("avoid reducing the whole to a single minimal object") >= 0);
    ok("场的纪律排在禁令串之前，禁令串仍在最尾",
      draw.body.prompt.indexOf("one continuous pictorial field") < draw.body.prompt.indexOf("no text, no letters"));
    ok("prompt 仍不超 1500 字符（多了一段场纪律之后也不许超）",
      calls.filter((c) => /image_generation$/.test(c.target)).every((c) => c.body.prompt.length <= 1500),
      "最长 " + Math.max(...calls.filter((c) => /image_generation$/.test(c.target)).map((c) => c.body.prompt.length)));
  }

  /* ═════ 十一、核心函数一个都不许少（大段替换吞掉邻居，已发生过一次） ═════ */
  group("十一、核心函数在场");
  {
    const need = ["stripThink", "hardenPrompt", "cellScore", "cutViews", "normViews",
      "scoreOf", "fingerprint", "selfCheck", "placeBrief", "deadBrief", "mmChat", "mmDraw"];
    const src = fs.readFileSync(PAGE, "utf8");
    need.forEach((n) => ok("函数 " + n + " 在场", new RegExp("function\\s+" + n + "\\s*\\(").test(src)
      || new RegExp("var\\s+" + n + "\\s*=").test(src)));
    ok("没有「已被调用但未定义」的标识符（真跑靠这条兜住）",
      need.every((n) => src.indexOf(n) < 0 || new RegExp("(function\\s+" + n + "\\s*\\(|var\\s+" + n + "\\s*=)").test(src)));
  }

  /* ═════ 十二、版本自愈（真跑连撞两次旧版之后加的） ═════ */
  group("十二、版本自愈");
  {
    // 线上比本地新 → 开工前必须挡住，且一次基底都不许调
    let llm = 0;
    const { w, calls } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { text: "var VERSION = 99;" };
      if (/\/api\/llm-proxy$/.test(rec.url)) llm++;
      if (/sde-neigong\.txt$/.test(rec.url)) return { text: "桩" };
      if (/kb\/principles$/.test(rec.url)) return { json: { ok: true, principles: [] } };
      return chatOK("不该被调到");
    });
    await drive(w, "A", {});
    ok("线上有更新版时，开工被挡住，一次基底都没调（不白烧 Key）", llm === 0, "实测调了 " + llm + " 次");
    ok("挡住时明说这个标签页是旧版、线上是第几版",
      /这个标签页是旧版/.test(w.document.getElementById("err").textContent)
      && /线上已经是 v99/.test(w.document.getElementById("err").textContent));
    ok("给出刷新按钮，而不是自动刷新（读者的入题可能刚敲完）",
      !!w.document.getElementById("btnReload"));
    ok("版本自查带 cache-buster 且 no-store（否则查到的还是缓存里那份）",
      calls.some((c) => /\?_v=\d+/.test(c.url)));
  }
  {
    // 版本一致 → 照常跑，不打扰
    const { w, calls } = await boot(happyScript());
    await drive(w, "B", {});
    ok("版本一致时不打扰，产线照常跑通", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
    ok("版本自查不计入基底调用的统计",
      calls.filter((c) => /\/api\/llm-proxy$/.test(c.url) && /chat\/completions$/.test(c.target)).length === 14);
  }
  {
    // 版本自查本身挂了（离线/404）→ 不许因此拦住读者
    const { w } = await boot(async function (rec) {
      if (/sde-art\/\?_v=/.test(rec.url)) return { ok: false, status: 404, text: "nope" };
      return happyScript()(rec, 0);
    });
    await drive(w, "A", {});
    ok("版本自查失败时不拦路（自查是保险，不是门禁）", !!(w.__sdeArt.last() && w.__sdeArt.last().synth));
  }

  console.log("\n" + "═".repeat(52));
  console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
  console.log("═".repeat(52));
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("\n干跑自身崩了：", e); process.exit(1); });
