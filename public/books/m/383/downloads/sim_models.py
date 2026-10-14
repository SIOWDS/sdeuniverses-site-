"""附录九：竞争模型判别模拟（纯模拟，无任何人体数据）。
五个模型在同一设计下的次序差 Δ = y(先高后低) − y(先低后高)，以及剂量分层设计能否把
「叠写门控」与「无阈值慢层」「适应速度」区分开。所有参数均为设定值，不是估计值。
运行：python3 sim_models.py   固定种子 20261014。
"""
import json
import numpy as np

# ---- 设定参数（全部为假设，附录九逐项写明） ----
ETA, LAM = 0.5, 0.5          # 慢层写入权重、保留旧层比例
RHO, MU = 0.5, 0.9           # 快层恢复因子、慢层保持因子（每周）
A_LEAK = 0.8                 # 单层泄漏积分的保留因子
H_HAB = 1.0                  # 适应速度模型：每单位累计偏移使增益下降的速度
DAYS = 14                    # 每个阶段的连续闭环天数
THETA = 14.0                 # 写入阈值（剂量 = 显示偏移(SD) × 连续天数）
STRATA = [0.4, 0.8, 1.2, 1.6, 2.0]   # 显示偏移层（SD），阈值落在 m=1.0
EXPECT_THETA_M = THETA / DAYS


def out(model, m, k, order):
    """order='AB' 先高后低；'BA' 先低后高。返回撤除 k 周后的可观察基线偏移（单位：SD）。"""
    uA, uB = +m, -m
    u = (uA, uB) if order == 'AB' else (uB, uA)
    d = [abs(x) * DAYS for x in u]
    if model == 'A_settle':        # 安定点：无历史，只有快回弹
        return RHO ** k * u[1]
    if model == 'B_leaky':         # 单层泄漏积分：次序有影响，但随同一速度衰减
        x = 0.0
        for ui in u:
            x = A_LEAK * x + (1 - A_LEAK) * ui
        return A_LEAK ** k * x
    if model == 'C_slow_linear':   # 双层，慢层无阈值（线性）
        R = 0.0
        for ui in u:
            R = LAM * R + ETA * ui
        return RHO ** k * u[1] + MU ** k * R
    if model == 'D_gated':         # 叠写：慢层只在越阈时更新
        R = 0.0
        for ui, di in zip(u, d):
            g = 1.0 if di > THETA else 0.0
            R = (1 - g + g * LAM) * R + g * ETA * ui
        return RHO ** k * u[1] + MU ** k * R
    if model == 'E_habituation':   # 适应速度：增益随累计暴露下降，慢层近似不衰减的一版
        R, cum = 0.0, 0.0
        for ui in u:
            eta_i = ETA / (1 + H_HAB * cum)
            R = LAM * R + eta_i * ui
            cum += abs(ui)
        return RHO ** k * u[1] + MU ** k * R
    raise ValueError(model)


MODELS = ['A_settle', 'B_leaky', 'C_slow_linear', 'D_gated', 'E_habituation']
LABEL = {'A_settle': 'A 安定点', 'B_leaky': 'B 单层泄漏积分', 'C_slow_linear': 'C 双层·无阈值',
         'D_gated': 'D 叠写·越阈门控', 'E_habituation': 'E 适应速度'}


def delta(model, m, k):
    return out(model, m, k, 'AB') - out(model, m, k, 'BA')


def table_dose(k):
    rows = []
    for mod in MODELS:
        rows.append([LABEL[mod]] + [round(delta(mod, m, k), 3) for m in STRATA])
    return rows


def table_time(m):
    ks = [0, 1, 2, 4, 8]
    rows = []
    for mod in MODELS:
        rows.append([LABEL[mod]] + [round(delta(mod, m, k), 3) for k in ks])
    return ks, rows


# ---- 单剂量设计下 C 与 D 是否可分 ----
def single_dose_identical(m=2.0, k=8):
    return delta('C_slow_linear', m, k), delta('D_gated', m, k)


# ---- 三个判别对比所需样本量（解析公式，双侧 α=0.05，功效 0.80） ----
Z = 1.96 + 0.8416


def n_cell(effect, sigma, strata_averaged=1):
    """两个次序各 n 人比较平均数：SE=sigma*sqrt(2/n)；若对 s 个层取平均，SE 再除以 sqrt(s)。"""
    return 2.0 * (Z * sigma / (abs(effect) * np.sqrt(strata_averaged))) ** 2


def contrasts(k=8):
    # 1 慢层是否存在：D 在最高层 vs A/B 的次序差
    c1 = abs(delta('D_gated', 2.0, k)) - abs(delta('B_leaky', 2.0, k))
    # 2 门控：阈值以下两层（m=0.4, 0.8），C 的预测与 D 的预测之差的平均
    c2 = np.mean([abs(delta('C_slow_linear', m, k) - delta('D_gated', m, k)) for m in (0.4, 0.8)])
    # 3 D 对 E：最高层上次序差的差
    c3 = abs(delta('D_gated', 2.0, k) - delta('E_habituation', 2.0, k))
    return c1, c2, c3


def main():
    global ETA
    rng = np.random.default_rng(20261014)
    result = {'params': dict(eta=ETA, lam=LAM, rho=RHO, mu=MU, a_leak=A_LEAK, h=H_HAB, days=DAYS,
                             theta=THETA, strata=STRATA)}
    result['dose_k8'] = table_dose(8)
    result['dose_k0'] = table_dose(0)
    ks, rows = table_time(2.0)
    result['time_m2'] = {'ks': ks, 'rows': rows}
    result['single_dose_C_vs_D'] = single_dose_identical()
    pw = {}
    eta0 = ETA
    for scale in (1.0, 0.5, 0.25):
        ETA = eta0 * scale
        c1, c2, c3 = contrasts()
        pw[str(scale)] = {'effects': [round(c1, 3), round(c2, 3), round(c3, 3)]}
        for sg in (1.0, 0.5):
            pw[str(scale)][f'n_sigma{sg}'] = [int(np.ceil(n_cell(c1, sg))), int(np.ceil(n_cell(c2, sg, 2))),
                                              int(np.ceil(n_cell(c3, sg)))]
    ETA = eta0
    result['n_per_cell'] = pw
    json.dump(result, open('sim_result.json', 'w'), ensure_ascii=False, indent=1)

    print('次序差 Δ（撤除后 8 周），按显示偏移层 m（SD）：', STRATA)
    for r in result['dose_k8']:
        print(r)
    print('\n次序差 Δ 随撤除周数（m=2.0）：', ks)
    for r in rows:
        print(r)
    print('\n单一剂量 m=2.0，k=8：C=%.4f，D=%.4f' % result['single_dose_C_vs_D'])
    print('\n三个对比所需每层每次序人数（双侧 0.05，功效 0.80；k=8）：')
    for scale, v in pw.items():
        print('效应缩放', scale, '三个对比的效应(SD)', v['effects'])
        for sg in ('1.0', '0.5'):
            print('   sigma', sg, '→ n/格 =', v['n_sigma' + sg], '(慢层存在 / 门控 / D对E)')


if __name__ == '__main__':
    main()
