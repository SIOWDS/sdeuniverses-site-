/* WDS 附件解析器 —— 全部在读者自己的浏览器里跑，文件本身绝不上传本站。
 * 解析出来的纯文字才会随提问发往读者自选的基底（他自己的 Key、他自己的账单）。
 *
 * 用法：
 *   WDSAttach.load(function (A) {           // A 为 null 表示这台浏览器跑不了（很旧的内核）
 *     A.pick({ multiple: true, onProgress: fn }).then(function (docs) { ... });
 *   });
 *   docs = [{ name, text, note }]
 *
 * 依赖全部懒加载（点了附件才拉）：pdf.js / mammoth / tesseract.js。
 * 与 /taste/article-sde/ 内联的那套是同源思路的精简版；那页跑得好好的，没去动它。
 */
(function () {
  "use strict";
  if (window.WDSAttach) return;

  var CDN = {
    pdf: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
    pdfWorker: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js",
    mammoth: "https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js",
    tesseract: "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js",
  };
  var MAX_CHARS = 120000;     // 单篇上限（后端还会再钳一次，这里只是别把浏览器撑爆）
  var OCR_MAX_PAGES = 20;     // 扫描件兜底只 OCR 前若干页——再多读者早不耐烦了
  var loaded = {};

  function script(src) {
    if (loaded[src]) return loaded[src];
    loaded[src] = new Promise(function (res, rej) {
      var s = document.createElement("script");
      s.src = src; s.async = true;
      s.onload = function () { res(true); };
      s.onerror = function () { rej(new Error("加载失败：" + src)); };
      document.head.appendChild(s);
    });
    return loaded[src];
  }
  function needPdf() {
    return script(CDN.pdf).then(function () {
      if (!window.pdfjsLib) throw new Error("PDF 解析库没起来");
      try { window.pdfjsLib.GlobalWorkerOptions.workerSrc = CDN.pdfWorker; } catch (e) {}
      return window.pdfjsLib;
    });
  }
  function needMammoth() { return script(CDN.mammoth).then(function () { if (!window.mammoth) throw new Error("Word 解析库没起来"); return window.mammoth; }); }
  function needTess() { return script(CDN.tesseract).then(function () { if (!window.Tesseract) throw new Error("OCR 库没起来"); return window.Tesseract; }); }

  function clean(s) {
    return String(s || "")
      .replace(/\r\n?/g, "\n")
      .replace(/[ \t\u00a0]+/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }
  function readBuf(file) {
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(r.result); };
      r.onerror = function () { rej(new Error("读不出这个文件")); };
      r.readAsArrayBuffer(file);
    });
  }
  function readText(file) {
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(String(r.result || "")); };
      r.onerror = function () { rej(new Error("读不出这个文件")); };
      r.readAsText(file, "utf-8");
    });
  }

  /* ── PDF：先抽文字层；文字层几乎空（扫描件）才退到 OCR ── */
  function pdfText(ab, prog) {
    return needPdf().then(function (lib) {
      return lib.getDocument({ data: ab }).promise.then(function (pdf) {
        var n = pdf.numPages, parts = [], i = 1;
        function step() {
          if (i > n) return Promise.resolve(parts.join("\n\n"));
          if (prog) prog("抽取", i, n);
          return pdf.getPage(i).then(function (pg) {
            return pg.getTextContent().then(function (tc) {
              var last = null, line = [], out = [];
              tc.items.forEach(function (it) {
                var y = it.transform && it.transform[5];
                if (last !== null && Math.abs(y - last) > 3) { out.push(line.join("")); line = []; }
                line.push(it.str);
                last = y;
              });
              if (line.length) out.push(line.join(""));
              parts.push(out.join("\n"));
              i++;
              return step();
            });
          });
        }
        return step().then(function (txt) {
          if (clean(txt).length >= 200) return { text: txt, note: n + " 页" };
          // 文字层是空的 —— 扫描件。别在这里投降，转 OCR。
          return ocrPdf(pdf, Math.min(n, OCR_MAX_PAGES), prog).then(function (o) {
            return { text: o, note: n + " 页 · 扫描件，已用本机 OCR 读前 " + Math.min(n, OCR_MAX_PAGES) + " 页" };
          });
        });
      });
    });
  }
  function ocrPdf(pdf, pages, prog) {
    return needTess().then(function (T) {
      var parts = [], i = 1;
      function step() {
        if (i > pages) return Promise.resolve(parts.join("\n\n"));
        if (prog) prog("OCR", i, pages);
        return pdf.getPage(i).then(function (pg) {
          var vp = pg.getViewport({ scale: 2 });
          var cv = document.createElement("canvas");
          cv.width = vp.width; cv.height = vp.height;
          return pg.render({ canvasContext: cv.getContext("2d"), viewport: vp }).promise.then(function () {
            return T.recognize(cv, "chi_sim+eng").then(function (r) {
              parts.push(((r && r.data && r.data.text) || "").trim());
              i++;
              return step();
            });
          });
        });
      }
      return step();
    });
  }
  // 图片读成 data URL：这串会原样发给视觉档（本站不留存、也不经过本站）
  function readDataURL(file) {
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(String(r.result || "")); };
      r.onerror = function () { rej(new Error("图片读不出来")); };
      r.readAsDataURL(file);
    });
  }
  // 按需 OCR：传 data URL 即可（tesseract 认这个），用在"这家基底看不了图"的退路上
  function ocrDataUrl(d) {
    return needTess().then(function (T) {
      return T.recognize(d, "chi_sim+eng").then(function (r) { return ((r && r.data && r.data.text) || "").trim(); });
    });
  }
  function ocrImage(file, prog) {
    return needTess().then(function (T) {
      if (prog) prog("OCR", 1, 1);
      return T.recognize(file, "chi_sim+eng").then(function (r) { return ((r && r.data && r.data.text) || "").trim(); });
    });
  }

  function parseFile(file, prog) {
    var name = file.name || "未命名";
    var low = name.toLowerCase();
    var P;
    if (/\.(txt|md|markdown|csv|json|log)$/.test(low)) P = readText(file).then(function (t) { return { text: t, note: "" }; });
    else if (/\.docx$/.test(low)) {
      P = readBuf(file).then(function (ab) {
        return needMammoth().then(function (M) {
          return M.extractRawText({ arrayBuffer: ab }).then(function (r) { return { text: (r && r.value) || "", note: "Word" }; });
        });
      });
    } else if (/\.pdf$/.test(low)) P = readBuf(file).then(function (ab) { return pdfText(ab, prog); });
    else if (/\.(png|jpe?g|webp|bmp|gif)$/.test(low)) P = readDataURL(file).then(function (d) { return { text: "", note: "图片", img: d }; });
    else if (/\.doc$/.test(low)) P = Promise.reject(new Error("旧版 .doc 读不了，请在 Word 里另存为 .docx 再上传"));
    else P = readText(file).then(function (t) { return { text: t, note: "按纯文本读" }; });

    return P.then(function (r) {
      var t = clean(r.text);
      // 图片没有文字是正常的（它本来就不是拿来读字的），不能按"读不出文字"退回
      if (r.img) return { name: name, text: t, note: r.note || "图片", img: r.img };
      if (!t) throw new Error("这个文件里没读出文字");
      var cut = t.length > MAX_CHARS;
      return { name: name, text: cut ? t.slice(0, MAX_CHARS) : t, note: (r.note || "") + (cut ? " · 太长，只取了前 " + MAX_CHARS + " 字" : "") };
    });
  }

  // 弹文件选择框 → 逐个解析。单个失败不连坐，其余照常返回，失败的挂在 .failed 上。
  function pick(opts) {
    opts = opts || {};
    return new Promise(function (res) {
      var inp = document.createElement("input");
      inp.type = "file";
      inp.accept = ".txt,.md,.markdown,.csv,.json,.log,.docx,.pdf,.png,.jpg,.jpeg,.webp,.bmp,.gif";
      if (opts.multiple !== false) inp.multiple = true;
      inp.style.cssText = "position:fixed;left:-9999px;top:0";
      document.body.appendChild(inp);
      inp.onchange = function () {
        var files = Array.prototype.slice.call(inp.files || []).slice(0, 5);
        if (inp.parentNode) inp.parentNode.removeChild(inp);
        if (!files.length) { res([]); return; }
        var out = [], failed = [], i = 0;
        function step() {
          if (i >= files.length) { out.failed = failed; res(out); return; }
          var f = files[i];
          parseFile(f, function (phase, a, b) { if (opts.onProgress) opts.onProgress(f.name, phase, a, b); })
            .then(function (d) { out.push(d); })
            .catch(function (e) { failed.push({ name: f.name, msg: (e && e.message) || "解析失败" }); })
            .then(function () { i++; step(); });
        }
        if (opts.onProgress) opts.onProgress(files[0].name, "准备", 0, files.length);
        step();
      };
      inp.click();
    });
  }

  /* ── 长文切块与按问题取段 ──
     全在浏览器里算，不额外调基底、不产生费用。
     中文没有空格可切词，所以用**字符二元组**做重合度，比按词切稳当得多。 */
  var CHUNK = 700, OVERLAP = 100;
  function chunk(text) {
    var t = String(text || ""), out = [], i = 0, n = 0;
    while (i < t.length) {
      var end = Math.min(i + CHUNK, t.length);
      // 尽量切在句末，别把一句话拦腰截断
      if (end < t.length) {
        var win = t.slice(end - 120, end), p = Math.max(win.lastIndexOf("。"), win.lastIndexOf("！"), win.lastIndexOf("？"), win.lastIndexOf("\n"));
        if (p > 20) end = end - 120 + p + 1;
      }
      out.push({ i: n++, t: t.slice(i, end) });
      if (end >= t.length) break;
      i = Math.max(end - OVERLAP, i + 1);
    }
    return out;
  }
  function bigrams(s) {
    var c = String(s || "").replace(/[\s\p{P}]+/gu, ""), set = Object.create(null);
    for (var i = 0; i + 1 < c.length; i++) set[c.slice(i, i + 2)] = 1;
    return set;
  }
  // 按问题挑段：始终先给开头（让它知道这是篇什么），再按重合度补相关段，最后按原文顺序排好
  function selectChunks(chunks, query, budget) {
    if (!chunks.length) return { text: "", take: 0, total: 0 };
    var q = bigrams(query), qn = 0, k;
    for (k in q) qn++;
    var scored = chunks.map(function (c) {
      var b = bigrams(c.t), hit = 0, x;
      for (x in q) if (b[x]) hit++;
      return { c: c, s: qn ? hit / Math.sqrt(c.t.length + 40) : 0 };
    });
    scored.sort(function (a, b) { return b.s - a.s; });
    var picked = {}, used = 0;
    picked[0] = 1; used += chunks[0].t.length;                 // 开头永远带上
    for (var j = 0; j < scored.length && used < budget; j++) {
      var ci = scored[j].c.i;
      if (picked[ci] || scored[j].s <= 0) continue;
      if (used + scored[j].c.t.length > budget) continue;
      picked[ci] = 1; used += scored[j].c.t.length;
    }
    var idxs = Object.keys(picked).map(Number).sort(function (a, b) { return a - b; });
    var text = idxs.map(function (i) { return "〔第 " + (i + 1) + " 段 / 共 " + chunks.length + " 段〕\n" + chunks[i].t; }).join("\n\n");
    return { text: text, take: idxs.length, total: chunks.length };
  }

  var API = { pick: pick, parseFile: parseFile, MAX_CHARS: MAX_CHARS, chunk: chunk, selectChunks: selectChunks, ocrDataUrl: ocrDataUrl };
  window.WDSAttach = {
    load: function (cb) {
      var okEnv = !!(window.FileReader && window.Promise);
      try { cb(okEnv ? API : null); } catch (e) {}
    },
    api: API,
  };
})();
