import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const out = path.join(root, "public", "assets", "essential-figures");
fs.mkdirSync(out, { recursive: true });

const articles = {
  "/ideas/genesis-vs-discovery/": {
    slug: "genesis", title: "发生取代发现",
    captions: ["从揭开现成世界，到参与新结构的发生", "发生不是单点产出，而是 E、D、S 的互生", "把旁观者改写为发生的参与者"],
    diagrams: [
      { name: "mutual", kind: "triad", labels: ["环境 E", "差异 D", "结构 S"], center: "互生" },
      { name: "practice", kind: "flow", labels: ["进入现场", "识别差异", "承受张力", "形成结构"] }
    ]
  },
  "/ideas/formula-six-paths/": {
    slug: "six-paths", title: "一句公式，六条路径",
    captions: ["同一任务可以从六条路径起手", "起点由任务 DNA 决定，不存在万能顺序", "六路径是一把随身的思考手术刀"],
    diagrams: [
      { name: "routes", kind: "radial", labels: ["S→D→E", "S→E→D", "D→S→E", "D→E→S", "E→S→D", "E→D→S"], center: "任务" },
      { name: "choice", kind: "flow", labels: ["读任务", "判起点", "走主轴", "校验闭环"] }
    ]
  },
  "/ideas/four-outcomes/": {
    slug: "four-outcomes", title: "四结局诊断",
    captions: ["同一份张力，会把系统带向四种不同结局", "关键差别：有没有产生新结构", "诊断之后，把能量重新导向跃迁"],
    diagrams: [
      { name: "matrix", kind: "matrix", labels: ["跃迁", "内卷", "轮回", "耗散"], axes: ["结构更新", "能量保留"] },
      { name: "redirect", kind: "flow", labels: ["识别结局", "停止耗损", "打开差异", "形成跃迁"] }
    ]
  },
  "/ideas/human-tool-complex/": {
    slug: "human-tool", title: "人—工具复合体",
    captions: ["人和工具共同工作，但判断之核不能外包", "工具扩展能力，人保留四项主体责任", "用强工具，同时守住人的核"],
    diagrams: [
      { name: "core", kind: "radial", labels: ["判根", "定向", "赋义", "承受"], center: "人的核" },
      { name: "loop", kind: "flow", labels: ["人定向", "工具生成", "人判断", "共同迭代"] }
    ]
  },
  "/ideas/information-not-knowledge/": {
    slug: "knowledge", title: "信息不等于知识",
    captions: ["信息只有扎根现实、点燃内驱，才长成知识", "知识形成需要 E1 扎根与 E3 内驱", "从搬运信息，转向生成可用结构"],
    diagrams: [
      { name: "roots", kind: "triad", labels: ["信息", "E1 扎根", "E3 内驱"], center: "知识" },
      { name: "practice", kind: "flow", labels: ["获取", "落地检验", "内在关联", "生成行动"] }
    ]
  },
  "/ideas/goal-is-not-structure/": {
    slug: "goal", title: "目标不是结构",
    captions: ["静态靶点会失去牵引，真正运行的是三律", "创造、自由、幸福共同维持目标的生命", "把目标从名词改写成动词"],
    diagrams: [
      { name: "laws", kind: "triad", labels: ["创造律", "自由律", "幸福律"], center: "运行" },
      { name: "verb", kind: "flow", labels: ["发现张力", "裁出新路", "完成闭环", "继续发生"] }
    ]
  },
  "/ideas/freedom-as-new-path/": {
    slug: "freedom", title: "自由是在约束中裁出新路",
    captions: ["自由不是没有墙，而是在墙中打开新路", "选项数量与真实自由并不是一回事", "把约束改写成生成新路的材料"],
    diagrams: [
      { name: "contrast", kind: "matrix", labels: ["选项多", "被路由", "约束强", "裁新路"], axes: ["现成选项", "生成能力"] },
      { name: "practice", kind: "flow", labels: ["看清约束", "寻找裂隙", "试切路径", "承担结果"] }
    ]
  },
  "/ideas/happiness-in-genesis/": {
    slug: "happiness", title: "幸福在完整走通的当下",
    captions: ["幸福不是远处奖杯，而是当下闭环的亮起", "张力被完整走通，真善美同时对齐", "在过程中制造可完成的小闭环"],
    diagrams: [
      { name: "whole", kind: "triad", labels: ["真", "善", "美"], center: "幸福" },
      { name: "cycle", kind: "flow", labels: ["张力积累", "投入行动", "结构完成", "释放感受"] }
    ]
  },
  "/column/where-genesis-begins/": {
    slug: "where", title: "何处正要发生",
    captions: ["裂缝不是瑕疵，而是新结构的产道", "从三大亏缺，进入九步发生机制", "机制允许回流，不是僵硬流水线"],
    diagrams: [
      { name: "deficits", kind: "triad", labels: ["结构亏缺", "路径亏缺", "意义亏缺"], center: "裂缝" },
      { name: "nine", kind: "flow9", labels: ["显缝", "判深", "判时", "定亏", "引差", "承张", "试形", "校验", "定型"] }
    ]
  },
  "/column/why-old-critical-thinking-fails/": {
    slug: "critical", title: "GPT 时代的批判性思维",
    captions: ["旧批判看表面裂缝，新批判追问对象如何生成", "前提、逻辑、证据、判断都已被复合化", "从裁判结论，转向揭示发生过程"],
    diagrams: [
      { name: "layers", kind: "radial", labels: ["前提缝合", "逻辑拼接", "证据混流", "判断量产"], center: "复合对象" },
      { name: "upgrade", kind: "flow", labels: ["暂停点头", "拆开来源", "追踪路径", "重建判断"] }
    ]
  }
};

const esc = s => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const base = body => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" role="img">
<defs><filter id="s"><feDropShadow dx="0" dy="8" stdDeviation="12" flood-opacity=".12"/></filter>
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#102a43"/><stop offset="1" stop-color="#1f4b5d"/></linearGradient></defs>
<rect width="1200" height="675" fill="#f5f0e5"/><path d="M0 88C240 10 386 130 598 72s340-40 602 34V0H0Z" fill="#e8dfce" opacity=".7"/>
<path d="M0 600c265-85 365 28 596-34 209-56 385 0 604 52v57H0Z" fill="#e8dfce" opacity=".65"/>${body}</svg>`;
function svg(d) {
  const labels = d.labels.map(esc);
  if (d.kind === "flow" || d.kind === "flow9") {
    const n = labels.length, x0 = 105, gap = 990 / Math.max(1, n - 1);
    return base(`<path d="M${x0} 340H${x0 + gap * (n - 1)}" stroke="#b58a3b" stroke-width="8" stroke-linecap="round"/>
      ${labels.map((l,i)=>`<g transform="translate(${x0+i*gap} 340)" filter="url(#s)"><circle r="${n>5?44:64}" fill="${i===n-1?"#a6422b":"url(#g)"}"/><text text-anchor="middle" y="7" fill="#fff" font-size="${n>5?22:28}" font-family="sans-serif">${l}</text>${i<n-1?`<path d="M${n>5?50:72} 0l28-16v32Z" fill="#b58a3b"/>`:""}</g>`).join("")}`);
  }
  if (d.kind === "triad") {
    const pts=[[600,160],[315,490],[885,490]];
    return base(`<path d="M600 210L365 450M835 450L600 210M370 490H830" stroke="#b58a3b" stroke-width="8" fill="none"/>
      <circle cx="600" cy="360" r="104" fill="#a6422b" filter="url(#s)"/><text x="600" y="370" text-anchor="middle" fill="#fff" font-size="34" font-family="sans-serif">${esc(d.center)}</text>
      ${labels.map((l,i)=>`<g><circle cx="${pts[i][0]}" cy="${pts[i][1]}" r="82" fill="url(#g)" filter="url(#s)"/><text x="${pts[i][0]}" y="${pts[i][1]+10}" text-anchor="middle" fill="#fff" font-size="30" font-family="sans-serif">${l}</text></g>`).join("")}`);
  }
  if (d.kind === "matrix") {
    return base(`<path d="M600 100V590M120 338H1080" stroke="#b58a3b" stroke-width="5"/><text x="600" y="75" text-anchor="middle" fill="#7a5c1e" font-size="24" font-family="sans-serif">${esc(d.axes[0])} ↑</text><text x="1090" y="330" text-anchor="end" fill="#7a5c1e" font-size="24" font-family="sans-serif">${esc(d.axes[1])} →</text>
      ${[[350,215],[850,215],[350,475],[850,475]].map((p,i)=>`<g filter="url(#s)"><rect x="${p[0]-115}" y="${p[1]-58}" width="230" height="116" rx="28" fill="${i===0?"#a6422b":"url(#g)"}"/><text x="${p[0]}" y="${p[1]+11}" text-anchor="middle" fill="#fff" font-size="34" font-family="sans-serif">${labels[i]}</text></g>`).join("")}`);
  }
  const n=labels.length, r=210;
  return base(`${labels.map((l,i)=>{const a=-Math.PI/2+i*Math.PI*2/n,x=600+Math.cos(a)*r,y=338+Math.sin(a)*r;return `<path d="M600 338L${x} ${y}" stroke="#b58a3b" stroke-width="6"/><g filter="url(#s)"><circle cx="${x}" cy="${y}" r="72" fill="url(#g)"/><text x="${x}" y="${y+9}" text-anchor="middle" fill="#fff" font-size="${n>4?22:28}" font-family="sans-serif">${l}</text></g>`}).join("")}<circle cx="600" cy="338" r="96" fill="#a6422b" filter="url(#s)"/><text x="600" y="349" text-anchor="middle" fill="#fff" font-size="32" font-family="sans-serif">${esc(d.center)}</text>`);
}

for (const a of Object.values(articles)) for (const d of a.diagrams) {
  fs.writeFileSync(path.join(out, `${a.slug}-${d.name}.svg`), svg(d));
}

const clientConfig = Object.fromEntries(Object.entries(articles).map(([url,a], index) => [url, {
  rank:index + 1, slug:a.slug, title:a.title, captions:a.captions, diagrams:a.diagrams.map(d=>d.name)
}]));
const client = `(()=>{const cfg=${JSON.stringify(clientConfig)};const key=location.pathname.endsWith("/")?location.pathname:location.pathname+"/";const a=cfg[key];if(!a)return;
const css='.sde-essential-nav{max-width:920px;margin:30px auto 8px;padding:13px 18px;border:1px solid rgba(122,92,30,.24);border-radius:12px;background:rgba(181,138,59,.08);display:flex;align-items:center;justify-content:space-between;gap:16px;font-size:13px;line-height:1.5}.sde-essential-nav a{color:#7a5c1e;text-decoration:none}.sde-essential-nav b{color:#9b3d2a;letter-spacing:.08em}.sde-figure{margin:42px auto 50px;max-width:980px}.sde-figure-open{display:block}.sde-figure img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:14px;border:1px solid rgba(122,92,30,.22);box-shadow:0 16px 42px rgba(28,37,43,.13);background:#f5f0e5}.sde-figure figcaption{margin:13px auto 0;max-width:780px;text-align:center;text-indent:0!important;color:#6b6250;font-size:14px;line-height:1.65;letter-spacing:.02em}.sde-figure .fig-no{color:#9b3d2a;font-weight:800;margin-right:.55em}.sde-figure .fig-zoom{color:#8a6817;margin-left:.6em;font-size:.9em;white-space:nowrap}.sde-figure .fig-zoom:before{content:"↗ "}.sde-figure .fig-zoom:hover{text-decoration:underline}@media(max-width:640px){.sde-essential-nav{margin:22px 0 5px;padding:11px 12px}.sde-essential-nav .nav-title{display:none}.sde-figure{margin:30px -4px 38px}.sde-figure img{border-radius:9px}.sde-figure figcaption{font-size:13px;padding:0 8px}}';const st=document.createElement('style');st.textContent=css;document.head.append(st);
const srcs=[a.slug+'-concept.webp',a.slug+'-'+a.diagrams[0]+'.svg',a.slug+'-'+a.diagrams[1]+'.svg'];const ids=key.includes('why-old-critical')?['c1','c4','c7']:key.includes('where-genesis')?['s1','s4','s7']:['c1','c4','c7'];
ids.forEach((id,i)=>{const anchor=document.getElementById(id);if(!anchor)return;const src='/assets/essential-figures/'+srcs[i];const f=document.createElement('figure');f.className='sde-figure';f.innerHTML='<a class="sde-figure-open" href="'+src+'" target="_blank" rel="noopener" aria-label="打开图 '+(i+1)+' 高清大图"><img width="1200" height="675" loading="'+(i?'lazy':'eager')+'" decoding="async" src="'+src+'" alt="'+a.captions[i]+'"></a><figcaption><span class="fig-no">图 '+(i+1)+'</span>'+a.captions[i]+'<a class="fig-zoom" href="'+src+'" target="_blank" rel="noopener">查看大图</a></figcaption>';if(anchor.tagName==='SECTION')anchor.insertAdjacentElement('afterend',f);else anchor.insertAdjacentElement('beforebegin',f);});
const keys=Object.keys(cfg),i=keys.indexOf(key),first=document.querySelector('.sde-figure');if(first){const n=document.createElement('aside');n.className='sde-essential-nav';n.setAttribute('aria-label','SDE 必读十篇导航');n.innerHTML=(i>0?'<a href="'+keys[i-1]+'">← 上一篇</a>':'<span></span>')+'<span class="nav-title"><b>SDE 必读十篇</b> · 第 '+a.rank+' 篇</span>'+(i<keys.length-1?'<a href="'+keys[i+1]+'">下一篇 →</a>':'<span></span>');first.insertAdjacentElement('beforebegin',n);}})();`;
fs.writeFileSync(path.join(root, "public", "assets", "sde-essential-figures.js"), client);

for (const url of Object.keys(articles)) {
  const file = path.join(root, "public", url, "index.html");
  let html = fs.readFileSync(file, "utf8");
  const tag = '<script src="/assets/sde-essential-figures.js?v=20260724c" defer></script>';
  if (/sde-essential-figures\.js(?:\?[^"]*)?/.test(html)) {
    html = html.replace(/<script src="\/assets\/sde-essential-figures\.js(?:\?[^"]*)?" defer><\/script>/, tag);
  } else {
    html = html.replace("</head>", `${tag}</head>`);
  }
  fs.writeFileSync(file, html);
}
