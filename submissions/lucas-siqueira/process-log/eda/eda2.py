import sys, pandas as pd
pd.set_option("display.width",200)
d=sys.argv[1]
p=pd.read_csv(f"{d}/sales_pipeline.csv",parse_dates=["engage_date","close_date"])
p["product"]=p["product"].replace({"GTXPro":"GTX Pro"})
a=pd.read_csv(f"{d}/accounts.csv"); pr=pd.read_csv(f"{d}/products.csv"); t=pd.read_csv(f"{d}/sales_teams.csv")
p=p.merge(t,on="sales_agent",how="left").merge(pr,on="product",how="left").merge(a,on="account",how="left")
c=p[p.deal_stage.isin(["Won","Lost"])].copy(); c["won"]=(c.deal_stage=="Won").astype(int)
c["days"]=(c.close_date-c.engage_date).dt.days
def wr(col):
    g=c.groupby(col).won.agg(["mean","count"]).sort_values("mean"); print(f"\n== win rate by {col}\n",g.round(3))
for col in ["product","regional_office","manager","sector","office_location"]: wr(col)
g=c.groupby("sales_agent").won.agg(["mean","count"]).sort_values("mean"); print("\n== agent win rate spread\n",g.round(3).head(5),"\n...\n",g.round(3).tail(5)); print("agent wr min/max/std",g["mean"].min(),g["mean"].max(),g["mean"].std())
c["rev_q"]=pd.qcut(c.revenue,4); wr("rev_q")
c["emp_q"]=pd.qcut(c.employees,4); wr("emp_q")
c["sub"]=c.subsidiary_of.notna(); wr("sub")
print("\n== cycle days won vs lost\n",c.groupby("deal_stage").days.describe().round(1))
c["days_b"]=pd.cut(c.days,[-1,7,14,30,60,90,120,200]); wr("days_b")
c["eq"]=c.engage_date.dt.to_period("Q"); wr("eq")
c["cq"]=c.close_date.dt.to_period("Q"); wr("cq")
w=c[c.won==1]; w["ratio"]=w.close_value/w.sales_price
print("\n== won close_value / list price\n",w.ratio.describe().round(3))
print("won value by product\n",w.groupby("product").close_value.agg(["mean","median","count"]).round(0))
o=p[~p.deal_stage.isin(["Won","Lost"])].copy()
ref=pd.Timestamp("2017-12-31"); o["age"]=(ref-o.engage_date).dt.days
print("\n== open engaging age (ref 2017-12-31)\n",o[o.deal_stage=="Engaging"].age.describe().round(1))
print("open by product\n",o.groupby(["deal_stage","product"]).size().unstack(0))
print("open per agent describe\n",o.groupby("sales_agent").size().describe().round(1))
print("open w/ account by stage\n",o.groupby("deal_stage").account.apply(lambda x:x.notna().mean()).round(3))
print("open potential list value total",o.sales_price.sum())
print("engage month of open engaging\n",o[o.deal_stage=="Engaging"].engage_date.dt.to_period("M").value_counts().sort_index())
# agent x product
ap=c.groupby(["sales_agent","product"]).won.agg(["mean","count"]); print("\nagent-product cells n>=20:",(ap["count"]>=20).sum(),"of",len(ap)," wr std within n>=20:",ap[ap["count"]>=20]["mean"].std().round(3))
# account historical win rate
acc=c.groupby("account").won.agg(["mean","count"]); print("\naccount wr spread: min",acc["mean"].min().round(3),"max",acc["mean"].max().round(3),"std",acc["mean"].std().round(3),"median n",acc["count"].median())
# repeat business: accounts with prior won
