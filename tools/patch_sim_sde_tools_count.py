# -*- coding: utf-8 -*-
"""把 sde_tools 模拟里写死的「九」改成跟着白名单走 —— 加一道工序就得改三处数字，
   这种断言迟早会被人图省事直接删掉。"""
P = "/home/claude/site/tools/sim_wds_sde_tools.js"
s = open(P, encoding="utf-8").read()
def sub1(old, new):
    assert s.count(old) == 1, old[:50]
    return s.replace(old, new, 1)
s = sub1('console.log("① 九道工序齐全且各有实体");\nconst KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "grid", "nine"];',
         'console.log("① 每道工序齐全且各有实体");\n'
         '// 别写死数量：加一道工序就要改三处数字，这种断言迟早被人图省事删掉。跟着白名单走。\n'
         'const KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "grid", "nine", "map"];')
s = sub1('ok(/本轮工序/.test(seg) && (seg.match(/本轮工序/g) || []).length === 9, "九道都以「本轮工序」开头，实得 " + (seg.match(/本轮工序/g) || []).length);',
         'ok(/本轮工序/.test(seg) && (seg.match(/本轮工序/g) || []).length === KEYS.length, "每道都以「本轮工序」开头，应 " + KEYS.length + " 道，实得 " + (seg.match(/本轮工序/g) || []).length);')
s = sub1('ok(bodies.length === 9, "切出九段工序正文，实得 " + bodies.length);',
         'ok(bodies.length === KEYS.length, "切出 " + KEYS.length + " 段工序正文，实得 " + bodies.length);')
# bodies 的顺序按源码出现次序，KEYS 是白名单次序，两者不一定同序——名字改成从段首自取
s = sub1('bodies.forEach((b, i) => ok(OUT.test(b), KEYS[i] + " 留了「做不到就直说」的出口"));',
         'bodies.forEach((b) => ok(OUT.test(b), (b.match(/^([a-z]+):/) || [0, "?"])[1] + " 留了「做不到就直说」的出口"));')
open(P, "w", encoding="utf-8").write(s)
print("已修")
