#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""顶配 DeepSeek(v4-pro,思考满档)输出上限高:把 WDS 走 deepseek+guide 这一路的每次生成 max_tokens
放大到 50000(≈5万中文字量级),让思考先吃 token 后仍有足够头寸写长正文/不被截断。
只动 deepseek+guide:其他厂商(GLM)的 guide 维持原值,陪读轻档维持原值。四处:答题/分部/总结/拟题。
assert 锚定;每处应恰 1 次。"""

W = "src/worker.js"
h = open(W, encoding="utf-8").read()

subs = [
    # 答题(/api/wds/read guide):deepseek+guide→5万,GLM guide 仍 8000,陪读仍 2200
    ('max_tokens: b.guide ? 8000 : 2200',
     'max_tokens: (b.guide && vd === "deepseek") ? 50000 : (b.guide ? 8000 : 2200)'),
    # 论文分部(read-paper part)
    ('max_tokens: 3600',
     'max_tokens: (GD && vd === "deepseek") ? 50000 : 3600'),
    # 总结(read-paper summary)
    ('max_tokens: 3200',
     'max_tokens: (GD && vd === "deepseek") ? 50000 : 3200'),
    # 拟题(read-paper plan):deepseek+guide 给思考满头寸→更少 JSON 截断重试;GLM guide 仍 8000,陪读仍 2400
    ('const planTok = GD ? 8000 : 2400;',
     'const planTok = (GD && vd === "deepseek") ? 50000 : (GD ? 8000 : 2400);'),
]
for old, new in subs:
    n = h.count(old)
    assert n == 1, "anchor not unique (%d): %s" % (n, old[:50])
    h = h.replace(old, new, 1)

open(W, "w", encoding="utf-8").write(h)
print("✅ deepseek+guide 四处 max_tokens 放大到 50000(答题/分部/总结/拟题);GLM guide 与陪读档未动")
