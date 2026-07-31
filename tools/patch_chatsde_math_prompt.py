# -*- coding: utf-8 -*-
"""ChatSDE 的答题 system 里加一条硬性【数学写法】。

根子在这里：基底按键盘写法输出 `e^(i3θ)`，前端再神也只是补救。
前端兜底（wds-mode.js 的 texify）照做不误，但两层的次序是：**先让它写对**。

幂等。
"""
import io, sys

P = "src/worker.js"
h = io.open(P, encoding="utf-8").read()
if "【数学写法】" in h:
    print("already patched"); sys.exit(0)

OLD = ('    + "\\n5. 说人话，短——两三段以内，别写论文。不确定就说不确定；绝不寒暄或\\"好的/我将\\"之类元话，'
       '直接从核心那句说起；结尾可留一个把读者往下一步推的反问或一句荐读。"\n')
assert h.count(OLD) == 1, "锚点不唯一/找不到 (count=%d)" % h.count(OLD)

NEW = OLD + (
    '    + "\\n\\n【数学写法（页面用 KaTeX 排版，写错了就排不出来）】"\n'
    '    + "\\n· 凡是数学式子，一律用 LaTeX 写，**不许用键盘代码写法**。"\n'
    '    + "\\n· 行内式包在 $…$ 里，独立成行的式子包在 $$…$$ 里。"\n'
    '    + "\\n· 指数写 $e^{i3\\\\theta}$，不写 e^(i3θ)；下标写 $x_{1}$，不写 x_1 或 x1。"\n'
    '    + "\\n· 希腊字母在式子里写 \\\\theta \\\\pi \\\\alpha \\\\lambda，不直接打 θ π α λ。"\n'
    '    + "\\n· 三角与对数写 \\\\cos 3\\\\theta、\\\\sin\\\\theta、\\\\log x、\\\\ln x，不写 cos3θ、sinθ。"\n'
    '    + "\\n· 分式写 \\\\frac{a}{b}，根号写 \\\\sqrt{x}，乘号写 \\\\cdot 或 \\\\times，积分求和写 \\\\int、\\\\sum。"\n'
    '    + "\\n· **绝不要把公式放进代码块（``` 或 `）里**——那会被当代码原样显示，不排版成公式。"\n'
    '    + "\\n· 正文里单独提一个符号（S、D、E 这类）不必套 $，只有真是式子时才套。"\n'
    '    + "\\n· 例：欧拉公式该写成 $e^{i3\\\\theta} = \\\\cos 3\\\\theta + i\\\\sin 3\\\\theta$，'
    '也可写成 $$e^{i3\\\\theta} = (e^{i\\\\theta})^{3} = (\\\\cos\\\\theta + i\\\\sin\\\\theta)^{3}$$"\n'
)
h = h.replace(OLD, NEW)
io.open(P, "wb").write(h.encode("utf-8"))
print("patched", P)
