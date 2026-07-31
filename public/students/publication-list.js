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
      ".sde-current-works{--pl-gold:#8a6817;--pl-ink:#2a2315;--pl-muted:#786b50;--pl-line:rgba(138,104,23,.25);max-width:920px;margin:48px auto 26px;padding:0 24px;font-family:\"Noto Serif SC\",\"Songti SC\",Georgia,serif;color:var(--pl-ink)}" +
      ".sde-cw-shell{position:relative;overflow:hidden;border:1px solid var(--pl-line);border-radius:20px;background:radial-gradient(circle at 90% 10%,rgba(200,145,23,.12),transparent 34%),linear-gradient(145deg,rgba(255,255,255,.76),rgba(239,231,211,.78));box-shadow:0 22px 60px rgba(73,52,10,.08);padding:34px clamp(20px,4vw,42px)}" +
      ".sde-cw-top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.sde-cw-count{flex:none;min-width:96px;text-align:center;border-left:1px solid var(--pl-line);padding-left:22px}.sde-cw-count b{display:block;color:var(--pl-gold);font:700 34px/1 Georgia,serif}.sde-cw-count span{display:block;margin-top:8px;color:var(--pl-muted);font-size:11px;letter-spacing:.12em}" +
      ".sde-cw-title{margin:9px 0 0;font-size:clamp(25px,4vw,36px);line-height:1.35;letter-spacing:.05em}.sde-cw-lead{margin-top:18px;color:var(--pl-muted);font-size:15px;line-height:2;text-align:justify}" +
      ".sde-cw-themes{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.sde-cw-theme{border:1px solid var(--pl-line);border-radius:99px;padding:5px 11px;color:var(--pl-gold);background:rgba(255,255,255,.45);font-size:11px;letter-spacing:.04em}" +
      ".sde-cw-featured{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:24px}.sde-cw-featured a{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:76px;border-top:1px solid var(--pl-line);padding:13px 4px;color:var(--pl-ink);text-decoration:none;font-size:13px;font-weight:700;line-height:1.55}.sde-cw-featured a:hover{color:var(--pl-gold)}" +
      ".sde-cw-action{display:inline-block;margin-top:20px;color:var(--pl-gold);text-decoration:none;font-size:13px;font-weight:700;letter-spacing:.08em;border-bottom:1px solid var(--pl-line);padding-bottom:3px}" +
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
      ".sde-pl-summary{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;margin-top:5px;color:var(--pl-muted);font-size:12.5px;line-height:1.7;letter-spacing:.015em}" +
      ".sde-pl-kind{display:block;margin-top:5px;color:var(--pl-gold);font-size:10.5px;line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.78}" +
      ".sde-pl-arrow{font:18px/1 Georgia,serif;color:var(--pl-gold);text-align:right}" +
      ".sde-pl-empty{padding:28px 0;text-align:center;color:var(--pl-muted);font-size:14px}" +
      "@media(max-width:700px){.sde-current-works{padding:0 15px}.sde-cw-shell{padding:28px 20px}.sde-cw-featured{grid-template-columns:1fr}.sde-cw-top{align-items:flex-start}.sde-cw-count{min-width:72px;padding-left:14px}.sde-cw-count b{font-size:28px}}" +
      "@media(max-width:600px){.sde-publication-list{padding:0 15px;margin-top:34px}.sde-pl-shell{padding:28px 18px 22px;border-radius:15px}.sde-pl-head{align-items:flex-start;flex-direction:column;gap:7px}.sde-pl-link{grid-template-columns:56px minmax(0,1fr) 16px;gap:8px}.sde-pl-kind{display:none}.sde-pl-summary{font-size:12px;line-height:1.65}.sde-pl-list{max-height:620px}}";
    document.head.appendChild(style);
  }

  function chineseNumber(value) {
    var digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
    // 百位以上必须单独处理：原先只写到两位数，作品过百之后 Math.floor(value/10)
    // 会取到 digits[10] === undefined，列单上就出现「之undefined十七」。
    if (value >= 100) {
      var hundreds = Math.floor(value / 100);
      var rest = value % 100;
      var head = digits[hundreds] + "百";
      if (rest === 0) return head;                                  // 100 → 一百
      if (rest < 10) return head + "零" + digits[rest];             // 107 → 一百零七
      var t = Math.floor(rest / 10), o = rest % 10;                 // 117 → 一百一十七
      return head + digits[t] + "十" + (o ? digits[o] : "");
    }
    if (value < 10) return digits[value];
    if (value === 10) return "十";
    if (value < 20) return "十" + digits[value % 10];
    var tens = Math.floor(value / 10);
    var ones = value % 10;
    return digits[tens] + "十" + (ones ? digits[ones] : "");
  }

  function render(student) {
    injectStyles();
    hideLegacyWorks(student.slug);
    var currentWorks = renderCurrentWorks(student);
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
        var summary = document.createElement("span");
        summary.className = "sde-pl-summary";
        summary.textContent = item.summary;
        var kind = document.createElement("span");
        kind.className = "sde-pl-kind";
        kind.textContent = item.kind;
        copy.appendChild(title);
        copy.appendChild(summary);
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
    if (footer && footer.parentNode) {
      footer.parentNode.insertBefore(currentWorks, footer);
      footer.parentNode.insertBefore(section, footer);
    } else {
      document.body.appendChild(currentWorks);
      document.body.appendChild(section);
    }
  }

  function hideLegacyWorks(slug) {
    if (slug === "qin-li" || slug === "he-lixia") return;
    var links = Array.prototype.slice.call(
      document.querySelectorAll('a[href="/students/' + slug + '/works/"],a[href="/students/' + slug + '/works"]')
    );
    if (!links.length) return;
    var first = links[0];
    var target = first.closest(".panel") || first.closest("a.works-entry") ||
      first.closest("a.works") || first.closest(".works");
    if (!target) return;
    target.hidden = true;
    var previous = target.previousElementSibling;
    if (previous && previous.classList.contains("level-tag")) previous.hidden = true;
  }

  function renderCurrentWorks(student) {
    var section = document.createElement("section");
    section.className = "sde-current-works";
    var shell = document.createElement("div");
    shell.className = "sde-cw-shell";
    var top = document.createElement("div");
    top.className = "sde-cw-top";
    var heading = document.createElement("div");
    heading.innerHTML = '<div class="sde-pl-eyebrow">CURRENT WORKS · 作品与专栏</div>' +
      '<h2 class="sde-cw-title">' + student.name + "的思想现场</h2>";
    var count = document.createElement("div");
    count.className = "sde-cw-count";
    count.innerHTML = "<b>" + student.count + "</b><span>篇已发表</span>";
    top.appendChild(heading);
    top.appendChild(count);
    shell.appendChild(top);
    var lead = document.createElement("p");
    lead.className = "sde-cw-lead";
    lead.textContent = student.promo.lead;
    shell.appendChild(lead);
    var themes = document.createElement("div");
    themes.className = "sde-cw-themes";
    student.promo.themes.forEach(function (value) {
      var chip = document.createElement("span");
      chip.className = "sde-cw-theme";
      chip.textContent = value;
      themes.appendChild(chip);
    });
    shell.appendChild(themes);
    var featured = document.createElement("div");
    featured.className = "sde-cw-featured";
    student.items.slice(0, 3).forEach(function (item) {
      var link = document.createElement("a");
      link.href = item.url;
      var label = document.createElement("span");
      label.textContent = item.title;
      var arrow = document.createElement("span");
      arrow.textContent = "→";
      link.appendChild(label);
      link.appendChild(arrow);
      featured.appendChild(link);
    });
    shell.appendChild(featured);
    var action = document.createElement("a");
    action.className = "sde-cw-action";
    action.href = "#sde-publication-list-title";
    action.textContent = "查看全部 " + student.count + " 篇作品 →";
    shell.appendChild(action);
    section.appendChild(shell);
    return section;
  }

    fetch("/students/publications.json?v=20260731-cy29")
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
