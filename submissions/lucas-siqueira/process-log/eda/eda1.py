import sys, pandas as pd
d=sys.argv[1]
p=pd.read_csv(f"{d}/sales_pipeline.csv",parse_dates=["engage_date","close_date"])
a=pd.read_csv(f"{d}/accounts.csv"); pr=pd.read_csv(f"{d}/products.csv"); t=pd.read_csv(f"{d}/sales_teams.csv")
print(p.shape); print(p.deal_stage.value_counts())
print("nulls:\n",p.isna().sum())
print("null by stage:\n",p.groupby("deal_stage")[["account","engage_date","close_date","close_value"]].apply(lambda x:x.isna().sum()))
print("products in pipeline not in catalog:",set(p["product"])-set(pr["product"]))
print("agents not in teams:",set(p.sales_agent)-set(t.sales_agent))
print("agents in teams w/o deals:",set(t.sales_agent)-set(p.sales_agent))
print("accounts not in table:",set(p.account.dropna())-set(a.account))
print("sectors:",a.sector.value_counts().to_dict())
print("subsidiary non-null:",a.subsidiary_of.notna().sum())
print("date ranges engage:",p.engage_date.min(),p.engage_date.max()," close:",p.close_date.min(),p.close_date.max())
print(t.groupby(["regional_office","manager"]).size())
print("product counts:",p["product"].value_counts().to_dict())
c=p[p.deal_stage.isin(["Won","Lost"])]
print("overall win rate:",(c.deal_stage=="Won").mean())
print("lost close_value nonzero:",(c[c.deal_stage=="Lost"].close_value!=0).sum())
