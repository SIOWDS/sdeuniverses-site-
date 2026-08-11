import pandas as pd, numpy as np
from scipy import stats
wc=pd.read_csv("db_29_1_text/Work Context.txt",sep="\t",dtype=str); wc=wc[wc["Scale ID"]=="CX"]
wc["v"]=pd.to_numeric(wc["Data Value"])
wa=pd.read_csv("db_29_1_text/Work Activities.txt",sep="\t",dtype=str); wa=wa[wa["Scale ID"]=="IM"]
wa["v"]=pd.to_numeric(wa["Data Value"])
occ=pd.read_csv("db_29_1_text/Occupation Data.txt",sep="\t",dtype=str).set_index("O*NET-SOC Code")["Title"]
P=wc.pivot_table(index="O*NET-SOC Code",columns="Element ID",values="v")
Q=wa.pivot_table(index="O*NET-SOC Code",columns="Element ID",values="v")
d=pd.DataFrame({"A":P["4.C.3.b.2"],"R1":P["4.C.3.b.7"],"R2":6-P["4.C.3.b.8"],
 "W1":P["4.C.3.a.2.a"],"W2":P["4.C.3.a.1"],"L":P["4.C.3.a.4"],"F":P["4.C.3.a.2.b"],
 "T":P["4.C.3.d.1"],"EQ":P["4.C.3.d.3"],"COMP":Q["4.A.3.b.1"]}).dropna()
print("n =",len(d))
print("\n【稳健性】换两个不依赖自评'自动化'的代理，重跑靶心")
for proxy,lab in [("EQ","设备节奏决定工作节奏"),("COMP","与计算机打交道的重要性")]:
    print(f"  —— 代理：{lab}")
    for k in ["R1","R2","W1","W2","L","F"]:
        r,p=stats.pearsonr(d[proxy],d[k]); print(f"     r({proxy},{k:2s}) = {r:+.3f} p={p:.1e}")
print("\n【2×2】自由度 L × 后果重量 W1（各按中位数切）")
mL,mW=d.L.median(),d.W1.median()
d["g"]=np.where((d.L>=mL)&(d.W1>=mW),"高自由·重后果",
        np.where((d.L<mL)&(d.W1>=mW),"低自由·重后果",
        np.where((d.L>=mL)&(d.W1<mW),"高自由·轻后果","低自由·轻后果")))
for g,sub in d.groupby("g"):
    ex=[occ.get(i,i) for i in sub.sort_values("W1",ascending=False).index[:3]]
    print(f"  {g}: {len(sub)} 个职业 ({len(sub)/len(d)*100:.0f}%)  自动化均值 {sub.A.mean():.2f}  例：{ '、'.join(ex) }")
print("\n  低自由·重后果 与 高自由·重后果 的自动化程度差：",
      round(d[d.g=="低自由·重后果"].A.mean()-d[d.g=="高自由·重后果"].A.mean(),3))
print("\n【F 不降而 L 降 的职业占比】")
hiF=d[d.F>=d.F.median()]
print("  决策频次在中位数以上、而自由度在下四分位以下的职业：",
      len(hiF[hiF.L<=d.L.quantile(.25)]), "个；例：",
      "、".join(occ.get(i,i) for i in hiF[hiF.L<=d.L.quantile(.25)].sort_values("F",ascending=False).index[:5]))
