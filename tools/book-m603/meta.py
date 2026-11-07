"""第 603 号《AI时代企业本体论的典范转移》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
由第 602 号工具链改来；排版引擎用通俗哲学专著格式（engine/，由 /tmp 下的改造脚本收进来）；版式照第 220、302 号。"""
NO = 603
SLUG = 'enterprise-ontology-paradigm'
TITLE = 'AI时代企业本体论的典范转移'
SUBTITLE = '从人力组织到人—AI思想复合主体'
SUBTITLE2 = '与德鲁克的管理学及企业组织理论对话'
FULL_TITLE = TITLE + '——' + SUBTITLE + '——' + SUBTITLE2
TITLE_EN = 'The Paradigm Shift of Enterprise Ontology in the AI Era'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-633-5'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m603'
DATE = '2026-11-07'
EDITION = '审读版 v0.3（含待裁待核标记）'
UNIT_REV = '20261107-m603-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
NPARTS, NCH = 10, 60
PART_RANGES = [(1, 6), (7, 12), (13, 18), (19, 24), (25, 30), (31, 36), (37, 42), (43, 48), (49, 54), (55, 60)]
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='作者令全文上站；立题卡无拟定标签，记“标签缺项”，按 L0 公开',
            tier_reason='理论提案与构造案例；无真跑数据，无独立外部评审；德鲁克相关内容据站内第207、214号转述，〔待核〕；〔待裁〕处如实保留；王德生令全文上站并做成三位一体',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生令；立题卡标签缺项）',
            tier_date='2026-11-07')
AUTHORSHIP = ('王德生 著：核心问题、SDE 框架与全书母题由王德生提出；正文由 AI（Claude）协作撰写，经分章质检与三遍内部审读修订；'
              '同一底座的执笔者与审稿者不能互作独立证据；无独立学术评审，无观察数据，无对照实验。')
SUB_FULL = SUBTITLE + '——' + SUBTITLE2
BODY_HAN = 339673          # 十编六十章正文汉字实数（统计口径：章节正文，不含出版信息、前言、导读、结语、附录）
WAN_AUTHOR = 33            # 作者稿口径“约33万字”，出版信息页与封底沿用；实数见 BODY_HAN
