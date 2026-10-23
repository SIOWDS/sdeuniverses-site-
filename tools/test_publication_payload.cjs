/* Run the actual payload functions in a Node VM; all network requests are mocked.
   This is not a live model or browser rendering test. No API credentials needed. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {webcrypto} = require('node:crypto');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const json = p => JSON.parse(read(p));
const catalog = json('public/books/catalog.json').books;
const agents = json('public/books/agents.json').agents;
const outputs = [];

async function test(no) {
  const base = `public/books/m/${no}/`;
  const book = catalog.find(b => b.number === no);
  const kp = json(base + 'keypoints.json');
  const rag = json(base + 'rag.json');
  const manifest = json(base + 'unit/learning.json');
  const source = json(base + 'unit/sources/chapter-01.json');
  const other = no === 414 ? 459 : 414;
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {value: '', checked: false, innerHTML: '', style: {}});
    return elements.get(id);
  };
  const requests = [], loaded = [];
  const sandbox = {
    window: {BOOK_AGENT: {no}}, document: {getElementById: element},
    location: {origin: 'http://publication.test', search: ''}, URL, URLSearchParams,
    localStorage: {getItem: k => k === 'sde_wds_key' ? 'mock-key-never-sent' : null, setItem() {}},
    crypto: webcrypto, TextEncoder, TextDecoder, ReadableStream, console,
    fetch: (url, options) => {
      if (options?.method === 'POST') {
        requests.push(JSON.parse(options.body));
        return Promise.resolve({ok: true, body: new ReadableStream({start(c) {c.close();}})});
      }
      loaded.push(url);
      return new Promise(() => {}); // Keep automatic page boot pending; install local fixtures below.
    }
  };
  vm.createContext(sandbox);
  let legacy = read('public/books/agent/app.js');
  const end = legacy.lastIndexOf('})();');
  assert(end >= 0);
  legacy = legacy.slice(0, end) + `
window.testPayload = {set: function(b,k,r,a,s) {
  BOOK=b; KP=k; RAG=r; AG=a; CH=[{t:s.title,x:s.text,n:s.text.length}];
  grow=save=paint=scroll=function(){};
  add=function(){return {querySelector:function(){return {innerHTML:'',querySelector:function(){return null}}},appendChild:function(){}}};
},send:send};
` + legacy.slice(end);
  vm.runInContext(legacy, sandbox);
  assert(loaded.includes(`/books/m/${no}/keypoints.json`));
  assert(loaded.includes(`/books/m/${no}/rag.json`));
  assert(!loaded.some(p => p.includes(`/books/m/${other}/`)));
  sandbox.window.testPayload.set(book, kp, rag, agents[no], source);
  element('q').value = '本书的核心主张是什么？';
  sandbox.window.testPayload.send();
  const body = requests[0];
  assert(body);
  assert.equal(body.bookNo, no);
  assert.equal(body.docTitle, book.title);
  assert.equal(body.agentName, agents[no].name);
  assert(body.bookMeta.includes(`第${no}号`));
  assert(body.bookPoints.includes(kp.items[0].x));
  assert(body.docText.includes(source.text));
  assert(!body.bookPoints.includes(json(`public/books/m/${other}/keypoints.json`).items[0].x));

  vm.runInContext(read(base + 'unit/core.js'), sandbox);
  const core = sandbox.window.BookUnitCore;
  assert.equal(core.BOOK, `m-${no}`);
  await assert.rejects(core.importArchive({book: `m-${other}`, schemaVersion: '1.0', events: []}));
  let unit = read(base + 'unit/app.js');
  const boot = unit.lastIndexOf('boot().catch(');
  assert(boot >= 0);
  unit = unit.slice(0, boot) + `window.testUnit={set:(m,s)=>{manifest=m;source=s},makePayload};})();`;
  vm.runInContext(unit, sandbox);
  sandbox.window.testUnit.set(manifest, source);
  element('mode').value = 'hint';
  element('question').value = '解释本章主张';
  element('vendor').value = 'ds';
  const payload = sandbox.window.testUnit.makePayload();
  assert.equal(payload.docTitle, book.title);
  assert.equal(payload.agentName, agents[no].name);
  assert(payload.bookMeta.includes(`第${no}卷`) || payload.bookMeta.includes(book.title));
  assert(payload.docText.includes(`/books/m/${no}/text/`));
  assert(!payload.docText.includes(`/books/m/${other}/`));
  assert(payload.docText.includes(source.text));
  outputs.push({number: no, legacyRequest: 'pass', learningPayload: 'pass', crossBookArchiveRejected: true});
}
(async () => {for (const n of [414, 459]) await test(n); console.log(JSON.stringify(outputs, null, 2));})()
  .catch(e => {console.error(e); process.exitCode = 1;});
