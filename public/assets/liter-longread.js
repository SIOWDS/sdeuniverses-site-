(() => {
  const root = document.documentElement;
  const progress = document.querySelector('.read-progress span');
  const prose = document.querySelector('.prose');
  const tocList = document.querySelector('.toc-list');
  const themeButton = document.querySelector('[data-action="theme"]');
  const storedTheme = localStorage.getItem('liter-reading-theme');
  const storedSize = Number(localStorage.getItem('liter-reading-size'));

  if (storedTheme === 'night') root.dataset.theme = 'night';
  if (storedSize >= 16 && storedSize <= 22) root.style.setProperty('--reading-size', `${storedSize}px`);

  const headings = prose ? [...prose.querySelectorAll('h2,h3')] : [];
  headings.forEach((heading, i) => {
    if (!heading.id) heading.id = `section-${i + 1}`;
    if (heading.tagName === 'H2' && !heading.dataset.index) {
      const index = headings.filter((item, n) => n <= i && item.tagName === 'H2').length;
      heading.dataset.index = String(index).padStart(2, '0');
    }
    if (tocList) {
      const link = document.createElement('a');
      link.href = `#${heading.id}`;
      link.textContent = heading.textContent;
      link.className = heading.tagName.toLowerCase();
      tocList.appendChild(link);
    }
  });

  if (!headings.length) document.querySelector('.toc')?.remove();

  const updateProgress = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    const value = max > 0 ? Math.min(100, Math.max(0, scrollY / max * 100)) : 0;
    if (progress) progress.style.width = `${value}%`;
  };
  updateProgress();
  addEventListener('scroll', updateProgress, {passive:true});
  addEventListener('resize', updateProgress, {passive:true});

  if ('IntersectionObserver' in window && headings.length) {
    const links = [...document.querySelectorAll('.toc a')];
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(entry => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      links.forEach(link => link.classList.toggle('active', link.hash === `#${visible.target.id}`));
    }, {rootMargin:'-15% 0px -72% 0px'});
    headings.forEach(heading => observer.observe(heading));
  }

  document.querySelectorAll('[data-action="size"]').forEach(button => {
    button.addEventListener('click', () => {
      const current = parseFloat(getComputedStyle(root).getPropertyValue('--reading-size')) || 18;
      const next = Math.min(22, Math.max(16, current + Number(button.dataset.step || 0)));
      root.style.setProperty('--reading-size', `${next}px`);
      localStorage.setItem('liter-reading-size', String(next));
    });
  });

  themeButton?.addEventListener('click', () => {
    const night = root.dataset.theme !== 'night';
    if (night) root.dataset.theme = 'night'; else delete root.dataset.theme;
    localStorage.setItem('liter-reading-theme', night ? 'night' : 'day');
    themeButton.setAttribute('aria-pressed', String(night));
  });
})();
