/* SDE 近邻闸 · 共用模块（window.SDENbr）
 *
 * 为什么要抽出来：这套判据现在有两个使用方——金点子发生器与中华智问。
 * 判据一旦被复制两份，就一定会漂：一边改了阈值另一边不知道，而这类失败是静默的
 * （论文照样产出、照样下载，只是某一关实际上没在把关，没有人会收到报错）。
 * 所以这里是唯一来源；页面内的同名函数只作为"模块没加载成功"时的兜底。
 *
 * 三关（任一不过就该补写那一节）：
 *   sectionOK(text)   —— 有没有做检测：该节存在 + 点名≥3 + 出现判决性预测
 *   postNameGap(text) —— 检测的是不是最后用的那个名字：抽出新命名，拿它再查一次站内近邻
 *   crossOK(text)     —— 三个近邻是不是全挤在同一学科：true / false / null(看不出→放行)
 *
 * 一条贯穿的取舍：**看不出就放行**。闸门冤枉一篇好论文的代价，比放过一篇没跨域的更大。
 */
(function (w) {
  'use strict';

  // ── 一、有没有做检测 ──
  function sectionOK(text) {
    const t = String(text || '');
    const m = t.match(/(近邻检测|最近邻[^\n]{0,12}(切割|检测|对质|判别)|近邻切割)[\s\S]{0,6000}/);
    if (!m) return false;
    const seg = m[0];
    // 点名以「(作者, 年份)」或「《作品》」计——一个该领域的人一听就知道指什么，才算点到。
    const named = (seg.match(/[（(]\s*[^）)]{0,30}(1[6-9]|20)\d{2}[^）)]{0,12}[）)]/g) || []).length
                + (seg.match(/《[^》]{2,40}》/g) || []).length;
    const hasPred = /(若|如果)[^\n]{0,80}(则本文|本文即错|本文错|本文不成立|说明本文)/.test(seg)
                 || /对照预测|判决性|可判定差异/.test(seg);
    return named >= 3 && hasPred;
  }

  // ── 二、检测的是不是最后用的那个名字 ──
  // 措辞比一条正则能装的杂得多，所以备几种；抽不出返回空串（宁可漏查，不可乱查）。
  function coinedName(text) {
    const t = String(text || '').slice(0, 20000);
    const pats = [
      /(?:本文|我)(?:将(?:其|这|之)?|把(?:它|这|其)?[^。\n]{0,12})?命名为[「“"《【]?([^」”"》】，。；\n]{2,14})/,
      /命名为[「“"《【]?([^」”"》】，。；\n]{2,14})/,
      /(?:本文|我)(?:提出|称(?:之为)?)[「“"《【]([^」”"》】]{2,14})/,
      /(?:把|将)(?:这一|这种|该|其)?[^。\n]{0,12}称(?:之)?为[「“"《【]?([^」”"》】，。；\n]{2,14})/,
      /(?:本文|我们|我)(?:据此|因此)?(?:提出|引入)[「“"《【]([^」”"》】]{2,14})/
    ];
    for (var i = 0; i < pats.length; i++) { var m = t.match(pats[i]); if (m && m[1]) return m[1].trim(); }
    return '';
  }
  async function postNameGap(text) {
    const name = coinedName(text);
    if (!name || !w.SDERag) return { name: '', block: '', missed: [] };
    var blk = '';
    try { blk = await w.SDERag.neighbors(name, { k: 6 }); } catch (e) { return { name: name, block: '', missed: [] }; }
    if (!blk) return { name: name, block: '', missed: [] };
    const titles = (blk.match(/《([^》]{2,60})》/g) || []).map(function (s) { return s.slice(1, -1); });
    const missed = [];
    for (var j = 0; j < titles.length; j++) {
      var head = titles[j].replace(/[：:—\-·].*$/, '').slice(0, 10);
      if (head && String(text).indexOf(head) < 0) missed.push(titles[j]);
    }
    return { name: name, block: blk, missed: missed };
  }

  // ── 三、三个近邻是不是全挤在同一学科 ──
  // 只放学科名，不放研究主题词：推断错一个学科就会冤枉一篇好论文。
  const DISC_HINTS = ['社会学', '心理学', '社会心理学', '认知心理学', '发展心理学', '人类学', '民族学', '经济学', '行为经济学',
    '管理学', '组织行为学', '法学', '法理学', '哲学', '伦理学', '现象学', '政治学', '历史学', '思想史', '教育学', '语言学',
    '传播学', '新闻学', '生理学', '病理学', '临床医学', '流行病学', '公共卫生', '神经科学', '生物学', '生态学', '营养学',
    '计算机科学', '人工智能', '统计学', '数学', '物理学', '工程学', '人因工程', '科学社会学', '知识社会学', '宗教学', '文学', '美学', '军事学'];
  function discTags(seg) {
    const s = String(seg || '');
    const own = (s.match(/本文所属学科\s*[：:]\s*([^\s，。；、（）()\n]{2,12})/) || [])[1] || '';
    const tags = (s.match(/[（(]\s*学科\s*[：:]\s*([^）)]{2,16})[）)]/g) || [])
      .map(function (x) { return (x.match(/学科\s*[：:]\s*([^）)]{2,16})/) || [])[1] || ''; })
      .map(function (x) { return x.trim(); }).filter(Boolean);
    return { own: own.trim(), tags: tags };
  }
  function crossOK(text) {
    const t = String(text || '');
    const m = t.match(/(近邻检测|最近邻[^\n]{0,12}(切割|检测|对质|判别)|近邻切割)[\s\S]{0,6000}/);
    if (!m) return null;
    const seg = m[0];
    const d = discTags(seg);
    if (d.tags.length >= 2) {
      const uniq = d.tags.filter(function (v, i) { return d.tags.indexOf(v) === i; });
      if (uniq.length >= 2) return true;
      if (d.own && uniq[0] && uniq[0] !== d.own) return true;
      return false;
    }
    const found = DISC_HINTS.filter(function (x) { return seg.indexOf(x) >= 0; });
    const uniq2 = found.filter(function (v, i) { return found.indexOf(v) === i; });
    if (uniq2.length >= 2) return true;
    if (uniq2.length === 0) return null;
    return d.own ? (uniq2[0] !== d.own ? true : false) : null;
  }

  // ── 三关合一：给调用方一个判定 ──
  // 返回 {need:Boolean, why:String, name, block}。why 用于状态栏，让用户看得见是哪一关没过。
  async function verdict(text) {
    if (!text) return { need: false, why: '', name: '', block: '' };
    const okSec = sectionOK(text);
    var pn = { name: '', block: '', missed: [] };
    try { pn = await postNameGap(text); } catch (e) {}
    const cross = crossOK(text);
    const why = !okSec ? '近邻检测未达标'
      : (pn.missed.length ? ('新命名「' + pn.name + '」还有 ' + pn.missed.length + ' 篇站内近邻未交代')
      : (cross === false ? '三个近邻全在同一学科内' : ''));
    return { need: !!why, why: why, name: pn.name, block: (pn.missed.length ? pn.block : ''), cross: cross };
  }

  w.SDENbr = { sectionOK: sectionOK, coinedName: coinedName, postNameGap: postNameGap,
               discTags: discTags, crossOK: crossOK, verdict: verdict, DISC_HINTS: DISC_HINTS };
  /* ⚠ 与 /assets/sde-nbr.js（近邻库查询）撞名。两者同页加载时后装的会静默盖掉前一个，
     而闸门照样显示"已过闸"——只是判的不是那件事了。同页要用两者，用 SDENbrGate / SDENbrLib。 */
  w.SDENbrGate = w.SDENbr;
})(window);
