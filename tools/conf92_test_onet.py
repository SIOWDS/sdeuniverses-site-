import pandas as pd, numpy as np, itertools
from scipy import stats
wc = pd.read_csv("db_29_1_text/Work Context.txt", sep="\t", dtype=str)
wc = wc[wc["Scale ID"]=="CX"].copy()
wc["v"] = pd.to_numeric(wc["Data Value"])
IDS = {"A":"4.C.3.b.2","R1":"4.C.3.b.7","R2raw":"4.C.3.b.8","W1":"4.C.3.a.2.a",
       "W2":"4.C.3.a.1","W3":"4.C.1.c.1","F":"4.C.3.a.2.b","L":"4.C.3.a.4","T":"4.C.3.d.1"}
piv = wc.pivot_table(index="O*NET-SOC Code", columns="Element ID", values="v")
df = pd.DataFrame({k: piv[v] for k,v in IDS.items()}).dropna()
df["R2"] = 6 - df["R2raw"]          # 反向：高 = 结构化
df["R"]  = (df["R1"].rank(pct=True)+df["R2"].rank(pct=True))/2   # 可结算性合成（事先写定：两项等权秩均）
print("职业数 n =", len(df))
print(df[["A","R1","R2","W1","W2","W3","F","L","T"]].describe().round(2).T[["mean","std","min","max"]])

def r(a,b):
    rr,p = stats.pearsonr(df[a],df[b]); return rr,p
def partial(x,y,ctrl):
    X=df[[x]+ctrl].values; Y=df[y].values
    import numpy.linalg as la
    def resid(t, C):
        C1=np.c_[np.ones(len(C)),C]; b=la.lstsq(C1,t,rcond=None)[0]; return t-C1@b
    C=df[ctrl].values
    rx=resid(df[x].values,C); ry=resid(Y,C)
    rr,p=stats.pearsonr(rx,ry); return rr,p

print("\n【P1 靶心】自动化 A 与 可结算性 / 后果重量")
for k in ["R","R1","R2"]:
    rr,p=r("A",k); print(f"  r(A,{k:2s}) = {rr:+.3f}  p={p:.2e}")
for k in ["W1","W2","W3"]:
    rr,p=r("A",k); print(f"  r(A,{k:2s}) = {rr:+.3f}  p={p:.2e}")
print("  偏相关：")
rr,p=partial("R1","A",["W1","W2","W3"]); print(f"  r(A,R1 | W1,W2,W3) = {rr:+.3f} p={p:.2e}")
rr,p=partial("R2","A",["W1","W2","W3"]); print(f"  r(A,R2 | W1,W2,W3) = {rr:+.3f} p={p:.2e}")
rr,p=partial("W1","A",["R1","R2"]);      print(f"  r(A,W1 | R1,R2)    = {rr:+.3f} p={p:.2e}")
rr,p=partial("W2","A",["R1","R2"]);      print(f"  r(A,W2 | R1,R2)    = {rr:+.3f} p={p:.2e}")
rr,p=partial("W3","A",["R1","R2"]);      print(f"  r(A,W3 | R1,R2)    = {rr:+.3f} p={p:.2e}")

print("\n【P2 两笔账】")
rr,p=r("T","L"); print(f"  r(T,L) = {rr:+.3f} p={p:.2e}")
rr,p=r("A","T"); print(f"  r(A,T) = {rr:+.3f} p={p:.2e}")

print("\n【P3 三条件】PCA on L, R2, W1")
Z=(df[["L","R2","W1"]]-df[["L","R2","W1"]].mean())/df[["L","R2","W1"]].std()
u,s,vt=np.linalg.svd(Z.values,full_matrices=False)
ev=s**2/ (s**2).sum()
print("  解释方差比：", np.round(ev,3))
print("  载荷 PC1:", dict(zip(["L","R2","W1"],np.round(vt[0],3))))
print("  载荷 PC2:", dict(zip(["L","R2","W1"],np.round(vt[1],3))))
print("  相关阵：\n", df[["L","R2","W1"]].corr().round(3))

print("\n【P4 频次 vs 自由】")
for a,b in [("F","L"),("F","A"),("L","A")]:
    rr,p=r(a,b); print(f"  r({a},{b}) = {rr:+.3f} p={p:.2e}")
df.to_csv("onet_panel.csv")
