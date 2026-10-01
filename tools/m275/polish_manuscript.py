"""Prepare the complete v1.4 edition from the author's supplied v1.3 DOCX.

Usage: python polish_manuscript.py SOURCE.docx OUTPUT.docx AUDIT.json
The source stays untouched. All substantive text edits are logged.
"""
from pathlib import Path
import sys, json, re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

source, target, audit = map(Path, sys.argv[1:4])
d = Document(source)
ps = list(d.paragraphs)
changes = []
edits = {
17: 'ISBN：979-8-90690-225-2（依来稿保留，待核对）',
19: '版本：v1.4 · 完整修订版',
23: '本版以六部三十章完整稿为底本，保留导论、结语、研究附论、参考书目与六项附录。修订着重澄清概念、精简重复表述，统一章首、目录、引文导航与版式。书中生活案例均为解释概念而设置的情境，不作为历史事实或实证研究结果。',
24: '写作与资料整理使用AI辅助。独立史实审校、原稿影像全面校勘与出版终审尚未完成。ISBN与定价沿用作者提供的信息；本版不据此声明已完成商业发行。',
29: '本书为“思想家通俗解构”系列中的马克思卷。它以“图纸”为线索，把目的、劳动、需要、研究过程与人的自我改变放在一起考察。具体诊断及其材料边界，见研究附论、参考书目和附录。',
104: '阅读时，暂时搁置一个判断并不意味着失败。能够说清为什么还不能判断，也是一项可保留的结果。原著、解释与尚待核查的材料，应始终分开。请把最后一个问号带回材料，而不只把最后一句话带走。',
225: '经验是哪一段经验？是过去画过类似房屋，还是这一次发现使用者行动不便？训练使哪些区别变得可以辨认？想象为什么沿着这个方向展开？若这些问题最后都收在“他有创造力”一句里，我们只是给结果换了一个名字。',
226: '更细的追问可以从图纸的前一页开始。设计要求在什么时刻、由谁提出？当时哪些方案被认为根本不值得考虑？后来哪一种材料或使用反馈，又使它们进入讨论？这些问题不能把思维完全打开，却能为思想的形成留下可检查的痕迹。',
242: '再设想一对兄妹为家人安排一天出游。先不问景点选得好不好，看看他们怎样逐渐弄清：这一天究竟想和家人一起做什么。',
252: '“建筑师”容易让人想到一个独自画图的人。但一个项目也可能由提出需求、设计、实施和使用的不同参与者共同完成。至少在概念上，一个劳动过程可以容纳不止一个目的承担者。',
406: '因此，信息由谁提供，是研究需要考虑的条件，却不能代替真伪判断。不能因为一个人是厂主就认定他的话都错，也不能因为他有经验就免除核查。来源位置帮助我们辨认他能看见什么、可能漏掉什么；具体陈述仍需证据。',
730: '问题出在把一种评价尺度扩大成全部。若负责人认为，不能增加当次交付量的时间都没有意义，学习便被排除在任务之外；若新成员认为，只要自己学到了东西，就不必顾及共同交付，个人学习又会凌驾于已经承担的责任之上。',
731: '更清楚的安排，是分别说明交付与训练的要求：哪些时间用于完成任务，哪些时间用于学习，哪些错误需要纠正，何时应当具备独立操作的能力。这样，学习不必伪装成即时高效率，交付也不必靠无限等待来容纳所有探索。',
922: '评价尺度本身，有时也会被工具改变。',
977: '外在结果也能够保存、传递和重新组织活动。',
1180: '到结束时，关键不在于他终于发现了一个从来藏在心底的“真实愿望”，而在于他开始能够作出此前做不出的判断。',
1870: '马克思并未仅凭“共同占有土地”，就把公社看成内部完全一致的整体。他讨论共同土地、家庭占有与分散劳动怎样结合，也分析这种结合何以可能支持发展，又何以可能在另一组条件下走向解体。[14]',
1935: '缺少的材料不能用想象补齐；最初一刻难以回溯，也不能据此抹去已经可见的形成过程。',
2132: '还有一种可能：旧秩序被取消后，人们为了尽快结束混乱，接受了一个容易执行、却没有回答原问题的尺度。',
2418: '本书的方法来自王德生的两份解构方法文件。方法提出了怎样追问；每一项具体诊断，则仍需由相应材料和论证承担。',
2736: 'SDE方法用三组关系表达显露、差异序列与特征纠缠的相互生成：',
2740: 'S是显露，指活动中形成并能够辨认的样态；D是差异序列；E是特征纠缠，不是独立摆在活动之外的一张环境清单。[方法1，第3节；方法2，第2节]',
2745: '这里的等号表达相互联系，并不表示本书已经建立了可计算的经验方程。F、G、H尚未被规定为可测量、可估计的统一函数；三行符号本身也不能代替因果论证。',
2749: '如果E可以随时装进任何遗漏，三方程就可能对所有结果都说得通，却无法帮助我们区分哪一种解释更好。',
2755: '研究的深度，不在于给E列出多少背景，而在于指出：哪些特征在当前活动中相互牵动，具体改变了什么。',
2756: '这里还要区分环境与特征纠缠。按SIO环境论，环境中的其他SIO与当前SIO在主体、互动或客体上具有共同性，并能对当前过程产生影响。E关注这些作用在当前过程中怎样形成特征纠缠。地理上靠近或概念上相似，均不足以单独证明某项因素已经产生作用。',
3197: '前半句提供文本入口，后半句提供材料线索。两者能否构成严格矛盾，必须分别论证；句式对称，并不会使判断自动成立。',
3198: '本书最后保留的是一个有明确范围的判断：当一种解释从已经形成的目的出发时，还需要追查目的本身的形成，并说明这个局部模型能解释哪些创造活动、不能解释哪些。它不支持用“马克思说一套、做一套”来概括整个人及其思想。',
3675: '三　本版修订',
3678: '本版为德麦国际专著第275号完整修订版v1.4。以v1.3完整排版稿为底本，保留六部三十章、导论、结语、研究附论、参考书目及六项附录；精简部分重复表述，澄清特征纠缠与环境的区别，增设章首主问，并调整字号、章末提示与目录导航。',
3679: '方法来源为王德生的两份解构方法文件。写作与资料整理使用AI辅助。具体解释与诊断的效力，取决于相应材料和论证，不能仅凭方法来源得到保证。',
3680: '独立史实审查、原稿影像全面校勘与出版终审尚未完成。已使用的公开文本列于参考书目，未完成的研究集中列于材料边界、失效记录与引文说明；不以版式完成替代学术审定。',
3688: '本版实际篇幅按修订后文本统计，区分汉字数与含标点、数字及字母的字符数。',
}
for i, new in edits.items():
    p=ps[i]; old=p.text
    changes.append({'paragraph_in_v1_3':i,'before':old,'after':new})
    p.text=new

navy='1F3A5F'; gold='B08A3C'; ink='2D2D2D'
def font(style,name,size,color):
    s=d.styles[style];s.font.name=name;s.font.size=Pt(size);s.font.color.rgb=RGBColor.from_string(color)
    rf=s.element.get_or_add_rPr().find(qn('w:rFonts'))
    if rf is None: rf=OxmlElement('w:rFonts');s.element.get_or_add_rPr().append(rf)
    rf.set(qn('w:eastAsia'),name)
    return s
s=font('Normal','Noto Serif CJK SC',11,ink)
s.paragraph_format.line_spacing=Pt(18.2)
s.paragraph_format.space_after=Pt(3)
s.paragraph_format.first_line_indent=Pt(22)
s.paragraph_format.widow_control=True
for name in ['Heading 1','Part Title','Major Title']:
    d.styles[name].font.color.rgb=RGBColor.from_string(navy)
font('Heading 2','Noto Sans CJK SC',11.5,navy)
font('Small','Noto Serif CJK SC',9.5,'5B6571')
font('Reference','Noto Serif CJK SC',9.5,ink).paragraph_format.line_spacing=Pt(16)
font('URL','Noto Sans CJK SC',7.6,'52677C')
for name in ['Chapter Number','Part Number','Ornament']:
    d.styles[name].font.color.rgb=RGBColor.from_string(gold)
font('Takeaway','Noto Serif CJK SC',10,navy)
st=d.styles['Takeaway'];st.paragraph_format.line_spacing=Pt(17)
st.paragraph_format.keep_with_next=True;st.paragraph_format.keep_together=True
st.paragraph_format.space_before=Pt(10);st.paragraph_format.space_after=Pt(4)
st.paragraph_format.first_line_indent=Pt(0)
# Match reference 220: navy titles, gold rules, unboxed chapter conclusions.
for p in d.paragraphs:
    p.paragraph_format.widow_control=True
    if p.style.name=='Takeaway':
        pr=p._p.get_or_add_pPr()
        for e in list(pr):
            if e.tag in [qn('w:pBdr'),qn('w:shd')]:pr.remove(e)
        b=OxmlElement('w:pBdr')
        for edge in ['top','bottom']:
            e=OxmlElement('w:'+edge)
            for k,v in {'val':'single','sz':'5','space':'6','color':gold}.items():e.set(qn('w:'+k),v)
            b.append(e)
        pr.append(b)
    if p.style.name=='Heading 1':
        for r in p.runs:
            if r.font.color.rgb and str(r.font.color.rgb)=='9B6045':r.font.color.rgb=RGBColor.from_string(gold)
    if p.style.name=='Heading 2':
        # A gold diamond is a structural marker in the reference edition.
        for r in p.runs:r.font.color.rgb=RGBColor.from_string(navy)
st=d.styles['Takeaway']
for e in list(st.element.get_or_add_pPr()):
    if e.tag in [qn('w:shd'),qn('w:pBdr')]:st.element.get_or_add_pPr().remove(e)

lead=d.styles.add_style('Chapter Lead',WD_STYLE_TYPE.PARAGRAPH)
lead.base_style=d.styles['Normal'];lead.font.size=Pt(11);lead.font.color.rgb=RGBColor.from_string('8C713A')
lead.paragraph_format.first_line_indent=Pt(0);lead.paragraph_format.line_spacing=Pt(18)
lead.paragraph_format.space_before=Pt(2);lead.paragraph_format.space_after=Pt(14)
lead.paragraph_format.keep_with_next=True;lead.paragraph_format.keep_together=True
questions=[
'图纸先于施工，是否等于它先于一切活动？',
'一本书已经付印，为什么研究仍在改换问题？',
'一封信送来的，怎样从生活支持变成思想材料？',
'换一种写法，什么时候会改变原来要说的事情？',
'怎样发现理论的缝隙，又不把人物压进预制的格子？',
'一件东西怎样进入交换，又怎样改变人与人的关系？',
'多付出了时间，为什么不等于创造了更多价值？',
'工资购买的是劳动成果，还是一定时间里的劳动能力？',
'机器节省下来的时间，怎样才能成为人的自由？',
'由人形成的关系，为什么会呈现为物自身的力量？',
'需要是在等待满足，还是也在满足的过程中形成？',
'改变环境的活动，怎样同时改变行动的人？',
'学会完成任务之后，谁来提出什么才值得完成？',
'执行者获得提问权，需要改变哪些实际安排？',
'有了空闲，为什么还可能不知道怎样过自己的生活？',
'一种历史趋势，要带着哪些条件才能说成“必然”？',
'一个新的对象，怎样逼理论重新说明自己的边界？',
'四份草稿留下的犹疑，能否成为理解结论的证据？',
'共享同一个时代，为什么不等于重复同一条道路？',
'旧秩序被否定之后，新能力靠什么形成？',
'研究先做的事，为什么未必写在书的第一章？',
'一个折旧小问题，怎样把研究带回实际过程？',
'当知识只剩下成品，形成知识的人会在哪里消失？',
'真正有力的反对，究竟击中了哪一步论证？',
'当原著反驳了本书的初判，本书怎样修改自己？',
'尚未成形、正在成形与已经成形，怎样相互转化？',
'改变结果、改变过程与改变条件，怎样相互牵动？',
'怎样用同一候选结果，辨认前后评价尺度的改变？',
'成功的故事，怎样保留那些当时尚未清楚的选择？',
'下一次开始时，你会把哪一处修改权留给实际发生？',
]
chapters=[p for p in list(d.paragraphs) if p.style.name=='Heading 1' and re.match(r'^第.+章',p.text)]
assert len(chapters)==30
for p,q in zip(chapters,questions):
    nxt=p._p.getnext()
    from docx.text.paragraph import Paragraph
    np=Paragraph(nxt,p._parent).insert_paragraph_before(q,style='Chapter Lead')
    changes.append({'addition_after':p.text,'after':q,'purpose':'章首主问'})
# Composition pass: absorb very short spill pages without shrinking the body type.
compact_prefixes=('前言','导读','导论','第一章','第六章','第八章','第十章',
                  '第十一章','第十二章','第十四章','第二十二章','第二十五章',
                  '第二十八章','研究附论','附录三')
compact=False
for p in d.paragraphs:
    if p.style.name=='Heading 1':
        compact=any(p.text.startswith(s+'　') for s in compact_prefixes)
    elif p.style.name in ['Part Number','Major Title']:
        compact=False
    if compact and p.style.name=='Normal':
        p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.line_spacing=Pt(18)
    elif compact and p.style.name=='Heading 2':
        p.paragraph_format.space_before=Pt(9)
        p.paragraph_format.space_after=Pt(5)
# Suppress running heads on the title page; preserve the book's physical-page numbering.
d.sections[1].different_first_page_header_footer=True
for e in d.sections[1].first_page_header._element: d.sections[1].first_page_header._element.remove(e)
for e in d.sections[1].first_page_footer._element: d.sections[1].first_page_footer._element.remove(e)
d.core_properties.title='马克思的图纸从哪里来？'
d.core_properties.subject='普通人都能读懂的马克思：理论、人生与创造的缝隙'
d.core_properties.author='王德生'
d.core_properties.version='1.4'
d.core_properties.comments=''
# Use the installed, language-specific Noto SC families in all direct and style runs.
for root in [d.element, d.styles.element]:
    for el in root.iter(qn('w:rFonts')):
        for attr, val in list(el.attrib.items()):
            if 'Noto Serif CJK SC' in val: el.set(attr,val.replace('Noto Serif CJK SC','Noto Serif SC'))
            if 'Noto Sans CJK SC' in val: el.set(attr,val.replace('Noto Sans CJK SC','Noto Sans SC'))
target.parent.mkdir(parents=True,exist_ok=True)
d.save(target)
audit.parent.mkdir(parents=True,exist_ok=True)
audit.write_text(json.dumps(changes,ensure_ascii=False,indent=2))
print(json.dumps({'output':str(target),'edits':len(edits),'chapter_leads':len(questions),'chapters':len(chapters),'tables':len(d.tables)},ensure_ascii=False))
