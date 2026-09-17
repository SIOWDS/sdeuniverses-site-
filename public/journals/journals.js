(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const PAGE = 200;
  let current = 'en', legacy = {}, extra = {}, catalog = {}, rows = [], shown = 0;
  let journal = null, selectedYear = null, requestId = 0, loading = false;
  let legacyState = 'loading', readingState = 'loading';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeURL = value => { if (!value) return ''; try { const u = new URL(value, location.href); return /^https?:$/.test(u.protocol) ? u.href : ''; } catch { return ''; } };
  async function json(url) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(url, {signal: controller.signal});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return await response.json();
    } finally { clearTimeout(timeout); }
  }
  function filter() {
    const term = $('q').value.trim().toLowerCase();
    let any = false;
    ['en', 'cn'].forEach(lang => $('p-' + lang).classList.toggle('hide', lang !== current));
    $('p-' + current).querySelectorAll('.grp').forEach(group => {
      let count = 0;
      group.querySelectorAll('.tile').forEach(tile => {
        const match = !term || tile.dataset.n.includes(term);
        tile.classList.toggle('hide', !match); if (match) count++;
      });
      group.classList.toggle('hide', !count); any ||= count > 0;
    });
    $('none').classList.toggle('hide', any || !!journal);
  }
  document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => {
    current = button.dataset.t;
    document.querySelectorAll('.tab').forEach(b => b.classList.toggle('on', b === button)); filter();
  }));
  $('q').addEventListener('input', filter);
  function rebuild() {
    catalog = {...legacy};
    Object.entries(extra).forEach(([name, entry]) => {
      const base = legacy[name];
      // Curated education records replace no existing archive. Other journals retain their archive.
      catalog[name] = base ? {...base, readingCount: entry.readingCount, readingRows: entry.rows} : entry;
    });
    let count = 0, papers = 0;
    document.querySelectorAll('.tile').forEach(tile => {
      const j = catalog[tile.dataset.j];
      tile.classList.toggle('plan', !j); tile.classList.toggle('live', !!j);
      const status = tile.querySelector('.st');
      if (j) {
        count++; papers += j.n;
        status.textContent = `${j.n.toLocaleString()} 条目录` + (j.readingCount ? ` · ${j.readingCount} 篇站内可读` : ' · 摘要待补');
        tile.tabIndex = 0; tile.setAttribute('role', 'link');
      } else {
        status.textContent = legacyState === 'loading' ? '目录载入中…' : legacyState === 'error' ? '目录状态未确认' : '尚未收录';
        tile.removeAttribute('tabindex'); tile.removeAttribute('role');
      }
    });
    $('done').textContent = legacyState === 'ready' ? count : legacyState === 'loading' ? '载入中…' : `${count}（部分）`;
    $('papers').textContent = legacyState === 'ready' ? papers.toLocaleString() : legacyState === 'loading' ? '载入中…' : '暂无法统计';
    $('load-status').textContent = legacyState === 'loading' ? '正在读取完整目录；下方站内阅读区单独加载。' : legacyState === 'error' ? '完整目录暂时加载失败，已载入的站内内容仍可阅读。' : '目录已载入。题名记录不等于已收录摘要或全文。';
    $('retry-manifest').classList.toggle('hide', legacyState !== 'error');
  }
  document.querySelectorAll('.tile').forEach(tile => {
    const open = () => { if (catalog[tile.dataset.j]) location.hash = catalog[tile.dataset.j].slug; };
    tile.addEventListener('click', open);
    tile.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } });
  });
  function displayJournal(name) {
    journal = catalog[name];
    $('lists').classList.add('hide'); $('none').classList.add('hide');
    document.querySelector('.bar').classList.add('hide'); $('reading-shelf').classList.add('hide');
    $('jv').classList.remove('hide'); $('jt').textContent = name;
    $('jm').textContent = `ISSN ${(journal.issn || []).join(' / ')} · ${journal.n.toLocaleString()} 条目录 · ${journal.coverage || '按年份收录；摘要与译文分批补充'} · 来源 ${journal.src || '期刊公开目录'}`;
    const years = Object.keys(journal.years).sort().reverse();
    $('jy').innerHTML = years.map(y => `<button class="yr" data-y="${esc(y)}">${esc(y)} · ${journal.years[y]}</button>`).join('');
    $('jy').querySelectorAll('button').forEach(button => button.addEventListener('click', () => year(button.dataset.y)));
    const curated = journal.rows || journal.readingRows || [];
    $('journal-reading').innerHTML = curated.filter(r => r.read).map(r => `<a class="read-link" href="${esc(safeURL(r.read))}">${esc(r.t)} <span>站内阅读 →</span></a>`).join('');
    $('journal-reading').classList.toggle('hide', !$('journal-reading').children.length);
    year(years[0]);
  }
  async function year(value) {
    const id = ++requestId, selected = journal;
    selectedYear = value; rows = []; shown = 0; loading = true;
    $('jy').querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.y === value));
    $('jl').replaceChildren(); $('jc').textContent = '正在载入本年目录…';
    $('more').classList.add('hide'); $('retry-year').classList.add('hide'); $('jq').value = ''; $('jq').disabled = true;
    try {
      const result = selected.rows ? selected.rows.filter(r => r.d.startsWith(value)) : await json(`data/${encodeURIComponent(selected.slug)}/${encodeURIComponent(value)}.json`);
      if (id !== requestId) return;
      if (!Array.isArray(result) || result.some(r => typeof r.t !== 'string')) throw new Error('Invalid records');
      const readings = selected.readingRows || [];
      rows = result.map(row => { const found = readings.find(r => (r.doi && r.doi === row.doi) || r.t === row.t); return found ? {...row, read: found.read} : row; });
      loading = false; $('jq').disabled = false; render();
    } catch {
      if (id !== requestId) return;
      loading = false; $('jc').textContent = '本年目录加载失败，请重试。'; $('retry-year').classList.remove('hide');
    }
  }
  function filtered() { const term = $('jq').value.trim().toLowerCase(); return rows.filter(r => !term || `${r.t} ${r.te || ''} ${r.authors || ''}`.toLowerCase().includes(term)); }
  function render() { if (loading) return; shown = 0; $('jl').replaceChildren(); page(); }
  function page() {
    const selected = filtered();
    $('jl').insertAdjacentHTML('beforeend', selected.slice(shown, shown + PAGE).map(r => {
      const read = r.read && safeURL(r.read), source = safeURL(r.doi ? 'https://doi.org/' + r.doi : r.url);
      return `<li>${read ? `<a href="${esc(read)}">${esc(r.t)}</a>` : `<span>${esc(r.t)}</span>`}<span class="dt">${esc(r.d)}</span>${r.authors ? `<span class="te">${esc(r.authors)}</span>` : ''}${r.te ? `<span class="te">${esc(r.te)}</span>` : ''}<div class="paper-actions">${read ? `<a href="${esc(read)}">站内阅读 →</a>` : '<span>仅目录 · 摘要待补</span>'}${source ? `<a href="${esc(source)}" target="_blank" rel="noopener noreferrer">原始来源 ↗</a>` : ''}</div></li>`;
    }).join(''));
    shown = Math.min(shown + PAGE, selected.length);
    $('jc').textContent = selected.length ? `${selectedYear} 年 · ${selected.length} 条${selected.length !== rows.length ? '（筛选后）' : ''} · 已显示 ${shown}` : rows.length ? '没有符合筛选条件的论文。' : '本年尚无目录记录。';
    $('more').classList.toggle('hide', shown >= selected.length);
  }
  function home() {
    requestId++; journal = null; rows = []; loading = false;
    $('jv').classList.add('hide'); $('lists').classList.remove('hide');
    document.querySelector('.bar').classList.remove('hide'); $('reading-shelf').classList.remove('hide'); filter();
  }
  function route() {
    const slug = location.hash.slice(1), name = Object.keys(catalog).find(n => catalog[n].slug === slug);
    if (name) displayJournal(name); else home();
  }
  $('back').addEventListener('click', () => { history.pushState(null, '', location.pathname); home(); });
  $('jq').addEventListener('input', render); $('more').addEventListener('click', page);
  $('retry-year').addEventListener('click', () => year(selectedYear));
  window.addEventListener('hashchange', route); window.addEventListener('popstate', route);
  async function loadLegacy() {
    legacyState = 'loading'; rebuild();
    try {
      const data = await json('data/manifest.json');
      if (!data.journals || Array.isArray(data.journals) || typeof data.journals !== 'object') throw new Error('Invalid manifest');
      if (Object.values(data.journals).some(j => !j.slug || !j.years || !Number.isFinite(j.n))) throw new Error('Invalid journal');
      legacy = data.journals; legacyState = 'ready';
    } catch { legacyState = 'error'; }
    rebuild(); if (!journal) route();
  }
  async function loadReading() {
    readingState = 'loading'; $('reading-status').textContent = '正在载入站内阅读目录…'; $('retry-reading').classList.add('hide');
    try {
      const data = await json('reading/catalog.json');
      if (!data.journals || !Array.isArray(data.articles)) throw new Error('Invalid reading catalog');
      extra = data.journals; readingState = 'ready';
      $('reading-status').textContent = `${data.articles.length} 篇站内可读 · 中文摘要导读与英文原文摘要 / 中文全译 · 更新于 ${data.updated}`;
      $('reading-cards').innerHTML = data.articles.map(a => `<a class="reading-card" href="${esc(safeURL(a.read))}"><span>${esc(a.journal)} · ${esc(a.date)}</span><h3>${esc(a.title)}</h3><p>${esc(a.description)}</p><strong>${esc(a.kind)} →</strong></a>`).join('');
    } catch {
      readingState = 'error'; $('reading-status').textContent = '阅读目录暂时加载失败，可重试或直接打开下面的阅读入口。'; $('retry-reading').classList.remove('hide');
    }
    rebuild(); if (!journal) route();
  }
  $('retry-manifest').addEventListener('click', loadLegacy); $('retry-reading').addEventListener('click', loadReading);
  filter(); loadReading(); loadLegacy();
})();
