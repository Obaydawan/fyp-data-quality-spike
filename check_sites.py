import pandas as pd

path = "export.csv"

cols = [
    "site",
    "state_territory",
    "sample_collect_date",
    "pcr_target_avg_conc_lin",
    "pcr_target_detect",
    "sample_matrix",
    "sample_location",
]

df = pd.read_csv(path, usecols=cols, low_memory=False)

df["date"] = pd.to_datetime(df["sample_collect_date"], errors="coerce")
df["conc_lin"] = pd.to_numeric(
    df["pcr_target_avg_conc_lin"],
    errors="coerce"
)

df = df[
    df["site"].notna()
    & df["date"].notna()
    & df["conc_lin"].notna()
].copy()

print("Usable linear-concentration rows:", len(df))
print("Sites:", df["site"].nunique())

rows = []

for site, g in df.groupby("site"):
    dates = (
        g["date"]
        .drop_duplicates()
        .sort_values()
    )

    if len(dates) < 2:
        continue

    gaps = dates.diff().dt.days.dropna()

    rows.append({
        "site": site,
        "state": g["state_territory"].iloc[0],
        "n_obs": len(g),
        "n_dates": len(dates),
        "start": dates.min().date(),
        "end": dates.max().date(),
        "span_days": (dates.max() - dates.min()).days,
        "median_gap": gaps.median(),
        "max_gap": gaps.max(),
        "mean_gap": gaps.mean(),
        "pct_gap_le_14": (gaps <= 14).mean() * 100,
        "detect_yes_pct": (
            (g["pcr_target_detect"] == "yes").mean() * 100
        ),
    })

sites = pd.DataFrame(rows)

# Strict candidate criteria
candidates = sites[
    (sites["n_obs"] >= 150)
    & (sites["span_days"] >= 365)
    & (sites["max_gap"] <= 14)
].copy()

candidates = candidates.sort_values(
    ["n_obs", "span_days"],
    ascending=False
)

print("\nSTRICT CANDIDATES:")
print(candidates.to_string(index=False))

print("\nNumber of strict candidates:", len(candidates))

print("\nTOP 30 BY OBSERVATION COUNT:")
print(
    sites.sort_values("n_obs", ascending=False)
    .head(30)
    .to_string(index=False)
)

sites.to_csv("linear_site_check.csv", index=False)

print("\nSaved: linear_site_check.csv")
