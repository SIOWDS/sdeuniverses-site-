import pandas as pd, numpy as np
from scipy import stats
def load(path):
    wc=pd.read_csv(path,sep="\t",dtype=str)
    wc=wc[wc["Scale ID"]=="CX"].copy(); wc["v"]=pd.to_numeric(wc["Data Value"])
    return wc
old=load("db_20_1_text/Work Context.txt"); new=load("db_29_1_text/Work Context.txt")
print("旧版日期范围:", sorted(old["Date"].unique())[:3], "…", sorted(old["Date"].unique())[-2:])
IDS={"A":"4.C.3.b.2","R1":"4.C.3.b.7","W1":"4.C.3.a.2.a","W2":"4.C.3.a.1","L":"4.C.3.a.4","F":"4.C.3.a.2.b"}
def pv(d):
    p=d.pivot_table(index="O*NET-SOC Code",columns="Element ID",values="v")
    dd=pd.DataFrame({k:p[v] for k,v in IDS.items()})
    dt=d[d["Element ID"]=="4.C.3.b.2"].set_index("O*NET-SOC Code")["Date"]
    dd["date"]=dt
    return dd.dropna()
O,N=pv(old),pv(new)
j=O.join(N,how="inner",lsuffix="_o",rsuffix="_n")
print("两版共有职业:",len(j))
# 只保留两次采集日期不同者 = 期间真被重新调查过
j=j[j["date_o"]!=j["date_n"]].copy()
print("期间被重新调查过的职业:",len(j))
j["dA"]=j["A_n"]-j["A_o"]; j["dL"]=j["L_n"]-j["L_o"]; j["dF"]=j["F_n"]-j["F_o"]
print("ΔA 均值 %.3f 标准差 %.3f | ΔL 均值 %.3f | ΔF 均值 %.3f"%(j.dA.mean(),j.dA.std(),j.dL.mean(),j.dF.mean()))
print("\n【纵向·靶心】基期特征预测自动化程度的增量 ΔA")
for k,lab in [("R1_o","基期例行度"),("W1_o","基期后果重量"),("W2_o","基期差错后果"),("L_o","基期自由度")]:
    r,p=stats.pearsonr(j[k],j["dA"]); print(f"  r({lab}, ΔA) = {r:+.3f} p={p:.2e}")
X=np.c_[np.ones(len(j)),j[["R1_o","W1_o","W2_o"]].values]
b=np.linalg.lstsq(X,j["dA"].values,rcond=None)[0]
res=j["dA"].values-X@b; se=np.sqrt((res@res)/(len(j)-4)*np.diag(np.linalg.inv(X.T@X)))
for n_,bb,ss in zip(["常数","基期例行度","基期后果重量","基期差错后果"],b,se):
    print(f"  {n_:8s} b={bb:+.4f}  t={bb/ss:+.2f}")
print("\n【纵向·步骤留下岔路删除】")
for a,bq in [("dA","dL"),("dA","dF")]:
    r,p=stats.pearsonr(j[a],j[bq]); print(f"  r({a},{bq}) = {r:+.3f} p={p:.2e}")
j.to_csv("onet_delta.csv")
