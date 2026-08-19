# -*- coding: utf-8 -*-
"""把「代码写法的数学」自动转成正式数学式。

用户令（配截图：`e^(i3θ) = cos3θ + i sin3θ`）：
「这些数学公式要能正式化，即 e^(i ..) 要正式数学化，目前是代码化。」

两层，缺一不可：
① **根子在提示词**——基底按键盘写法输出，前端再神也只能补救。所以 WDS_CHAT_SYS 里
   加一条硬性【数学写法】：一律 LaTeX，$…$ / $$…$$，指数写 e^{i3\\theta}。
② **前端兜底 texify()**——已经生成的对话、以及基底偶尔不听话的那几句，
   在 mdRender 里就地把键盘写法扶正成 $…$，交给 KaTeX 排。

⚠️ 兜底这一层最容易帮倒忙：一旦把普通句子误判成公式，整句会变成一串数学斜体。
   所以判据收得极紧——**一段文字里每一个英文词都必须是"单字母 / 已知函数名 / 希腊字母名"**，
   并且必须出现至少一个硬数学符号（^ √ ∫ ∑ ∏ ∞ ≤ ≥ ≠ × ÷ ·）或希腊字母。
   "The identity e^(iθ) is Euler's" 里有 identity/Euler 这种词 ⇒ 整段不碰。

幂等。
"""
import io, sys

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
if "function texify(" in h:
    print("already patched"); sys.exit(0)

def rep(old, new, what):
    global h
    assert h.count(old) == 1, "锚点不唯一/找不到：" + what + " (count=%d)" % h.count(old)
    h = h.replace(old, new)

TEXIFY = r'''
  /* ══════ 键盘写法的数学 → 正式数学式 ══════
     基底常把式子写成 `e^(i3θ) = cos3θ + i sin3θ`（代码写法）而不是 LaTeX。
     提示词里已经硬性要求写 LaTeX（见 worker 的 WDS_CHAT_SYS【数学写法】），
     这里是**兜底**：已经生成的旧对话、以及基底偶尔不听话的那几句，就地扶正。

     ⚠️ 这一层最容易帮倒忙——把普通句子误判成公式，整句会变成一串数学斜体。
     所以判据收得极紧，两条同时成立才动：
       ① 段内出现至少一个**硬数学符号**（^ √ ∫ ∑ ∏ ∞ ≤ ≥ ≠ × ÷ ·）或希腊字母；
       ② 段内**每一个英文词**都得是「单字母 / 已知函数名 / 希腊字母名」。
     ②是那道真正的闸：`The identity e^(iθ) is Euler's` 里有 identity、Euler，整段不碰。 */
  var TEX_GREEK = {
    "α": "\\alpha", "β": "\\beta", "γ": "\\gamma", "δ": "\\delta", "ε": "\\epsilon", "ζ": "\\zeta",
    "η": "\\eta", "θ": "\\theta", "ι": "\\iota", "κ": "\\kappa", "λ": "\\lambda", "μ": "\\mu",
    "ν": "\\nu", "ξ": "\\xi", "π": "\\pi", "ρ": "\\rho", "σ": "\\sigma", "τ": "\\tau",
    "υ": "\\upsilon", "φ": "\\phi", "χ": "\\chi", "ψ": "\\psi", "ω": "\\omega",
    "Γ": "\\Gamma", "Δ": "\\Delta", "Θ": "\\Theta", "Λ": "\\Lambda", "Ξ": "\\Xi", "Π": "\\Pi",
    "Σ": "\\Sigma", "Φ": "\\Phi", "Ψ": "\\Psi", "Ω": "\\Omega", "∇": "\\nabla", "∂": "\\partial",
  };
  var TEX_SYM = {
    "×": "\\times", "÷": "\\div", "·": "\\cdot", "≤": "\\le", "≥": "\\ge", "≠": "\\neq",
    "∞": "\\infty", "√": "\\sqrt", "∫": "\\int", "∑": "\\sum", "∏": "\\prod", "≈": "\\approx",
    "→": "\\to", "⇒": "\\Rightarrow", "∈": "\\in", "⊂": "\\subset", "±": "\\pm",
  };
  var TEX_FUNCS = ("sin cos tan cot sec csc sinh cosh tanh arcsin arccos arctan "
    + "log ln lg exp lim max min sup inf det dim deg gcd mod arg sqrt").split(" ");
  var TEX_GNAMES = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
    + "pi rho sigma tau upsilon phi chi psi omega").split(" ");
  function texWordOk(w) {
    var s = String(w).toLowerCase();
    if (s.length === 1) return true;                       // 单字母变量：e、i、x、n…
    if (TEX_FUNCS.indexOf(s) >= 0) return true;
    if (TEX_GNAMES.indexOf(s) >= 0) return true;
    if (/^d[a-z]$/.test(s)) return true;                   // 微分 dx、dt
    return false;
  }
  // 允许进入"公式段"的字符。**刻意不含** * _ ` \ : ; 这些 Markdown 或断句字符——
  // 含了就会跟 **加粗**、__下划__ 抢，而它们出现在真公式里的机会远小于出现在正文里。
  var TEX_SUP = { "\u00b9": "1", "\u00b2": "2", "\u00b3": "3", "\u2070": "0", "\u2074": "4", "\u2075": "5",
    "\u2076": "6", "\u2077": "7", "\u2078": "8", "\u2079": "9", "\u207a": "+", "\u207b": "-", "\u207f": "n" };
  var TEX_SUB = { "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3", "\u2084": "4", "\u2085": "5",
    "\u2086": "6", "\u2087": "7", "\u2088": "8", "\u2089": "9" };
  var TEX_CH = "A-Za-z0-9\u00b9\u00b2\u00b3\u2070\u2074-\u2079\u207a\u207b\u207f\u2080-\u2089"
    + "αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ∇∂()\\[\\]{}+\\-=<>^_*/,.'|√∫∑∏∞≤≥≠×÷·≈→⇒∈⊂± ";
  var TEX_RUN = new RegExp("[" + TEX_CH + "]{3,240}", "g");
  var TEX_HARD = /[\^√∫∑∏∞≤≥≠×÷·≈±\u00b9\u00b2\u00b3\u2070\u2074-\u2079\u207f\u2080-\u2089αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ∇∂]/;
  function texBody(x) {
    var s = String(x);
    // 上标/下标字符（³ ² ₁…）先折成 ^{3} / _{1}：它们在正文里极常见，留着 KaTeX 认不出
    s = s.replace(/[\u00b9\u00b2\u00b3\u2070\u2074-\u2079\u207a\u207b\u207f]+/g, function (r) {
      var o = ""; for (var i = 0; i < r.length; i++) o += TEX_SUP[r.charAt(i)] || "";
      return o ? ("^{" + o + "}") : "";
    }).replace(/[\u2080-\u2089]+/g, function (r) {
      var o = ""; for (var i = 0; i < r.length; i++) o += TEX_SUB[r.charAt(i)] || "";
      return o ? ("_{" + o + "}") : "";
    });
    s = s.replace(/\u221a\s*\(([^()]{1,60})\)/g, "\\sqrt{$1}").replace(/\u221a\s*([A-Za-z0-9]+)/g, "\\sqrt{$1}");
    s = s.split("*").join(" \\times ");
    for (var k in TEX_SYM) s = s.split(k).join(TEX_SYM[k] + " ");
    for (var g in TEX_GREEK) s = s.split(g).join(TEX_GREEK[g] + " ");
    s = s.replace(/\^\(([^()]{1,60})\)/g, function (m, c) { return "^{" + c + "}"; })
         .replace(/_\(([^()]{1,60})\)/g, function (m, c) { return "_{" + c + "}"; })
         .replace(/\^(-?[A-Za-z0-9\\]+)/g, function (m, c) { return "^{" + c + "}"; })
         .replace(/_(-?[A-Za-z0-9\\]+)/g, function (m, c) { return "_{" + c + "}"; });
    for (var i = 0; i < TEX_FUNCS.length; i++) {
      var f = TEX_FUNCS[i];
      s = s.replace(new RegExp("(^|[^A-Za-z\\\\])" + f + "(?![A-Za-z])", "g"), "$1\\" + f + " ");
    }
    // 命令后面那个占位空格只在"下一个字符还是字母"时才需要（\theta x），否则去掉——
    // 留着会长出 e^{i3\theta } 这种带空格的丑式子
    return s.replace(/\\([A-Za-z]+) +(?![A-Za-z0-9])/g, "\\$1")
            .replace(/\s+/g, " ").trim();
  }
  function texRun(raw) {
    var s = String(raw), lead = "", tail = "";
    var m = /^(\s*)([\s\S]*?)([\s.,]*)$/.exec(s);
    if (m) { lead = m[1]; s = m[2]; tail = m[3]; }
    if (s.length < 3 || s.length > 200) return null;
    if (s.indexOf("**") >= 0 || s.indexOf("__") >= 0) return null;   // 别跟 Markdown 抢
    if (!TEX_HARD.test(s)) return null;                    // 闸①：没有硬数学符号，不碰
    var words = s.match(/[A-Za-z]+/g) || [];
    for (var i = 0; i < words.length; i++) if (!texWordOk(words[i])) return null;   // 闸②
    if (!/[A-Za-z0-9]/.test(s)) return null;               // 纯符号（如一串箭头）不是公式
    return { lead: lead, body: texBody(s), tail: tail };
  }
  /* 对整段文字跑一遍。已经是 $…$／$$…$$ 的、以及代码桩 \u0000B/\u0000I，一律原样让路。 */
  function texify(src) {
    var s = String(src || "");
    if (s.indexOf("$") < 0 && !TEX_HARD.test(s)) return s;          // 绝大多数段落在这里就返回
    return s.replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\u0000[BI]\d+\u0000)|([^$\u0000]+)/g,
      function (m0, keep, plain, at) {
        if (keep) return keep;
        if (!plain) return m0;
        return plain.replace(TEX_RUN, function (run, off) {
          var r = texRun(run);
          if (!r) return run;
          /* 独占一行的式子排成块级（居中、单独一行），句子里的排成行内式。
             ⚠️ "独占一行"必须拿**原文**量，不能拿当前这一段量：一行里如果前面已经有
             一条 $…$，剩下的残段自己看起来就像"整行"，会把行内式误升成块级、把句子劈成两半。 */
          var abs = at + off;
          var ls = s.lastIndexOf("\n", abs) + 1;
          var le = s.indexOf("\n", abs); if (le < 0) le = s.length;
          var block = s.slice(ls, le).trim() === run.trim();
          return r.lead + (block ? ("$$" + r.body + "$$") : ("$" + r.body + "$")) + r.tail;
        });
      });
  }
'''

rep("  function mdRender(src) {\n", TEXIFY + "  function mdRender(src) {\n", "texify 定义")

rep("""    // ③ 摘公式（块级先摘，免得 $$ 被 $ 抢走）
    raw = raw.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, function (m, c) { return texStub(c, 1); })""",
    """    // ②之半 键盘写法的数学扶正成 $…$（必须排在代码摘除**之后**、公式摘除**之前**：
    //   之后＝代码块里的 x^2 不该被当公式；之前＝扶正出来的 $…$ 才能被下一步摘走）
    raw = texify(raw);
    // ③ 摘公式（块级先摘，免得 $$ 被 $ 抢走）
    raw = raw.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, function (m, c) { return texStub(c, 1); })""",
    "texify 接入点")

io.open(P, "wb").write(h.encode("utf-8"))
print("patched", P)
