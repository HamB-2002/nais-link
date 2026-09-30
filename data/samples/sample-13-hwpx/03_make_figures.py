import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8,
    "axes.linewidth": 0.6,
})

IEEE_COL_W = 3.5

# ============================================================
# FIGURE 1: fix legend / corpus-mean-label collision
# ============================================================
df = pd.read_csv("ovis_scored_table.csv").sort_values("OVIS_pct", ascending=True)
color_map = {
    "outcome-only": "#8c8c8c",
    "process-aware": "#3068a8",
    "process-aware-unpublished": "#3068a8",
    "outcome-only-but-audited": "#e07b1f",
}
colors = df["metric_design"].map(color_map)
labels = (df["source_id"] + " \u2014 " + df["name"].str.replace(r"\s*\(.*\)", "", regex=True)).str.slice(0, 34)

fig, ax = plt.subplots(figsize=(IEEE_COL_W, 3.3))
bars = ax.barh(labels, df["OVIS_pct"], color=colors, edgecolor="black", linewidth=0.4, height=0.62)

mean_val = df["OVIS_pct"].mean()
ax.axvline(mean_val, color="black", linestyle="--", linewidth=0.8, zorder=0)
# Put the mean label at the TOP of the chart, horizontal, not rotated, well clear of the legend
ax.text(mean_val, len(labels) - 0.15, f"mean = {mean_val:.1f}%", fontsize=6.6,
        rotation=0, va="bottom", ha="center")

for bar, val in zip(bars, df["OVIS_pct"]):
    ax.text(val + 1.0, bar.get_y() + bar.get_height()/2, f"{val:.0f}%",
            va="center", ha="left", fontsize=6.8)

ax.set_xlim(0, 108)
ax.set_ylim(-0.7, len(labels) - 0.1 + 0.9)
ax.set_xlabel("OVIS (%)", fontsize=8)
ax.tick_params(axis="y", labelsize=6.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend placed BELOW the plot (its own reserved strip), never inside the bar area
legend_handles = [
    plt.Rectangle((0,0),1,1, facecolor=color_map["outcome-only"], edgecolor="black", linewidth=0.4, label="Outcome-only"),
    plt.Rectangle((0,0),1,1, facecolor=color_map["process-aware"], edgecolor="black", linewidth=0.4, label="Process-aware"),
    plt.Rectangle((0,0),1,1, facecolor=color_map["outcome-only-but-audited"], edgecolor="black", linewidth=0.4, label="Outcome-only, audited"),
]
leg = ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.16),
                 fontsize=6.6, frameon=False, ncol=1, handlelength=1.2, handletextpad=0.5,
                 labelspacing=0.35)

fig.subplots_adjust(left=0.42, right=0.97, top=0.95, bottom=0.30)
plt.savefig("fig1_ovis_ranked.pdf", pad_inches=0.05)
plt.savefig("fig1_ovis_ranked.png", dpi=300, pad_inches=0.05)
plt.close()

# Bounding-box sanity check: does the legend bbox intersect any bar-label text bbox?
print("Figure 1 saved. Legend bbox (axes fraction):", leg.get_window_extent())

# ============================================================
# FIGURE 2: shorter tick labels + legend in its own reserved strip
# ============================================================
rs256 = 28/69*100
none_ = 41/69*100
hs256 = 0/69*100

fig2, ax2 = plt.subplots(figsize=(IEEE_COL_W, 3.9))

x = [0, 1]
# Short, single-purpose tick labels; full detail lives in the LaTeX/DOCX caption, not on the chart
bar_labels = ["nemotron-3-super\n(n=69)", "All 6 models\n(nominal)"]

ax2.bar(x[0], rs256, width=0.55, color="#9fb8d8", edgecolor="black", linewidth=0.5,
        label="RS256 token replay (unintended)")
ax2.bar(x[0], none_, width=0.55, bottom=rs256, color="#f2b56b", edgecolor="black", linewidth=0.5,
        label="alg:none forgery (unintended)")
ax2.bar(x[0], hs256, width=0.55, bottom=rs256+none_, color="#c0392b", edgecolor="black", linewidth=0.5,
        label=r"RS256$\to$HS256 confusion (intended exploit)")
ax2.bar(x[1], 98.5, width=0.55, color="#7f7f7f", edgecolor="black", linewidth=0.5)

ax2.set_xticks(x)
ax2.set_xticklabels(bar_labels, fontsize=7.2)
ax2.set_ylabel("Percent (%)", fontsize=8)
ax2.set_ylim(0, 122)
ax2.set_xlim(-0.55, 1.55)

ax2.text(x[0], rs256/2, f"{rs256:.0f}%\nRS256 replay", ha="center", va="center", fontsize=6.6)
ax2.text(x[0], rs256+none_/2, f"{none_:.0f}%\nalg:none", ha="center", va="center", fontsize=6.6)
ax2.annotate("", xy=(x[0], rs256+none_+0.5), xytext=(x[0], rs256+none_+7),
             arrowprops=dict(arrowstyle="-", color="#c0392b", lw=0.8))
ax2.text(x[0], rs256+none_+8, "0 of 69\nintended exploit\n(0.0%)", ha="center", va="bottom",
         fontsize=6.8, color="#c0392b", fontweight="bold")
ax2.text(x[1], 98.5+2, "98.5%\n(nominal)", ha="center", va="bottom", fontsize=7.2)

ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

leg2 = ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), fontsize=6.8, frameon=False,
                   ncol=1, handlelength=1.2, handletextpad=0.5, labelspacing=0.5)

fig2.subplots_adjust(left=0.15, right=0.97, top=0.95, bottom=0.30)
plt.savefig("fig2_jwt_case.pdf", pad_inches=0.05)
plt.savefig("fig2_jwt_case.png", dpi=300, pad_inches=0.05)
plt.close()
print("Figure 2 saved. Legend bbox (display coords):", leg2.get_window_extent())
