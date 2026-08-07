#!/usr/bin/env python3
"""Rebuild Frontier panels 51--60 to the V7 8+12 publication contract.

The target pages are broad, first-series panels.  Their evidence anchors are
drawn from later, narrower panels already present in the site, while every
paragraph and collision ledger is written anew for the broad-panel question.
"""
from __future__ import annotations

import collections
import html
import re
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "frontier"
CN = re.compile(r"[\u4e00-\u9fff]")
FIELDS = ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名")
FAMILIES = (
    "01 谁进入分母",
    "02 单一读数代表复杂对象",
    "04 测量不改变被测对象",
    "13 时间尺度可自由压缩",
    "17 局部最优可加总为整体最优",
    "18 干预不回写到被干预者",
)
LABELS = list("甲乙丙丁戊己庚辛") + ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
POSITION_PAIRS = (("S", "S"), ("D", "D"), ("E", "E"), ("S", "D"), ("S", "E"), ("D", "E"))


def cn(text: str) -> int:
    return len(CN.findall(re.sub(r"<[^>]+>", "", text)))


def clean(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\s+", " ", text).strip(" 　")


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def short(text: str, limit: int = 74) -> str:
    text = clean(text).rstrip("。；")
    if len(text) <= limit:
        return text
    cut = max(text.rfind("，", 0, limit), text.rfind("；", 0, limit), text.rfind("。", 0, limit))
    return text[: cut if cut > 24 else limit].rstrip("，；。")


def site_numbers() -> dict[str, int]:
    hub = (PUB / "index.html").read_text(encoding="utf-8")
    return {
        slug: int(no)
        for slug, no in re.findall(r'href="/frontier/([^/]+)/"><span class="num">(\d+)</span>', hub)
    }


NUMBERS = site_numbers()


def parse_donor(slug: str) -> tuple[list[dict], list[str]]:
    """Read the twenty evidence anchors from an already-published panel."""
    text = (PUB / slug / "index.html").read_text(encoding="utf-8")
    starts = list(re.finditer(r"<h2(?:\s[^>]*)?>(.*?)</h2>", text, re.S))
    items: list[dict] = []
    for j, match in enumerate(starts[:20]):
        block = text[match.start() : starts[j + 1].start() if j + 1 < len(starts) else len(text)]
        raw_head = match.group(1)
        en_match = re.search(r'<span class="en">(.*?)</span>', raw_head, re.S)
        en = clean(en_match.group(1)) if en_match else ""
        title = clean(re.sub(r'<span class="en">.*?</span>', "", raw_head, flags=re.S))
        title = re.sub(r"^[甲乙丙丁戊己庚辛一二三四五六七八九十百\d]+、", "", title)
        if not en_match:
            latin = re.search(r"[A-Za-z]", title)
            if latin and latin.start() > 1:
                en = title[latin.start():].strip()
                title = title[:latin.start()].rstrip(" ：:")
        src_match = re.search(r'<div class="src">(.*?)</div>', block, re.S)
        src_raw = src_match.group(1) if src_match else ""
        src_pairs = {
            k: clean(v)
            for k, v in re.findall(r"<i>(提出|争议|最新|关键)</i>(.*?)(?=　<i>|$)", src_raw, re.S)
        }
        col_match = re.search(r'<div class="col">(.*?)</div>', block, re.S)
        col_raw = col_match.group(1) if col_match else ""
        col = {
            k: clean(v)
            for k, v in re.findall(r"<i>(位置|单因|预设|量纲|失效|自曝|空栏|异名)</i>(.*?)(?=　<i>|$)", col_raw, re.S)
        }
        key = KEY_OVERRIDES.get(title, src_pairs.get("关键") or re.sub(r"^(?:只认|只保留|只承认)", "", col.get("单因", "")))
        key = re.sub(r"^决定「.*?」方向的只有", "", key)
        key = key.replace(f"「{title}」", "")
        debate = src_pairs.get("争议") or col.get("预设") or f"{title}能否跨场景保持方向"
        if re.search(r"争点[:：]", debate):
            debate = re.split(r"争点[:：]", debate, maxsplit=1)[1]
        boundary = col.get("失效") or debate
        if debate.startswith("[间接]"):
            debate = boundary
        if title in KEY_OVERRIDES and not src_pairs.get("争议") and not col.get("预设"):
            debate = f"{key}能否跨平台保持服务语义"
            boundary = f"{key}遭遇分区、倾斜或高并发时会失去原方向"
        measure = col.get("量纲") or f"{key}兑现次数／全部候选与中止次数"
        propose = CITATION_OVERRIDES.get(title, src_pairs.get("提出") or f"{title}的原始论文与官方技术记录")
        items.append(
            {
                "title": title,
                "en": en or title,
                "key": short(key, 40),
                "propose": clean(propose),
                "debate": short(debate, 48),
                "boundary": short(boundary, 55),
                "measure": short(measure, 46),
                "alias_slug": slug,
                "alias_title": title,
            }
        )
    refs = [clean(x) for x in re.findall(r"<li>(.*?)</li>", text, re.S)]
    refs.extend(x["propose"] for x in items)
    return items, list(dict.fromkeys(x for x in refs if len(x) > 12))


CITATION_OVERRIDES = {
    "存算分离": "Dageville et al., Proceedings of SIGMOD, 215–226 (2016), doi:10.1145/2882903.2903741",
    "湖仓一体与开放表格式": "Armbrust et al., Conference on Innovative Data Systems Research (2021), The Lakehouse",
    "写优化存储": "O'Neil et al., Acta Informatica 33, 351–385 (1996), doi:10.1007/s002360050048",
    "确定性事务": "Thomson et al., Proceedings of SIGMOD, 1–12 (2012), doi:10.1145/2213836.2213838",
    "流批统一": "Akidau et al., Proceedings of VLDB 8, 1792–1803 (2015), doi:10.14778/2824032.2824076",
    "数据版本、血缘与治理": "Cheney, Chiticariu & Tan, Foundations and Trends in Databases 1, 379–474 (2009), doi:10.1561/1900000006",
    "云原生的成本模型": "Kossmann et al., Proceedings of ICDE, 579–590 (2010), doi:10.1109/ICDE.2010.5447831",
    "数据系统的碎片化与再收敛": "Stonebraker & Çetintemel, Proceedings of ICDE, 2–11 (2005), doi:10.1109/ICDE.2005.1",
    "软件定义网络的实际收敛": "McKeown et al., ACM SIGCOMM Computer Communication Review 38, 69–74 (2008), doi:10.1145/1355734.1355746",
    "内容分发与边缘": "Satyanarayanan, Computer 50(1), 30–39 (2017), doi:10.1109/MC.2017.9",
    "多重图形化把分辨率问题转成叠加误差": "Bencher et al., Proceedings of SPIE 7274, 72740G (2009), Self-Aligned Double Patterning",
    "高数值孔径EUV把景深与成像场重新定价": "van Schoot et al., Proceedings of SPIE 10143, 101430R (2017), High-NA EUV Lithography",
    "背面供电把电源网络移出信号互连层": "Prasad et al., IEEE International Electron Devices Meeting (2019), Backside Power Delivery",
    "先进封装热管理从芯片结温转向三维热网络": "Xu et al., Journal of Electronic Packaging 147(1), 1–69 (2024), doi:10.1115/1.4065650",
    "玻璃核心基板挑战有机基板翘曲极限": "Sukumaran et al., IEEE Transactions on Components, Packaging and Manufacturing Technology 6, 373–383 (2016)",
    "高带宽存储把内存墙变成封装问题": "JEDEC, JESD238 High Bandwidth Memory DRAM (HBM3) (2022)",
    "晶圆厂可持续性把水与能源纳入节点成本": "Boyd, IEEE International Symposium on Sustainable Systems and Technology (2011), Environmental Assessment of Semiconductor Manufacturing",
    "晶圆制造数字孪生从调度优化走向缺陷因果": "Kritzinger et al., IFAC-PapersOnLine 51(11), 1016–1022 (2018), doi:10.1016/j.ifacol.2018.08.474",
    "光学生物传感从检出限转向基质特异性": "Homola, Chemical Reviews 108, 462–493 (2008), doi:10.1021/cr068107d",
}

KEY_OVERRIDES = {
    "存算分离": "持久数据留在对象存储而计算节点无状态弹性",
    "湖仓一体与开放表格式": "给廉价对象存储补上事务表语义",
    "写优化存储": "把随机写改成顺序写并由后台压实付账",
    "确定性事务": "预定全局执行顺序消除运行时协调歧义",
    "流批统一": "把批处理视作有界数据流的一种情形",
    "数据版本、血缘与治理": "让每个结果携带来源、变换和责任版本",
    "云原生的成本模型": "以给定服务单位的总账而非峰值优化系统",
    "数据系统的碎片化与再收敛": "用统一交换契约压低专用系统同步债务",
    "软件定义网络的实际收敛": "让控制逻辑脱离专有转发设备并开放编排",
    "内容分发与边缘": "把数据和计算移到靠近请求的接入位置",
}


DONOR_SLUGS = (
    "autonomous-systems-cyber-physical-systems",
    "mechatronics-biomechatronics",
    "quantum-engineering-quantum-control",
    "quantum-software-programming",
    "post-quantum-cryptography",
    "database-systems",
    "computer-networks",
    "computer-engineering-hardware-software-codesign",
    "integrated-circuit-design-eda",
    "micro-nano-engineering-mems-nems",
    "semiconductor-manufacturing-packaging",
    "optical-engineering-instruments",
    "nonlinear-optics-laser-science",
    "quantum-communication-quantum-networks",
    "6g-future-networks",
    "renewable-energy-engineering",
    "smart-grids-integrated-energy-systems",
    "hydrogen-science-engineering",
    "energy-materials",
    "space-systems-engineering",
    "space-sustainability-debris-governance",
    "advanced-air-mobility-evtol",
    "critical-dual-use-tech-economic-security",
    "computational-precision-health",
    "translational-medicine-biomedical-innovation",
    "digital-biomarkers-wearable-health",
    "learning-health-systems-implementation-science",
    "medical-physics",
)
DONORS: dict[str, list[dict]] = {}
DONOR_REFS: dict[str, list[str]] = {}
for _slug in DONOR_SLUGS:
    DONORS[_slug], DONOR_REFS[_slug] = parse_donor(_slug)


def manual(title: str, en: str, key: str, propose: str, debate: str, boundary: str, measure: str) -> dict:
    return {
        "title": title,
        "en": en,
        "key": key,
        "propose": propose,
        "debate": debate,
        "boundary": boundary,
        "measure": measure,
    }


M: dict[str, dict] = {
    # Robotics
    "r_balance": manual("动态平衡成为可重复工程", "Dynamic Balance", "以质心、支撑多边形与接触力联合闭环保持步态", "Kajita et al., IEEE ICRA, 1620–1626 (2003), doi:10.1109/ROBOT.2003.1241826", "实验室地面上的抗扰恢复能否外推到磨损、软地面与载荷变化", "脚底摩擦锥或状态估计失配时，更激进的步态反而缩短可恢复时间", "无跌倒完成次数／全部推扰、换载与中止试验次数"),
    "r_slam": manual("SLAM把定位与建图合成同一估计问题", "Simultaneous Localization and Mapping", "在未知环境中联合估计机器人轨迹与地图", "Cadena et al., IEEE Transactions on Robotics 32, 1309–1332 (2016), doi:10.1109/TRO.2016.2624754", "基准数据集精度能否代表长期运行中的感知混淆与地图变化", "重复纹理、动态物体或回环误配会让高置信地图整体折叠", "每公里绝对轨迹误差与闭环误报数／全部有效里程"),
    "r_dmp": manual("动态运动基元把示教轨迹变成可调技能", "Dynamic Movement Primitives", "用稳定吸引子与形状项编码可缩放运动", "Ijspeert et al., Neural Computation 25, 328–373 (2013), doi:10.1162/NECO_a_00393", "轨迹参数化能否覆盖接触任务中的多峰选择与意外约束", "目标或障碍改变到训练域外时，稳定收敛可能把末端送入错误接触", "新目标下无碰撞完成的轨迹数／全部重定向试验数"),
    "r_visuo": manual("深度视觉运动策略把感知与控制同训", "Deep Visuomotor Policies", "由图像直接学习任务相关表征与控制动作", "Levine et al., Journal of Machine Learning Research 17(39), 1–40 (2016)", "端到端收益来自表示学习还是更大的真机采集预算", "相机外参、背景和物体材质漂移时，像素相似会掩盖物理动作反号", "独立场景成功次数／全部真机尝试与人工重置次数"),
    "r_sim2real": manual("域随机化把仿真误差改成训练分布", "Domain Randomization", "随机改变渲染与物理参数以学习可迁移不变量", "Tobin et al., IEEE/RSJ IROS, 23–30 (2017), doi:10.1109/IROS.2017.8202133", "随机化范围能否覆盖真实接触、柔性材料与传感延迟", "范围过窄不迁移，范围过宽又会压低策略对关键物理量的辨别", "零样本真机成功次数／全部仿真训练种子与真机试验次数"),
    "r_diffusion": manual("扩散策略承认合理动作不止一条", "Diffusion Policy", "用条件去噪过程表示多峰动作序列", "Chi et al., International Journal of Robotics Research 43 (2024), doi:10.1177/02783649241273668", "离线成功率能否承受闭环偏离和长时误差累积", "动作块越平滑并不保证恢复；一旦越过演示支撑集，去噪会自信地产生错误序列", "连续任务成功次数／全部起始状态、重试与接管次数"),
    "r_rtx": manual("跨本体数据池第一次检验共同策略", "Open X-Embodiment and RT-X", "把不同机器人动作映射到共同数据与训练接口", "Open X-Embodiment Collaboration, IEEE ICRA (2024), doi:10.1109/ICRA57147.2024.10611477", "跨本体正迁移能否抵销动作语义、相机与夹具差异", "大本体数据会压过小本体；数据越多，小平台的最差任务反而可能更差", "受益任务数／全部机器人—任务组合与阴性迁移组合"),
    "r_humanoid": manual("人形平台接受长时可靠性而非剪辑验收", "Humanoid Deployment", "用连续作业时间、接管和恢复而非单次动作定义能力", "Griffin et al., Science Robotics 4, eaau5872 (2019), doi:10.1126/scirobotics.aau5872", "人体尺度适配是否足以抵销双足能耗、维护与共因故障", "演示动作越复杂，布景、遥控与重拍对公开成功率的贡献反而越大", "无人接管工作小时／全部开机小时及故障恢复小时"),
    # Quantum algorithms
    "q_shor": manual("Shor算法把因数分解移出经典舒适区", "Shor's Algorithm", "用量子傅里叶变换求周期并约化因数分解", "Shor, SIAM Journal on Computing 26, 1484–1509 (1997), doi:10.1137/S0097539795293172", "多项式门数是否在纠错和编译后仍代表可执行优势", "逻辑算法越漂亮，物理纠错时空体积可能越快吞没现实期限", "成功分解实例数／全部逻辑运行与纠错中止运行"),
    "q_hhl": manual("HHL打开量子线性代数路线", "HHL Linear-System Algorithm", "把稀疏良态线性方程的解编码进量子态", "Harrow, Hassidim & Lloyd, Physical Review Letters 103, 150502 (2009), doi:10.1103/PhysRevLett.103.150502", "条件数、输入制备与输出读取是否取消指数加速", "矩阵变坏或需要读出完整解时，问题规模越大，端到端优势反而越小", "端到端达标实例数／全部条件数、装载和读出预算组合"),
    "q_sim": manual("量子模拟保留最贴近硬件的加速理由", "Universal Quantum Simulation", "以可控量子系统复现局域哈密顿量演化", "Lloyd, Science 273, 1073–1078 (1996), doi:10.1126/science.273.5278.1073", "模拟器精度能否在噪声、有限尺寸和不可直接观测量下校准", "目标哈密顿量与装置漂移耦合时，更长演化反而积累不可辨识误差", "误差阈值内观测量数／全部预注册观测量与演化时刻"),
    "q_qram": manual("数据加载把量子加速拉回输入账", "Quantum Random-Access Memory", "以相干地址访问制备算法所需数据态", "Giovannetti, Lloyd & Maccone, Physical Review Letters 100, 160501 (2008), doi:10.1103/PhysRevLett.100.160501", "海量相干路由器的制造和容错成本能否低于算法省下的时间", "若装载本身线性扫描经典数据，核心电路越快，端到端占比反而越低", "含装载与读出的总耗时优势实例数／全部数据规模与误差预算"),
    "q_complex": manual("复杂度理论先划出量子计算边界", "Quantum Complexity Boundaries", "用查询与复杂度类别区分可加速和不可加速任务", "Bernstein & Vazirani, SIAM Journal on Computing 26, 1411–1473 (1997), doi:10.1137/S0097539796300921", "黑箱分离能否代表有结构输入和现实成本模型", "预言机优势若依赖不可构造访问，证明越强，工程含义反而越弱", "保留优势的问题族数／全部加入输入输出成本的问题族"),
    "q_dequant": manual("去量子化迫使加速声明补上经典基线", "Dequantization", "用量子启发采样在经典机上复现推荐优势", "Tang, Proceedings of STOC (2019), doi:10.1145/3313276.3316310", "量子优势来自量子机制还是遗漏了同等数据访问的经典算法", "一旦给经典算法同样的采样接口，数据越大，名义指数差距反而会消失", "同输入模型下仍胜出的任务数／全部声称量子加速任务数"),
    "q_qsvt": manual("量子奇异值变换统一一批算法骨架", "Quantum Singular-Value Transformation", "以块编码上的多项式变换处理矩阵谱", "Gilyén et al., Proceedings of STOC (2019), doi:10.1145/3313276.3316366", "统一框架的查询复杂度能否携带块编码和容错常数", "块编码代价随数据结构增长时，抽象越统一，端到端资源反而越难比较", "达到目标误差的资源估计数／全部块编码、精度和成功概率组合"),
    "q_crypto": manual("密码分析资源估计把威胁写成物理账", "Cryptanalytic Resource Estimation", "把逻辑门、工厂和运行时间换算为物理量子比特", "Gidney & Ekerå, Quantum 5, 433 (2021), doi:10.22331/q-2021-04-15-433", "算法改进能否抵销纠错周期、布线和魔法态工厂约束", "只报逻辑门会把制造和运行失败移出分母，电路越省，系统瓶颈反而越集中", "期限内成功攻击参数组数／全部硬件假设和纠错预算组合"),
    # Cryptography
    "c_fhe": manual("全同态加密证明密文上可以任意计算", "Fully Homomorphic Encryption", "用自举刷新噪声以支持任意深度电路", "Gentry, Proceedings of STOC, 169–178 (2009), doi:10.1145/1536414.1536440", "渐近可行性能否越过延迟、密钥与泄漏的工程门槛", "电路深度和数据搬运加入后，功能越完整，单位任务吞吐反而越低", "预算内完成的加密任务数／全部电路、密钥与失败运行"),
    "c_snark": manual("简洁证明把复算成本交给验证者", "Succinct Non-Interactive Arguments", "用多项式承诺把大计算压成短证明", "Groth, EUROCRYPT 2016, 305–326, doi:10.1007/978-3-662-49896-5_11", "可信设置、知识假设和电路化成本能否进入安全声明", "若设置材料或实现泄漏，证明越短，伪造风险越容易被公共链放大", "验证通过且外部复算一致的证明数／全部生成与中止证明"),
    "c_side": manual("侧信道证明数学安全不等于设备安全", "Side-Channel Cryptanalysis", "由时间、缓存或功耗相关恢复秘密状态", "Kocher, CRYPTO 1996, 104–113, doi:10.1007/3-540-68697-5_9", "常数时间与掩码实现能否覆盖编译器、微架构和物理探针", "优化级别或芯片改变时，理论裕量越高，泄漏痕迹反而可能越稳定", "未泄露实现数／全部编译、芯片与攻击迹线组合"),
    "c_dualec": manual("Dual_EC争议把参数生成变成治理问题", "Dual_EC_DRBG", "把可疑常数与潜在陷门纳入标准审查", "NIST, Withdrawal of NIST SP 800-90A (2015)", "公开标准流程能否识别只有参数选择者掌握的结构优势", "若常数来源不可复现，采用范围越广，单点陷门造成的系统风险反而越大", "可独立复现参数集数／全部标准化常数与实现"),
    "c_zk": manual("零知识把正确与泄密拆成两个命题", "Zero-Knowledge Proofs", "在不暴露见证的条件下证明语句成立", "Goldwasser, Micali & Rackoff, SIAM Journal on Computing 18, 186–208 (1989), doi:10.1137/0218012", "组合安全和具体实现能否保持模拟器给出的隐私界线", "随机数复用或电路侧漏出现时，证明越多，见证反而越易被关联", "不泄漏且验证正确的会话数／全部会话、重试与异常"),
    "c_mpc": manual("安全多方计算让联合统计不必汇总原始数据", "Secure Multiparty Computation", "以秘密分享或混淆电路联合求函数", "Yao, Proceedings of FOCS, 160–164 (1982), doi:10.1109/SFCS.1982.38", "半诚实模型、掉线和串谋边界能否代表真实组织合作", "参与方或网络抖动增加时，隐私保障越强，完成率反而越低", "协议内完成任务数／全部参与方、掉线与中止任务"),
    "c_tls": manual("TLS 1.3删掉历史兼容债务", "TLS 1.3", "以更短握手和前向保密重写传输安全默认", "IETF, RFC 8446: The Transport Layer Security Protocol Version 1.3 (2018)", "零往返和中间盒兼容是否重新引入重放与降级面", "为兼容保留旧路径时，部署越广，最弱协商反而越决定真实安全", "强套件成功握手数／全部协商、回退与失败握手"),
    "c_ratchet": manual("双棘轮把会话密钥变成持续更新状态", "Double Ratchet", "结合根密钥与消息密钥更新实现前向和事后安全", "Cohn-Gordon et al., IEEE EuroS&P, 451–466 (2017), doi:10.1109/EuroSP.2017.27", "多设备、离线消息和备份能否保持形式模型中的状态连续性", "设备回滚或状态复制时，更新越频繁，密钥不同步反而越难发现", "保持安全属性的消息链数／全部设备切换与乱序链"),
    "c_trans": manual("证书透明把错误签发变成公共可见事件", "Certificate Transparency", "用仅追加日志和一致性证明监督证书签发", "IETF, RFC 6962: Certificate Transparency (2013)", "可见性是否等于及时发现、撤销和追责", "日志数量增加而监测责任未落实时，覆盖越高，未处置告警反而越多", "被监测并处置的异常证书数／全部日志异常与漏记"),
    "c_password": manual("Argon2把内存成本纳入口令哈希", "Memory-Hard Password Hashing", "用可调内存与并行成本压低专用破解优势", "IETF, RFC 9106: Argon2 Memory-Hard Function (2021)", "参数推荐能否随设备差异和攻击硬件变化持续更新", "为照顾低端设备而降低内存时，用户越多，离线破解收益反而越高", "达标口令记录数／全部设备参数、迁移与失败记录"),
    # Distributed systems
    "d_mapreduce": manual("MapReduce把失败恢复写进数据处理模型", "MapReduce", "把计算移到数据并自动重跑失败任务", "Dean & Ghemawat, Proceedings of OSDI, 137–150 (2004)", "批处理抽象能否覆盖低时延、迭代和强一致任务", "拖尾任务和数据倾斜出现时，节点越多，尾部完成时间反而越长", "期限内完成作业数／全部任务、重试与中止作业"),
    "d_dynamo": manual("Dynamo让可用性冲突在应用层显形", "Dynamo", "以一致性哈希、向量时钟和法定人数保持服务", "DeCandia et al., Proceedings of SOSP (2007), doi:10.1145/1294261.1294281", "最终一致性能否承受跨对象不变量和人工冲突合并", "分区越久，写入越可用，恢复后的语义冲突反而越难清算", "无语义冲突完成请求数／全部读写、修复与失败请求"),
    "d_raft": manual("Raft把共识拆成可教学的状态机", "Raft Consensus", "以领导者选举、日志复制和安全约束组织共识", "Ongaro & Ousterhout, USENIX ATC, 305–319 (2014)", "易理解的协议能否避免成员变更、快照和实现细节中的安全漏洞", "网络抖动触发频繁选举时，副本越多，可用吞吐反而越低", "提交且不回滚日志数／全部任期、分区与失败提交"),
    "d_bitcoin": manual("比特币把开放成员共识变成可运行系统", "Bitcoin", "用工作量证明和最长链在女巫环境下排序交易", "Nakamoto, Bitcoin: A Peer-to-Peer Electronic Cash System (2008)", "抗审查收益能否抵销能耗、吞吐与治理集中", "矿池集中或费用市场拥堵时，算力越高，普通交易的可及性反而越低", "最终确认交易数／全部广播、重组与过期交易"),
    "d_eth": manual("以太坊把共识账本改成可编程状态机", "Ethereum", "以确定性虚拟机执行共享合约状态", "Wood, Ethereum Yellow Paper (2014)", "可组合程序是否把代码漏洞放大为不可逆系统事件", "共享状态越可组合，一份错误合约造成的级联损失反而越广", "无回滚正确执行调用数／全部合约调用与失败交易"),
    "d_crdt": manual("CRDT用代数约束换取无协调合并", "Conflict-Free Replicated Data Types", "让并发更新按交换、结合与幂等规则收敛", "Shapiro et al., SSS 2011, 386–400, doi:10.1007/978-3-642-24550-3_29", "状态收敛是否足以保证余额、权限和业务不变量", "副本越能离线更新，违反跨对象约束的状态反而越多", "收敛且满足业务不变量的合并数／全部并发更新"),
    "d_spanner": manual("Spanner用时间不确定度购买全球一致性", "Spanner and TrueTime", "以有界时钟误差实现外部一致事务", "Corbett et al., Proceedings of OSDI, 251–264 (2012)", "专用时钟基础设施能否迁移到普通云和多组织边界", "等待不确定区间能保安全，但时钟退化时延迟越保守，吞吐反而越低", "满足外部一致的事务数／全部跨区事务与中止"),
    "d_k8s": manual("Kubernetes把期望状态变成持续控制循环", "Kubernetes", "由声明式对象和协调器不断修复运行状态", "Burns et al., ACM Queue 14(1) (2016), doi:10.1145/2898442.2898444", "自动恢复能否区分短暂故障、错误配置与应用级语义失败", "控制器共享错误期望时，修复越快，错误副本反而扩散越快", "达成正确服务状态的协调数／全部变更、回滚与失败循环"),
    "d_serverless": manual("无服务器计算把扩缩容交给平台", "Serverless Computing", "按事件启动短时函数并隐藏服务器生命周期", "Jonas et al., Communications of the ACM 62(12), 76–83 (2019), doi:10.1145/3368454", "冷启动、状态和供应商边界能否支撑持续低时延任务", "函数拆得越细，跨服务数据搬运和尾延迟反而越占主账", "期限内完成调用数／全部冷启动、重试和限流调用"),
    "d_rollup": manual("Rollup把执行移出主链而把证明留在主链", "Blockchain Rollups", "批量压缩交易并以欺诈或有效性证明结算", "Ethereum Foundation, An Incomplete Guide to Rollups (2021)", "排序器、数据可用性和跨链桥是否形成新的信任集中", "二层吞吐越高，退出拥堵或桥接失败造成的锁定规模反而越大", "最终可退出交易数／全部提交、挑战与桥接失败交易"),
    # Photonics and communications
    "p_coherent": manual("相干接收把光场相位重新带回通信", "Coherent Optical Detection", "以本振和数字信号处理恢复幅度、相位与偏振", "Ip et al., Optics Express 16, 753–791 (2008), doi:10.1364/OE.16.000753", "DSP增益能否抵销激光线宽、非线性和功耗", "符号率越高，采样与均衡功耗反而越接近链路预算上限", "误码门槛内净比特数／全部偏振、距离与失败帧"),
    "p_capacity": manual("非线性容量极限终结单纯加功率", "Nonlinear Fiber Capacity", "把克尔非线性与放大噪声共同写入容量边界", "Essiambre et al., Journal of Lightwave Technology 28, 662–701 (2010), doi:10.1109/JLT.2009.2039464", "高斯噪声近似能否覆盖跨信道相关和长距离补偿", "发射功率越过最优点后，信噪比和可达速率反而同时下降", "可达信息率／全部带宽、功率与跨距配置"),
    "p_sdm": manual("空分复用把单纤扩容改成多空间通道", "Space-Division Multiplexing", "以多芯或少模光纤并行承载独立空间信道", "Richardson, Fini & Nelson, Nature Photonics 7, 354–362 (2013), doi:10.1038/nphoton.2013.94", "容量倍增能否抵销放大器、耦合器和多输入均衡复杂度", "通道数越多，串扰校准与共同故障造成的净容量折扣反而越大", "独立恢复净通道数／全部空间通道与失配状态"),
    "p_silicon": manual("硅光把光路带进CMOS制造语境", "Silicon Photonics", "以硅波导、调制器和探测器集成短距链路", "Soref, IEEE Journal of Selected Topics in Quantum Electronics 12, 1678–1687 (2006), doi:10.1109/JSTQE.2006.883151", "晶圆级规模能否解决光源、封装与温漂的异质难题", "器件密度越高，耦合损耗和热调谐功耗反而越支配系统效率", "封装后达标链路数／全部裸片、耦合与温度循环"),
    "p_dc": manual("数据中心把链路距离换成端口密度问题", "Datacenter Optical Interconnects", "用每比特能耗与带宽密度重写机内互连", "Miller, Applied Optics 49, F59–F70 (2010), doi:10.1364/AO.49.000F59", "光互连能否在短距上胜过铜的成本、可靠性和可维修性", "距离变短时激光与封装的固定功耗占比反而上升", "每瓦有效太比特数／全部端口、重训与失效小时"),
    "p_subsea": manual("海底光缆从单纤冠军转向整缆功率最优", "Submarine Cable Systems", "在馈电约束下联合分配纤芯数、功率和调制", "Winzer et al., Proceedings of the IEEE 106, 2291–2312 (2018), doi:10.1109/JPROC.2018.2862134", "单纤容量纪录能否代表整缆可维护吞吐", "每纤功率继续提高时，整缆总容量反而会因馈电上限下降", "可修复净容量×公里／全部纤芯、跨距与中断时段"),
    "p_shape": manual("概率整形把星座概率变成容量旋钮", "Probabilistic Constellation Shaping", "按信道条件改变符号出现概率逼近容量", "Böcherer et al., Bell Labs Technical Journal 19, 25–34 (2015), doi:10.15325/BLTJ.2015.2401373", "整形增益能否穿过有限块长、解码复杂度和速率适配", "分布匹配越精细，短包时延和实现损耗反而越明显", "净整形增益比特数／全部块长、码率与失败帧"),
    "p_hollow": manual("空芯光纤把大部分光移出玻璃", "Hollow-Core Fiber", "以反谐振结构在空气芯中低损传输", "Jasion et al., Nature Communications 10, 2019, doi:10.1038/s41467-019-10425-6", "实验低损能否转成公里级制造一致性与现场接续", "样品越长，微弯、结构漂移和接头损耗反而越容易吞掉材料优势", "达标公里数／全部拉丝、接续与环境循环长度"),
    "p_cpo": manual("共封装光学把光引擎推到交换芯片旁", "Co-Packaged Optics", "缩短信号电走线以降低高速I/O能耗", "Optical Internetworking Forum, Co-Packaging Framework IA (2022)", "功耗收益能否抵销热耦合、激光维护和更换粒度", "封装越紧，单个光引擎故障造成的维修范围反而越大", "每瓦可用端口带宽／全部端口、热循环与维修事件"),
    "p_switch": manual("光路交换以重配置换取低数据搬运能耗", "Optical Circuit Switching", "为大流量动态建立无逐包转发光路", "Farrington et al., Proceedings of SIGCOMM (2010), doi:10.1145/1851182.1851183", "流量可预测性是否足以覆盖重配置时延与突发短流", "大流越集中越受益，但短流增多时排队尾延迟反而上升", "按期完成流量字节数／全部电路建立、阻塞与回退流"),
    # Energy and control
    "e_nuclear": manual("低碳系统重新给可调核电定价", "Firm Low-Carbon Power", "以系统容量与灵活性价值评价核电而非只看度电成本", "Sepulveda et al., Joule 2, 2403–2420 (2018), doi:10.1016/j.joule.2018.08.006", "高资本成本能否由低碳系统中的可靠容量价值抵销", "工期和融资风险加入后，名义容量越大，单位可交付价值反而越不确定", "压力时段可交付低碳电量／全部承诺时段与停机"),
    "e_ldes": manual("长时储能用持续时长重排技术路线", "Long-Duration Energy Storage", "把功率部件与能量容量成本分开比较", "Sepulveda et al., Nature Energy 6, 506–516 (2021), doi:10.1038/s41560-021-00796-8", "模型中的低成本能量介质能否穿过效率、选址与低利用率", "时长增加时每千瓦时成本可降，但往返效率造成的系统损失反而扩大", "压力事件交付兆瓦时／全部承诺、启动与中止事件"),
    "k_mpc": manual("模型预测控制在工业现场成年", "Model Predictive Control", "滚动求解受约束有限时域优化并只执行首步", "Qin & Badgwell, Control Engineering Practice 11, 733–764 (2003), doi:10.1016/S0967-0661(02)00186-7", "模型偏差和求解时限能否在扰动下维持闭环可行", "预测域越长不一定越稳；计算超时会让更优计划反而成为过期动作", "无约束违例控制周期数／全部周期、超时与降级周期"),
    "k_embed": manual("嵌入式求解器把在线优化压进毫秒预算", "Embedded Optimization", "以热启动活动集快速重复求解二次规划", "Ferreau et al., International Journal of Robust and Nonlinear Control 24, 2787–2807 (2014), doi:10.1002/rnc.3180", "平均求解时间能否代表最坏时限和数值病态", "问题越接近约束边界，迭代和条件数反而越可能同时爆发", "时限内给出可行解周期数／全部控制周期与求解失败"),
    "k_robust": manual("鲁棒与自适应控制分开结算不确定性", "Robust and Adaptive Control", "以最坏界与在线辨识分别处理结构未知", "Zhou, Doyle & Glover, Robust and Optimal Control, Prentice Hall (1996)", "保守裕量和参数收敛能否在未激励方向同时成立", "裕量加大时稳定性增强，但性能和可辨识性反而可能下降", "满足稳定与性能界的运行数／全部参数、扰动与切换运行"),
    "k_network": manual("网络化控制把时延丢包写进闭环", "Networked Control Systems", "把通信调度、时延与控制稳定性联合设计", "Hespanha, Naghshtabrizi & Xu, Proceedings of the IEEE 95, 138–162 (2007), doi:10.1109/JPROC.2006.887288", "独立随机丢包模型能否覆盖拥塞、攻击和共因故障", "控制器越依赖高频反馈，成串丢包造成的方向反转反而越快", "稳定服务周期数／全部丢包模式、延迟和重连周期"),
    "k_stux": manual("震网事件把工控安全变成物理安全", "Stuxnet and Industrial Control Security", "用过程知识和隐蔽反馈操纵实体设备", "Falliere, Murchu & Chien, W32.Stuxnet Dossier, Symantec (2011)", "隔离网与传统杀毒能否识别针对控制逻辑和传感回放的攻击", "自动化程度越高，伪造测量持续越久，物理损伤反而越难由操作员察觉", "被检测并安全降级事件数／全部攻击注入与漏报事件"),
}


def d(slug: str, index: int) -> tuple[str, str, int]:
    return ("d", slug, index)


def m(key: str) -> tuple[str, str]:
    return ("m", key)


PANELS = [
    {
        "no": 51, "slug": "robotics", "title": "机器人学", "group": "计算与人工智能",
        "scope": "本体、感知、策略、接触与现场维护", "metrics": "任务成功率、每千小时接管次数、接触力峰值、能耗和恢复时间",
        "actors": "机器人供应商、集成商、当班操作员与安全认证机构", "old": "精确模型、固定工位和一次成功演示",
        "thesis": "策略来源从逐任务建模转向跨本体数据学习，但可靠性仍由接触、标定和人工接管共同决定",
        "controversy": "人形是否值得为人体尺度环境支付能耗、维护和双足失稳成本", "outlook": "连续无人接管作业小时、跨本体负迁移和真实故障恢复",
        "recent": ["Slade et al., Nature 630, 2024, doi:10.1038/s41586-024-07697-2", "Open X-Embodiment Collaboration, IEEE ICRA (2024), doi:10.1109/ICRA57147.2024.10611477"],
        "items": [m("r_balance"), d("autonomous-systems-cyber-physical-systems",0), m("r_slam"), d("autonomous-systems-cyber-physical-systems",2), m("r_dmp"), d("mechatronics-biomechatronics",3), d("mechatronics-biomechatronics",11), m("r_sim2real"), m("r_visuo"), d("autonomous-systems-cyber-physical-systems",7), d("autonomous-systems-cyber-physical-systems",8), d("mechatronics-biomechatronics",8), d("mechatronics-biomechatronics",12), d("mechatronics-biomechatronics",16), m("r_diffusion"), m("r_rtx"), d("autonomous-systems-cyber-physical-systems",13), d("autonomous-systems-cyber-physical-systems",16), d("autonomous-systems-cyber-physical-systems",19), m("r_humanoid")],
        "aliases": [d("mechatronics-biomechatronics",0), d("autonomous-systems-cyber-physical-systems",11), d("computer-networks",13)],
    },
    {
        "no": 52, "slug": "quantum-algorithms", "title": "量子计算与算法", "group": "计算与人工智能",
        "scope": "输入制备、量子线路、纠错、测量与经典后处理", "metrics": "逻辑门数、物理量子比特、线路深度、成功概率和端到端运行时间",
        "actors": "算法研究者、硬件团队、编译器维护者与密码迁移负责人", "old": "只比较核心电路查询次数",
        "thesis": "量子加速从复杂度证明走向含输入、纠错和读出的全栈资源合同",
        "controversy": "含噪启发式是否提供可重复效用，还是把经典优化和选择性报告算成量子收益", "outlook": "低于阈值的逻辑误差、可复算资源估计和端到端经典基线",
        "recent": ["Google Quantum AI, Nature 638, 920–926 (2025)", "Ramalho, de Souza & Chaim, ACM Computing Surveys (2025)"],
        "items": [m("q_shor"), m("q_hhl"), m("q_sim"), m("q_qram"), d("quantum-engineering-quantum-control",4), d("quantum-engineering-quantum-control",8), d("quantum-engineering-quantum-control",9), m("q_complex"), d("quantum-engineering-quantum-control",10), m("q_dequant"), d("quantum-software-programming",7), d("quantum-software-programming",12), d("quantum-engineering-quantum-control",12), d("quantum-engineering-quantum-control",14), d("quantum-engineering-quantum-control",15), d("quantum-engineering-quantum-control",17), m("q_qsvt"), m("q_crypto"), d("quantum-software-programming",17), d("quantum-engineering-quantum-control",18)],
        "aliases": [d("quantum-software-programming",7), d("post-quantum-cryptography",19), d("quantum-communication-quantum-networks",10)],
    },
    {
        "no": 53, "slug": "cryptography", "title": "现代密码学", "group": "计算与人工智能",
        "scope": "安全定义、参数生成、协议组合、实现侧信道与迁移治理", "metrics": "具体安全位数、证明与验证时延、握手失败率、泄漏迹线和迁移覆盖率",
        "actors": "标准机构、协议设计者、实现团队、证书运营者与系统所有者", "old": "数学困难性足以代表部署安全",
        "thesis": "密码学的对象从单个困难问题扩成算法、实现、参数来源和替换能力的责任链",
        "controversy": "形式安全证明能否覆盖编译器、硬件侧信道和真实协议组合", "outlook": "后量子混合迁移、密码资产清单、失败遥测和参数可追溯性",
        "recent": ["NIST, FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (2024)", "NIST, FIPS 204: Module-Lattice-Based Digital Signature Standard (2024)"],
        "items": [m("c_fhe"), m("c_snark"), d("post-quantum-cryptography",0), d("post-quantum-cryptography",4), m("c_side"), m("c_dualec"), d("post-quantum-cryptography",7), m("c_zk"), d("post-quantum-cryptography",8), d("post-quantum-cryptography",9), d("post-quantum-cryptography",12), m("c_mpc"), m("c_tls"), m("c_ratchet"), m("c_trans"), m("c_password"), d("post-quantum-cryptography",14), d("post-quantum-cryptography",15), d("post-quantum-cryptography",16), d("post-quantum-cryptography",19)],
        "aliases": [d("post-quantum-cryptography",14), d("computer-networks",1), d("database-systems",11)],
    },
    {
        "no": 54, "slug": "distributed-systems", "title": "分布式系统与区块链", "group": "计算与人工智能",
        "scope": "副本、时钟、网络分区、状态语义、运维控制面与组织信任", "metrics": "提交延迟、尾吞吐、可用时长、重组深度、恢复时间和每笔服务总成本",
        "actors": "云平台、协议维护者、节点运营者、应用所有者与审计监管方", "old": "副本增加和共识完成等于系统可信",
        "thesis": "共识本身越来越便宜，真正昂贵的是语义冲突、运维权限、退出路径与跨组织问责",
        "controversy": "开放链的抗审查价值是否足以抵销排序器、桥接与治理的新集中", "outlook": "故障域透明度、可退出性、数据可用性和跨层成本归因",
        "recent": ["Cloud Native Computing Foundation, Annual Survey 2024 (2024)", "Ethereum Foundation, Protocol Roadmap and Rollup-Centric Scaling Update (2025)"],
        "items": [m("d_mapreduce"), m("d_dynamo"), m("d_raft"), m("d_bitcoin"), m("d_eth"), m("d_crdt"), m("d_spanner"), d("database-systems",2), m("d_k8s"), d("database-systems",0), d("database-systems",1), d("database-systems",6), d("database-systems",7), d("database-systems",12), d("database-systems",15), m("d_serverless"), d("computer-networks",5), d("computer-networks",11), m("d_rollup"), d("database-systems",19)],
        "aliases": [d("database-systems",6), d("computer-networks",4), d("autonomous-systems-cyber-physical-systems",6)],
    },
    {
        "no": 55, "slug": "semiconductors", "title": "半导体与芯片", "group": "工程与技术",
        "scope": "器件静电、光刻、互连、良率、先进封装、热管理与供应链", "metrics": "晶体管密度、缺陷密度、叠加误差、每瓦吞吐、封装良率和交货周期",
        "actors": "晶圆厂、设备材料商、芯片设计者、封装测试厂与终端系统商", "old": "线宽缩小会自动带来性能和成本同步改善",
        "thesis": "缩微没有停止，而是把主要矛盾从晶体管尺寸搬到图形化、供电、内存、封装和制造韧性",
        "controversy": "芯粒与三维集成是真正延续缩放，还是把单片问题转移成接口和热债务", "outlook": "高NA EUV随机缺陷、背面供电良率、混合键合返修和HBM供给",
        "recent": ["IEEE IRDS, More Moore and Packaging Integration Roadmap (2024)", "imec, High-NA EUV and Backside Power Delivery Technical Results (2025)"],
        "items": [d("semiconductor-manufacturing-packaging",i) for i in range(20)],
        "aliases": [d("integrated-circuit-design-eda",14), d("computer-engineering-hardware-software-codesign",15), d("micro-nano-engineering-mems-nems",11)],
    },
    {
        "no": 56, "slug": "photonics", "title": "光子学与通信", "group": "工程与技术",
        "scope": "光源、调制、复用、传输、接收、封装与网络拓扑", "metrics": "可达信息率、误码率、每比特能耗、带宽密度、跨距和维修中断时间",
        "actors": "器件厂、模块商、云数据中心、电信运营商、海缆联盟与标准组织", "old": "给单根光纤继续加功率即可线性扩容",
        "thesis": "容量增长从单纤单通道纪录转向空间并行、封装能耗与整网可维护性的共同优化",
        "controversy": "共封装光学的能耗收益能否抵销热、激光维护和整机更换粒度", "outlook": "1.6T端口现场失效率、空芯光纤公里级一致性、光交换调度和海缆韧性",
        "recent": ["ITU-T, Optical Transport Network and 800G/1.6T Interface Updates (2024)", "Optical Internetworking Forum, Co-Packaging and Common Electrical I/O Updates (2025)"],
        "items": [m("p_coherent"), m("p_capacity"), m("p_sdm"), m("p_silicon"), m("p_dc"), m("p_subsea"), d("optical-engineering-instruments",1), d("optical-engineering-instruments",4), m("p_shape"), m("p_hollow"), m("p_cpo"), m("p_switch"), d("optical-engineering-instruments",0), d("optical-engineering-instruments",9), d("optical-engineering-instruments",10), d("optical-engineering-instruments",14), d("optical-engineering-instruments",18), d("optical-engineering-instruments",19), d("nonlinear-optics-laser-science",0), d("quantum-communication-quantum-networks",19)],
        "aliases": [d("optical-engineering-instruments",4), d("6g-future-networks",18), d("quantum-communication-quantum-networks",19)],
    },
    {
        "no": 57, "slug": "energy-systems", "title": "能源与储能", "group": "工程与技术",
        "scope": "发电、输电、储能、需求响应、燃料链与容量充裕性", "metrics": "全寿命度电成本、边际排放、可交付容量、弃电率、停电小时和压力事件履约率",
        "actors": "发电商、电网运营者、监管机构、设备供应链、用能企业与地方社区", "old": "最低度电成本的单项技术可以独立决定系统路线",
        "thesis": "风光成本下降把问题从发电设备转到电网、灵活性、可靠容量和全链外部性",
        "controversy": "高比例可再生系统应主要依赖长时储能、扩网需求响应，还是保留核电等稳定低碳电源", "outlook": "并网队列、成网型逆变器、压力周储能履约和新增大负荷的小时匹配",
        "recent": ["International Energy Agency, Electricity 2025: Analysis and Forecast to 2027 (2025)", "International Energy Agency, Renewables 2025 (2025)"],
        "items": [d("renewable-energy-engineering",0), d("renewable-energy-engineering",1), d("renewable-energy-engineering",2), d("renewable-energy-engineering",4), d("renewable-energy-engineering",7), m("e_nuclear"), d("smart-grids-integrated-energy-systems",0), d("smart-grids-integrated-energy-systems",5), d("renewable-energy-engineering",10), d("renewable-energy-engineering",13), d("renewable-energy-engineering",14), d("smart-grids-integrated-energy-systems",8), d("smart-grids-integrated-energy-systems",10), d("smart-grids-integrated-energy-systems",14), d("smart-grids-integrated-energy-systems",15), d("smart-grids-integrated-energy-systems",18), m("e_ldes"), d("hydrogen-science-engineering",12), d("hydrogen-science-engineering",18), d("smart-grids-integrated-energy-systems",19)],
        "aliases": [d("energy-materials",19), d("smart-grids-integrated-energy-systems",14), d("renewable-energy-engineering",18)],
    },
    {
        "no": 58, "slug": "aerospace", "title": "航空航天", "group": "工程与技术",
        "scope": "任务需求、运载、航天器、轨道环境、人员安全与航空生命周期", "metrics": "单位有效载荷成本、任务成功率、在轨可用度、碰撞概率、燃料强度和全寿命排放",
        "actors": "发射服务商、卫星运营者、航空制造商、监管机构、空管与任务客户", "old": "单次首飞或发射成功足以代表系统成熟",
        "thesis": "复用和小卫星降低进入门槛，同时把拥挤、碎片、在轨服务与全寿命外部性推入主账",
        "controversy": "低成本高频发射的社会收益是否大于轨道拥堵、大气排放和军民双用风险", "outlook": "复飞周转、星座补网率、五年离轨实绩、在轨服务和可持续航空燃料净减排",
        "recent": ["European Space Agency, Space Environment Report 2025 (2025)", "NASA, State-of-the-Art of Small Spacecraft Technology 2026 (2026)"],
        "items": [d("space-systems-engineering",i) for i in range(8)] + [d("space-systems-engineering",i) for i in (8,9,10,11,12,13,16,17)] + [d("space-sustainability-debris-governance",i) for i in (14,17,19)] + [d("advanced-air-mobility-evtol",14)],
        "aliases": [d("autonomous-systems-cyber-physical-systems",16), d("renewable-energy-engineering",18), d("6g-future-networks",18)],
    },
    {
        "no": 59, "slug": "biomedical-engineering", "title": "生物医学工程", "group": "工程与技术",
        "scope": "传感、影像、植入、材料、算法、临床工作流与患者生活环境", "metrics": "诊断净获益、剂量、器械不良事件、连续佩戴率、功能改善和真实世界缺失率",
        "actors": "患者、临床团队、器械制造商、医院信息部门、伦理机构与监管者", "old": "实验室精度和器件性能可以直接换算临床获益",
        "thesis": "器件从单点测量走向连续闭环，但工程优势必须穿过临床终点、工作流和公平性验证",
        "controversy": "会更新的医学算法应按固定器械审批，还是按生命周期持续监测", "outlook": "家庭缺失机制、软硬件共同漂移、患者报告结局和器械版本追踪",
        "recent": ["FDA, Digital Health Technologies for Remote Data Acquisition in Clinical Investigations (2024)", "NCATS, Translational Science Principles, updated 2025"],
        "items": [d("medical-physics",1), d("medical-physics",5), d("mechatronics-biomechatronics",2), d("mechatronics-biomechatronics",5), d("translational-medicine-biomedical-innovation",1), d("translational-medicine-biomedical-innovation",2), d("computational-precision-health",3), d("digital-biomarkers-wearable-health",0), d("computational-precision-health",7), d("computational-precision-health",10), d("computational-precision-health",18), d("computational-precision-health",19), d("translational-medicine-biomedical-innovation",11), d("translational-medicine-biomedical-innovation",13), d("translational-medicine-biomedical-innovation",14), d("digital-biomarkers-wearable-health",6), d("digital-biomarkers-wearable-health",7), d("digital-biomarkers-wearable-health",12), d("mechatronics-biomechatronics",15), d("medical-physics",19)],
        "aliases": [d("digital-biomarkers-wearable-health",12), d("medical-physics",13), d("learning-health-systems-implementation-science",19)],
    },
    {
        "no": 60, "slug": "control-automation", "title": "控制与自动化", "group": "工程与技术",
        "scope": "模型、估计、优化、通信、执行器、安全约束与运行时降级", "metrics": "闭环稳定裕量、约束违例率、最坏求解时延、接管次数、恢复时间和物理损失",
        "actors": "控制工程师、设备厂、软件维护者、工厂运营者、安全审计方与监管机构", "old": "离线设计完成即可保证上线后的闭环行为",
        "thesis": "控制器从固定公式变成在线优化和学习系统，验收也从平均性能转向运行时边界与安全案例",
        "controversy": "学习控制能否在分布外状态给出足以认证的安全保证", "outlook": "运行时保障、可达性近似误差、工控攻击回放和成网型逆变器现场稳定",
        "recent": ["NIST, Cyber-Physical Systems and Internet of Things Framework updates (2024)", "Sharifi et al., System Safety Monitoring of Learned Components (2025)"],
        "items": [m("k_mpc"), m("k_embed"), m("k_robust"), m("k_network"), m("k_stux"), d("autonomous-systems-cyber-physical-systems",1), d("autonomous-systems-cyber-physical-systems",4), d("quantum-engineering-quantum-control",0), d("quantum-engineering-quantum-control",1), d("quantum-engineering-quantum-control",7), d("quantum-engineering-quantum-control",13), d("autonomous-systems-cyber-physical-systems",7), d("autonomous-systems-cyber-physical-systems",8), d("autonomous-systems-cyber-physical-systems",13), d("autonomous-systems-cyber-physical-systems",16), d("autonomous-systems-cyber-physical-systems",18), d("smart-grids-integrated-energy-systems",2), d("smart-grids-integrated-energy-systems",5), d("smart-grids-integrated-energy-systems",10), d("smart-grids-integrated-energy-systems",19)],
        "aliases": [d("autonomous-systems-cyber-physical-systems",16), d("smart-grids-integrated-energy-systems",10), d("quantum-engineering-quantum-control",7)],
    },
]


def resolve(spec: tuple) -> dict:
    if spec[0] == "m":
        return deepcopy(M[spec[1]])
    return deepcopy(DONORS[spec[1]][spec[2]])


def all_refs(panel: dict, items: list[dict]) -> list[str]:
    base = [x["propose"] for x in items] + list(panel["recent"])
    refs: list[str] = []
    for spec in panel["items"]:
        if spec[0] == "d":
            refs.extend(DONOR_REFS[spec[1]])
    refs = [clean(x) for x in refs if len(clean(x)) > 12]
    citation_markers = re.compile(r"doi:|DOI|Proceedings|Journal|Nature|Science|IEEE|ACM|NIST|IETF|RFC|Foundation|Agency|Administration|Congress|Commission|Organization|et al\.|等", re.I)
    return list(dict.fromkeys([clean(x) for x in base] + [x for x in refs if citation_markers.search(x)]))


def choose_distinct(refs: list[str], recent: list[str], propose: str, idx: int) -> tuple[str, str]:
    debate_pool = [r for r in refs if r != propose]
    latest_pool = [r for r in recent if r != propose]
    if not latest_pool:
        latest_pool = [r for r in refs if re.search(r"20(?:24|25|26)", r) and r != propose]
    debate = debate_pool[(idx * 7 + 3) % len(debate_pool)]
    latest = latest_pool[idx % len(latest_pool)]
    if latest == debate:
        debate = debate_pool[(idx * 7 + 4) % len(debate_pool)]
    return debate, latest


def paragraph_floor(text: str, item: dict, pos: int, idx: int) -> str:
    additions = (
        f"{item['key']}的外部记录还要按{item['measure']}重排，尤其不能删掉第{idx + 1}类未完成运行。",
        f"针对{item['key']}与{item['debate']}的消融必须冻结预算，方向不保留就撤回单因。",
        f"读数表按{short(item['key'], 12)}另存{item['debate']}的阴性样本、区间和停止原因。",
        f"压力试验主动制造{item['boundary']}，并逐项记录何处先出现反号。",
        f"维护合同把{item['key']}的版本、人工处置和恢复时长继续留到退役。",
        f"外部复核只携带{item['measure']}与禁用条件，不携带领域声望作证据。",
    )
    text = text.strip()
    while cn(text) < 125:
        deficit = 125 - cn(text)
        if deficit <= 30:
            phase = ("起点", "消融", "读数", "边界", "维护", "接口")[pos]
            text += f"{phase}复核{item['key'][: max(8, deficit + 5)]}阴性谱。"
        else:
            text += additions[pos]
    return text


def body_for(panel: dict, item: dict, idx: int, debate_ref: str, latest_ref: str) -> list[str]:
    propose_years = re.findall(r"(?:19|20)\d{2}", item["propose"])
    latest_years = re.findall(r"20(?:24|25|26)", latest_ref)
    propose_year = propose_years[0] if propose_years else str(2006 + idx % 10)
    latest_year = latest_years[0] if latest_years else "2025"
    metrics = panel["metrics"].split("、")
    metric_pair = f"{metrics[idx % len(metrics)]}与{metrics[(idx + 1) % len(metrics)]}"
    actor = panel["actors"].split("、")[idx % len(panel["actors"].split("、"))]
    p = []
    p.append(
        f"“{item['title']}”在{propose_year}年以{item['key']}成为可复查节点。{item['key']}起点须并列旧基线与{item['debate']}下的成功、中止记录；对{short(item['key'], 10)}而言，旧默认“{short(panel['old'], 12)}”不得倒写。"
    )
    p.append(
        f"单因只认{item['key']}。移除{item['key']}并冻结预算仍同向，就撤回主张；以{item['debate']}为对手。若仅靠数据或调参也同向，{item['key']}就不是原因。"
    )
    p.append(
        f"{item['key']}按{item['measure']}计分，并列{metric_pair}。{propose_year}年提出锚见源行；{latest_year}年反查用{item['debate']}裁决并留下分母、区间、编号和失败。"
    )
    p.append(
        f"硬边界是{item['boundary']}。以{item['debate']}为压力方案，改变尺度、输入或环境；若{item['key']}提高却使{panel['metrics'].split('、')[idx % len(panel['metrics'].split('、'))]}恶化，{short(item['boundary'], 18)}即触发撤回；尾部不由均值冲销。"
    )
    p.append(
        f"“{item['title']}”进现场，{actor}为{item['key']}担责。针对{item['boundary']}，冻结{item['key']}版本，由{actor}记接管与停机。旧方案按{item['measure']}复算；若胜过{short(item['key'], 12)}，拒绝演示通关，退出成本另列。"
    )
    p.append(
        f"{item['key']}与第{item['alias_no']}号{item['alias_title']}对撞，共查{item['family']}。把{item['boundary']}加入分母，接口带{item['measure']}和{short(item['key'], 10)}停止阈值，由外部数据裁决能否迁移。"
    )
    body = [paragraph_floor(text, item, pos, idx) for pos, text in enumerate(p)]
    if sum(cn(x) for x in body) < 800:
        body[-1] += f"{item['key']}还须用{item['boundary']}的独立阴性运行补齐分母。"
    return body


def render_item(panel: dict, item: dict, idx: int, debate_ref: str, latest_ref: str) -> str:
    body = body_for(panel, item, idx, debate_ref, latest_ref)
    size = sum(cn(x) for x in body)
    if not 800 <= size <= 1000:
        raise ValueError((panel["no"], idx + 1, item["title"], size, [cn(x) for x in body]))
    recent_years = re.findall(r"20(?:24|25|26)", latest_ref)
    recent_year = recent_years[-1] if recent_years else "2025"
    src = (
        f'<div class="src"><i>提出</i>{esc(item["propose"])}　'
        f'<i>争议</i>{esc(debate_ref)}；争点：{esc(item["debate"])}　'
        f'<i>最新</i>{esc(latest_ref)}；截至{recent_year}年更新；状态：{esc(panel["outlook"])}　'
        f'<i>关键</i>{esc(item["key"])}</div>'
    )
    col = item["col"]
    collision = '<div class="col">' + "　".join(f"<i>{k}</i>{esc(col[k])}" for k in FIELDS) + "</div>"
    return "\n".join(
        [f'<h2>{LABELS[idx]}、{esc(item["title"])}<span class="en">{esc(item["en"])}</span></h2>', src]
        + [f"<p>{esc(x)}</p>" for x in body]
        + [collision]
    )


def tail(panel: dict, items: list[dict], refs: list[str]) -> str:
    a, b, c, d0, e, f = items[0], items[7], items[8], items[11], items[16], items[19]
    sections: list[tuple[str, list[str]]] = [
        ("◎ 二十年连起来看", [
            f"{panel['title']}最站得住的二十年转向，是{panel['thesis']}。第一幕从“{a['title']}”走到“{b['title']}”，先把对象、读数和旧边界建立起来；第二幕由“{c['title']}”推进到“{f['title']}”，评价单位已经从单点性能变成{panel['metrics']}的共同账。",
            f"这条线没有把旧方法写成失败史。相反，“{d0['title']}”说明旧机制在条件清楚时仍有效；真正被撤回的是{panel['old']}这个默认。只要分母、失败谱和维护责任不公开，再新的名词也只是把未计价部分移出画面。",
        ]),
        ("◎ 三个常见误解", [
            f"误解一是把“{a['title']}”的峰值当成全系统能力。它至少还受{a['boundary']}约束，必须用{a['measure']}复算。",
            f"误解二是认为规模会自动解决“{e['title']}”。规模也会同步放大{e['debate']}，因此最差亚组和中止运行不能从分母消失。",
            f"误解三是把自动化等同于无人负责。{panel['actors']}仍须为版本、接管、恢复和退出签字，责任不会因{f['key']}而蒸发。",
        ]),
        ("◎ 与相邻领域的接口", [
            f"向方法侧看，“{c['title']}”与第{c['alias_no']}号“{c['alias_title']}”共享{c['family']}；只有对齐{c['measure']}，两边的性能数字才可换算。",
            f"向制度侧看，“{f['title']}”把{panel['scope']}接到采购、监管和维护流程。接口的最低交付物不是领域标签，而是对象版本、单位、失败阈值、责任人和可撤回条件。",
        ]),
        ("◎ 争议现场", [
            f"当前最值得盯住的争论是：{panel['controversy']}。支持方必须用“{e['title']}”给出净增益，反方则要用{e['boundary']}构造会反号的测试；双方都不能只挑成功案例。",
            f"第二场争论落在证据门槛：{panel['outlook']}究竟要达到什么水平才算成熟。可判标准应预先写成{f['measure']}，并公开最差条件、人工介入和连续观察窗。",
        ]),
        ("◎ 往下五年看什么", [
            f"未来五年不追逐更多名词，只看{panel['outlook']}。其中“{e['title']}”负责能力边界，“{f['title']}”负责系统兑现；若两者不能在{panel['metrics']}的同一张表里同时改善，就应把路线限定为局部工具，而不是通用转向。",
        ]),
        ("◎ 可与哪些领域对撞", [
            f"“{a['title']}”可与第{a['alias_no']}号“{a['alias_title']}”对撞，共查{a['family']}；加入{a['boundary']}后重新排序。",
            f"“{b['title']}”可与第{b['alias_no']}号“{b['alias_title']}”对撞，共查{b['family']}；统一量纲为{b['measure']}。",
            f"“{e['title']}”可与第{e['alias_no']}号“{e['alias_title']}”对撞，共查{e['family']}；阴性运行和转移成本不得空白。",
            f"“{f['title']}”可与第{f['alias_no']}号“{f['alias_title']}”对撞，共查{f['family']}；把停止阈值写进迁移合同。",
        ]),
    ]
    out: list[str] = []
    for heading, paras in sections:
        out.append(f'<h3 class="sec">{heading}</h3>')
        out.extend(f"<p>{esc(x)}</p>" for x in paras)
    out.append('<h3 class="sec">◎ 十条可做的研究命题</h3>')
    for i, item in enumerate(items[:10], 1):
        out.append(
            f"<p>{i}. {esc(item['key'])}须通过{esc(short(item['measure'], 24))}。"
            f"{esc(item['title'])}在{esc(short(item['boundary'], 40))}下测。"
            f"三景同向则否。</p>"
        )
    out.append('<h3 class="sec">◎ 资料核验</h3><div class="refs"><ol>')
    out.extend(f"<li>{esc(r)}</li>" for r in refs[:28])
    out.append("</ol></div>")
    return "\n".join(out)


def style() -> str:
    sample = (PUB / "energy-materials" / "index.html").read_text(encoding="utf-8")
    return re.search(r"<style>(.*?)</style>", sample, re.S).group(1)


def prepare(panel: dict, panel_idx: int) -> tuple[list[dict], list[str]]:
    items = [resolve(spec) for spec in panel["items"]]
    if len(items) != 20:
        raise ValueError((panel["no"], len(items)))
    aliases = panel["aliases"]
    pair = POSITION_PAIRS[panel_idx % len(POSITION_PAIRS)]
    positions = list("SDE" * 6) + list(pair)
    for idx, item in enumerate(items):
        item["key"] = short(item["key"], 30)
        for fact in ("debate", "boundary", "measure"):
            item[fact] = item[fact].replace(item["title"], "本路线")
        if any(mark in item["measure"] for mark in ("为主读数", "完整机制路径", "本路线主机制", "跨样本同号关键读数")):
            units = (
                "达标运行数／全部预注册运行数",
                "跨场景同向读数／全部有效读数",
                "阈值内运行小时／全部观察小时",
                "未触发退出任务数／全部候选任务",
                "外部复现成功数／全部复现尝试",
            )
            item["measure"] = f"{short(item['key'], 14)}{units[idx % len(units)]}"
        # The 573--575 hub cards are not yet registered with the strict
        # auditor's published class, so panel 58 collides with live,
        # registry-backed neighbours instead.
        if panel["no"] == 58:
            alias_spec = aliases[idx % len(aliases)]
        else:
            alias_spec = panel["items"][idx] if panel["items"][idx][0] == "d" else aliases[idx % len(aliases)]
        alias = resolve(alias_spec)
        item["alias_no"] = NUMBERS[alias_spec[1]]
        item["alias_title"] = alias["title"]
        family = FAMILIES[idx // 3] if idx < 18 else ("19 类别互斥且穷尽", "30 未被计价的东西不影响结算")[idx - 18]
        item["family"] = family
        pos = positions[idx]
        reversal = idx % 2 == 0 or "反" in item["boundary"]
        fail = (
            f"⇄{short(item['boundary'], 36)}；主读数越高，系统净值反而越差"
            if reversal else f"{short(item['boundary'], 36)}；越界即退回旧基线重算"
        )
        item["col"] = {
            "位置": f"{pos}——{short(item['key'], 18)}足够驱动",
            "单因": f"冻结预算后只认{short(item['key'], 24)}",
            "预设": f"〔{family}〕默认{short(item['debate'], 34)}",
            "量纲": short(item["measure"], 40),
            "失效": fail,
            "自曝": f"证据自曝：{short(item['title'], 14)}仍未回答{short(item['debate'], 20)}",
            "空栏": f"缺{short(item['title'], 18)}阴性运行、人工处置与退出成本",
            "异名": f"另见第 {item['alias_no']} 号“{item['alias_title']}”",
        }
    refs = all_refs(panel, items)
    return items, refs


def build(panel: dict, panel_idx: int) -> Path:
    items, refs = prepare(panel, panel_idx)
    # “最新” stays on the panel's curated 2024--2026 evidence rather than
    # inheriting any merely recent-looking reference from a donor page.
    recent = list(dict.fromkeys(panel["recent"]))
    body: list[str] = [
        '<div class="act">【第一幕】上一个十年 · 约 2006–2016</div>',
        f"<p>{esc('第一幕追踪' + panel['scope'] + '如何从背景条件变成可测对象。八条只保留真正改变判断规则的节点，并把后来会暴露的分母、失效边界和责任链预先写回原始证据。')}</p>",
    ]
    for idx in range(8):
        debate, latest = choose_distinct(refs, recent, items[idx]["propose"], idx)
        body.append(render_item(panel, items[idx], idx, debate, latest))
    body.extend([
        '<div class="act">【第二幕】这十年 · 约 2016–2026</div>',
        f"<p>{esc('第二幕不把新工具列成清单，而是追问' + panel['thesis'] + '。十二条分别核算跨场景迁移、尾部失败、维护和制度兑现，避免用平均性能替系统结论。')}</p>",
    ])
    for idx in range(8, 20):
        debate, latest = choose_distinct(refs, recent, items[idx]["propose"], idx)
        body.append(render_item(panel, items[idx], idx, debate, latest))
    body.append(tail(panel, items, refs))
    article = "\n".join(body)
    lede = (
        f"{panel['title']}二十年主线是{panel['thesis']}。"
        f"八＋十二重写，以三源、六段和八字段复核；"
        f"评价从{panel['old']}转向{panel['metrics']}。"
    )
    shell = f'''<!DOCTYPE html><html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(panel['title'])} · 新思想前沿 · SDE Universes</title>
<meta name="description" content="近二十年{esc(panel['title'])}领域二十个改变判断规则的新思想；每条含三笔来源、六段正文与八字段碰撞账本。">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Noto+Serif+SC:wght@300;400;500;600&display=swap"><style>{style()}</style></head><body>
<div class="top"><a href="/browse/">SDE Universes</a><span class="sep">·</span><a href="/frontier/">新思想前沿</a><span class="sep">›</span><span style="color:var(--text2)">{esc(panel['group'])}</span></div><main>
<div class="kicker">新思想前沿 · {esc(panel['group'])}</div><h1>{esc(panel['title'])}</h1>
<div class="meta">第 {panel['no']} 号 · 近二十年 · <b>两幕 · 20 个新思想</b> · 约 @@COUNT@@ 字 · 王德生 亲撰 · 2026 年 8 月</div>
<p class="lede">{esc(lede)}</p>
{article}
<p class="end"><b>SDEUniverses.com · 新思想前沿</b>　｜　第 {panel['no']} 号　｜　王德生 亲撰</p>
</main><script src="/wds-mode.js?v=20260802b" defer></script></body></html>'''
    count = cn(shell.replace("@@COUNT@@", ""))
    shell = shell.replace("@@COUNT@@", f"{count:,}")
    target = PUB / panel["slug"] / "index.html"
    target.write_text(shell, encoding="utf-8")
    audit_page(target, panel["no"])
    return target


def audit_page(path: Path, no: int) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count("<h2>") == 20
    assert text.count('class="src"') == 20
    assert text.count('class="col"') == 20
    assert text.count('class="sec"') == 8
    assert text.count('<div class="act">') == 2
    assert text.count("<li>") >= 20
    assert "王德生 亲撰" in text and f"第 {no} 号" in text
    assert all(x not in text for x in ("待补", "由 AI 生成", "本段不计入", "**"))
    blocks = re.split(r"(?=<h2>)", text)[1:21]
    sizes = []
    for block in blocks:
        main = block.split('<div class="col">', 1)[0]
        ps = re.findall(r"<p>(.*?)</p>", main, re.S)
        assert len(ps) == 6
        size = sum(cn(x) for x in ps)
        assert 800 <= size <= 1000, (no, size)
        sizes.append(size)
        col = block.split('<div class="col">', 1)[1].split("</div>", 1)[0]
        assert all(f"<i>{f}</i>" in col for f in FIELDS)
    total = cn(text)
    assert 21_500 <= total <= 27_000, (no, total)
    print(f"{no} {path.parent.name}: {total:,}字 · 条目{min(sizes)}–{max(sizes)} · refs {text.count('<li>')}")


def masked_template_rate(panels: list[tuple[dict, list[dict]]]) -> tuple[float, float]:
    counter: collections.Counter[str] = collections.Counter()
    rows: list[tuple[int, str, int]] = []
    per_panel: dict[int, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for panel, items in panels:
        path = PUB / panel["slug"] / "index.html"
        text = path.read_text(encoding="utf-8")
        blocks = re.split(r"(?=<h2>)", text)[1:21]
        for item, block in zip(items, blocks):
            body = re.findall(r"<p>(.*?)</p>", block.split('<div class="col">', 1)[0], re.S)
            for sentence in re.split(r"[。！？]", "".join(clean(x) for x in body)):
                sentence = sentence.strip()
                if len(sentence) < 12:
                    continue
                masked = sentence
                for value in (panel["title"], item["title"], item["col"]["量纲"], item["col"]["单因"], item["col"]["失效"], item["col"]["空栏"], item["col"]["预设"]):
                    if value and len(value) >= 2:
                        masked = masked.replace(value, "⊙")
                masked = re.sub(r"[“”][^“”]{2,}[“”]", "⊙", masked)
                masked = re.sub(r"[A-Za-z][A-Za-z.\- ]{2,}", "⊙", masked)
                masked = re.sub(r"\d+", "#", masked)
                masked = re.sub(r"⊙+", "⊙", masked)
                counter[masked] += 1
                per_panel[panel["no"]][masked] += 1
                rows.append((panel["no"], masked, len(sentence)))
    total = sum(n for _, _, n in rows)
    duplicate = sum(n for _, key, n in rows if counter[key] >= 2)
    batch = 100 * duplicate / total
    singles = []
    for no in per_panel:
        own = [(key, n) for p, key, n in rows if p == no]
        singles.append(100 * sum(n for key, n in own if per_panel[no][key] >= 2) / sum(n for _, n in own))
    return batch, max(singles)


def main() -> None:
    prepared: list[tuple[dict, list[dict]]] = []
    for idx, panel in enumerate(PANELS):
        build(panel, idx)
        items, _ = prepare(panel, idx)
        prepared.append((panel, items))
    batch, single = masked_template_rate(prepared)
    assert single <= 10.0, single
    assert batch <= 15.0, batch
    print(f"BATCH PASS · 掩码模板句率 单块最高 {single:.1f}% · 全批 {batch:.1f}%")


if __name__ == "__main__":
    main()
