import sys
from pathlib import Path
import pandas as pd

INPUT = Path(sys.argv[1])
N_SITES = int(sys.argv[2]) if len(sys.argv) > 2 else 20

USECOLS = [
    "record_id",
    "site",
    "state_territory",
    "county_fips",
    "population_served",
    "sample_id",
    "sample_collect_date",
    "sample_type",
    "sample_matrix",
    "sample_location",
    "pcr_target",
    "pcr_gene_target_agg",
    "pcr_target_avg_conc",
    "pcr_target_detect",
    "pcr_target_avg_conc_lin",
    "pcr_target_flowpop_lin",
]

print(f"input: {INPUT}")
print(f"target sites: {N_SITES}")
print("reading CSV in chunks...")

frames = []

for chunk in pd.read_csv(
    INPUT,
    usecols=USECOLS,
    chunksize=50_000,
    low_memory=False,
):
    # Keep SARS-CoV-2 records with a usable site/date/concentration.
    chunk = chunk[
        chunk["site"].notna()
        & chunk["sample_collect_date"].notna()
        & chunk["pcr_target_avg_conc"].notna()
    ].copy()

    chunk["sample_collect_date"] = pd.to_datetime(
        chunk["sample_collect_date"],
        errors="coerce",
    )

    chunk["pcr_target_avg_conc"] = pd.to_numeric(
        chunk["pcr_target_avg_conc"],
        errors="coerce",
    )

    chunk = chunk[
        chunk["sample_collect_date"].notna()
        & chunk["pcr_target_avg_conc"].notna()
        & (chunk["pcr_target"] == "sars-cov-2")
    ]

    if not chunk.empty:
        frames.append(chunk)

if not frames:
    raise RuntimeError("No usable SARS-CoV-2 records were found.")

df = pd.concat(frames, ignore_index=True)

print(f"rows after filters: {len(df):,}")
print(f"sites after filters: {df['site'].nunique():,}")

# ------------------------------------------------------------
# Build site-level summary
# ------------------------------------------------------------

summary_rows = []

for site, g in df.groupby("site"):
    dates = (
        g["sample_collect_date"]
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    if len(dates) < 2:
        continue

    gaps = dates.diff().dt.days.dropna()

    summary_rows.append({
        "site": site,
        "state": g["state_territory"].dropna().iloc[0]
            if g["state_territory"].notna().any() else "",
        "n_rows": len(g),
        "n_dates": len(dates),
        "start_date": dates.min().date(),
        "end_date": dates.max().date(),
        "span_days": (dates.max() - dates.min()).days,
        "median_gap_days": gaps.median(),
        "mean_gap_days": gaps.mean(),
        "pct_gaps_2_to_4_days": (
            ((gaps >= 2) & (gaps <= 4)).mean() * 100
        ),
    })

summary = pd.DataFrame(summary_rows)

if summary.empty:
    raise RuntimeError("Could not build a site summary.")

summary = summary.sort_values(
    ["pct_gaps_2_to_4_days", "n_dates", "span_days"],
    ascending=[False, False, False],
)

summary.to_csv("site_summary_all.csv", index=False)

print("\nsite summary:")
print(summary.head(20).to_string(index=False))

# ------------------------------------------------------------
# Select approximately regular sites
# ------------------------------------------------------------

eligible = summary[
    (summary["n_dates"] >= 20)
    & (summary["span_days"] >= 60)
    & (summary["median_gap_days"] >= 1)
    & (summary["median_gap_days"] <= 7)
].copy()

if len(eligible) < N_SITES:
    print(
        f"\nOnly {len(eligible)} sites met the normal criteria."
        " Relaxing criteria."
    )

    eligible = summary[
        (summary["n_dates"] >= 15)
        & (summary["span_days"] >= 45)
    ].copy()

if len(eligible) < N_SITES:
    print(
        f"\nOnly {len(eligible)} sites met the relaxed criteria."
    )
    chosen = eligible.head(N_SITES).copy()
else:
    chosen = eligible.head(N_SITES).copy()

if chosen.empty:
    raise RuntimeError(
        "No suitable sites were found. "
        "Upload site_summary_all.csv for manual selection."
    )

chosen_sites = chosen["site"].tolist()

print("\nchosen sites:")
print(chosen.to_string(index=False))

subset = df[df["site"].isin(chosen_sites)].copy()

subset = subset.sort_values(
    ["site", "sample_collect_date"]
)

subset.to_csv("subset_sites.csv", index=False)

print("\nwrote subset_sites.csv")
print(f"subset rows: {len(subset):,}")
print(f"subset sites: {subset['site'].nunique():,}")
print(
    f"subset size: "
    f"{Path('subset_sites.csv').stat().st_size / (1024**2):.2f} MB"
)
