import sys, pandas as pd, numpy as np
d=sys.argv[1]
p=pd.read_csv(f"{d}/sales_pipeline.csv",parse_dates=["engage_date","close_date"])
c=p[p.deal_stage.isin(["Won","Lost"])].copy(); c["won"]=(c.deal_stage=="Won").astype(int)
def auc(y,s):
    r=pd.Series(s).rank().values; y=np.asarray(y); n1=y.sum(); n0=len(y)-n1
    return (r[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
for snap in ["2017-04-30","2017-06-30","2017-08-31","2017-10-31"]:
    s=pd.Timestamp(snap); o=c[(c.engage_date<=s)&(c.close_date>s)].copy(); o["age"]=(s-o.engage_date).dt.days
    print(snap,"open-at-snapshot",len(o),"wr",round(o.won.mean(),3),"AUC(age)",round(auc(o.won,o.age),3))
print("monthly close counts\n",c.close_date.dt.to_period("M").value_counts().sort_index().to_dict())
print("monthly engage counts (all)\n",p.engage_date.dt.to_period("M").value_counts().sort_index().to_dict())
