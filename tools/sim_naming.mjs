/* 品牌名护栏 —— 站上不许再出现旧名「SDE 微信 / 朋友圈 / SDE Chat / Messenger」。
 *
 * 为什么要有这一份（它是被同一个坑咬第三次之后立的）：
 *   页面里的可见文案有两种写法——**真汉字**和 `\uXXXX` 转义。
 *   入口三角与三态切换器的标签正是转义写的（`zh: "SDE \u5fae\u4fe1"`），
 *   于是 2026-08-02 那次按真汉字做的全站更名**一处都没碰到它们**：
 *   社区页、about、首页全改干净了，而**打开网站第一眼看到的那个三角**还写着旧名。
 *   ⇒ 凡是「查某个词还在不在」的护栏，必须**两种写法都查**。
 *
 * 只在**我们自己的界面**上强制（SURFACES）。学员文章、专栏与金句里讲的是真微信
 * （「楼栋微信群里」「没发朋友圈的旅行像白去了」），那些不归这条管。
 * 我们自己的界面上仍有几句是拿真微信作比（「像微信群一样」「发到微信、群、邮件」），
 * 逐句列在 ALLOW 里——**白名单只放句子，不放整个文件**，否则等于没查。
 */
import fs from "node:fs";
import path from "node:path";

const PUB = new URL("../public/", import.meta.url).pathname;

/* 我们自己的界面：前缀匹配 */
const SURFACES = [
  "sde-wechat/", "assets/", "taste/assets/", "taste/wds-companion/",
  "wds-mode.js", "index.html", "browse/", "about/", "search/",
  "sde-talk/", "discussions/", "nbr/", "challenge/", "growth-tree/", "meeting/",
];

/* 旧名：真汉字 ＋ 转义两种写法 */
const OLD = [
  ["\u5fae\u4fe1", /\u5fae\u4fe1/g, /\\u5[Ff][Aa][Ee]\\u4[Ff][Ee]1/g],
  ["\u670b\u53cb\u5708", /\u670b\u53cb\u5708/g, /\\u670[Bb]\\u53[Cc][Bb]\\u5708/g],
  ["SDE Chat", /\bSDE Chat\b/g, null],
  ["Messenger", /\bMessenger\b/g, null],
];

/* 拿真微信作比、或逐字引用用户原话的句子——逐句列，不放整个文件 */
const ALLOW = [
  "\u50cf\u5fae\u4fe1\u7fa4\u4e00\u6837",                 // 像微信群一样
  "\u53d1\u5230\u5fae\u4fe1\u3001\u7fa4\u3001\u90ae\u4ef6", // 发到微信、群、邮件
  "\u7c98\u8d34\u5230\u5fae\u4fe1/\u7fa4/\u90ae\u4ef6",     // 粘贴到微信/群/邮件
  "Google\u3001\u5fae\u4fe1\u3001GPT",
  "\u4e0e\u5fae\u4fe1\u4e00\u81f4", "\u548c\u5fae\u4fe1\u4e00\u81f4", "\u5fae\u4fe1\u5f0f",
  "\u6ca1\u53d1\u670b\u53cb\u5708", "\u670b\u53cb\u5708\u6652\u56fe",   // 金句里的真朋友圈
  /* 代码注释里**逐字引用用户当初的指令**——引用不改，故放行 */
  "\u81ea\u52a8\u8fdb\u5165\u5fae\u4fe1\u7684\u67d0\u4e2a\u5e93\u5b58",
  "\u6216\u8005\u5fae\u4fe1\u6574\u4e2a\u5171\u7528",
  "\u65b0\u601d\u60f3\u548c\u670b\u53cb\u5708\u53ef\u4ee5\u5171\u7528",
];

let files = [];
(function walk(d){
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    const st = fs.statSync(p);
    if (st.isDirectory()) { if (f !== ".git") walk(p); }
    else if (f.endsWith(".html") || f.endsWith(".js")) files.push(p);
  }
})(PUB);

const ours = files.filter((p) => {
  const rel = p.slice(PUB.length);
  return SURFACES.some((s) => rel === s || rel.startsWith(s));
});

let bad = 0, checked = 0;
for (const p of ours) {
  const t = fs.readFileSync(p, "utf8");
  for (const [name, reLit, reEsc] of OLD) {
    for (const re of [reLit, reEsc]) {
      if (!re) continue;
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(t)) !== null) {
        checked++;
        const ctx = t.slice(Math.max(0, m.index - 30), m.index + 30);
        if (ALLOW.some((a) => ctx.indexOf(a) >= 0)) continue;
        bad++;
        console.log("  \u2717 " + p.slice(PUB.length) + "  [" + name +
          (re === reEsc ? " \u00b7 \u8f6c\u4e49\u5199\u6cd5" : "") + "]  \u2026" +
          ctx.replace(/\n/g, " ") + "\u2026");
      }
    }
  }
}

/* 反向断言：新名必须真的在那几处可见标签上（否则「查不到旧名」可能只是因为整段被删了） */
const modes = fs.readFileSync(path.join(PUB, "assets/sde-modes.js"), "utf8");
const portal = fs.readFileSync(path.join(PUB, "assets/sde-portal.js"), "utf8");
const wm = fs.readFileSync(path.join(PUB, "wds-mode.js"), "utf8");
let miss = 0;
const need = (n, c) => { if (!c) { miss++; console.log("  \u2717 " + n); } };
need("\u4e09\u6001\u5207\u6362\u5668\u7684\u4e2d\u6587\u6807\u7b7e\u662f SDE \u793e\u533a",
     /zh: "SDE \\u793e\\u533a"/.test(modes));
need("\u4e09\u6001\u5207\u6362\u5668\u7684\u82f1\u6587\u6807\u7b7e\u662f Community", /en: "Community"/.test(modes));
need("\u5165\u53e3\u4e09\u89d2\u7b2c\u4e09\u9876\u70b9\u662f SDE \u793e\u533a / SDE Community",
     /zh: "SDE \\u793e\\u533a", en: "SDE Community"/.test(portal));
need("\u6d4f\u89c8\u9875\u9876\u680f\u6309\u94ae\u4e2d\u82f1\u90fd\u5df2\u6539\u540d",
     /tabIm: "\uD83D\uDCAC SDE \u793e\u533a"/.test(wm) && /tabIm: "\uD83D\uDCAC Community"/.test(wm));

console.log("\n\u626b\u4e86 " + ours.length + " \u4e2a\u6211\u4eec\u81ea\u5df1\u7684\u754c\u9762\u6587\u4ef6\uff0c\u547d\u4e2d " + checked + " \u5904\uff0c\u5176\u4e2d\u65e7\u540d " + bad + " \u5904\uff1b\u65b0\u540d\u53cd\u5411\u65ad\u8a00\u7f3a " + miss + " \u6761");
console.log(bad + miss === 0 ? "===== \u5168\u7eff =====" : "===== \u6709\u95ee\u9898 =====");
process.exit(bad + miss ? 1 : 0);
