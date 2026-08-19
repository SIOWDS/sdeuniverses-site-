/* sim_chatsde_firstleg.js —— 「开始就不行」：开工那一趟失败之后，退路上一道闸都没有
 *
 * 真跑读数：状态栏写着「完成 · 54」——整篇 54 个字，断在半句上，而它被记成"完成"。
 * 走的是这条路：提纲（plan）那一趟没吐出可用的 sections → 退回 `runLeg({}).then(done)`
 * ——单趟、不看长度、不重试。本文件把这条路上的两道新闸真跑一遍。
 * 顺带查顶栏：一行 flex 塞不下标题＋状态＋七颗按钮时，被压扁的是状态那一栏
 * （挤到一个字宽，汉字一个一个竖着排）。
 * 跑法：node tools/sim_chatsde_firstleg.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };
const FSRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ═══ 一、把 planOnce ＋ 回退那一段抠出来真跑 ═══ */
const a = FSRC.indexOf("    var FLOOR = 400;");
/* 终点锚改到 `function startParts(plan)` 这一行之前：写正文那一大段已被抽成具名函数，
   切到这里括号正好是平的，不必再补合成收尾（上一版补的 `});` 现在会多一个右括号）。
   startParts 在壳里用替身接住——这一份只测开工那两趟，不测写正文。 */
const b = FSRC.indexOf("    function startParts(plan) {", a);
const SRC = (a > 0 && b > a) ? FSRC.slice(a, b) : "";
ok("抠得到 planOnce 与回退那一段", SRC.indexOf("planOnce") > 0 && SRC.indexOf("runLeg({})") > 0);
ok("切片括号是平的（不必补合成收尾）", SRC.split("{").length === SRC.split("}").length);

const FLOOR = +((SRC.match(/var FLOOR = (\d+);/) || [])[1] || 0);
ok("下限是从源码取的，不是这里手抄的（" + FLOOR + "）", FLOOR > 0);

/* legs 描述每一趟怎么回：{plan:…} 或 {out:N}；按调用顺序取用 */
function run(legs, cb, opt) {
  const box = { calls: [], notes: [], done: false, text: "", planTries: 0, oneTries: 0,
                started: null, bare: 0,
                kind: (opt && opt.kind) || "essay", chunked: (opt && opt.chunked) || {} };
  const src =
    /* CHUNKED/kind 决定走哪条退路：骨架档要骨架，自由分节档才退回一趟写完。
       壳里由调用方指定，两条路各测各的。 */
    "var dStopped=false, text='', pTrace={}, kind=__b.kind, CHUNKED=__b.chunked;" +
    "function startParts(p){ __b.started=p; __b.done=true; __b.text=text; }" +
    "function dNote(v){ __b.notes.push(String(v)); } function t(k){ return k; }" +
    "function done(){ __b.done=true; __b.text=text; }" +
    "function runLeg(o){" +
    "  var st=(o&&o.stage)||'one'; __b.calls.push(st);" +
    /* bare 那一趟单独记：它不打上游，不该算进"提纲试了几遍"。 */
    "  if (st==='plan') { if (o&&o.bare) __b.bare++; else __b.planTries++; } else __b.oneTries++;" +
    "  var r=__b.legs.shift()||{out:0};" +
    "  if (r.out) text += 'x'.repeat(r.out);" +      // 边流边加，才测得出回滚
    "  return Promise.resolve({ plan:r.plan||null, out:r.out||0, err:'' });" +
    "}\n" + SRC +
    "\n__b.tick = function(){ __b.text = text; };";
  box.legs = legs.slice();
  new Function("__b", src)(box);
  const t0 = Date.now();
  (function w() {
    if (box.done || Date.now() - t0 > 9000) return cb(box);
    setTimeout(w, 10);
  })();
}

const GOODPLAN = { plan: { title: "T", sections: [{ h: "一", ask: "a", words: 1000 }] } };

console.log("── 提纲那一趟 ──");
run([{ plan: null }, GOODPLAN], (bx) => {
  ok("提纲第一趟没成 → 自动再来一趟", bx.planTries === 2);
  ok("重试之前跟读者说了一声", bx.notes.join("|").indexOf("dPlanRetry") >= 0);
  ok("第二趟成了就不再退回单趟", bx.notes.join("|").indexOf("dPlanFallback") < 0);

  run([GOODPLAN], (bx2) => {
    ok("第一趟就成 → 不多打一趟（别白烧一次额度）", bx2.planTries === 1);

    console.log("── 退路那一趟 ──");
    run([{ plan: null }, { plan: null }, { out: 54 }, { out: 3000 }], (bx3) => {
      ok("提纲两趟都没成 → 才退回单趟", bx3.notes.join("|").indexOf("dPlanFallback") >= 0);
      ok("★ 单趟只吐 54 字 → 不当完成，重写一遍（这正是真跑那份「完成 · 54」）", bx3.oneTries === 2);
      ok("重写前把残字回滚了（不是接在半句后面）", bx3.text.length === 3000);
      ok("第二遍够长就不再报警", bx3.notes.join("|").indexOf("dOneShort") < 0);

      run([{ plan: null }, { plan: null }, { out: 54 }, { out: 60 }], (bx4) => {
        ok("两遍都短 → 明说这一趟没写成，并指出稿子在哪、怎么重来", bx4.notes.join("|").indexOf("dOneShort") >= 0);
        ok("两遍都短也照样收口（不把面板吊死）", bx4.done === true);

        run([{ plan: null }, { plan: null }, { out: FLOOR + 1 }], (bx5) => {
          ok("单趟一遍就过下限 → 不重写", bx5.oneTries === 1);

          run([{ plan: null }, { plan: null }, { out: FLOOR - 1 }, { out: 5000 }], (bx6) => {
            ok("卡在下限下方一个字也算没写成（闸是硬的）", bx6.oneTries === 2);

            /* ═══ 一之二、骨架档：提纲垮了也不许退成"一趟写完" ══════════════
               真跑读数（2026-08-12 18:14）：提纲两趟都没成 → 退回一趟写完 → 交回 **55 字**。
               而这一档的十六节分工与字数本来就写死在体例表里。 */
            console.log("── 骨架档的退路 ──");
            const PAPER = { kind: "paper", chunked: { paper: 1 } };
            const BARE = { plan: { title: "T", sections: [{ h: "一", ask: "a", words: 1000 }] } };
            run([{ plan: null }, { plan: null }, BARE], (bx7) => {
              ok("★ 骨架档不退回一趟写完（一次单趟调用都没打）", bx7.oneTries === 0);
              ok("★ 改成向服务端要一份免调用的骨架（bare=1）", bx7.bare === 1);
              ok("拿到骨架就照常开写", !!bx7.started && bx7.started.sections.length === 1);
              ok("跟读者说清为什么不退成一趟写完", bx7.notes.join("|").indexOf("dPlanBare") >= 0);
              ok("不再报 dPlanFallback（那是自由分节档的话）", bx7.notes.join("|").indexOf("dPlanFallback") < 0);

              run([{ plan: null }, { plan: null }, { plan: null }], (bx8) => {
                ok("连骨架都没取回来 → 明说并收口，不吊死面板", bx8.done === true
                  && bx8.notes.join("|").indexOf("dPlanNo") >= 0);
                ok("这种时候也不去打单趟（别再拿两万字赌一次调用）", bx8.oneTries === 0);

                /* ★ 这就是 18:14 那份真跑的形状：提纲交回一个**数组** */
                run([{ plan: ["Kuhn 1962", "Polanyi 1966"] }, { plan: ["Kuhn 1962"] }, BARE], (bx9) => {
                  ok("★★ 提纲交回的是数组（没有 sections）⇒ 判为没成，不当它成了",
                    bx9.planTries === 2 && bx9.bare === 1 && !!bx9.started);
                  ok("★★ 数组这一种也不会静默退成一趟写完", bx9.oneTries === 0);
                  tail();
                }, PAPER);
              }, PAPER);
            }, PAPER);
          });
        });
      });
    });
  });
});

function tail() {
  /* ═══ 二、顶栏：换行 ＋ 按钮不缩 ＋ 状态不被压成一个字宽 ═══ */
  console.log("── 顶栏 ──");
  const css = (FSRC.match(/"\.wdsm-dist-top\{[^"]*"/) || [""])[0];
  ok("顶栏允许换行（塞不下就换一行，而不是把状态压扁）", /flex-wrap:wrap/.test(css));
  ok("顶栏里的按钮一律不许收缩", /"\.wdsm-dist-top \.wdsm-tbtn\{flex:0 0 auto\}"/.test(FSRC));
  const dstCss = (FSRC.match(/"\.wdsm-dist-top \.dst\{[^"]*"/) || [""])[0];
  ok("状态栏给了 min-width:0（否则 min-content 会把它顶成一个字宽）", /min-width:0/.test(dstCss));
  ok("状态栏不换行、超长用省略号收口", /white-space:nowrap/.test(dstCss) && /text-overflow:ellipsis/.test(dstCss));
  /* 行内 style 的优先级高于样式表——只改样式表是改不动的 */
  const inline = (FSRC.match(/<span class='dst' style='[^']*'/) || [""])[0];
  ok("★ 行内 style 也一并写全了（行内优先级更高，只改样式表等于没改）",
    /min-width:0/.test(inline) && /text-overflow:ellipsis/.test(inline));
  ok("行内不再是那个会被压扁的裸 flex:1", !/flex:1'/.test(inline));

  /* 顶栏上到底挂了几颗按钮——超过五颗就必须能换行，这条是上面那几条的由来 */
  const panel = FSRC.slice(FSRC.indexOf("    var wrap = el(\"div\", \"wdsm-dist\");"),
                           FSRC.indexOf("    /* ══ 关掉这个面板"));
  const n = (panel.match(/wdsm-tbtn/g) || []).length;
  console.log("     顶栏一带出现 wdsm-tbtn " + n + " 次");
  ok("按钮确实多到一行放不下（所以换行不是可选项）", n >= 6);

  console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}
