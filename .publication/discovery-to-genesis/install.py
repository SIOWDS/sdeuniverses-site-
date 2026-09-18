from pathlib import Path
import hashlib

URL = '/column/discovery-to-genesis/'
EXPECTED = '387ca77177cbfabfff55bcd758593c6da573e56bd164aa9dcb65204ecd65b894'
page = Path('/tmp/discovery-to-genesis.html').read_bytes()
assert hashlib.sha256(page).hexdigest() == EXPECTED, 'Article checksum mismatch'
assert page.count(b'<math ') == 95, 'An equation was lost'
assert page.count(b'<h2 ') == 17, 'A section was lost'
dest = Path('public/column/discovery-to-genesis/index.html')
assert not dest.exists() or dest.read_bytes() == page, 'Refusing to overwrite a different article'

card = '''<a href="/column/discovery-to-genesis/" style="display:block;text-decoration:none;margin-bottom:16px">
<div style="border:1px solid rgba(74,115,184,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(16,22,38,0.98),rgba(11,14,26,0.98));padding:34px 32px">
<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#7FA0DC;margin-bottom:14px">★ 新论文 · AI教育 · 正文21,359汉字 · 2026年9月18日</div>
<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#7FA0DC;margin-bottom:14px">NEW PAPER · AI EDUCATION · 21,359 CHINESE CHARACTERS · 18 SEPTEMBER 2026</div>
<h3 class="zh-only" style="color:#F6EAD5;font-size:25px;line-height:1.5;margin:0 0 14px">从发现到发生：AI时代思考竞争力的典范转移</h3>
<h3 class="en-only" style="color:#F6EAD5;font-size:23px;line-height:1.5;margin:0 0 14px">From Discovery to Genesis: A Paradigm Shift in Thinking Competence in the AI Era</h3>
<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">以“大模型是语言发生学的工程化”为逻辑起点，区分语言发生、有效认识发生与学习者能力发生，通过形式证明、SDE结构分析、三个教育案例及可证伪研究方案，论证思考竞争力如何从发现结果转向发生条件的组织与重构。全文保留成立条件、最强反对意见与失效边界。网页完整正文，含章节目录、95处公式和12项参考文献。</p>
<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">Starting from language models as an engineering realization of linguistic genesis, this paper distinguishes text generation, warranted knowledge and learner development. Formal arguments, an SDE analysis, three educational examples and a falsifiable study design examine the conditional shift from discovering results to organizing the conditions of inquiry. Full Chinese text with navigation, equations and references.</p>
</div></a>

'''
education_card = '''<h2>最新论文</h2>
<div class="flag">
<div class="ft"><a href="/column/discovery-to-genesis/">从发现到发生：AI时代思考竞争力的典范转移</a></div>
<div class="fm">依王德生 SDE 理论 · AI辅助撰稿 · 2026年9月18日 · 正文21,359汉字</div>
<div class="fw">以“大模型是语言发生学的工程化”为逻辑起点，分别论证语言发生、有效认识发生与学习者能力发生。包含条件性竞争优势迁移的形式证明、SDE三方程分析、教育案例、最强反对意见和可证伪实验方案；不把作品的形成直接登记为学生能力的成长。</div>
<div class="bar"><a class="btn dl" href="/column/discovery-to-genesis/">阅读全文</a><a class="btn" href="/column/discovery-to-genesis/#section-6">竞争优势迁移的证明</a><a class="btn" href="/column/discovery-to-genesis/#section-10">学生的能力发生</a></div>
</div>

'''
changes = {}
today = Path('public/today/index.html')
s = today.read_text(encoding='utf-8')
if URL not in s:
    anchor = '<a href="/column/why-learn-genesis-philosophy/"'
    assert s.count(anchor) == 1, 'Long-read anchor changed; stop without overwriting'
    pos = s.index(anchor)
    assert pos > s.index('id="today-longread"'), 'Wrong section'
    s = s[:pos] + card + s[pos:]
changes[today] = s
education = Path('public/new-education/index.html')
s = education.read_text(encoding='utf-8')
if URL not in s:
    anchor = '<h2>奠基之作</h2>'
    assert s.count(anchor) == 1, 'Education anchor changed; stop without overwriting'
    s = s.replace(anchor, education_card + anchor, 1)
changes[education] = s
# All assertions above pass before any tracked file is changed.
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(page)
for p, content in changes.items():
    p.write_text(content, encoding='utf-8')
print('Installed full article and both navigation entries; existing index schedule unchanged.')
