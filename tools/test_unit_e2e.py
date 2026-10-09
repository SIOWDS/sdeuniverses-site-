#!/usr/bin/env python3
"""三位一体单元端到端（真实 Chromium + 真实 IndexedDB/localStorage；模型用替身，不是真实模型验收）。
用法: python3 tools/test_unit_e2e.py [repo_root]"""
import sys, os, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
PUB = os.path.join(ROOT, "public")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def translate_path(self, p):
        p = p.split("?")[0].split("#")[0]
        r = os.path.join(PUB, p.lstrip("/"))
        return os.path.join(r, "index.html") if os.path.isdir(r) else r
srv = socketserver.TCPServer(("127.0.0.1", 0), Q); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
B = "http://127.0.0.1:%d" % port
ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1
    else: fail += 1; print("FAIL:", m)
def sse(tokens, end=True, truncated=False):
    out = "".join("data: " + json.dumps({"t": "token", "v": t}, ensure_ascii=False) + "\n\n" for t in tokens)
    if end: out += "data: " + json.dumps({"t": "end", "v": {"truncated": truncated}}) + "\n\n"
    return out + "data: [DONE]\n\n"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium") if os.path.exists("/opt/pw-browsers/chromium") else None)
    def newctx():
        ctx = br.new_context(); pg = ctx.new_page()
        ctx.add_init_script("localStorage.setItem('sde_wds_key','sk-test-fake-key-0000');localStorage.setItem('sde_wds_vendor','ds');")
        return ctx, pg
    # ---- 1 完整回答：预览只含勾选材料，采纳需本人文字，记录落账
    ctx, pg = newctx(); bodies = []
    def handler(route):
        bodies.append(json.loads(route.request.post_data)); route.fulfill(status=200, headers={"content-type": "text/event-stream"}, body=sse(["建议：", "把名词目标改成动词目标。"]))
    pg.route("**/api/wds/read", handler)
    pg.goto(B + "/books/m/3/agent/?node=P1&task=diagnose")
    pg.evaluate("localStorage.setItem('wds_learn_3', JSON.stringify({p:{P1:{s:3,a1:'目标要更具体',a2:'名词化了，应改成动词',t:'',r:[],read:{},done:false}}}))")
    pg.reload(); pg.wait_for_selector("#unitBar", timeout=20000)
    check("空目标" in pg.inner_text("#unitBar"), "node bar shows title")
    check(pg.locator("#unitBar .ut button[aria-pressed=true]").inner_text() == "比较理解", "task from URL")
    pg.fill("#unitBar #uExtra", "我反对这一条（异议文字）"); pg.click("#send")
    pg.wait_for_selector("#uMats", timeout=5000)
    txt = pg.inner_text("#uMats")
    check("目标要更具体" in txt and "名词化了" in txt, "preview shows a1/a2 text")
    check(not bodies, "nothing sent before confirm")
    # 取消勾选复答
    pg.locator("#uMats input").nth(1).uncheck()
    pg.click("#uOk"); pg.wait_for_selector(".usug", timeout=10000)
    b = bodies[0]; kinds = [m["kind"] for m in b["unit"]["materials"]]
    check(kinds == ["a1"], "only checked material sent: %s" % kinds)
    check(b["history"] == [], "no chat history sent in unit mode")
    check("我反对这一条" not in json.dumps(b, ensure_ascii=False), "unchecked objection not sent")
    check(b["unit"]["task"] == "diagnose" and b["unit"]["node"]["id"] == "P1", "task+node in request")
    led = json.loads(pg.evaluate("localStorage.getItem('wds_unit_3')"))
    types = [e["type"] for e in led["events"]]
    check(types == ["prepared", "sent", "receipt"], "ledger order %s" % types)
    check(led["events"][2]["status"] == "complete", "complete receipt")
    check(pg.get_by_role('button', name='采纳', exact=True).count() == 1, "adopt available for complete")
    pg.get_by_role('button', name='采纳', exact=True).click(); pg.wait_for_selector("#uRev")
    pg.click("#uOk2")   # 空文字：应拒绝
    pg.wait_for_timeout(300)
    led = json.loads(pg.evaluate("localStorage.getItem('wds_unit_3')")); check(not any(e["type"] == "revision" for e in led["events"]), "empty adopt refused")
    pg.once("dialog", lambda d: d.accept())
    pg.fill("#uRev", "我采纳：把名词目标改成动词目标，因为……"); pg.click("#uOk2"); pg.wait_for_timeout(300)
    led = json.loads(pg.evaluate("localStorage.getItem('wds_unit_3')")); rv = [e for e in led["events"] if e["type"] == "revision"]
    check(len(rv) == 1 and rv[0]["confirmedBy"] == "reader" and rv[0]["stance"] == "adopt", "reader revision stored")
    # 学习页能看到本人修订
    pg.goto(B + "/books/learn/?b=3#/p/P1/3"); pg.wait_for_selector(".card", timeout=10000)
    pg.evaluate("location.hash='#/p/P1/4'"); pg.wait_for_timeout(500)
    check("我采纳：把名词目标改成动词目标" in pg.inner_text("#app"), "learn page shows my revision")
    ctx.close()
    # ---- 2 中断回答：不能采纳，只能独立修订
    ctx, pg = newctx()
    pg.route("**/api/wds/read", lambda r: r.fulfill(status=200, headers={"content-type": "text/event-stream"}, body=sse(["半截回答"], end=False)))
    pg.goto(B + "/books/m/3/agent/?node=P1&task=hint"); pg.wait_for_selector("#unitBar", timeout=20000)
    pg.click("#send"); pg.wait_for_selector("#uOk"); pg.click("#uOk"); pg.wait_for_selector(".usug", timeout=10000)
    check(pg.get_by_role('button', name='采纳', exact=True).count() == 0 and pg.locator(".usug button:has-text('我自己重写')").count() == 1, "interrupted: no adopt, independent allowed")
    led = json.loads(pg.evaluate("localStorage.getItem('wds_unit_3')")); check([e for e in led["events"] if e["type"] == "receipt"][0]["status"] == "interrupted", "interrupted receipt")
    ctx.close()
    # ---- 3 服务错误 / 无节点时不启用 / 无密钥
    ctx, pg = newctx()
    pg.route("**/api/wds/read", lambda r: r.fulfill(status=500, body="boom"))
    pg.goto(B + "/books/m/3/agent/?node=P1"); pg.wait_for_selector("#unitBar", timeout=20000)
    pg.fill("#q", "问一句"); pg.click("#send"); pg.wait_for_selector("#uOk"); pg.click("#uOk"); pg.wait_for_timeout(1500)
    led = json.loads(pg.evaluate("localStorage.getItem('wds_unit_3')")); rc = [e for e in led["events"] if e["type"] == "receipt"]
    check(rc and rc[0]["status"] == "error", "http 500 -> error receipt")
    ctx.close()
    ctx, pg = newctx(); pg.goto(B + "/books/m/3/agent/"); pg.wait_for_selector("#app", state="visible", timeout=20000)
    check(pg.locator("#unitBar").count() == 0, "no node param -> classic agent unchanged")
    ctx.close()
    ctx, pg = newctx(); pg.goto(B + "/books/m/3/agent/?node=P99"); pg.wait_for_selector("#app", state="visible", timeout=20000); pg.wait_for_timeout(500)
    check(pg.locator("#unitBar").count() == 0, "unknown node -> not enabled")
    ctx.close()
    # ---- 4 手机宽度无横向溢出
    ctx = br.new_context(viewport={"width": 390, "height": 800}); pg = ctx.new_page()
    pg.goto(B + "/books/m/3/agent/?node=P1"); pg.wait_for_selector("#unitBar", timeout=20000)
    check(pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), "no horizontal overflow at 390px")
    ctx.close(); br.close()
print("%d passed, %d failed" % (ok, fail)); sys.exit(1 if fail else 0)
