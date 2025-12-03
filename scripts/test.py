import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Get data directory relative to script location
script_dir = Path(__file__).parent
data_dir = script_dir.parent / "data"
output_dir = script_dir.parent / "output"

# Load data
df = pd.read_csv(data_dir / "bls_metrics_with_filters.csv")

top_lift = df.sort_values(by="LIFT", ascending=False).head(10)
print(top_lift)

# Create output directory if it doesn't exist
output_dir.mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(12, 6))
df.boxplot(column="LIFT", by="GROUP_NAME", rot=90, ax=ax)
plt.tight_layout()
plt.savefig(output_dir / "lift_boxplot.png", dpi=300, bbox_inches="tight")
plt.show()
