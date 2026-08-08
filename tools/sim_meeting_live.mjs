// sim_meeting_live.mjs —— SDE 讲堂直播厅页的脱机模拟
//
// 用最小 DOM 桩加载 public/meeting/index.html 的内联脚本，检查五条会真咬人的路径：
//   A 未开播（status.live=false）        → 遮罩显示"没有课在直播"、video 藏起、不加载 hls.js
//   B 开播（status.live=true）           → 拉 hls.js、接上 m3u8、遮罩收掉、video 露出
//   C 开播中途下课（true → false）        → 播放器销毁、回到未开播态（不能继续转圈或卡在旧画面）
//   D status.json 取不到（网络/桶挂了）   → 不许抛异常，按未开播处理
//   E 回放与预告渲染                      → 有数据就换掉"筹备中"占位，空数据不许把占位清成空白
//
// 跑法：node tools/sim_meeting_live.mjs
import fs from 'fs';

const html = fs.readFileSync(new URL('../public/meeting/index.html', import.meta.url), 'utf8');
const blocks = (html.match(/<script>([\s\S]*?)<\/script>/g) || [])
  .map(s => s.replace(/^<script>/, '').replace(/<\/script>$/, ''));
const code = blocks.filter(s => s.includes('SDE_LIVE')).join('\n');
if (!code.includes('function tick')) { console.error('FAIL 抽不到直播厅脚本'); process.exit(1); }

function makeEnv(statusSeq, opts = {}) {
  const els = {};
  const env = { scripts: [], fetched: [], timers: 0, hlsMade: [], destroyed: 0, played: 0 };

  function mk(id) {
    return {
      id, value: '', textContent: '', innerHTML: '', className: '', style: {},
      _h: {},
      addEventListener(k, f) { (this._h[k] = this._h[k] || []).push(f); },
      removeAttribute() {}, focus() {}, scrollIntoView() {},
      canPlayType() { return opts.nativeHls ? 'maybe' : ''; },
      play() { env.played++; }, pause() {},
      set onload(f) { this._onload = f; }, get onload() { return this._onload; },
    };
  }
  ['lvDot', 'lvTitle', 'lvMeta', 'lvVeil', 'lvVideo', 'lvFoot', 'schBox', 'repBox', 'oldlink', 'lvBtn', 'screen']
    .forEach(id => { els[id] = mk(id); });

  const document = {
    hidden: false,
    readyState: 'complete',
    getElementById: id => els[id] || null,
    addEventListener() {},
    createElement(tag) {
      const e = mk('_' + tag);
      e.tagName = tag;
      return e;
    },
    head: {
      appendChild(s) {
        env.scripts.push(s.src);
        // 模拟 hls.js 到货：置 window.Hls 再回调 onload
        if (!opts.hlsFails) {
          window.Hls = FakeHls;
          if (s.onload) s.onload();
        } else {
          if (s.onerror) s.onerror();
        }
      }
    },
  };

  let seq = 0;
  function FakeHls(cfg) {
    env.hlsMade.push(cfg);
    this.cfg = cfg;
    this.loadSource = src => { env.lastSrc = src; };
    this.attachMedia = () => {};
    this.on = () => {};
    this.destroy = () => { env.destroyed++; };
    this.startLoad = () => {};
    this.recoverMediaError = () => {};
  }
  FakeHls.isSupported = () => !opts.noMse;
  FakeHls.Events = { ERROR: 'err' };
  FakeHls.ErrorTypes = { NETWORK_ERROR: 'n', MEDIA_ERROR: 'm' };

  const window = {
    Hls: null,
    location: { search: opts.search || '' },
    document,
  };

  function fetchStub(u) {
    env.fetched.push(u);
    if (u.indexOf('replays.json') >= 0) {
      if (opts.replaysFail) return Promise.reject(new Error('boom'));
      return Promise.resolve({ json: () => Promise.resolve(opts.replays || {}) });
    }
    const st = statusSeq[Math.min(seq, statusSeq.length - 1)];
    seq++;
    if (st === 'FAIL') return Promise.reject(new Error('down'));
    return Promise.resolve({ json: () => Promise.resolve(st) });
  }

  const sandbox = {
    window, document, fetch: fetchStub,
    URLSearchParams,
    setTimeout: () => { env.timers++; return env.timers; },
    clearTimeout: () => {},
    Date, Promise, JSON, String, Math,
  };
  env.els = els;
  env.window = window;
  return { sandbox, env };
}

function run(code, sandbox) {
  const keys = Object.keys(sandbox);
  const fn = new Function(...keys, code + '\n;return window.SDE_LIVE;');
  return fn(...keys.map(k => sandbox[k]));
}

let fails = 0;
function ok(name, cond, detail) {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (cond ? '' : '  → ' + detail));
  if (!cond) fails++;
}

// ---- A 未开播 -------------------------------------------------------------
{
  const { sandbox, env } = makeEnv([{ live: false }]);
  const api = run(code, sandbox);
  await api.tick();
  ok('A 未开播：遮罩说没有课在直播',
    env.els.lvVeil.innerHTML.includes('现在没有课在直播'), env.els.lvVeil.innerHTML.slice(0, 80));
  ok('A 未开播：video 不显示', env.els.lvVideo.style.display === 'none', env.els.lvVideo.style.display);
  ok('A 未开播：不下载 hls.js（400KB 不该白下）',
    env.scripts.length === 0, JSON.stringify(env.scripts));
  ok('A 未开播：状态点不是直播态', env.els.lvDot.className === 'dot', env.els.lvDot.className);
}

// ---- B 开播 ---------------------------------------------------------------
{
  const { sandbox, env } = makeEnv([{ live: true, title: 'SDE 本体论第三讲', startedAt: '20:00' }]);
  const api = run(code, sandbox);
  await api.tick();
  await new Promise(r => setTimeout(r, 0));
  ok('B 开播：拉了 hls.js', env.scripts.some(s => /hls\.min\.js/.test(s)), JSON.stringify(env.scripts));
  ok('B 开播：接到了 m3u8', env.lastSrc === '/live/stream.m3u8', String(env.lastSrc));
  ok('B 开播：video 露出', env.els.lvVideo.style.display === 'block', env.els.lvVideo.style.display);
  ok('B 开播：标题栏亮直播中', env.els.lvTitle.innerHTML.includes('直播中'), env.els.lvTitle.innerHTML);
  ok('B 开播：状态点点亮', env.els.lvDot.className === 'dot on', env.els.lvDot.className);
  const cfg = env.hlsMade[0] || {};
  ok('B 缓冲参数没被调成低延迟（跨境要的是稳）',
    cfg.lowLatencyMode === false && cfg.liveSyncDurationCount >= 4 && cfg.maxBufferLength >= 30,
    JSON.stringify(cfg));
  ok('B 开播：调用了 play()', env.played >= 1, String(env.played));
}

// ---- C 下课 ---------------------------------------------------------------
{
  const { sandbox, env } = makeEnv([{ live: true, title: '第三讲' }, { live: false }]);
  const api = run(code, sandbox);
  await api.tick();
  await new Promise(r => setTimeout(r, 0));
  ok('C 前置：已在播', api.state() === 'playing', api.state());
  await api.tick();
  ok('C 下课：播放器被销毁', env.destroyed >= 1, String(env.destroyed));
  ok('C 下课：回到未开播态', api.state() === '', api.state());
  ok('C 下课：遮罩换回未开播文案',
    env.els.lvVeil.innerHTML.includes('现在没有课在直播'), env.els.lvVeil.innerHTML.slice(0, 80));
}

// ---- D status.json 取不到 --------------------------------------------------
{
  const { sandbox, env } = makeEnv(['FAIL']);
  const api = run(code, sandbox);
  let threw = null;
  await api.tick().catch(e => { threw = e; });
  ok('D 取不到状态：不抛异常', threw === null, String(threw));
  ok('D 取不到状态：按未开播处理',
    env.els.lvVeil.innerHTML.includes('现在没有课在直播'), env.els.lvVeil.innerHTML.slice(0, 80));
}

// ---- E 回放与预告 ----------------------------------------------------------
{
  const { sandbox, env } = makeEnv([{ live: false }], {
    replays: { items: [{ title: '第一讲 · 何谓发生', date: '2026-08-09', url: '/live/replay/01.mp4' }] }
  });
  const api = run(code, sandbox);
  api.renderReplays([{ title: '第一讲 · 何谓发生', date: '2026-08-09', url: '/live/replay/01.mp4' }]);
  ok('E 回放：占位被真数据换掉',
    env.els.repBox.innerHTML.includes('第一讲') && env.els.repBox.innerHTML.includes('/live/replay/01.mp4'),
    env.els.repBox.innerHTML.slice(0, 90));

  env.els.repBox.innerHTML = '筹备中';
  api.renderReplays([]);
  ok('E 回放：空清单不许把占位抹成空白', env.els.repBox.innerHTML === '筹备中', env.els.repBox.innerHTML);

  env.els.schBox.innerHTML = '筹备中';
  api.renderNext({ title: '第二讲 · 承载权', at: '8 月 12 日 20:00', note: '接着上一讲往下讲' });
  ok('E 预告：卡片被真预告换掉',
    env.els.schBox.innerHTML.includes('第二讲') && env.els.schBox.innerHTML.includes('8 月 12 日'),
    env.els.schBox.innerHTML.slice(0, 90));

  env.els.schBox.innerHTML = '筹备中';
  api.renderNext(null);
  ok('E 预告：没预告不许抹成空白', env.els.schBox.innerHTML === '筹备中', env.els.schBox.innerHTML);
}

// ---- F XSS：status.json 是服务器写的，但也别让它能往页面里塞标签 ----------------
{
  const { sandbox, env } = makeEnv([{ live: false }]);
  const api = run(code, sandbox);
  api.renderNext({ title: '<img src=x onerror=alert(1)>', at: '', note: '' });
  ok('F 预告标题被转义', !env.els.schBox.innerHTML.includes('<img'), env.els.schBox.innerHTML.slice(0, 90));
  api.setBar(false, '<script>bad()</' + 'script>', '');
  ok('F 标题栏被转义', !env.els.lvTitle.innerHTML.includes('<script'), env.els.lvTitle.innerHTML.slice(0, 90));
}

// ---- G hls.js 下不来时的兜底 -------------------------------------------------
{
  const { sandbox, env } = makeEnv([{ live: true }], { hlsFails: true, nativeHls: true });
  const api = run(code, sandbox);
  await api.tick();
  await new Promise(r => setTimeout(r, 0));
  ok('G hls.js 下不来：回落到原生 HLS 播放',
    env.els.lvVideo.src === '/live/stream.m3u8' && env.els.lvVideo.style.display === 'block',
    String(env.els.lvVideo.src) + ' / ' + env.els.lvVideo.style.display);
}

console.log('\n' + (fails ? 'FAILED ' + fails + ' 项' : '全部通过'));
process.exit(fails ? 1 : 0);
