// ── LANGUAGE
function setLang(lang){
  document.body.className=lang;
  document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('active',b.textContent.toLowerCase()===lang||(b.textContent==='中'&&lang==='zh')));
  document.documentElement.lang=lang==='zh'?'zh':'en';
  renderMatrix();
  if(window.__renderPress)window.__renderPress();
}

// ── INDUSTRY DATA (10 industries)
const industries=[
  {id:'edu', zh:'教育',    en:'Education',  tag:'learning as meaning-genesis'},
  {id:'law', zh:'法律',    en:'Law',        tag:'triadic jurisprudence'},
  {id:'med', zh:'医疗',    en:'Medicine',   tag:'health as structural reconstruction'},
  {id:'ent', zh:'企业管理',en:'Enterprise', tag:'organization as meaning-field'},
  {id:'art', zh:'艺术创作',en:'Arts',       tag:'from discovery to genesis'},
  {id:'aca', zh:'学术研究',en:'Academia',   tag:'paper as knowledge weapon'},
  {id:'fin', zh:'金融投资',en:'Finance',    tag:'value as feature-entanglement'},
  {id:'mda', zh:'媒体传播',en:'Media',      tag:'narrative as difference-flow'},
  {id:'gov', zh:'公共治理',en:'Governance', tag:'society as S-D-E coupling'},
  {id:'tec', zh:'科技创新',en:'Tech',       tag:'product as generative body'}
];

// ── SDE AGENTS (99 total — 10 per industry except tec=9)
const employees=[
  // 教育 Education (10)
  {i:'edu', zh:'课程设计师',   en:'Course Designer',         zhDesc:'根据学生画像生成个性化课程大纲与学习路径。', enDesc:'Personalized course outlines & learning paths.'},
  {i:'edu', zh:'教案发生器',   en:'Lesson Generator',        zhDesc:'一键生成完整教案 + 教学步骤 + 课堂互动设计。', enDesc:'One-click full lesson plans & interactive design.'},
  {i:'edu', zh:'作业诊断师',   en:'Homework Diagnostician',  zhDesc:'诊断学生作业中的结构性漏洞与发生学断点。', enDesc:'Diagnose structural gaps in student work.'},
  {i:'edu', zh:'个性化辅导员', en:'Personalized Tutor',      zhDesc:'基于 SDE 发生学的一对一动态辅导。', enDesc:'One-on-one tutoring via SDE generativics.'},
  {i:'edu', zh:'考试命题师',   en:'Exam Designer',           zhDesc:'按知识发生路径出题，而非按知识点清单。', enDesc:'Exam items built on knowledge-genesis pathways.'},
  {i:'edu', zh:'学习路径规划师',en:'Learning Path Planner',  zhDesc:'为跨学科学习者规划长程发展路径。', enDesc:'Long-range paths for cross-disciplinary learners.'},
  {i:'edu', zh:'论文指导师',   en:'Thesis Coach',            zhDesc:'学位论文从选题到定稿的全程陪跑。', enDesc:'End-to-end thesis coaching, topic to defense.'},
  {i:'edu', zh:'教材改写师',   en:'Textbook Rewriter',       zhDesc:'把现有教材用 SDE 发生顺序重写。', enDesc:'Rewrite textbooks in SDE generative order.'},
  {i:'edu', zh:'教育咨询师',   en:'Education Consultant',    zhDesc:'学校/机构层面的教育改革咨询。', enDesc:'School-level education reform consulting.'},
  {i:'edu', zh:'学习动机师',   en:'Motivation Coach',        zhDesc:'重建学习者的意义动机与内在驱动。', enDesc:'Rebuild learners\' meaning-driven motivation.'},

  // 法律 Law (10)
  {i:'law', zh:'合同审查师',   en:'Contract Reviewer',       zhDesc:'条款风险识别、对手方陷阱扫描、修订建议。', enDesc:'Risk detection, trap scanning, revision advice.'},
  {i:'law', zh:'法律文书撰写师',en:'Legal Document Drafter', zhDesc:'起诉状、答辩状、法律意见书一键生成。', enDesc:'One-click pleadings & legal opinions.'},
  {i:'law', zh:'案例检索师',   en:'Case Retriever',          zhDesc:'全球判例库检索 + 相似度排序 + 要点提炼。', enDesc:'Global case search, similarity ranking, key points.'},
  {i:'law', zh:'法律顾问',     en:'Legal Advisor',           zhDesc:'企业/个人法律咨询 · 可工作的策略建议。', enDesc:'Actionable legal strategy for firms & individuals.'},
  {i:'law', zh:'合规审查师',   en:'Compliance Reviewer',     zhDesc:'跨司法辖区合规要点与冲突点识别。', enDesc:'Multi-jurisdiction compliance review.'},
  {i:'law', zh:'知识产权专员', en:'IP Specialist',           zhDesc:'专利/商标/著作权的布局与风险诊断。', enDesc:'Patent/trademark/copyright strategy & risk.'},
  {i:'law', zh:'诉讼策略师',   en:'Litigation Strategist',   zhDesc:'诉讼路径规划 · 证据链梳理 · 对抗预测。', enDesc:'Litigation paths, evidence chains, adversary prediction.'},
  {i:'law', zh:'劳动法顾问',   en:'Labor Law Advisor',       zhDesc:'用工合规 · 劳动争议 · 员工关系处理。', enDesc:'Employment compliance, disputes, HR relations.'},
  {i:'law', zh:'国际商法顾问', en:'Int\'l Commercial Law',   zhDesc:'跨境交易合规 · 国际仲裁 · 制裁合规。', enDesc:'Cross-border compliance, arbitration, sanctions.'},
  {i:'law', zh:'法律培训师',   en:'Legal Trainer',           zhDesc:'面向非法律人员的企业法务能力培训。', enDesc:'Legal training for non-lawyers in enterprises.'},

  // 医疗 Medicine (10)
  {i:'med', zh:'诊断助理',     en:'Diagnostic Assistant',    zhDesc:'症状分析 · 鉴别诊断 · 检查建议。', enDesc:'Symptom analysis, differential diagnosis, test advice.'},
  {i:'med', zh:'慢病管理师',   en:'Chronic Disease Manager', zhDesc:'高血压/糖尿病从指标控制转向结构重建。', enDesc:'Chronic disease: from indicators to structure.'},
  {i:'med', zh:'心理健康顾问', en:'Mental Health Advisor',   zhDesc:'抑郁/焦虑的 SDE 视角诊断与干预。', enDesc:'Depression/anxiety diagnosis via SDE.'},
  {i:'med', zh:'营养规划师',   en:'Nutrition Planner',       zhDesc:'个性化营养方案 · 慢性病膳食干预。', enDesc:'Personalized nutrition & dietary interventions.'},
  {i:'med', zh:'康复指导师',   en:'Rehab Coach',             zhDesc:'术后康复 · 运动康复 · 功能重建。', enDesc:'Post-op, sports, and functional rehabilitation.'},
  {i:'med', zh:'医患沟通师',   en:'Doctor-Patient Bridge',   zhDesc:'医嘱翻译 · 就医流程 · 医患矛盾调解。', enDesc:'Translating medical advice; mediating disputes.'},
  {i:'med', zh:'病历整理师',   en:'Medical Record Organizer',zhDesc:'多家医院病历整合 · 时间线重建。', enDesc:'Integrate records across hospitals into timelines.'},
  {i:'med', zh:'医学文献分析师',en:'Medical Literature Analyst',zhDesc:'最新研究综述 · 证据等级评估。', enDesc:'Latest research reviews, evidence-level grading.'},
  {i:'med', zh:'睡眠改善师',   en:'Sleep Optimizer',         zhDesc:'睡眠结构诊断 · 节律重建方案。', enDesc:'Sleep architecture diagnosis & rhythm rebuild.'},
  {i:'med', zh:'长寿策略师',   en:'Longevity Strategist',    zhDesc:'Sirtuins-AMPK-mTOR 三角的个性化干预。', enDesc:'Personalized Sirtuins-AMPK-mTOR interventions.'},

  // 企业管理 Enterprise (10)
  {i:'ent', zh:'战略咨询师',   en:'Strategy Consultant',     zhDesc:'企业战略诊断 · 方向选择 · 路径规划。', enDesc:'Strategy diagnosis, direction, path planning.'},
  {i:'ent', zh:'组织诊断师',   en:'Org Diagnostician',       zhDesc:'组织能力 · 文化 · 结构三维诊断。', enDesc:'Org capability, culture, structure diagnosis.'},
  {i:'ent', zh:'HR 规划师',   en:'HR Planner',              zhDesc:'人才梯队 · 能力模型 · 继任规划。', enDesc:'Talent pipeline, competency models, succession.'},
  {i:'ent', zh:'商业模式设计师',en:'Business Model Designer',zhDesc:'价值主张 · 盈利模式 · 护城河设计。', enDesc:'Value prop, revenue model, moat design.'},
  {i:'ent', zh:'运营优化师',   en:'Ops Optimizer',           zhDesc:'流程再造 · 效率提升 · 成本结构。', enDesc:'Process redesign, efficiency, cost structure.'},
  {i:'ent', zh:'企业文化建构师',en:'Culture Builder',        zhDesc:'以意义三律重建企业文化底盘。', enDesc:'Rebuild culture via the Three Axioms of Meaning.'},
  {i:'ent', zh:'绩效设计师',   en:'Performance Designer',    zhDesc:'KPI/OKR 设计 · 激励机制 · 考核闭环。', enDesc:'KPI/OKR design, incentives, feedback loops.'},
  {i:'ent', zh:'领导力教练',   en:'Leadership Coach',        zhDesc:'CEO/高管一对一发展教练。', enDesc:'CEO/executive one-on-one development.'},
  {i:'ent', zh:'危机管理师',   en:'Crisis Manager',          zhDesc:'重大危机响应 · 声誉修复 · 情景推演。', enDesc:'Major crisis response, reputation, scenarios.'},
  {i:'ent', zh:'董事会顾问',   en:'Board Advisor',           zhDesc:'董事会议程 · 治理结构 · 股东沟通。', enDesc:'Board agenda, governance, shareholder comm.'},

  // 艺术创作 Arts (10)
  {i:'art', zh:'剧本发生师',   en:'Screenplay Genesis',      zhDesc:'剧本从主题到场次的 SDE 结构化发生。', enDesc:'Screenplay genesis from theme to scenes via SDE.'},
  {i:'art', zh:'小说结构师',   en:'Novel Architect',         zhDesc:'长篇小说的底层结构与节奏设计。', enDesc:'Deep structure & pacing for long-form fiction.'},
  {i:'art', zh:'诗歌炼字师',   en:'Poetry Refiner',          zhDesc:'意象选择 · 声韵打磨 · 张力控制。', enDesc:'Imagery, sonic refinement, tension control.'},
  {i:'art', zh:'艺术评论师',   en:'Art Critic',              zhDesc:'作品的发生学评论 · 超越风格学分析。', enDesc:'Generative criticism beyond stylistic analysis.'},
  {i:'art', zh:'视觉概念师',   en:'Visual Concept',          zhDesc:'品牌/展览/插画的视觉概念生成。', enDesc:'Visual concepts for brands, exhibits, illustrations.'},
  {i:'art', zh:'音乐结构师',   en:'Music Architect',         zhDesc:'编曲结构 · 情绪曲线 · 段落发生学。', enDesc:'Arrangement, emotion curves, section genesis.'},
  {i:'art', zh:'舞蹈编导',     en:'Choreographer',           zhDesc:'舞蹈动机发生 · 空间调度 · 叙事整合。', enDesc:'Motif genesis, spatial design, narrative.'},
  {i:'art', zh:'游戏叙事师',   en:'Game Narrator',           zhDesc:'游戏世界观 · 任务链 · 玩家体验弧。', enDesc:'Worldbuilding, quest chains, player arcs.'},
  {i:'art', zh:'广告文案师',   en:'Ad Copywriter',           zhDesc:'洞察-概念-文案的三阶生成。', enDesc:'Insight-concept-copy three-stage generation.'},
  {i:'art', zh:'品牌美学师',   en:'Brand Aesthetician',      zhDesc:'品牌视觉体系 · 调性 · 触点设计。', enDesc:'Brand visual system, tone, touchpoints.'},

  // 学术研究 Academia (10)
  {i:'aca', zh:'文献综述师',   en:'Literature Reviewer',     zhDesc:'研究领域全景综述 · 流派谱系梳理。', enDesc:'Panoramic reviews, school lineage mapping.'},
  {i:'aca', zh:'研究设计师',   en:'Research Designer',       zhDesc:'研究问题 · 方法选择 · 效度保障。', enDesc:'Research questions, methodology, validity.'},
  {i:'aca', zh:'论文发生师',   en:'Paper Geneticist',        zhDesc:'论文从裂缝识别到成文的完整发生。', enDesc:'Full paper genesis: fissure to publication.'},
  {i:'aca', zh:'数据分析师',   en:'Data Analyst',            zhDesc:'定量分析 · 可视化 · 统计诊断。', enDesc:'Quant analysis, visualization, diagnostics.'},
  {i:'aca', zh:'同行评议师',   en:'Peer Reviewer',           zhDesc:'投稿前的预审 · 反驳预测 · 修订建议。', enDesc:'Pre-submit review, rebuttal prediction.'},
  {i:'aca', zh:'学术写作教练', en:'Academic Writing Coach',  zhDesc:'论文语言 · 论证链 · 读者意识训练。', enDesc:'Prose, argumentation, reader-awareness.'},
  {i:'aca', zh:'开题报告师',   en:'Proposal Writer',         zhDesc:'博硕开题 · 基金申请 · 评审导向。', enDesc:'Thesis proposals, grant applications.'},
  {i:'aca', zh:'期刊匹配师',   en:'Journal Matcher',         zhDesc:'投稿期刊精准匹配 · 影响因子 · 审稿周期。', enDesc:'Journal matching, IF, review timelines.'},
  {i:'aca', zh:'答辩训练师',   en:'Defense Trainer',         zhDesc:'答辩情景演练 · 关键问题预判。', enDesc:'Defense rehearsals & critical Q prediction.'},
  {i:'aca', zh:'课题诊断师',   en:'Topic Diagnostician',     zhDesc:'研究方向的裂缝扫描与生长性评估。', enDesc:'Fissure scan & growth assessment of research.'},

  // 金融投资 Finance (10)
  {i:'fin', zh:'投研分析师',   en:'Investment Researcher',   zhDesc:'行业/公司深度研究 · 估值建模。', enDesc:'Deep industry/company research, valuation.'},
  {i:'fin', zh:'财报解读师',   en:'Financial Statement Reader',zhDesc:'三表联动分析 · 异常点识别。', enDesc:'Three-statement analysis, anomaly detection.'},
  {i:'fin', zh:'宏观经济分析师',en:'Macro Analyst',          zhDesc:'宏观周期 · 政策解读 · 资产配置建议。', enDesc:'Macro cycles, policy, asset allocation.'},
  {i:'fin', zh:'量化策略师',   en:'Quant Strategist',        zhDesc:'因子挖掘 · 回测 · 策略组合。', enDesc:'Factor mining, backtesting, portfolios.'},
  {i:'fin', zh:'风险管理师',   en:'Risk Manager',            zhDesc:'VaR/压力测试 · 尾部风险识别。', enDesc:'VaR, stress tests, tail risk.'},
  {i:'fin', zh:'个人财务规划师',en:'Personal Finance Planner',zhDesc:'家庭资产规划 · 税务 · 传承。', enDesc:'Family wealth, tax, succession planning.'},
  {i:'fin', zh:'公司估值师',   en:'Corporate Valuator',      zhDesc:'DCF/可比/期权法估值与敏感度分析。', enDesc:'DCF/comparables/options valuation.'},
  {i:'fin', zh:'行业研究师',   en:'Industry Researcher',     zhDesc:'行业图谱 · 竞争格局 · 投资机会。', enDesc:'Industry maps, competition, opportunities.'},
  {i:'fin', zh:'尽调专员',     en:'Due Diligence Specialist',zhDesc:'财务/法务/商业尽调要点清单。', enDesc:'Financial, legal, commercial DD checklists.'},
  {i:'fin', zh:'并购顾问',     en:'M&A Advisor',             zhDesc:'交易结构 · 估值谈判 · 整合路径。', enDesc:'Deal structuring, valuation, integration.'},

  // 媒体传播 Media (10)
  {i:'mda', zh:'新闻写作师',   en:'News Writer',             zhDesc:'事实核查 · 结构化叙事 · 中立表达。', enDesc:'Fact-checking, narrative, neutral voice.'},
  {i:'mda', zh:'深度报道师',   en:'Feature Reporter',        zhDesc:'长篇深度报道的选题、采访、写作。', enDesc:'Long-form features: topic, interview, write.'},
  {i:'mda', zh:'社交媒体策划师',en:'Social Media Planner',   zhDesc:'平台策略 · 内容日历 · 互动设计。', enDesc:'Platform strategy, content calendar, engagement.'},
  {i:'mda', zh:'短视频脚本师', en:'Short Video Writer',      zhDesc:'抖音/小红书/YouTube Shorts 脚本。', enDesc:'TikTok/Reels/Shorts scripts.'},
  {i:'mda', zh:'播客策划师',   en:'Podcast Producer',        zhDesc:'播客选题 · 嘉宾策略 · 节目结构。', enDesc:'Podcast topics, guest strategy, structure.'},
  {i:'mda', zh:'传播策略师',   en:'Comms Strategist',        zhDesc:'品牌/组织的整合传播战略。', enDesc:'Integrated communication strategy.'},
  {i:'mda', zh:'公关危机师',   en:'PR Crisis Manager',       zhDesc:'舆情监测 · 危机响应 · 声誉修复。', enDesc:'Sentiment, crisis response, reputation.'},
  {i:'mda', zh:'新媒体运营师', en:'New Media Operator',      zhDesc:'账号运营 · 粉丝增长 · 变现路径。', enDesc:'Account ops, audience growth, monetization.'},
  {i:'mda', zh:'内容编辑师',   en:'Content Editor',          zhDesc:'稿件编辑 · 风格统一 · 事实校验。', enDesc:'Editorial: style unification, fact-checking.'},
  {i:'mda', zh:'品牌故事师',   en:'Brand Storyteller',       zhDesc:'品牌的本源故事 · 叙事线构建。', enDesc:'Brand origin story, narrative arc design.'},

  // 公共治理 Governance (10)
  {i:'gov', zh:'政策研究师',   en:'Policy Researcher',       zhDesc:'公共政策分析 · 比较研究 · 建议报告。', enDesc:'Policy analysis, comparative studies, memos.'},
  {i:'gov', zh:'社区治理师',   en:'Community Governor',      zhDesc:'社区自治 · 居民参与 · 矛盾调解。', enDesc:'Self-governance, participation, mediation.'},
  {i:'gov', zh:'社会创新师',   en:'Social Innovator',        zhDesc:'社会问题的发生学诊断与系统性创新。', enDesc:'Genetic diagnosis & systemic innovation.'},
  {i:'gov', zh:'城市规划师',   en:'Urban Planner',           zhDesc:'城市空间 · 功能分区 · 人本尺度。', enDesc:'Urban spaces, zoning, human scale.'},
  {i:'gov', zh:'环境治理师',   en:'Env Governance',          zhDesc:'环保政策 · ESG 战略 · 可持续方案。', enDesc:'Environmental policy, ESG, sustainability.'},
  {i:'gov', zh:'公共服务设计师',en:'Public Service Designer', zhDesc:'政府服务的用户体验再设计。', enDesc:'Gov service UX redesign.'},
  {i:'gov', zh:'社会调研师',   en:'Social Researcher',       zhDesc:'问卷/访谈/民族志 · 混合方法研究。', enDesc:'Surveys, interviews, ethnography, mixed methods.'},
  {i:'gov', zh:'非营利运营师', en:'NGO Operator',            zhDesc:'NGO 战略 · 募款 · 项目评估。', enDesc:'NGO strategy, fundraising, evaluation.'},
  {i:'gov', zh:'政府沟通师',   en:'Gov Communications',      zhDesc:'政策阐释 · 公众沟通 · 危机应对。', enDesc:'Policy explanation, public comms, crisis.'},
  {i:'gov', zh:'青年发展师',   en:'Youth Development',       zhDesc:'青年政策 · 成长支持 · 代际对话。', enDesc:'Youth policy, development, generational dialogue.'},

  // 科技创新 Tech (9)
  {i:'tec', zh:'AI 应用设计师',en:'AI App Designer',         zhDesc:'AI 产品的场景发掘与体验设计。', enDesc:'AI product scenarios & experience design.'},
  {i:'tec', zh:'产品发生师',   en:'Product Genesis',         zhDesc:'产品从需求裂缝到 MVP 的完整发生。', enDesc:'Full product genesis from fissure to MVP.'},
  {i:'tec', zh:'UX 研究师',   en:'UX Researcher',           zhDesc:'用户研究 · 体验地图 · 可用性测试。', enDesc:'User research, journey maps, usability.'},
  {i:'tec', zh:'技术评估师',   en:'Tech Evaluator',          zhDesc:'新技术成熟度 · 落地性 · ROI 评估。', enDesc:'Tech maturity, viability, ROI assessment.'},
  {i:'tec', zh:'原型设计师',   en:'Prototyper',              zhDesc:'快速原型 · 交互验证 · 迭代优化。', enDesc:'Rapid prototypes, interaction validation.'},
  {i:'tec', zh:'专利策略师',   en:'Patent Strategist',       zhDesc:'技术专利布局 · 规避设计 · 许可策略。', enDesc:'Patent portfolio, design-around, licensing.'},
  {i:'tec', zh:'开源项目顾问', en:'OSS Advisor',             zhDesc:'开源战略 · 社区运营 · 商业化路径。', enDesc:'OSS strategy, community, commercialization.'},
  {i:'tec', zh:'创业孵化师',   en:'Startup Incubator',       zhDesc:'从 0 到 1 · 早期团队 · 融资路径。', enDesc:'Zero-to-one, early team, fundraising paths.'},
  {i:'tec', zh:'科技伦理师',   en:'Tech Ethicist',           zhDesc:'AI/基因/数据科技的伦理审查。', enDesc:'Ethics review: AI, genomics, data tech.'}
];

// ── RENDER MATRIX
let activeInd='all';
const tabsEl=document.getElementById('industriesTabs');
const gridEl=document.getElementById('employeesGrid');

function renderTabs(){
  if(!tabsEl) return;
  const isZh=document.body.classList.contains('zh');
  const all=[{id:'all',zh:'全部',en:'All',count:employees.length}]
    .concat(industries.map(i=>({...i,count:employees.filter(e=>e.i===i.id).length})));
  tabsEl.innerHTML=all.map(t=>`
    <button class="tab-btn${t.id===activeInd?' active':''}" data-ind="${t.id}" onclick="selectInd('${t.id}')">
      <span>${isZh?t.zh:t.en}</span>
      <span class="tab-count">${t.count}</span>
    </button>`).join('');
}

function renderGrid(){
  if(!gridEl) return;
  const isZh=document.body.classList.contains('zh');
  const filtered=activeInd==='all'?employees:employees.filter(e=>e.i===activeInd);
  gridEl.innerHTML=filtered.map(e=>{
    const ind=industries.find(i=>i.id===e.i);
    return`<div class="emp-card emp-soon" data-emp="${e.en.toLowerCase().replace(/[^a-z0-9]/g,'-')}" role="note" aria-disabled="true">
      <div class="emp-badge-soon">${isZh?'即将开通':'SOON'}</div>
      <div class="emp-industry">${isZh?ind.zh:ind.en}</div>
      <div class="emp-name">${isZh?e.zh:e.en}</div>
      <div class="emp-name-en">${isZh?e.en:e.zh}</div>
      <div class="emp-desc">${isZh?e.zhDesc:e.enDesc}</div>
      <div class="emp-enter emp-enter-soon">
        <span>${isZh?'尚未上线':'NOT YET LIVE'}</span>
      </div>
    </div>`;
  }).join('');
}

function renderMatrix(){renderTabs();renderGrid();}

window.selectInd=function(id){
  activeInd=id;
  renderMatrix();
};

renderMatrix();

// Prevent employee cards/claw link from navigating (placeholder URLs)
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-emp]');
  if(t){e.preventDefault();
    const el=document.getElementById('taste');
    if(el) el.scrollIntoView({behavior:'smooth',block:'start'});
  }
});

// ===== 访问总次数（Durable Object 计数）=====
(async function(){
  try{
    var el=document.getElementById('visitCount'); if(!el) return;
    var counted=sessionStorage.getItem('sde_visit_counted');
    var r=await fetch('/api/visits',{method:counted?'GET':'POST'});
    if(!counted) sessionStorage.setItem('sde_visit_counted','1');
    var d=await r.json();
    el.textContent=d.total.toLocaleString('zh-Hans-CN');
  }catch(e){/* 静默失败，不影响页面 */}
})();

// 今日长文星光生成
(function(){
  var c=document.getElementById('ll-stars');
  if(!c)return;
  var html='';
  for(var i=0;i<60;i++){
    var x=Math.random()*100,y=Math.random()*100,size=Math.random()*2+0.8,dur=Math.random()*3+2,dl=Math.random()*4,mo=Math.random()*0.45+0.5;
    html+='<span class="ll-star" style="left:'+x+'%;top:'+y+'%;width:'+size+'px;height:'+size+'px;--d:'+dur+'s;--dl:'+dl+'s;--mo:'+mo+'"></span>';
  }
  html+='<span class="ll-shoot" style="left:10%;top:15%;animation-delay:2s"></span>';
  html+='<span class="ll-shoot" style="left:60%;top:8%;animation-delay:5s"></span>';
  c.innerHTML=html;
})();
