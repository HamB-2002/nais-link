"""
02_significance_tests.py

Reproduces the two statistical tests reported in Section 7 (Limitations) of
"Markets for Unverified Capability" (Akhunzada).

Input:  ovis_scored_table.csv  (produced by 01_ovis_scoring_and_group_means.py)
Output: printed test statistics, exactly as quoted in the manuscript:
    Mann-Whitney U on method-verification (MV) scores, outcome-only vs process-aware
    Fisher's exact test on the cruder binary MV=0 vs MV>0 split

Requirements: pandas, scipy
    pip install pandas scipy --break-system-packages   (if needed)

Run:
    python3 02_significance_tests.py
"""
import pandas as pd
from scipy import stats

df = pd.read_csv("ovis_scored_table.csv")

outcome_only = df[df.metric_design == "outcome-only"]["MV"]
process_aware = df[df.metric_design.isin(["process-aware", "process-aware-unpublished"])]["MV"]

print("Outcome-only MV scores (n={}): {}".format(len(outcome_only), list(outcome_only)))
print("Process-aware MV scores (n={}): {}".format(len(process_aware), list(process_aware)))
print()

# --- Mann-Whitney U test (primary test reported in the manuscript) ---
u_stat, p_mw = stats.mannwhitneyu(outcome_only, process_aware, alternative="two-sided")
print(f"Mann-Whitney U = {u_stat}, p = {p_mw:.4f}")

# --- Fisher's exact test on the binary MV=0 vs MV>0 split (secondary, weaker test) ---
mv_zero_outcome = int((outcome_only == 0).sum())
mv_pos_outcome = int((outcome_only > 0).sum())
mv_zero_process = int((process_aware == 0).sum())
mv_pos_process = int((process_aware > 0).sum())
table = [[mv_zero_outcome, mv_pos_outcome], [mv_zero_process, mv_pos_process]]
print(f"2x2 contingency table (rows = outcome-only / process-aware, cols = MV==0 / MV>0): {table}")
odds_ratio, p_fisher = stats.fisher_exact(table)
print(f"Fisher's exact test: odds ratio = {odds_ratio}, p = {p_fisher:.4f}")

print()
print("These are the exact figures quoted in the manuscript's Limitations section:")
print(f"  'U = {int(u_stat)}, p = {p_mw:.3f}' (Mann-Whitney)")
print(f"  'p = {p_fisher:.3f}' (Fisher's exact, binary version)")
