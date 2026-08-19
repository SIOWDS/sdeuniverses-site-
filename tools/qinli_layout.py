# -*- coding: utf-8 -*-
"""秦莉专栏版式统一：把四批不同模板攒出来的页面收敛到一套。

改四处（都只动展示层，不动正文）：
  ① <title> 后缀 → 「· 秦莉 · SDE 学员专栏」（原有四种写法）
  ② readbar 返回链 → 「‹ 秦莉 · 全部作品」指向 works/（原有四种指向与文案）
  ③ 三读法按钮补齐图标（有两页是纯文字）
  ④ 眉题 art-series 去掉内部批次标签（「金点子③ 纠缠(E)」这类读者不解其意）

不动的：正文、各页专有模块（.xp-* 评审卡、.tk-* 工具卡）、页脚金点子发生器导流区、
《发生的宇宙》与《审美发生方程》的正文术语（这两篇讲的就是 SDE 本体论，改了就毁文）。
"""
import re
from pathlib import Path

STU = Path(__file__).resolve().parents[1] / "public" / "students" / "qin-li"
SKIP = {"works", "poems", "essays"}

TITLE_SUFFIX = " · 秦莉 · SDE 学员专栏"
NAV = '<a class="nav-back" href="/students/qin-li/works/">‹ 秦莉 · 全部作品</a>'

# 眉题里要摘掉的内部批次标签
SERIES_STRIP = re.compile(r"\s*·\s*金点子[①②③④⑤]?\s*(?:显露\(S\)|差异\(D\)|纠缠\(E\)|新典范)?\s*")


def fix_title(t, log):
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    if not m:
        return t
    old = m.group(1).strip()
    # 取正题：第一个 · 或 | 之前
    head = re.split(r"\s*[·|]\s*", old)[0].strip()
    new = head + TITLE_SUFFIX
    if new == old:
        return t
    log.append(f"标题「…{old[-22:]}」→「…{TITLE_SUFFIX.strip()}」")
    return t.replace(m.group(0), f"<title>{new}</title>", 1)


def fix_nav(t, log):
    m = re.search(r'<a class="nav-back"[^>]*>.*?</a>', t, re.S)
    if not m:
        return t
    if m.group(0) == NAV:
        return t
    lbl = re.sub(r"<[^>]+>", "", m.group(0)).strip()
    log.append(f"返回链「{lbl}」→「‹ 秦莉 · 全部作品」")
    return t.replace(m.group(0), NAV, 1)


def fix_modes(t, log):
    n = 0
    for plain, rich in (("长文阅读", "📖 长文阅读"), ("在线 PDF", "📄 在线 PDF"), ("下载 PDF", "⬇ 下载 PDF")):
        pat = re.compile(r'(<(?:span|a) class="rb-btn[^"]*"[^>]*>)' + re.escape(plain) + r"(</(?:span|a)>)")
        t, k = pat.subn(r"\1" + rich + r"\2", t)
        n += k
    if n:
        log.append(f"三读法按钮补图标 {n} 个")
    return t


def fix_series(t, log):
    m = re.search(r'<div class="art-series">(.*?)</div>', t, re.S)
    if not m:
        return t
    old = m.group(1)
    new = SERIES_STRIP.sub("", old).strip()
    if new == old.strip():
        return t
    log.append(f"眉题去内部标签：「{old.strip()}」→「{new}」")
    return t.replace(m.group(0), f'<div class="art-series">{new}</div>', 1)


def main():
    dirs = sorted(d for d in STU.iterdir()
                  if d.is_dir() and (d / "index.html").exists() and d.name not in SKIP)
    touched = 0
    for d in dirs:
        f = d / "index.html"
        src = f.read_text(encoding="utf-8")
        log = []
        t = src
        tags_before = len(re.findall(r"<[a-zA-Z/][^>]*>", t))
        t = fix_title(t, log)
        t = fix_nav(t, log)
        t = fix_modes(t, log)
        t = fix_series(t, log)
        if t == src:
            continue
        assert len(re.findall(r"<[a-zA-Z/][^>]*>", t)) == tags_before, f"{d.name} 标签数变了"
        assert t.count("<title>") == 1 and t.count("<html") == 1, f"{d.name} 结构异常"
        f.write_text(t, encoding="utf-8")
        touched += 1
        print(f"  ✓ {d.name}")
        for x in log:
            print(f"      · {x}")
    print(f"\n  共调整 {touched} 页")


if __name__ == "__main__":
    main()
