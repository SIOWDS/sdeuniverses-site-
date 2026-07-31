#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""入口页三角形正中放「爱思乐园」四个字

位置取三角形的重心：三个顶点是 (50,9) (91,84) (9,84)，重心 = (50, 59)。
写死 50% / 59% 会在改顶点坐标时飘出去，所以由 NODES 现算——三角形与三个入口
已经共用一组坐标了，中间这四个字也该跟着同一组走。
"""
P = "/home/claude/site/public/assets/sde-portal.js"
h = open(P, encoding="utf-8").read()


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    h = h.replace(old, new, 1)


sub1(
    '    ".sdep-nm{font:700 14.5px/1 inherit;letter-spacing:.5px;white-space:nowrap}" +',
    '    /* 三角形正中的字号：letter-spacing 会在最后一个字后面也加一份，右边看着就偏了，'
    '所以补一个等量的负边距把它抵掉 */\n'
    '    ".sdep-mid{position:absolute;transform:translate(-50%,-50%);pointer-events:none;'
    'font:700 clamp(20px,3.8vw,38px)/1 inherit;letter-spacing:.34em;margin-right:-.34em;'
    'color:#D4B25E;text-shadow:0 0 26px rgba(212,178,94,.28);white-space:nowrap;'
    'animation:sdepPop .6s ease 1s both}" +\n'
    '    ".sdep-nm{font:700 14.5px/1 inherit;letter-spacing:.5px;white-space:nowrap}" +',
    "中间四个字的样式",
)
sub1(
    '    stage.appendChild(svg);\n',
    '    stage.appendChild(svg);\n'
    '    // 正中「爱思乐园」：位置由三个顶点现算重心，改顶点它自己跟着走，不写死\n'
    '    var mid = document.createElement("div");\n'
    '    mid.className = "sdep-mid";\n'
    '    mid.textContent = "\\u7231\\u601d\\u4e50\\u56ed";\n'
    '    mid.setAttribute("aria-hidden", "true");\n'
    '    var cx = 0, cy = 0;\n'
    '    NODES.forEach(function (n) { cx += n.x; cy += n.y; });\n'
    '    mid.style.left = (cx / NODES.length) + "%";\n'
    '    mid.style.top = (cy / NODES.length) + "%";\n'
    '    stage.appendChild(mid);\n',
    "中间四个字",
)
open(P, "w", encoding="utf-8").write(h)
print("sde-portal.js 已加中间四字")
