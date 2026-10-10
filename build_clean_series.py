import pandas as pd
import numpy as np

SITES = [967, 970, 972]

df = pd.read_csv(
    "export.csv",
    usecols=[
        "site",
        "sample_collect_date",
        "pcr_target_avg_conc_lin",
        "pcr_target_units",
    ]
)

df = df[df["site"].isin(SITES)].copy()

df["date"] = pd.to_datetime(
    df["sample_collect_date"],
    errors="coerce"
)

df["conc"] = pd.to_numeric(
    df["pcr_target_avg_conc_lin"],
    errors="coerce"
)

df = df.dropna(subset=["date", "conc"])

df = df[
    df["pcr_target_units"] == "copies/l wastewater"
].copy()

# Explicit Monday-starting calendar week.
# weekday(): Monday=0 ... Sunday=6
df["week"] = (
    df["date"]
    - pd.to_timedelta(df["date"].dt.weekday, unit="D")
).dt.normalize()

weekly = (
    df.groupby(["site", "week"])
      .agg(
          concentration=("conc", "median"),
          n_samples=("conc", "size"),
      )
      .reset_index()
)

weekly["log_concentration"] = np.log1p(
    weekly["concentration"]
)

weekly = weekly.sort_values(
    ["site", "week"]
)

weekly.to_csv(
    "clean_weekly_series.csv",
    index=False
)

print("CLEAN WEEKLY SERIES")
print(
    weekly.groupby("site")
    .agg(
        weeks=("week", "count"),
        first_week=("week", "min"),
        last_week=("week", "max"),
        median_conc=("concentration", "median"),
        median_log=("log_concentration", "median"),
    )
    .to_string()
)

print("\nWEEKDAY CHECK")
print(
    weekly["week"].dt.day_name().value_counts().to_string()
)

print("\nFIRST 10 ROWS")
print(
    weekly.head(10).to_string(index=False)
)

print("\nSAVED:")
print("clean_weekly_series.csv")
