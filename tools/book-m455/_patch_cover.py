"""一次性补丁：把由第 520 号复制来的 cover.py 改成第 455 号《晕痛苦》的封面与封底。"""
from pathlib import Path

p = Path(__file__).parent / 'cover.py'
s = p.read_text()
s = s.replace("ISBN = '979-8-90690-520-8'", "ISBN = '979-8-90690-455-3'")
s = s.replace('第 520 号《欠：走了两步的发生》（王德生著）封面与封底（由第 519 号改来，回到藏青底，220 系列版式）：主图是金环里一张没合上的口，口里三颗点——两颗实心，第三颗虚线空心（回写未到）。',
              '第 455 号《晕痛苦——SDE 方法论的三种不顺》（王德生著）封面与封底（照第五二〇号工具链，藏青底，220 系列版式）：主图是金环里三枚小圆章——旋涡（晕）、断路（痛）、将熄的火（苦）——环心一颗金菱形（平·通·足）。')
a0 = s.index('def art(W, H, uid):')
a1 = s.index('def barcode(')
ART = '''def art(W, H, uid):
    """主图（第 455 号）：金环里三枚小圆章排成三角——上为旋涡（晕：坐标乱了）、左下为一条被横杠截断的路（痛：走不过去）、
    右下为一簇将熄的火苗（苦：走不动）；三章之间虚线相连，环心一颗金菱形（平·通·足）。环下标「晕 · 痛 · 苦」。"""
    import random
    rnd = random.Random(455)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.60, 470 * s
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".30"/>
  <stop offset=".5" stop-color="{GOLD}" stop-opacity=".08"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
</defs>"""]
    out.append(rings(cx, cy, r).replace('{uid}', uid))
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*0.70:.0f}" fill="url(#glow{uid})"/>')
    R = r * 0.50
    pos = [(cx, cy - R), (cx - R * 0.87, cy + R * 0.5), (cx + R * 0.87, cy + R * 0.5)]
    m = 118 * s
    for i in range(3):
        (x1, y1), (x2, y2) = pos[i], pos[(i + 1) % 3]
        out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{GOLD}" stroke-opacity=".40" stroke-width="{2.4*s:.1f}" stroke-dasharray="{10*s:.0f} {9*s:.0f}"/>')
    for (x, y) in pos:
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{m:.0f}" fill="#13264A" stroke="{GOLD2}" stroke-width="{5*s:.1f}"/>')
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{m*1.12:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".30" stroke-width="{1.6*s:.1f}"/>')
    x, y = pos[0]
    pts = []
    for i in range(220):
        t = i / 219 * 5.2 * math.pi
        rr = m * 0.80 * (1 - i / 260)
        pts.append((x + rr * math.cos(t), y + rr * math.sin(t)))
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in pts[::-1]) + f'" fill="none" stroke="{CREAM}" stroke-width="{5.5*s:.1f}" stroke-linecap="round"/>')
    x, y = pos[1]
    out.append(f'<path d="M {x-m*0.75:.0f} {y+m*0.35:.0f} Q {x-m*0.35:.0f} {y-m*0.45:.0f} {x-m*0.08:.0f} {y-m*0.05:.0f}" fill="none" stroke="{CYAN}" stroke-width="{10*s:.0f}" stroke-linecap="round"/>')
    out.append(f'<path d="M {x+m*0.22:.0f} {y+m*0.10:.0f} Q {x+m*0.45:.0f} {y+m*0.40:.0f} {x+m*0.75:.0f} {y-m*0.30:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".40" stroke-width="{10*s:.0f}" stroke-linecap="round" stroke-dasharray="{12*s:.0f} {12*s:.0f}"/>')
    out.append(f'<line x1="{x+m*0.06:.0f}" y1="{y-m*0.42:.0f}" x2="{x+m*0.06:.0f}" y2="{y+m*0.46:.0f}" stroke="{GOLD2}" stroke-width="{13*s:.0f}" stroke-linecap="round"/>')
    x, y = pos[2]
    out.append(f'<path d="M {x:.0f} {y-m*0.62:.0f} C {x+m*0.48:.0f} {y-m*0.10:.0f} {x+m*0.42:.0f} {y+m*0.48:.0f} {x:.0f} {y+m*0.55:.0f} C {x-m*0.42:.0f} {y+m*0.48:.0f} {x-m*0.48:.0f} {y-m*0.05:.0f} {x:.0f} {y-m*0.62:.0f} Z" fill="{GOLD}" fill-opacity=".18" stroke="{GOLD2}" stroke-opacity=".75" stroke-width="{4*s:.1f}" stroke-dasharray="{9*s:.0f} {7*s:.0f}"/>')
    out.append(f'<ellipse cx="{x:.0f}" cy="{y+m*0.30:.0f}" rx="{m*0.16:.0f}" ry="{m*0.20:.0f}" fill="{GOLD2}" fill-opacity=".85"/>')
    k = 34 * s
    out.append(f'<path d="M {cx:.0f} {cy-k:.0f} L {cx+k*0.7:.0f} {cy:.0f} L {cx:.0f} {cy+k:.0f} L {cx-k*0.7:.0f} {cy:.0f} Z" fill="{GOLD2}"/>')
    base = cy + r * 0.86
    for (x, lab) in [(cx - r * 0.42, '晕'), (cx, '痛'), (cx + r * 0.42, '苦')]:
        out.append(f'<circle cx="{x:.0f}" cy="{base:.0f}" r="{9*s:.0f}" fill="{GOLD2}"/>')
        out.append(f'<text x="{x:.0f}" y="{base + 56*s:.0f}" font-size="{34*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" fill="{CREAM}" fill-opacity=".9" letter-spacing="{6*s:.0f}">{lab}</text>')
    out.append(f'<line x1="{cx - r*0.62:.0f}" y1="{base:.0f}" x2="{cx + r*0.62:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    for _ in range(60):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.40):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
    return ''.join(out)


'''
s = s[:a0] + ART + s[a1:]
reps = [
    ('<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 520 号</div>', '<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 455 号</div>'),
    ('<div class="t"><div class="pre">普通人都能明白的</div><div class="big" style="font-size:{70*s:.1f}pt">欠</div>\n<div class="sub">走了两步的发生</div><div class="rule"></div></div>',
     '<div class="t"><div class="pre">SDE 方法论的三种不顺</div><div class="big" style="font-size:{60*s:.1f}pt">晕痛苦</div>\n<div class="sub">晕是不知往哪走，痛是走不过去，苦是走不动</div><div class="rule"></div></div>'),
    ('<div class="q">欠不是账上的负数，<br>是一次发生走了两步、<br>还差回写的那一步。</div><div class="by">——前言</div>',
     '<div class="q">三方程失衡，叫做晕；<br>六路径不通，叫做痛；<br>三原理动力疲软，叫做苦。</div><div class="by">——总母题</div>'),
    ('<div class="gold">第三步到了没有？</div>', '<div class="gold">此刻，你是晕，是痛，还是苦？</div>'),
    ('德麦国际专著第 520 号 · 三篇九编五十四章 · 约 20 万字<br>ISBN 979-8-90690-520-8 · 定价 US$20.00',
     '德麦国际专著第 455 号 · 五编三十三章 · 约 52 万字<br>ISBN 979-8-90690-455-3 · 定价 US$30.00'),
]
for a, b in reps:
    assert a in s, a[:40]
    s = s.replace(a, b)
i0 = s.index('<div class="bl"><p>还清了')
i1 = s.index('</div>\n<div class="gold">')
s = s[:i0] + '''<div class="bl"><p>同样说「难受」，有人不知往哪走，有人知道往哪走却走不过去，有人路通着却走不动。三种不顺常被混成一个词，处理就常常对不上号：给晕的人止痛，给苦的人指路，给痛的人打气。</p>
<p>本书用 SDE 方法论的三合一装置看不顺：三方程失衡是晕，分形晕、路晕、土晕；六路径不通是痛，分僵、悬、空、撞、闷、困；三原理动力疲软是苦，分乏苦、滞苦、散苦。十二种不顺，乘三界，三十六格。顺的发生，就是平·通·足。</p>
<p>五编三十三章，三遍九问，一百零八位古今中外的邻居：《黄帝内经》、庄子、孟子、王阳明，佛陀与一行禅师，世阿弥、森田正马，柏拉图、尼采、克尔凯郭尔，还有做实验的人。最后收到读人：AI 平权了知识与执行之后，读出眼前这个人此刻是晕、是痛还是苦，是人与人新的核心竞争力。</p>''' + s[i1:]
bad = [l for l in s.split('\n') if '520' in l or '欠' in l]
assert not bad, bad[:3]
p.write_text(s)
print('cover.py patched')
