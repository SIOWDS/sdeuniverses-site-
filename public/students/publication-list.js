(function () {
  "use strict";

  var slug = document.body && document.body.getAttribute("data-student-slug");
  if (!slug || document.querySelector(".sde-publication-list")) return;

  function injectStyles() {
    if (document.getElementById("sde-publication-list-style")) return;
    var style = document.createElement("style");
    style.id = "sde-publication-list-style";
    style.textContent =
      ".sde-publication-list{--pl-gold:#8a6817;--pl-ink:#2a2315;--pl-muted:#786b50;--pl-line:rgba(138,104,23,.25);max-width:920px;margin:46px auto 72px;padding:0 24px;font-family:\"Noto Serif SC\",\"Songti SC\",Georgia,serif;color:var(--pl-ink)}" +
      ".sde-pl-shell{position:relative;overflow:hidden;border:1px solid var(--pl-line);border-radius:20px;background:linear-gradient(145deg,rgba(255,255,255,.7),rgba(239,231,211,.72));box-shadow:0 22px 60px rgba(73,52,10,.08);padding:34px clamp(20px,4vw,42px) 30px}" +
      ".sde-pl-shell:before{content:\"\";position:absolute;inset:0 0 auto;height:4px;background:linear-gradient(90deg,transparent,var(--pl-gold),transparent)}" +
      ".sde-pl-eyebrow{color:var(--pl-gold);font:700 11px/1.4 Georgia,serif;letter-spacing:.34em;text-transform:uppercase}" +
      ".sde-pl-head{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin:11px 0 22px}" +
      ".sde-pl-title{font-size:clamp(26px,4vw,38px);line-height:1.25;margin:0;font-weight:800;letter-spacing:.06em}" +
      ".sde-pl-count{flex:none;color:var(--pl-gold);font-size:13px;letter-spacing:.08em}" +
      ".sde-pl-search{width:100%;border:1px solid var(--pl-line);border-radius:11px;background:rgba(255,255,255,.62);color:var(--pl-ink);font:14px/1.4 inherit;padding:12px 15px;margin:0 0 17px;outline:none}" +
      ".sde-pl-search:focus{border-color:var(--pl-gold);box-shadow:0 0 0 3px rgba(138,104,23,.1)}" +
      ".sde-pl-list{list-style:none;margin:0;padding:0;max-height:680px;overflow:auto;scrollbar-color:rgba(138,104,23,.35) transparent}" +
      ".sde-pl-item{border-top:1px solid var(--pl-line)}.sde-pl-item:first-child{border-top:0}" +
      ".sde-pl-link{display:grid;grid-template-columns:72px minmax(0,1fr) 24px;align-items:center;gap:13px;padding:14px 4px;text-decoration:none;color:inherit;transition:color .18s,transform .18s}" +
      ".sde-pl-link:hover{color:var(--pl-gold);transform:translateX(3px)}" +
      ".sde-pl-num{font:700 12px/1.4 Georgia,\"Noto Serif SC\",serif;color:var(--pl-gold);letter-spacing:.05em;white-space:nowrap}" +
      ".sde-pl-copy{min-width:0}.sde-pl-name{display:block;font-size:15px;font-weight:700;line-height:1.55}" +
      ".sde-pl-kind{display:block;margin-top:3px;color:var(--pl-muted);font-size:11px;line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
      ".sde-pl-arrow{font:18px/1 Georgia,serif;color:var(--pl-gold);text-align:right}" +
      ".sde-pl-empty{padding:28px 0;text-align:center;color:var(--pl-muted);font-size:14px}" +
      "@media(max-width:600px){.sde-publication-list{padding:0 15px;margin-top:34px}.sde-pl-shell{padding:28px 18px 22px;border-radius:15px}.sde-pl-head{align-items:flex-start;flex-direction:column;gap:7px}.sde-pl-link{grid-template-columns:56px minmax(0,1fr) 16px;gap:8px}.sde-pl-kind{display:none}.sde-pl-list{max-height:620px}}";
    document.head.appendChild(style);
  }

  function chineseNumber(value) {
    var digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
    if (value < 10) return digits[value];
    if (value === 10) return "十";
    if (value < 20) return "十" + digits[value % 10];
    var tens = Math.floor(value / 10);
    var ones = value % 10;
    return digits[tens] + "十" + (ones ? digits[ones] : "");
  }

  function render(student) {
    injectStyles();
    var section = document.createElement("section");
    section.className = "sde-publication-list";
    section.setAttribute("aria-labelledby", "sde-publication-list-title");

    var shell = document.createElement("div");
    shell.className = "sde-pl-shell";
    shell.innerHTML =
      '<div class="sde-pl-eyebrow">PUBLICATION LIST</div>' +
      '<div class="sde-pl-head"><h2 class="sde-pl-title" id="sde-publication-list-title">作品列单</h2>' +
      '<div class="sde-pl-count">共 ' + student.count + " 篇 · 点击标题阅读</div></div>";

    var search = document.createElement("input");
    search.className = "sde-pl-search";
    search.type = "search";
    search.placeholder = "检索标题或主题…";
    search.setAttribute("aria-label", "检索作品");
    if (student.items.length > 12) shell.appendChild(search);

    var list = document.createElement("ol");
    list.className = "sde-pl-list";
    shell.appendChild(list);
    section.appendChild(shell);

    function draw(query) {
      var normalized = (query || "").trim().toLowerCase();
      var visible = student.items.filter(function (item) {
        return !normalized || (item.title + " " + item.kind).toLowerCase().indexOf(normalized) !== -1;
      });
      list.textContent = "";
      visible.forEach(function (item) {
        var row = document.createElement("li");
        row.className = "sde-pl-item";
        var link = document.createElement("a");
        link.className = "sde-pl-link";
        link.href = item.url;
        var number = document.createElement("span");
        number.className = "sde-pl-num";
        number.textContent = "之" + chineseNumber(item.number);
        var copy = document.createElement("span");
        copy.className = "sde-pl-copy";
        var title = document.createElement("span");
        title.className = "sde-pl-name";
        title.textContent = item.title;
        var kind = document.createElement("span");
        kind.className = "sde-pl-kind";
        kind.textContent = item.kind;
        copy.appendChild(title);
        copy.appendChild(kind);
        var arrow = document.createElement("span");
        arrow.className = "sde-pl-arrow";
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "→";
        link.appendChild(number);
        link.appendChild(copy);
        link.appendChild(arrow);
        row.appendChild(link);
        list.appendChild(row);
      });
      if (!visible.length) {
        var empty = document.createElement("li");
        empty.className = "sde-pl-empty";
        empty.textContent = "没有找到匹配的作品";
        list.appendChild(empty);
      }
    }

    if (student.items.length > 12) {
      search.addEventListener("input", function () { draw(search.value); });
    }
    draw("");
    var footer = document.querySelector("footer");
    if (footer && footer.parentNode) footer.parentNode.insertBefore(section, footer);
    else document.body.appendChild(section);
  }

  fetch("/students/publications.json")
    .then(function (response) {
      if (!response.ok) throw new Error("Publication data unavailable");
      return response.json();
    })
    .then(function (data) {
      var student = data.students.find(function (entry) { return entry.slug === slug; });
      if (student) render(student);
    })
    .catch(function (error) {
      if (window.console) console.warn("[Publication List]", error);
    });
})();
