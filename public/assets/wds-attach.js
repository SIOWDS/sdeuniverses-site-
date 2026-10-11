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
  var MAX_CHARS = 400000;     // 单篇文字上限 40 万字（2026-10-10 王德生令由 20 万提到 40 万：20 万汉字的专著连标点约 22 万字符，原上限会截掉书尾；与后端「全篇全带」上限 DOC_CAP 400000 一致。后端仍按每轮预算取段）
  /* 文件大小（2026-10-11 王德生报「输入 100M 就不行了」）：原先一刀切 100 MB 拒收。
     书稿文件大，几乎全是图片——文字本身不过几 MB。所以改成按格式分开算：
       · Word：只从压缩包里单独取出正文那一块来解压（docxFast），图片一字节不读，文件多大都不怕；
       · 纯文本：只读开头够 40 万字的那一段；
       · PDF：大文件按需分段读（不整份载入内存），抽够 40 万字就停；整份载入的退路仍设上限。 */
  var MAX_BYTES = 2 * 1024 * 1024 * 1024;     // 2 GB：浏览器 File 再大就不稳了
  var PDF_BUF_MAX = 600 * 1024 * 1024;        // PDF 整份载入内存的退路上限
  var BIG_PDF = 60 * 1024 * 1024;             // 超过它先试分段读
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
    // 40 万字 × 每字至多 4 字节，再留余量给空白与换行：只读这一段，几百 MB 的文本也不卡
    var cap = MAX_CHARS * 4 + 65536;
    var part = (file && file.size > cap && file.slice) ? file.slice(0, cap) : file;
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(String(r.result || "").replace(/\uFFFD$/, "")); };
      r.onerror = function () { rej(new Error("读不出这个文件")); };
      r.readAsText(part, "utf-8");
    });
  }
  function readSlice(file, a, b) {
    var part = file.slice(a, b);
    if (part.arrayBuffer) return part.arrayBuffer().then(function (ab) { return new Uint8Array(ab); });
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(new Uint8Array(r.result)); };
      r.onerror = function () { rej(new Error("读不出这个文件")); };
      r.readAsArrayBuffer(part);
    });
  }

  /* ── Word 快读：.docx 是个 zip。从文件尾读中央目录，找到 word/document.xml，
       只把这一块切下来解压（浏览器自带 DecompressionStream），再从 XML 里抽字。
       图片、字体、嵌入对象一律不碰——100 MB、500 MB 的书稿和 1 MB 的读起来一样快。
       任何一步不认（zip64、加密、浏览器太旧）就抛错，由调用处回落到 mammoth。 */
  function u16(b, o) { return b[o] | (b[o + 1] << 8); }
  function u32(b, o) { return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0; }
  function inflateRaw(bytes) {
    if (typeof DecompressionStream === "undefined") return Promise.reject(new Error("no DecompressionStream"));
    var ds = new DecompressionStream("deflate-raw");
    var out = new Blob([bytes]).stream().pipeThrough(ds);
    return new Response(out).arrayBuffer().then(function (ab) { return new Uint8Array(ab); });
  }
  function zipEntry(file, want) {
    var size = file.size, tailLen = Math.min(size, 65557);
    return readSlice(file, size - tailLen, size).then(function (tail) {
      var e = -1;
      for (var i = tail.length - 22; i >= 0; i--) if (u32(tail, i) === 0x06054b50) { e = i; break; }
      if (e < 0) throw new Error("not a zip");
      var cdSize = u32(tail, e + 12), cdOff = u32(tail, e + 16);
      if (cdOff === 0xFFFFFFFF || cdSize === 0xFFFFFFFF) throw new Error("zip64");
      return readSlice(file, cdOff, cdOff + cdSize);
    }).then(function (cd) {
      var p = 0, dec = new TextDecoder("utf-8"), hit = null;
      while (p + 46 <= cd.length && u32(cd, p) === 0x02014b50) {
        var flags = u16(cd, p + 8), method = u16(cd, p + 10), csize = u32(cd, p + 20);
        var nl = u16(cd, p + 28), xl = u16(cd, p + 30), cl = u16(cd, p + 32), loff = u32(cd, p + 42);
        var name = dec.decode(cd.subarray(p + 46, p + 46 + nl));
        if (want.test(name)) { hit = { flags: flags, method: method, csize: csize, loff: loff, name: name }; break; }
        p += 46 + nl + xl + cl;
      }
      if (!hit) throw new Error("no " + want);
      if (hit.flags & 1) throw new Error("encrypted");
      if (hit.csize === 0xFFFFFFFF || hit.loff === 0xFFFFFFFF) throw new Error("zip64");
      return readSlice(file, hit.loff, hit.loff + 30).then(function (lh) {
        if (u32(lh, 0) !== 0x04034b50) throw new Error("bad local header");
        var start = hit.loff + 30 + u16(lh, 26) + u16(lh, 28);
        return readSlice(file, start, start + hit.csize);
      }).then(function (raw) {
        if (hit.method === 0) return raw;
        if (hit.method === 8) return inflateRaw(raw);
        throw new Error("method " + hit.method);
      });
    });
  }
  var ENT = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" };
  function xmlUnesc(s) {
    return s.replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos);/gi, function (m, k) {
      if (k[0] === "#") { var n = k[1] === "x" || k[1] === "X" ? parseInt(k.slice(2), 16) : parseInt(k.slice(1), 10); try { return String.fromCodePoint(n); } catch (e) { return ""; } }
      return ENT[k.toLowerCase()] || m;
    });
  }
  // document.xml → 纯文字：段落之间空一行（与 mammoth.extractRawText 同样的分段），制表符、换行照留；
  // 修订里删掉的字（w:delText）、域代码（w:instrText）不算正文；文本框的「旧版兜底」副本（mc:Fallback）去掉免得重复。
  function docxXmlText(xml) {
    xml = xml.replace(/<mc:Fallback\b[\s\S]*?<\/mc:Fallback>/g, "");
    var out = [], para = "", re = /<w:t(?=[\s>\/])[^>]*?(?:\/>|>([^<]*)<\/w:t>)|<w:tab\/>|<w:(?:br|cr)\b[^>]*\/>|<\/w:p>/g, m;
    while ((m = re.exec(xml))) {
      var s = m[0];
      if (s === "</w:p>") { out.push(para); para = ""; }
      else if (s.charCodeAt(3) === 116 && s.charCodeAt(4) === 97) para += "\t";      // <w:tab/>
      else if (s.indexOf("<w:t") === 0 && s.indexOf("<w:tab") !== 0) para += m[1] ? xmlUnesc(m[1]) : "";
      else para += "\n";
    }
    if (para) out.push(para);
    return out.join("\n\n");
  }
  function docxFast(file) {
    return zipEntry(file, /^word\/document\d*\.xml$/).then(function (bytes) {
      return docxXmlText(new TextDecoder("utf-8").decode(bytes));
    });
  }

  /* ── PDF：先抽文字层；文字层几乎空（扫描件）才退到 OCR ── */
  // 大 PDF 不整份载入：给 pdf.js 一个本机 blob 网址，按需分段读（disableAutoFetch）；不支持就回落整份载入
  function pdfOpen(lib, file) {
    function byBuf() {
      if (file.size > PDF_BUF_MAX) return Promise.reject(new Error("PDF 太大（超过 600 MB），这台浏览器分段读不了它；请在 PDF 软件里另存一份不含图片的，或导出成 Word/文本再传"));
      return readBuf(file).then(function (ab) { return lib.getDocument({ data: new Uint8Array(ab) }).promise; });
    }
    if (file.size <= BIG_PDF || typeof URL === "undefined" || !URL.createObjectURL) return byBuf();
    var url = URL.createObjectURL(file);
    return lib.getDocument({ url: url, disableAutoFetch: true, disableStream: true, rangeChunkSize: 1048576 }).promise
      .then(function (pdf) { pdf._wdsUrl = url; return pdf; },
            function () { try { URL.revokeObjectURL(url); } catch (e) {} return byBuf(); });
  }
  function pdfText(file, prog) {
    return needPdf().then(function (lib) {
      return pdfOpen(lib, file).then(function (pdf) {
        var n = pdf.numPages, parts = [], i = 1, got = 0, stopAt = 0;
        function finish(x) { if (pdf._wdsUrl) { try { URL.revokeObjectURL(pdf._wdsUrl); } catch (e) {} } return x; }
        function step() {
          if (i > n || got > MAX_CHARS * 1.1) { if (i <= n) stopAt = i - 1; return Promise.resolve(parts.join("\n\n")); }
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
              var pt = out.join("\n"); parts.push(pt); got += pt.length;
              try { pg.cleanup(); } catch (e) {}
              i++;
              return step();
            });
          });
        }
        return step().then(function (txt) {
          if (clean(txt).length >= 200) return finish({ text: txt, note: n + " 页" + (stopAt ? (" · 读到第 " + stopAt + " 页已满 40 万字") : "") });
          // 文字层是空的 —— 扫描件。别在这里投降，转 OCR。
          return ocrPdf(pdf, Math.min(n, OCR_MAX_PAGES), prog).then(function (o) {
            return finish({ text: o, note: n + " 页 · 扫描件，已用本机 OCR 读前 " + Math.min(n, OCR_MAX_PAGES) + " 页" });
          });
        }, function (e) { finish(); throw e; });
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
    if (file && file.size > MAX_BYTES) return Promise.reject(new Error("文件太大（超过 2 GB），浏览器读不动；请拆成几份再传"));
    var low = name.toLowerCase();
    var P;
    if (/\.(txt|md|markdown|csv|json|log)$/.test(low)) P = readText(file).then(function (t) { return { text: t, note: "" }; });
    else if (/\.docx$/.test(low)) {
      var mb = file.size / 1048576;
      if (prog) prog("读取正文", 0, 1);
      P = docxFast(file).then(function (t) {
        if (!clean(t)) throw new Error("empty");
        return { text: t, note: "Word" + (mb >= 20 ? (" · " + Math.round(mb) + " MB，只读正文、未读图片") : "") };
      }).catch(function () {
        // 快读不认这份（zip64、旧浏览器等）：回落 mammoth 整份读，但太大的整份读会卡死浏览器，宁可早说
        if (file.size > 300 * 1048576) throw new Error("这份 Word 太大（" + Math.round(mb) + " MB），这台浏览器读不了；请用新版 Chrome／Edge，或在 Word 里删掉图片另存一份再传");
        return readBuf(file).then(function (ab) {
          return needMammoth().then(function (M) {
            return M.extractRawText({ arrayBuffer: ab }).then(function (r) { return { text: (r && r.value) || "", note: "Word" }; });
          });
        });
      });
    } else if (/\.pdf$/.test(low)) P = pdfText(file, prog);
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

  var API = { _docxXmlText: docxXmlText, _docxFast: docxFast, pick: pick, parseFile: parseFile, MAX_CHARS: MAX_CHARS, chunk: chunk, selectChunks: selectChunks, ocrDataUrl: ocrDataUrl };
  window.WDSAttach = {
    load: function (cb) {
      var okEnv = !!(window.FileReader && window.Promise);
      try { cb(okEnv ? API : null); } catch (e) {}
    },
    api: API,
  };
})();
