import sys, io, pandas as pd, numpy as np
path = sys.argv[1]
want = ['site','state_territory','sample_id','sample_collect_date','sample_type','sample_matrix','sample_location',
        'pcr_target','pcr_gene_target_agg','pcr_target_avg_conc','pcr_target_detect','pcr_target_avg_conc_lin',
        'pcr_target_flowpop_lin','population_served','date_updated','pcr_target_units','lab_id','major_lab_method']
have = [c for c in pd.read_csv(path, nrows=0).columns if c in want]
df = pd.read_csv(path, usecols=have, low_memory=False)
out = io.StringIO()
def p(*a): print(*a); print(*a, file=out)

p("ROWS:", len(df), "| COLUMNS READ:", have)
p("\n== null rate / unique values ==")
for c in have:
    p(f"{c:28s} dtype={str(df[c].dtype):10s} null={df[c].isna().mean():6.1%} unique={df[c].nunique()}")
p("\n== value counts for low-cardinality columns ==")
for c in have:
    if df[c].nunique() <= 12:
        p(f"-- {c}"); p(df[c].value_counts(dropna=False).to_string())
p("\n== numeric columns: quantiles and share <= 0 ==")
for c in ['pcr_target_avg_conc','pcr_target_avg_conc_lin','pcr_target_flowpop_lin']:
    if c in df:
        x = pd.to_numeric(df[c], errors='coerce')
        p(f"-- {c}: n={x.notna().sum()}  share<=0={(x<=0).mean():.3f}")
        p(x.quantile([0,.01,.25,.5,.75,.99,1]).to_string())
if 'pcr_target_avg_conc_lin' in df:
    k = df[pd.to_numeric(df['pcr_target_avg_conc_lin'], errors='coerce').notna()]
    per = k.groupby('site').size()
    p("\nsites with linear conc:", per.shape[0]); p("rows/site quantiles:\n", per.quantile([.5,.75,.9,.99,1]).to_string())
    p("sites with >=150 rows:", int((per>=150).sum()), "| >=100:", int((per>=100).sum()))
if {'date_updated','sample_collect_date'} <= set(df.columns):
    lag = (pd.to_datetime(df['date_updated'], errors='coerce') - pd.to_datetime(df['sample_collect_date'], errors='coerce')).dt.days
    p("\n== date_updated minus sample_collect_date (days) =="); p(lag.describe(percentiles=[.1,.5,.9]).to_string())
open('diagnostic.txt','w').write(out.getvalue()); print("\nsaved diagnostic.txt")
