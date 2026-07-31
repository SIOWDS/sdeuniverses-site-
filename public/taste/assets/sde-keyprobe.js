/* ============================================================
   SDE · API Key 有效性检测（全站智能体共用一份）
   window.SDEKeyProbe = { verdict, shrink, attach, PROBE_TOKENS, PROBE_MS }

   为什么要真打一次而不是查格式：Key 长得对不代表能用。真实故障是
   ①账户余额不足 ②未实名/未开通该服务 ③这个型号没在账户里开通 ④境外中转不通。
   这四种原来都要等流水线跑到一两小时之后才暴露，代价太大。
   所以检测＝向所选厂商真发一次最小请求：关掉深度思考、预算压到 32 token，
   一次几厘钱、几秒钟，走的路径与真跑逐字相同（同一个 chatHeaders / apiUrl / 中转）。

   判档纪律：只有「这个 Key 本身不能用」才准报 ✗。
   余额不足、限流、型号未开通、厂商故障一律报 ⚠ 并写明「Key 本身有效」——
   报成"无效"会让用户白白去换一把新 Key。

   ⚠ 改本文件必须同步 bump 各页 <script src="...sde-keyprobe.js?v=N">，
     否则 force-cache / 边缘拿到旧版。当前 v=1。
   ============================================================ */
(function () {
  'use strict';

  var PROBE_TOKENS = 32;
  var PROBE_MS = 30000;

  var VENDOR_LABEL = {
    ds: 'DeepSeek', glm: '智谱 GLM', kimi: '月之暗面 Kimi', qwen: '通义千问',
    minimax: 'MiniMax（稀宇）', gpt: 'GPT（OpenAI）', claude: 'Claude（Anthropic）', gemini: 'Gemini（Google）'
  };
  function vendorOf(sel) { return String(sel || '').split(':')[0]; }
  function label(sel) { return VENDOR_LABEL[vendorOf(sel)] || vendorOf(sel) || '所选基底'; }

  /* 把页面自己造的正式 payload 压成一次最小探测：不思考、不流式、预算 32。
     不关思考这条是硬的——顶配档一次"检测"会真的思考几分钟并烧钱。 */
  function shrink(p, sel) {
    var v = vendorOf(sel);
    if (!p || typeof p !== 'object') return p;
    if (v === 'gemini') { p.generationConfig = { maxOutputTokens: PROBE_TOKENS, temperature: 0 }; return p; }
    if ('stream' in p) p.stream = false;
    if (v === 'claude') { p.max_tokens = PROBE_TOKENS; return p; }
    if (p.thinking) p.thinking = { type: 'disabled' };
    if ('reasoning_effort' in p) delete p.reasoning_effort;
    if ('enable_thinking' in p) p.enable_thinking = false;
    if ('reasoning_split' in p) delete p.reasoning_split;
    if ('max_completion_tokens' in p) p.max_completion_tokens = PROBE_TOKENS; else p.max_tokens = PROBE_TOKENS;
    return p;
  }

  /* 纯函数：一次探测的 HTTP 状态 + 响应体 → 三档结论。单独抽出来是为了能被模拟脚本逐条验。 */
  function verdict(status, raw) {
    var t = String(raw == null ? '' : raw);
    var low = t.toLowerCase();
    var j = null; try { j = JSON.parse(t); } catch (_) { }
    if (status === 200 && j) {
      var br = j.base_resp;   // MiniMax 把错误裹在 200 里
      if (br && br.status_code) {
        if (br.status_code === 1004) return { level: 'bad', msg: '✗ 鉴权失败（MiniMax 1004）——Key 不对或尚未生效' };
        if (br.status_code === 1008) return { level: 'warn', msg: '⚠ Key 有效，但账户余额不足（MiniMax 1008）——充值后即可跑' };
        if (br.status_code !== 0) return { level: 'warn', msg: '⚠ 接口返回错误码 ' + br.status_code + '：' + (br.status_msg || '') };
      }
      if (j.error) { var m = (j.error.message || j.error.type || j.error.code || ''); return { level: 'warn', msg: '⚠ 接口在 200 里报了错：' + String(m).slice(0, 160) }; }
    }
    if (status === 200) return { level: 'ok', msg: '✓ Key 有效，所选基底可以调用（已真发一次最小请求验过）' };
    if (status === 401) return { level: 'bad', msg: '✗ Key 无效或未授权（401）——请核对有没有复制全、是不是拿错了厂商的 Key' };
    if (status === 403) return { level: 'bad', msg: '✗ 被拒绝（403）——Key 可能未实名、未开通该服务，或所在地区受限' };
    if (status === 402 || /insufficient[ _-]?balance|余额不足|欠费|arrears/.test(low)) return { level: 'warn', msg: '⚠ Key 本身有效，但账户余额不足（402）——充值后即可跑' };
    if (status === 429) return { level: 'warn', msg: '⚠ Key 有效，但被限流或额度已用尽（429）——稍后再试' };
    if (status === 404 || /model.{0,4}not.{0,4}found|does not exist|无此模型|model_not_found/.test(low)) return { level: 'warn', msg: '⚠ Key 可能有效，但这个基底型号在你的账户下不可用（404）——换一档或去厂商后台开通' };
    if (status === 400 && /(api[_ -]?key|apikey|invalid.{0,16}key|token)/.test(low)) return { level: 'bad', msg: '✗ Key 格式或内容不对（400）：' + t.slice(0, 140) };
    if (status >= 500) return { level: 'warn', msg: '⚠ 厂商或本站中转暂时故障（' + status + '）——不是你的 Key 的问题，稍后再试' };
    return { level: 'warn', msg: '⚠ 未能判定（' + status + '）：' + t.slice(0, 160) };
  }

  var CSS = '.sdekp-btn{display:inline-block;background:rgba(212,178,94,0.12);border:1px solid rgba(212,178,94,0.32);color:#D9BE72;border-radius:8px;padding:5px 12px;font-size:12.5px;line-height:1.4;cursor:pointer;margin-top:7px;font-family:inherit}'
    + '.sdekp-btn:hover:not(:disabled){border-color:#D4B25E;color:#E5C86E}'
    + '.sdekp-btn:disabled{opacity:0.45;cursor:not-allowed}'
    + '.sdekp-btn{align-self:flex-start}'
    + '.sdekp-msg{display:block;flex-basis:100%;font-size:12px;color:#8B98A5;margin-top:5px;line-height:1.55;word-break:break-word}'
    + '.sdekp-msg.ok{color:#5FBF7F}.sdekp-msg.warn{color:#E8A33D}.sdekp-msg.bad{color:#E06C60}';
  function injectCSS() {
    if (document.getElementById('sdekp-css')) return;
    var s = document.createElement('style'); s.id = 'sdekp-css'; s.textContent = CSS;
    (document.head || document.documentElement).appendChild(s);
  }

  function el(id) { return document.getElementById(id); }

  /* 真跑一次探测。hooks 由各页提供自己的那一套（同一套函数，真跑与检测共用）。 */
  async function run(sel, key, btn, msg, hooks) {
    if (!sel || sel === 'off' || sel === 'follow') {
      msg.className = 'sdekp-msg warn';
      msg.textContent = '这一席跟随/关闭时用的是主基底那个 Key，检测主基底那个即可。';
      return;
    }
    if (!key) { msg.className = 'sdekp-msg bad'; msg.textContent = '请先把 Key 填进上面的框。'; return; }
    var overseas = hooks.isOverseas ? !!hooks.isOverseas(sel) : false;
    var old = btn.textContent;
    btn.disabled = true; btn.textContent = '检测中…';
    msg.className = 'sdekp-msg';
    msg.textContent = '正在向 ' + label(sel) + ' 发一次最小请求（' + (overseas ? '经本站中转' : '浏览器直连') + '，约几秒，几乎不计费）……';
    var ac = new AbortController();
    var killer = setTimeout(function () { try { ac.abort(); } catch (_) { } }, PROBE_MS);
    var v;
    try {
      var url = overseas ? (hooks.proxyUrl || '/api/llm-proxy') : hooks.apiUrl(sel);
      var payload = shrink(hooks.buildPayload(sel, '回答一个字。', '嗨', PROBE_TOKENS), sel);
      var r = await fetch(url, { method: 'POST', headers: hooks.chatHeaders(sel, key), body: JSON.stringify(payload), signal: ac.signal });
      var raw = ''; try { raw = await r.text(); } catch (_) { }
      v = verdict(r.status, raw);
    } catch (e) {
      v = {
        level: 'warn', msg: (e && e.name === 'AbortError')
          ? '⚠ ' + Math.round(PROBE_MS / 1000) + ' 秒内没有响应——网络或中转不通，这一次没能判定 Key'
          : '⚠ 请求发不出去：' + (e && e.message ? e.message : e) + (overseas ? '（境外基底走本站中转，可能是中转不通）' : '（国内直连，可能是网络或浏览器插件拦截）')
      };
    }
    clearTimeout(killer);
    btn.disabled = false; btn.textContent = old;
    msg.className = 'sdekp-msg ' + v.level; msg.textContent = v.msg;
  }

  /* list = [{key:'apiKey', sel:'modelSel'} | {key:'dsKey', model:'ds:pro'}]
     按钮与结论位由本模块注入到 Key 输入框之后——各页 HTML 一行不用改。
     改 Key、换基底都会清掉上一次结论，免得旧结论贴在新基底上。 */
  function attach(list, hooks) {
    injectCSS();
    var n = 0;
    (list || []).forEach(function (item) {
      var input = el(item.key);
      if (!input || input.__sdekpWired) return;
      var selEl = item.sel ? el(item.sel) : null;
      if (item.sel && !selEl) return;
      var btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'sdekp-btn'; btn.id = 'sdekp-btn-' + item.key;
      btn.textContent = '🔎 检测这个 Key 是否有效';
      var msg = document.createElement('span');
      msg.className = 'sdekp-msg'; msg.id = 'sdekp-msg-' + item.key;
      /* 落位：默认紧跟输入框；item.at 给一个祖先选择器时改为挂到那个容器末尾——
         用于 .key-row 这类"输入框＋显示钮"且不换行的 flex 行，插在行内会把行挤扁。 */
      if (item.at) {
        var box = (input.closest ? input.closest(item.at) : null) || input.parentNode;
        box.appendChild(btn); box.appendChild(msg);
      } else {
        var host = input.parentNode;
        host.insertBefore(btn, input.nextSibling);
        host.insertBefore(msg, btn.nextSibling);
      }
      function clear() { msg.className = 'sdekp-msg'; msg.textContent = ''; }
      btn.addEventListener('click', function () {
        var sel = selEl ? selEl.value : item.model;
        run(sel, String(input.value || '').trim(), btn, msg, hooks);
      });
      input.addEventListener('input', clear);
      if (selEl) selEl.addEventListener('change', clear);
      input.__sdekpWired = 1;
      n++;
    });
    return n;
  }

  window.SDEKeyProbe = { verdict: verdict, shrink: shrink, attach: attach, run: run, PROBE_TOKENS: PROBE_TOKENS, PROBE_MS: PROBE_MS, label: label };
})();
