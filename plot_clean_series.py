import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(
    "clean_weekly_series.csv",
    parse_dates=["week"]
)

plt.figure(figsize=(14, 6))

for site in [967, 970, 972]:
    s = df[df["site"] == site]
    plt.plot(
        s["week"],
        s["log_concentration"],
        marker=".",
        linewidth=1,
        label=f"Site {site}"
    )

plt.xlabel("Week")
plt.ylabel("log1p(wastewater concentration)")
plt.title("Clean weekly wastewater series")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()

plt.savefig("clean_weekly_series.png", dpi=150)

print("Saved: clean_weekly_series.png")
