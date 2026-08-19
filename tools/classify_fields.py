#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从文章页的标题＋关键词＋摘要开头，把每篇归入一张固定的一级领域表。

为什么不用页面上的学科标签：那是每篇自造的长复合标签，不是分类——
高鹏 74 篇能产出 49 个"领域"，而黄倩盈 51 篇、胡敏 65 篇、张琼 45 篇的眉题里
根本没有学科字段（只有"学员专栏 · 姓名"）。按标签数算广度会得出与事实相反的结论。
"""
import re, os, html

FIELDS = [
    ('教育学',       '教学 学习 课堂 学生 教师 学校 教育 课程 评价 考试 认证 素养 师生 教改 教养 育儿 孩子 学员 教学法'),
    ('法学',         '司法 法律 法官 法院 判决 裁判 权利 程序正义 立法 刑事 民事 法理 法条 诉讼 律师 罪 合宪 法治 法规'),
    ('医学与健康',   '中医 临床 诊断 患者 病人 疗效 证候 辨证 脉 经络 气血 健康 疾病 护理 医生 药 医学 症状 慢性病 康复'),
    ('心理与心理治疗','咨询 来访者 疗法 心理 情绪 创伤 共情 治疗师 人本 精神分析 抑郁 焦虑 依恋 自尊 心理学 疗愈'),
    ('哲学',         '本体论 形而上 现象学 存在 认识论 伦理学 哲学 主体性 先验 辩证 康德 黑格尔 海德格尔 亚里士多德 柏拉图 道德哲学'),
    ('认知科学',     '认知 记忆 注意 元认知 知觉 心智 大模型 人工智能 神经 意识 思维 判断力 直觉 学习机制 智能'),
    ('社会学',       '制度 组织 社会 科层 共同体 阶层 家庭 群体 规范 角色 社会学 结构 关系网 信任 权威'),
    ('经济与管理',   '经济 市场 企业 创业 管理 资本 货币 繁荣 财富 商业 绩效 组织建设 效率 成本 产业 通货'),
    ('艺术与美学',   '审美 艺术 电影 影视 音乐 绘画 美学 诗歌 舞蹈 摄影 意象 镜头 演奏 艺术家 美感'),
    ('语言与文学',   '语言 文学 叙事 文本 写作 翻译 汉语 修辞 小说 阅读 词语 语法 文体 诗学'),
    ('宗教与神学',   '信仰 神学 基督 教会 福音 圣经 宗教 灵性 祷告 上帝 救赎 圣灵'),
    ('城市与空间',   '城市 街区 空间 规划 聚落 建筑 社区 地方 街道 都市 区划 邻里'),
    ('政治与治理',   '权力 治理 国家 政策 民主 自由 秩序 政治 公共 官僚 主权 意识形态'),
    ('科学技术',     '技术 算法 工程 物理 量子 科学 数据 系统设计 实验 模型 计算 粒子'),
    ('历史',         '历史 朝代 王朝 古代 史 明清 宋代 唐 近代 文明史 演化史'),
]
# 横切范畴（社会学／认知科学／哲学）在本站几乎每篇都会出现——SDE 的写法本来就
# 谈制度、谈认知、谈本体论。若不打折，胡敏 88 篇全在中医却会被算成跨七个领域。
# 打折让「实体学科」词（中医、法院、电影）压过横切词，归到真正的课题域。
CROSSCUT = {'社会学': 0.55, '认知科学': 0.65, '哲学': 0.65, '科学技术': 0.8}
LEX = [(n, set(w.split())) for n, w in FIELDS]


def page_text(idx):
    s = open(idx, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
    title = ''
    m = re.search(r'class="art-title"[^>]*>(.*?)</h1>', s, re.S) or re.search(r'<title>(.*?)</title>', s, re.S)
    if m:
        title = re.sub(r'<[^>]+>', '', m.group(1))
    kw = ''
    m = re.search(r'关键词[^<]{0,4}[：:]?\s*</?[^>]*>?\s*([^<]{0,200})', s)
    if m:
        kw = m.group(1)
    body = re.sub(r'<[^>]+>', ' ', s)
    body = html.unescape(body)
    i = body.find('摘')
    head = body[i:i + 700] if i > 0 else body[:700]
    return title, kw, head


def classify(idx):
    title, kw, head = page_text(idx)
    # 标题与关键词权重更高：它们是作者自报的题域
    blob = (title + ' ') * 4 + (kw + ' ') * 3 + head
    best, bestn = None, 0
    for name, words in LEX:
        n = sum(blob.count(w) for w in words) * CROSSCUT.get(name, 1.0)
        if n > bestn:
            best, bestn = name, n
    return (best, bestn) if bestn >= 3 else (None, bestn)


if __name__ == '__main__':
    import glob, collections, json, sys
    root = 'public/students'
    out = collections.defaultdict(collections.Counter)
    unc = collections.Counter()
    per = {}
    for p in sorted(glob.glob(f'{root}/*/*/index.html')):
        parts = p.split('/')
        if parts[3] in ('works',):
            continue
        slug = parts[2]
        f, n = classify(p)
        per[p] = f
        if f:
            out[slug][f] += 1
        else:
            unc[slug] += 1
    json.dump({k: v for k, v in per.items()}, open('/tmp/fields.json', 'w'), ensure_ascii=False)
    tot = sum(sum(c.values()) for c in out.values())
    print('已分类 %d 篇 / 未分类 %d 篇' % (tot, sum(unc.values())))
    import math
    print('\n%-16s %4s %5s %6s  %s' % ('学员', '篇数', '有效领域', '未分类', '领域分布'))
    for slug in sorted(out, key=lambda s: -sum(out[s].values())):
        c = out[slug]; n = sum(c.values())
        H = -sum((v / n) * math.log(v / n) for v in c.values())
        eff = math.exp(H)
        top = ' '.join('%s%d' % (k, v) for k, v in c.most_common(5))
        print('%-16s %4d %8.2f %6d  %s' % (slug, n, eff, unc[slug], top))
