// 对话 → 微信 接缝的模拟：把涌现档撞出的典范「立成候选卡」。
// 跑法：node tools/sim_seam.js
//
// 这条缝此前是**完全断的**：典范只活在一次会话的内存里，刷新即失。
// 接上之后最容易出错的不是网络，是**解析**——典范骨架八节的节名会漂移，
// 而候选卡的三段是硬门（缺一段就落不了卡）。所以这里主要钉解析与"取不到就说取不到、绝不编造"。
const fs = require("fs");
const path = require("path");
const PAGE = path.join(__dirname, "..", "public", "search", "index.html");
const html = fs.readFileSync(PAGE, "utf8");
const js = (html.match(/<script>([\s\S]*?)<\/script>/g) || []).join("\n");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}
function group(n) { console.log("\n【" + n + "】"); }

/* 抠出两个纯函数真跑 */
function extract(re, label) {
  const m = js.match(re);
  if (!m) throw new Error("抠不出 " + label + "——页面结构变了，先改这个 sim");
  return m[0];
}
const src = [
  extract(/function cdSection\(txt,names\)\{[\s\S]*?\n}/, "cdSection"),
].join("\n");
const box = {};
new Function("box", src + "\nbox.cdSection=cdSection;")(box);

/* 一份像样的典范骨架（照 worker 里 collide 的八节要求） */
const PARA = `一、典范名：划界者的拇指不在指纹里
二、承重命题：任何划界者都无法在自己划出的界内安置自己的划界动作
三、它切开的辨别面：把「规则适用于对象」与「规则适用于自身」分开
四、第二轴与 2×2：纵轴是可见性，横轴是可归属性……
五、可裁决判据：找到一条能规定自身适用条件的规则，本判断即失效
六、可观测代理：司法解释里对"解释权归属"的沉默频次
七、它从哪撞出来：换母学科，从法学换到控制论
八、最容易在哪被推翻：如果元规则可以无穷回归而不失效`;

group("一、典范骨架 → 候选卡三段");
ok("取得到承重命题", /任何划界者都无法/.test(box.cdSection(PARA, ["二、承重命题", "承重命题"])));
ok("取得到辨别面", /规则适用于对象/.test(box.cdSection(PARA, ["三、它切开的辨别面", "它切开的辨别面", "辨别面"])));
ok("取得到可裁决判据", /能规定自身适用条件/.test(box.cdSection(PARA, ["五、可裁决判据", "可裁决判据"])));
ok("★ 不会把下一节的内容一起吞进来（节与节要切干净）",
  !/第二轴/.test(box.cdSection(PARA, ["二、承重命题"])), box.cdSection(PARA, ["二、承重命题"]));
ok("最后一节取到结尾不越界", /无穷回归/.test(box.cdSection(PARA, ["八、最容易在哪被推翻"])));

group("二、节名漂移时的退路");
const DRIFT = "承重命题 任何划界者都无法在界内安置自己\n辨别面：把甲与乙分开\n可裁决判据：找到反例即失效";
ok("没有序号也能取（备选名单里排第二个）", /任何划界者/.test(box.cdSection(DRIFT, ["二、承重命题", "承重命题"])));
ok("「辨别面」这个短名也能兜住", /把甲与乙分开/.test(box.cdSection(DRIFT, ["三、它切开的辨别面", "它切开的辨别面", "辨别面"])));

group("三、取不到就说取不到——绝不编造");
ok("整段里根本没有这一节 → 返回空串", box.cdSection(PARA, ["九、根本不存在的节"]) === "");
ok("节名在但内容太短（≤3 字）→ 也算没取到", box.cdSection("二、承重命题：无\n三、下一节：x", ["二、承重命题"]) === "");
ok("空输入不炸", box.cdSection("", ["二、承重命题"]) === "" && box.cdSection(null, ["承重命题"]) === "");

group("四、三段是硬门（缺一段就不许落卡）");
ok("缺承重命题时明说去手动立卡，且点出是哪一段",
  /没解析出「承重命题」/.test(js) && /先手动去微信立卡/.test(js));
ok("缺辨别面时给的理由是「缺这一段就没法被顶回」",
  /缺这一段就没法被顶回/.test(js));
ok("缺判据时给的理由是「没有判据别人只能表态」",
  /没有判据别人只能表态/.test(js));
ok("三段都按后端的上限先裁（120/200/300），不靠服务端截",
  /prop=prop\.slice\(0,120\); face=face\.slice\(0,200\); crit=crit\.slice\(0,300\)/.test(js));

group("五、身份：复用全站单点登录");
ok("先读 sessionStorage 的 sde_gauth（与 SDE 微信同一个键）", /sessionStorage\.getItem\("sde_gauth"\)/.test(js));
ok("再退到 localStorage 的 sde_talk_id 跨标签副本", /localStorage\.getItem\("sde_talk_id"\)/.test(js));
ok("副本要看过期时间，不认过期的", /o\.exp>Date\.now\(\)/.test(js));
ok("没登录时给的是可点的去处，不是一句「请登录」",
  /要先在 <a href="\/sde-wechat\/"/.test(js) && /登好回来再点/.test(js));

group("六、落卡契约");
ok("走 /api/im 的 op:cd a:post", /op:"cd",a:"post"/.test(js));
ok("凭证放 body 的 credential（与全站 /api/im 一致）", /credential:cred/.test(js));
ok("三段都带上", /prop:prop,face:face,crit:crit/.test(js));
ok("落卡前先查近邻库（零调用、不烧 Key）", /window\.SDENbr[\s\S]{0,80}\.ask\(prop,5\)/.test(js));
ok("★ 近邻库没装载或查失败时照样落卡（占位查询是保险，不是门禁）",
  /catch\(function\(\)\{go\(null\)\;\}\)/.test(js) && /\} else go\(null\);/.test(js));
ok("落卡成功后给出去处，而不是只说「成功」",
  /已立卡 · 72 小时顶回期开始/.test(js) && /去「🎯 候选」看/.test(js));

group("七、按钮与可见性");
ok("每张典范卡上都有立卡按钮（不只胜出那张）", /onclick="toCandidate\('\+ix\+'\)/.test(js));
ok("按钮名字自带线索（说清它要干什么）", /立成候选卡（交给不共享语汇的人顶回）/.test(js));
ok("每张卡有自己的消息位，不会互相覆盖",
  js.indexOf("cdmsg'+ix+'") >= 0 && js.indexOf('getElementById("cdmsg"+ix)') >= 0);
ok("页面引了近邻库模块", /assets\/sde-nbr\.js/.test(html));
ok("注释写明这条缝此前是断的、为什么要接", /只活在一次会话的内存里/.test(js));

console.log("\n" + "═".repeat(52));
console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
console.log("═".repeat(52));
process.exit(fail ? 1 : 0);
