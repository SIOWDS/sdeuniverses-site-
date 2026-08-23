#!/usr/bin/env node
/* 「下拉菜单要能滚」护栏（2026-08-23）
   报障：成文 · PPT 那张菜单看不到最下面的几条（应用文五档与成文历史都在末尾）。
   这类毛病不报错、单测也测不到——jsdom 没有排版，offsetHeight 恒为 0，
   所以判据只能落在两处：CSS 里真有 overflow，和 menuFit 的算术真跑一遍。
   变异检验：M_JS=/tmp/wm.before.js node tools/sim_menu_scroll.js 应当变红。 */
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const M = process.env.M_JS || path.join(ROOT, 'public/wds-mode.js');
const S = fs.readFileSync(M, 'utf8');

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log('  ✗ ' + n + (x ? '  ← ' + x : '')); } };

console.log('\n【一】CSS：能滚，而且看得出能滚');
const css = (S.match(/"\.wdsm-menu\{[^"]*"/) || [''])[0];
ok(/overflow-y:auto/.test(css), '.wdsm-menu 有 overflow-y:auto', css.slice(0, 90));
ok(/max-height:/.test(css), '.wdsm-menu 有 max-height 兜底');
ok(/overscroll-behavior:contain/.test(css), '滚到底不把下面的对话一起带着滚');
ok(/scrollbar-width:thin/.test(css), 'Firefox 侧有细滚动条');
ok(S.indexOf('".wdsm-menu::-webkit-scrollbar{') >= 0, 'WebKit 侧滚动条有宽度（不是默认的隐形）');
ok(S.indexOf('".wdsm-menu::-webkit-scrollbar-thumb{') >= 0, '滑块有颜色（看得见）');
ok(/-webkit-overflow-scrolling:touch/.test(css), 'iOS 上惯性滚动');

console.log('【二】menuFit 的算术（真跑）');
const src = (S.match(/function menuFit\(menu, rect, down\) \{[\s\S]*?\n  \}/) || [''])[0];
ok(!!src, '抠得出 menuFit');
if (src) {
  const mk = (vh) => new Function('window', src + '; return menuFit;')({ innerHeight: vh });
  const fit = mk(800);
  const box = () => ({ style: {} });
  let m = box(); fit(m, { top: 48, bottom: 78 }, true);
  ok(m.style.maxHeight === '706px', '往下开：窗口高 − 按钮下沿 − 16', m.style.maxHeight);
  m = box(); fit(m, { top: 700, bottom: 730 }, false);
  ok(m.style.maxHeight === '684px', '往上开：按钮上沿 − 16（不是窗口高）', m.style.maxHeight);
  // 下限：空间被挤没了也不许夹成一条缝
  m = box(); fit(m, { top: 770, bottom: 790 }, true);
  ok(m.style.maxHeight === '200px', '可用空间极小时兜到 200px', m.style.maxHeight);
  m = box(); fit(m, { top: 10, bottom: 40 }, false);
  ok(m.style.maxHeight === '200px', '往上开且贴顶时也兜到 200px', m.style.maxHeight);
  // 小屏（手机横屏 375×360）：仍要给得出一个正数
  const fitS = mk(360); m = box(); fitS(m, { top: 40, bottom: 70 }, true);
  ok(parseInt(m.style.maxHeight, 10) >= 200, '小屏上仍是可用的高度', m.style.maxHeight);
  // 拿不到 window 也不许抛（菜单开不出来比不能滚更糟）
  const fitBad = new Function('window', src + '; return menuFit;')(null);
  let threw = false;
  try { fitBad({ style: {} }, { top: 1, bottom: 2 }, true); } catch (e) { threw = true; }
  ok(!threw, '取不到窗口尺寸时静默退出，不抛');
}

console.log('【三】两个调用点都接上了');
ok(/menuFit\(menu, r, true\);/.test(S), '成文菜单落位后夹一次');
ok(/menuFit\(menu, r, _down\);/.test(S), '通用菜单按开的方向夹一次');
ok(/var _down = !\(r\.top > 320\);/.test(S), '开的方向抽成了变量（原来只在 if 里判一次）');
const i1 = S.indexOf('function menuFit(menu, rect, down)');
ok(i1 >= 0 && i1 < S.indexOf('menuFit(menu, r, true);'), 'menuFit 定义在调用之前');

console.log('【四】没误伤');
ok(/max-height:84vh;overflow:auto/.test(S), '模板选单原有的滚动没被动过');
ok(/\.wdsm-dist-c\{flex:1;overflow-y:auto/.test(S), '成文正文区的滚动没被动过');
ok(/min-width:210px/.test(S), '菜单最小宽度还在');

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' PASS / ' + fail + ' FAIL\n');
process.exit(fail ? 1 : 0);
