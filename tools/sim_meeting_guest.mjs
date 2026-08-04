// sim_meeting_guest.mjs —— 模拟"非社区听课者"打开邀请链接后的四条路径
// 用最小 DOM 桩加载 public/meeting/index.html 里的内联脚本，检查：
//  A 从 ?room= 深链进来、没名字 → 点横幅「进入会议」会发生什么
//  B 填了名字后点横幅 → 应当进房
//  C 填了名字后点「参加会议」卡片里的按钮（会议号框为空）→ 应当进房，而不是报"再填会议号"
//  D 手输会议号 → 进房
import fs from 'fs';

const html = fs.readFileSync(new URL('../public/meeting/index.html', import.meta.url), 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/g).map(s => s.replace(/^<script>/, '').replace(/<\/script>$/, ''));
const code = m.filter(s => s.includes('canonicalRoom') || s.includes('SDE_MEET_PICK')).join('\n');
if (!code.includes('canonicalRoom')) { console.error('FAIL 抽不到脚本'); process.exit(1); }

function makeEnv(search, opts = {}) {
  const store = {};
  const els = {};
  function mk(id) {
    const e = {
      id, value: '', textContent: '', innerHTML: '', style: {}, className: '',
      _h: {}, classList: { add() {}, remove() {} }, offsetWidth: 1,
      addEventListener(k, f) { (this._h[k] = this._h[k] || []).push(f); },
      focus() { env.focused = id; },
      scrollIntoView() { env.scrolled = id; },
      dispatch(k, ev) { (this._h[k] || []).forEach(f => f(ev)); },
    };
    return e;
  }
  ['joinName', 'meetCode', 'ma-out', 'ma-in', 'ma-name', 'ma-msg', 'ma-signout',
   'join-msg', 'joincard', 'rb-room', 'roomBanner', 'inv-room', 'inv-link', 'inv-msg',
   'rbName', 'rb-msg', 'invite', 'hostName', 'schTopic', 'schTime', 'schOut', 'schBtns', 'meet-roster', 'meet-auth']
    .forEach(id => { els[id] = mk(id); });

  const opened = [];
  const alerts = [];
  const env = { opened, alerts, els, focused: null, scrolled: null };
  const localStorage = {
    _d: opts.ls || {},
    getItem(k) { return k in this._d ? this._d[k] : null; },
    setItem(k, v) { this._d[k] = String(v); },
    removeItem(k) { delete this._d[k]; },
  };
  const sessionStorage = { getItem() { return null; }, setItem() {}, removeItem() {} };
  const document = {
    getElementById: id => els[id] || null,
    querySelector: () => null,
    createElement: () => ({ style: {}, focus() {}, select() {} }),
    body: { appendChild() {}, removeChild() {} },
    execCommand: () => true,
  };
  const window = {
    open: (u, t) => { opened.push(u); },
    location: { search, origin: 'https://sdeuniverses.com' },
    alert: t => alerts.push(t),
  };
  env.window = window;
  const sandbox = {
    window, document, localStorage, sessionStorage,
    location: window.location, alert: window.alert,
    URLSearchParams, encodeURIComponent, JSON, Math, String, setTimeout: () => {},
    navigator: {}, fetch: () => ({ then: () => ({ then: () => ({ catch: () => {} }) }) }),
    console,
  };
  const keys = Object.keys(sandbox);
  const fn = new Function(...keys, code + '\n;return {joinRoom,joinByCode,enterInvited,canonicalRoom,window};');
  env.api = fn(...keys.map(k => sandbox[k]));
  return env;
}

let fails = 0;
function check(name, cond, extra) {
  console.log((cond ? 'PASS  ' : 'FAIL  ') + name + (extra ? '  → ' + extra : ''));
  if (!cond) fails++;
}

// A：深链、无名字、直接点横幅
let a = makeEnv('?room=SDE-abc123');
a.api.enterInvited();
check('A 深链无名字点横幅：没有进房（被拦）', a.opened.length === 0, 'opened=' + JSON.stringify(a.opened));
console.log("    横幅提示：" + JSON.stringify(a.els["rb-msg"].textContent) + "  焦点=" + a.focused);
check("A2 无名字时提示落在横幅里、焦点在横幅输入框", !!a.els["rb-msg"].textContent && a.focused === "rbName");

// B：深链、先填名字、再点横幅
let b = makeEnv('?room=SDE-abc123');
b.els.joinName.value = '张三';
b.api.enterInvited();
check('B 深链填名字点横幅：进房', b.opened.length === 1 && /SDE-abc123/i.test(b.opened[0] || ''), b.opened[0] || '(无)');

// C：深链、填名字、点「参加会议」卡片按钮（会议号框空）
let c = makeEnv('?room=SDE-abc123');
c.els.joinName.value = '张三';
c.api.joinByCode();
check('C 深链填名字点参加会议（号框空）：应进被邀房间', c.opened.length === 1 && /SDE-abc123/i.test(c.opened[0] || ''),
  c.opened[0] || ('未进房，提示：' + JSON.stringify(c.els['join-msg'].textContent)));

// D：手输会议号
let d = makeEnv('');
d.els.joinName.value = '李四';
d.els.meetCode.value = 'SDE-abc123';
d.api.joinByCode();
check('D 手输名字+会议号：进房', d.opened.length === 1 && /SDE-abc123/i.test(d.opened[0] || ''), d.opened[0] || '(无)');

// E：名字是否写进链接（进房自动显示名字）
check('E 进房链接带 displayName', /displayName/.test(d.opened[0] || ''), (d.opened[0] || '').slice(-90));

// F：房间号规范化四路一致
const cr = d.api.canonicalRoom;
check('F 房号规范化一致', cr('SDE-abc123') === cr('sde-ABC123') && cr('SDE-abc123') === cr('abc123'),
  [cr('SDE-abc123'), cr('sde-ABC123'), cr('abc123')].join(' | '));

// G：中文名字房间
check('G 中文房名可用', cr('今晚讲课') === 'SDE-今晚讲课', cr('今晚讲课'));

console.log(fails ? `\n${fails} 项不通过` : '\n全部通过');
process.exit(0);
