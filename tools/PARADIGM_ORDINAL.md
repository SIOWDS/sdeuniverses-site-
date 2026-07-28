# 每日必读 · 序号怎么领

## 为什么改

序号原本由发布者临发布时从栏目页现状推算。两条线并行时，双方在相隔几分钟内
各自算出同一个「下一个号」，于是必撞——一天之内撞了四次。每撞一次要回头改四处
（文章页 art-series、read.html、栏目页卡片、PDF 封面），极易漏改。

## 怎么改的

把号从「推算出来的」改成「领来的」。

`public/paradigm/ordinals.json` 是唯一真相，形如：

```json
{ "1": "paradigm/taken-out", "5": "column/power-to-stop", "21": "paradigm/swapped-out" }
```

**领号 = 写台账 + 立刻 push。push 成功才算领到。**
远端只会接受先到的那一次写入，后到的被拒；被拒就 pull 一次重领。
原子性来自 git 本身，不需要任何锁。

## 发布脚本怎么用

```python
from paradigm_ordinal import claim
no, NO_CN = claim("paradigm/my-slug", title="标题")   # → (24, "二十四")
```

放在**生成正文与 PDF 之前**——先把号占住，再干耗时的活。
补发或重建已发布的篇目时，跳过领号：

```bash
python3 tools/publish_xxx.py --src …/essay.md --ordinal 二十一
```

## 日常自检

```bash
python3 tools/paradigm_ordinal.py --audit
```

一次查四处是否一致：台账 / 栏目页卡片 / 文章页题头 / read.html。
有重复、缺口、或某一处写的号跟别处不一样，都会被列出来。

**建议跟 check_page_integrity.py 一起，作为每次推送前的固定两步。**

## 另一条线怎么接过去

只需两行：把自己脚本里硬写的 `NO_CN = "…"` 换成上面那句 `claim(...)`。
不接也不会坏：领号时会把台账与栏目页现状**并起来**看，取两者的最大值，
所以即使只有一条线接入，也不会领到对方已经占掉的号。
只是那种情况下台账会落后于现状，需要偶尔 `--backfill` 一次把它对齐。

## 边界

- 台账只管 /paradigm/ 这个栏目的序号，别处不受影响。
- 外链篇（文章物理上不在 /paradigm/ 下，如之五在 /column/power-to-stop/）
  在台账里存完整站内路径，审计会按路径去找它的页面。
- `--backfill` 用栏目页现状重建台账，用于初始化或台账损坏时的恢复。
