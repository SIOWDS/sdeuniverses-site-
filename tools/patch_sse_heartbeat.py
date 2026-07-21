#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 WDS 的四条 SSE 流加保活心跳:/api/wds/read(答题) + /api/wds/read-paper 的 plan/part/summary。
出流后每 15 秒往流里塞一个 SSE 注释行 ": ping"(客户端只认 data: 行,自动忽略),在思考满档模型
"只思考不吐正文"的长静默期保持连接活着,避免被 Cloudflare/代理/浏览器的空闲超时掐断。finalizer 清除定时器。
纯附加:不改任何逻辑与产出字符串(e2e 断言不受影响)。assert 锚定。"""

W = "src/worker.js"
h = open(W, encoding="utf-8").read()

# ---- 1) /api/wds/read:finalizer 名为 done(10 空格缩进),唯一 ----
READ_OLD = r'''          const done = () => { try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };'''
assert h.count(READ_OLD) == 1, "read 'done' finalizer anchor not unique"
READ_NEW = r'''          let _hb = null;
          const done = () => { if (_hb) clearInterval(_hb); try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
          _hb = setInterval(() => { try { controller.enqueue(_ENC.encode(": ping\n\n")); } catch (e) {} }, 15000);'''
h = h.replace(READ_OLD, READ_NEW, 1)

# ---- 2) read-paper 三个 mode:finalizer 名为 fin(12 空格缩进),三处完全相同 → 全部替换 ----
FIN_OLD = r'''            const fin = () => { try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };'''
n_fin = h.count(FIN_OLD)
assert n_fin == 3, "expected exactly 3 'fin' finalizers in read-paper, got %d" % n_fin
FIN_NEW = r'''            let _hb = null;
            const fin = () => { if (_hb) clearInterval(_hb); try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
            _hb = setInterval(() => { try { controller.enqueue(_ENC.encode(": ping\n\n")); } catch (e) {} }, 15000);'''
h = h.replace(FIN_OLD, FIN_NEW)   # 无 count → 三处一并替换

open(W, "w", encoding="utf-8").write(h)
print("✅ 四条 SSE 流已加 15s 保活心跳(read×1 + read-paper×3),finalizer 清除定时器")
