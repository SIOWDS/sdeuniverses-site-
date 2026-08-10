#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二次真跑：一次有日期的判定装置改革前后，同一批对象的两套读数。
数据：Open LLM Leaderboard v1 (open-llm-leaderboard-old/contents) 与 v2 (open-llm-leaderboard/contents)
预注册：PREREG2.md（冻结在先）
"""
import json
import numpy as np
import pandas as pd

A_COLS = ['ARC', 'HellaSwag', 'MMLU', 'TruthfulQA', 'Winogrande', 'GSM8K']          # 旧读法
B_COLS = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']               # 新读法


def prep(path, cols, drop_flagged=True):
    df = pd.read_parquet(path)
    if drop_flagged and 'Flagged' in df.columns:
        # v1 存档快照里 Flagged 全为 True，字段不携带信息；见 PREREG2.md「执行偏离」
        if df['Flagged'].mean() < 0.99:
            df = df[df['Flagged'] != True]                                          # noqa: E712
    df = df.dropna(subset=cols + ['fullname'])
    df = df.sort_values('Average ⬆️', ascending=False).drop_duplicates('fullname')
    return df.set_index('fullname')[cols]


def r2(y, X):
    """y 在 X 上的最小二乘决定系数（各列已标准化，含截距）。"""
    Xd = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    resid = y - Xd @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss_res / ss_tot


def lam(B, A):
    """λ(B|A)：B 各列被 A 线性重构的方差比例，取均值。"""
    per = {c: r2(B[c].values, A.values) for c in B.columns}
    return float(np.mean(list(per.values()))), per


def loo_internal(M):
    """同口径内部：每一列由其余各列重构，取均值（量表的另一端）。"""
    per = {}
    for c in M.columns:
        rest = M.drop(columns=[c])
        per[c] = r2(M[c].values, rest.values)
    return float(np.mean(list(per.values()))), per


def zs(df):
    return (df - df.mean()) / df.std(ddof=0)


def main():
    a = prep('v1.parquet', A_COLS)
    b = prep('v2.parquet', B_COLS)
    b_nf = prep('v2.parquet', B_COLS, drop_flagged=False)
    common = sorted(set(a.index) & set(b.index))
    n = len(common)
    out = {'n_v1': len(a), 'n_v2': len(b), 'n_common': n}
    print(f"v1 去重后 {len(a)} 个模型；v2 去重后 {len(b)} 个；两版共同 {n} 个")
    assert n >= 60, f"样本量 {n} < 10×6，按预注册判为不可用"

    A = zs(a.loc[common])
    B = zs(b.loc[common])

    # Q1 主件
    l_ba, per_ba = lam(B, A)
    l_ab, per_ab = lam(A, B)
    out['lambda_B_given_A'] = l_ba
    out['lambda_A_given_B'] = l_ab
    out['per_col_B_given_A'] = per_ba
    out['per_col_A_given_B'] = per_ab
    print(f"\nQ1  λ(新|旧) = {l_ba:.3f}    λ(旧|新) = {l_ab:.3f}")

    # Q3 量表两端
    ia, per_ia = loo_internal(A)
    ib, per_ib = loo_internal(B)
    out['internal_v1'] = ia
    out['internal_v2'] = ib
    out['per_col_internal_v1'] = per_ia
    out['per_col_internal_v2'] = per_ib
    print(f"Q3  同口径内部 λ：v1 = {ia:.3f}   v2 = {ib:.3f}")

    # Q4 逐项
    print("\nQ4  新六项各自被旧六项重构：")
    for c, v in sorted(per_ba.items(), key=lambda kv: -kv[1]):
        print(f"     {c:<12} {v:.3f}")

    # Q2 分配后果
    avg_a = A.mean(axis=1)
    avg_b = B.mean(axis=1)
    k = max(1, int(round(n * 0.20)))
    top_a = set(avg_a.sort_values(ascending=False).head(k).index)
    top_b = set(avg_b.sort_values(ascending=False).head(k).index)
    jac = len(top_a & top_b) / len(top_a | top_b)
    ov = len(top_a & top_b) / k
    sp = float(pd.Series(avg_a).rank().corr(pd.Series(avg_b).rank(), method='pearson'))
    out.update({'top_k': k, 'jaccard_top20': jac, 'overlap_top20': ov, 'spearman_avg': sp})
    print(f"\nQ2  前 20%（各 {k} 个）名单：重合 {ov:.3f}（Jaccard {jac:.3f}）；全样本平均分秩相关 {sp:.3f}")

    # 粒度敏感性（照原稿清点手册那条）
    l_tot, _ = lam(pd.DataFrame({'avg': avg_b}), A)
    out['lambda_totalonly'] = l_tot
    print(f"\n粒度敏感性：只用新读法总分时 λ = {l_tot:.3f}（逐项时 {l_ba:.3f}）")

    # 敏感性：v2 不剔除 Flagged
    common2 = sorted(set(a.index) & set(b_nf.index))
    A2, B2 = zs(a.loc[common2]), zs(b_nf.loc[common2])
    l_sens, _ = lam(B2, A2)
    out['n_common_noflagfilter'] = len(common2)
    out['lambda_B_given_A_noflagfilter'] = l_sens
    print(f"敏感性（v2 不剔除 Flagged，n={len(common2)}）：λ(新|旧) = {l_sens:.3f}")

    with open('result2.json', 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n写入 result2.json")


if __name__ == '__main__':
    main()
