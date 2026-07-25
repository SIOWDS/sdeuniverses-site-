// 新增一篇解构：在数组顶部加一行对象（含中英字段）即可，卡片自动并列生成。
  window.__DECONSTRUCTIONS__ = [
    {
      chip:"第三篇 · 黑格尔", chipEn:"No.3 · Hegel",
      title:"黑格尔造出了那台引擎，却把它锁进了一个圆",
      titleEn:"Hegel Built the Engine, Then Locked It in a Circle",
      hook:"他是最像「发生」的人——造出了矛盾驱动、自我推进的辩证法引擎，说对了「生成高于存在」。可他杀死了发生的混沌与介生、只供养秩序，把引擎锁进一个「完全清楚」的圆。他差的，只是一个字：开。",
      hookEn:"The thinker who came closest to \u2018genesis\u2019 \u2014 he built a self-driving dialectical engine and rightly held that becoming outranks being. Yet he killed off chaos and the liminal, feeding only order, and locked the engine inside a fully-transparent circle. He lacked just one thing: an opening.",
      words:"约 3 万字 · 三种读法", wordsEn:"~30,000 chars · 3 reading modes",
      slug:"deconstructing-hegel", pdf:"deconstructing-hegel.pdf"
    },
    {
      chip:"第一篇 · 福柯", chipEn:"No.1 · Foucault",
      title:"福柯站到了悬崖边，却没有桥",
      titleEn:"Foucault Reached the Cliff\u2019s Edge, but Had No Bridge",
      hook:"他是离「发生」最近的人——证明主体是被生产的结果，却缺三样东西：判权力的尺子、组织权力的坐标、反抗的「我」从何而来。本文在他的悬崖上，架起三座桥。",
      hookEn:"The thinker nearest to \u2018genesis\u2019 \u2014 he proved the subject is a produced result, but lacked three things: a ruler to judge power, coordinates to organize it, and where the resisting \u2018I\u2019 comes from. This essay builds three bridges on his cliff.",
      words:"约 3 万字 · 三种读法", wordsEn:"~30,000 chars · 3 reading modes",
      slug:"deconstructing-foucault", pdf:"deconstructing-foucault.pdf"
    },
    {
      chip:"第二篇 · 尼采", chipEn:"No.2 · Nietzsche",
      title:"解构尼采：视角主义的错误",
      titleEn:"Deconstructing Nietzsche: The Error of Perspectivism",
      hook:"你以为你在「选一个角度」看杯子——尼采把这一秒的错觉，盖成了一整座权力哲学。断口，在第二步。",
      hookEn:"You think you\u2019re \u2018choosing an angle\u2019 to view a cup \u2014 Nietzsche built a whole philosophy of power on that split-second illusion. The break is at the second step.",
      words:"约 2 万字 · 三种读法", wordsEn:"~20,000 chars · 3 reading modes",
      slug:"nietzsche-perspectivism", pdf:"nietzsche-perspectivism.pdf"
    }
  ];

  (function(){
    var data = window.__DECONSTRUCTIONS__ || [];
    var grid = document.getElementById('masters-grid');
    if(!grid) return;
    function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
    function bi(zh,en){ return '<span class="zh-only">'+esc(zh)+'</span><span class="en-only">'+esc(en)+'</span>'; }
    var html = data.map(function(d, idx){
      var base = '/column/' + d.slug + '/';
      var newTag = idx===0 ? '<span class="m-new zh-only">最新</span><span class="m-new en-only">Latest</span>' : '';
      return ''
        + '<article class="m-card">'
        +   '<div class="m-chip">' + bi(d.chip,d.chipEn) + newTag + '</div>'
        +   '<h3 class="m-title">' + bi(d.title,d.titleEn) + '</h3>'
        +   '<p class="m-hook">' + bi(d.hook,d.hookEn) + '</p>'
        +   '<div class="m-words">' + bi(d.words,d.wordsEn) + '</div>'
        +   '<div class="m-btns">'
        +     '<a class="m-btn primary" href="' + base + '">' + bi('📖 长文阅读','📖 Read Long-form') + '</a>'
        +     '<a class="m-btn ghost" href="' + base + 'read.html">' + bi('📄 在线 PDF 阅读','📄 Read PDF Online') + '</a>'
        +     '<a class="m-btn ghost" href="' + base + esc(d.pdf) + '" download>' + bi('⬇ 下载阅读','⬇ Download') + '</a>'
        +   '</div>'
        + '</article>';
    }).join('');
    grid.innerHTML = html;
  })();
