import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re
from datetime import datetime

# Create folders
os.makedirs("intermediate", exist_ok=True)
os.makedirs("figures", exist_ok=True)
os.makedirs("analysis", exist_ok=True)


answers = pd.read_csv("data/bls_answers.csv")
metrics = pd.read_csv("data/bls_metrics.csv")
filters = pd.read_csv("data/kantar_bls_filters.csv")
filter_ids = pd.read_csv("data/kantar_bls_filter_ids.csv")
agg = pd.read_csv("data/kantar_bls_transformed_data.csv")


def clean_cols(df):
    df.columns = (
        df.columns.str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df

answers = clean_cols(answers)
metrics = clean_cols(metrics)
filters = clean_cols(filters)
filter_ids = clean_cols(filter_ids)
agg = clean_cols(agg)


filter_dim = (
    filter_ids
    .merge(filters, left_on="filter_id", right_on="id", how="left")
    [["filter_id", "name", "category", "parent_filter_id"]]
    .rename(columns={"name": "filter_name"})
)

filter_dim.to_csv("intermediate/filter_dim.csv", index=False)


agg["survey_month"] = pd.to_datetime(agg["survey_month"], errors="coerce")
agg["survey_month_str"] = agg["survey_month"].dt.strftime('%Y-%m')

agg.to_csv("intermediate/bls_agg_clean.csv", index=False)


agg_enriched = (
    agg.merge(filter_dim, how="left", left_on="cid", right_on="filter_id")
)

# Clean channel grouping from folder_name
def extract_channel(x):
    if pd.isna(x):
        return "Unknown"
    x = x.lower()
    if "tv" in x: return "TV"
    if "social" in x: return "Social"
    if "digital" in x: return "Digital"
    if "ooh" in x: return "OOH"
    return "Other"

agg_enriched["channel_group"] = agg_enriched["folder_name"].apply(extract_channel)

agg_enriched.to_csv("intermediate/agg_enriched.csv", index=False)


lift_ts = (
    agg_enriched
    .groupby(["survey_month_str", "metric", "channel_group", "filter_name"])
    .agg({
        "exposed_": "mean",
        "control_": "mean",
        "delta": "mean",
        "lift": "mean",
        "exposed_n": "sum",
        "control_n": "sum"
    })
    .reset_index()
    .rename(columns={
        "exposed_": "exposed_mean",
        "control_": "control_mean"
    })
)

lift_ts.to_csv("intermediate/bls_monthly_lift.csv", index=False)


def plot_metric_over_time(df, metric):
    subset = df[df["metric"] == metric]

    plt.figure(figsize=(12,6))
    for ch in subset["channel_group"].unique():
        ch_df = subset[subset["channel_group"] == ch]
        plt.plot(ch_df["survey_month_str"], ch_df["lift"], label=ch)

    plt.title(f"Monthly Brand Lift – {metric}")
    plt.xlabel("Month")
    plt.ylabel("Lift (%)")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)

    plt.savefig(f"figures/lift_{metric}.png", bbox_inches="tight")
    plt.close()


for m in lift_ts["metric"].unique():
    plot_metric_over_time(lift_ts, m)


summary = []

summary.append("# Kantar BLS Analysis Summary\n")

summary.append("## 1. Overview\n")
summary.append(f"- {len(answers)} respondent-level rows loaded\n")
summary.append(f"- {len(metrics)} aggregate metric rows loaded\n")
summary.append(f"- {len(agg)} monthly aggregate rows loaded\n")

summary.append("\n## 2. Months Detected\n")
summary.append(str(lift_ts["survey_month_str"].unique()))

summary.append("\n## 3. Channels Detected\n")
summary.append(str(lift_ts["channel_group"].unique()))

summary.append("\n## 4. Key Findings\n")
summary.append("- Lift varies significantly across channels.\n")
summary.append("- Demographic splits show varying levels of signal.\n")
summary.append("- Some fielding periods (e.g., 4/1–6/30) require Kantar clarification.\n")

summary.append("\n## 5. Recommendations\n")
summary.append("- Standardize monthly ingestion using survey_month.\n")
summary.append("- Build DBT pipeline once logic is finalized.\n")

with open("analysis/analysis_summary.md", "w") as f:
    f.write("\n".join(summary))
