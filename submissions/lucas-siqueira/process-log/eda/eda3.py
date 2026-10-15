import sys, pandas as pd, numpy as np
d=sys.argv[1]
p=pd.read_csv(f"{d}/sales_pipeline.csv",parse_dates=["engage_date","close_date"])
p["product"]=p["product"].replace({"GTXPro":"GTX Pro"})
a=pd.read_csv(f"{d}/accounts.csv"); t=pd.read_csv(f"{d}/sales_teams.csv")
p=p.merge(t,on="sales_agent",how="left").merge(a,on="account",how="left")
c=p[p.deal_stage.isin(["Won","Lost"])].copy(); c["won"]=(c.deal_stage=="Won").astype(int); c["days"]=(c.close_date-c.engage_date).dt.days
print("P(win | still open after a days) among closed:")
for a_ in [0,7,14,30,60,90,100,110,120,130,138]:
    s=c[c.days>a_]; print(f"  a>{a_:>3}: wr={s.won.mean() if len(s) else float('nan'):.3f} n={len(s)}")
print("days pct: p90",c.days.quantile(.9),"p95",c.days.quantile(.95),"p99",c.days.quantile(.99))
o=p[p.deal_stage=="Engaging"].copy(); o["age"]=(pd.Timestamp("2017-12-31")-o.engage_date).dt.days
for th in [30,60,90,120,138]: print(f"engaging age>{th}: {(o.age>th).mean():.3f} ({(o.age>th).sum()})")
# time-split AUC check
def auc(y,s):
    r=pd.Series(s).rank().values; y=np.asarray(y); n1=y.sum(); n0=len(y)-n1
    return (r[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
c=c.sort_values("close_date"); cut=pd.Timestamp("2017-09-30")
tr=c[c.close_date<=cut]; te=c[c.close_date>cut]; base=tr.won.mean(); k=50
print("train",len(tr),"test",len(te),"base",round(base,3))
for col in ["sales_agent","product","account","sector","regional_office","manager"]:
    g=tr.groupby(col).won.agg(["sum","count"]); sh=(g["sum"]+k*base)/(g["count"]+k)
    s=te[col].map(sh).fillna(base); print(f"  AUC {col}: {auc(te.won,s):.3f}")
