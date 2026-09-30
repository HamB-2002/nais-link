"""
Outcome-Validation Integrity Score (OVIS) - Paper 1 analysis
Scores each benchmark/study source on 5 rubric dimensions (0-2 each, max 10)
based on documented evidence gathered from primary-source reading.
Only sources with sufficient primary-source depth are scored; others are
flagged INSUFFICIENT_EVIDENCE and excluded from headline statistics (but listed).
"""
import pandas as pd
import json

# Rubric dimensions:
#   MV = Method Verification      (does grading check *how* the outcome was reached, not just *that* it was reached?)
#   SA = Shortcut/Contamination Audit (explicit audit for shortcut-solving / reward hacking?)
#   HG = Human Ground-Truth Anchor (independent human baseline or human/maintainer confirmation?)
#   IG = Grader Independence       (deterministic / non-collusive grader, not self-graded or same-family LLM-judge?)
#   RT = Reproducibility/Transparency (harness, transcripts, or grading logic publicly released?)
# Each 0 (absent) / 1 (partial) / 2 (present, explicit, documented)
# OVIS = sum(MV,SA,HG,IG,RT) -> percentage of 10

records = [
 # source_id, short_name, MV,SA,HG,IG,RT, metric_design, justification
 ("S01","Sultan2026 (XBOW-104 scaffold study)",1,2,0,2,2,"outcome-only",
  "Flag=sha256(id) audited across 142 transcripts for id leakage/hash shortcuts (SA=2); "
  "grading is exact-flag match, no chain-of-actions check (MV=1, partial via shortcut audit only); "
  "no independent human baseline (HG=0); deterministic grader (IG=2); harness+transcripts released (RT=2)."),
 ("S02","CyberSOCEval2025 (Meta/CrowdStrike)",0,1,0,2,2,"outcome-only",
  "MCQ correctness only, no reasoning-path check (MV=0); random-guess baseline computed to contextualize "
  "but not a shortcut audit of model behavior (SA=1); no model-performance human baseline, only QA-construction "
  "review (HG=0); deterministic MCQ match (IG=2); benchmark released open-source (RT=2)."),
 ("S04","Microsoft ExCyTIn-Bench 2025",2,0,0,2,1,"process-aware",
  "Graph-grounded stepwise reward validates intermediate investigative actions against a known "
  "investigation graph, not just final answer (MV=2); no explicit reward-hacking audit documented (SA=0); "
  "no human-analyst baseline reported (HG=0); deterministic graph-based scoring (IG=2); "
  "methodology blogged, full transcript release unconfirmed (RT=1)."),
 ("S05","ExploitBench 2026 (v8-bench)",2,1,0,2,1,"process-aware",
  "Tiered 5-level, 16-capability ladder graded by deterministic verifier explicitly requires demonstrated "
  "capability progression, not a single pass/fail flag (MV=2); ladder design structurally limits (but does not "
  "formally audit) shortcut solving (SA=1); no human-baseline comparison found (HG=0); explicitly 'no LLM-judge' "
  "(IG=2); verifier described as deterministic but full public release unconfirmed at time of review (RT=1)."),
 ("S07","TrustedSec 2026 (Juice Shop local-model benchmark)",2,2,1,2,2,"outcome-only-but-audited",
  "Automated grader was outcome-only (string match), but authors manually decoded every passing JWT and traced "
  "every SQLi login across 4,800 runs, discovering the intended method (RS256->HS256 confusion) was used in "
  "ZERO of 681 relevant runs despite high nominal pass rates (MV=2, SA=2 -- textbook reward-hacking case study); "
  "every challenge hand-verified solvable before the run ('proving ground') = partial human ground truth on task "
  "validity (HG=1); deterministic string-match grader (IG=2); full harness, curl reproductions, and per-model "
  "raw transcripts published (RT=2)."),
 ("S11","Visa VVAH / Project Glasswing 2026",2,1,2,2,0,"process-aware-unpublished",
  "S6 adversarial verification + S11 validation panel explicitly confirm exploit-path reality before a finding "
  "or fix counts as resolved (MV=2); multi-agent deterministic voting reduces false positives structurally, but "
  "no published shortcut-audit report (SA=1); human security engineers review and validate every finding before "
  "action (HG=2); validation panel is an independent adversarial process, deterministic weighted gates (IG=2); "
  "explicitly publishes NO accuracy numbers or transcripts for external audit (RT=0)."),
 ("S13","DARPA AIxCC 2025 Finals",2,2,1,2,2,"process-aware",
  "Scoring requires functional proof a vulnerability exists AND that a patch actually closes it, not a string "
  "match (MV=2); human interaction strictly prohibited by competition rule, independent DARPA-run scoring "
  "infrastructure (SA=2, IG=2); systems found 18 real zero-days outside the built-in answer key, an unplanned "
  "but strong validity signal (HG=1, partial -- not a formal human-time baseline); 4 of 7 systems open-sourced, "
  "methodology publicly documented (RT=2)."),
 ("S17","Cybench 2024",1,0,2,2,2,"outcome-only",
  "Primary metric is exact flag capture (MV=1, partial credit only because subtask decomposition exposes some "
  "intermediate reasoning steps); no explicit reward-hacking/shortcut audit documented (SA=0); rigorous human "
  "solve-time baseline for every one of 40 tasks, up to 24h54m for hardest (HG=2); deterministic flag matching "
  "(IG=2); full code/data/transcripts public and reused as the reference baseline by multiple derivative papers "
  "in this corpus (RT=2)."),
 ("S20","CAIBench 2025 (CAI framework on Cybench subset)",0,0,0,2,1,"outcome-only",
  "pass@1 binary flag accuracy, no method check reported (MV=0); no shortcut audit (SA=0); does not directly "
  "report Cybench's own human baseline alongside its numbers (HG=0); deterministic flag grading inherited from "
  "Cybench (IG=2); published as arXiv preprint, full artifact release unconfirmed (RT=1)."),
 ("S21","EnIGMA 2024 (NYU CTF / Cybench / HTB)",0,0,0,2,2,"outcome-only",
  "Binary flag capture across all three benchmarks used (MV=0); no shortcut audit (SA=0); reports comparison to "
  "prior SOTA, not a raw independent human baseline in this paper (HG=0); deterministic grading (IG=2); code and "
  "transcripts released and reused as baseline by D-CIPHER (RT=2)."),
 ("S22","D-CIPHER 2025 (Cybench / NYU CTF / HTB)",0,0,0,2,2,"outcome-only",
  "Same binary-flag paradigm as EnIGMA across all three benchmarks (MV=0, SA=0); inherits but does not foreground "
  "Cybench's human baseline (HG=0); deterministic grading (IG=2); reruns and publishes EnIGMA transcripts "
  "alongside its own for direct comparison (RT=2)."),
]

cols = ["source_id","name","MV","SA","HG","IG","RT","metric_design","justification"]
df = pd.DataFrame(records, columns=cols)
df["OVIS_raw"] = df[["MV","SA","HG","IG","RT"]].sum(axis=1)
df["OVIS_pct"] = (df["OVIS_raw"]/10*100).round(1)
df = df.sort_values("OVIS_pct", ascending=False).reset_index(drop=True)
df.insert(0,"rank", df.index+1)

pd.set_option("display.width",140)
print(df[["rank","source_id","name","MV","SA","HG","IG","RT","OVIS_raw","OVIS_pct","metric_design"]].to_string(index=False))

df.to_csv("ovis_scored_table.csv", index=False)

# ---- headline stat: metric-design category vs mean MV subscore ----
outcome_only = df[df.metric_design=="outcome-only"]
process_aware = df[df.metric_design.isin(["process-aware","process-aware-unpublished"])]
audited_outcome = df[df.metric_design=="outcome-only-but-audited"]

def summarize(group,label):
    if len(group)==0: return
    print(f"\n--- {label} (n={len(group)}) ---")
    print(f"  mean MV subscore: {group.MV.mean():.2f}/2  ({group.MV.mean()/2*100:.1f}% method-validated)")
    print(f"  mean OVIS: {group.OVIS_pct.mean():.1f}%")
    print(f"  sources: {', '.join(group.source_id)}")

summarize(outcome_only, "Outcome-only metric design (binary-flag / MCQ / pass@1)")
summarize(process_aware, "Process-aware metric design (tiered / process-reward / functional-patch / adversarial-validated)")
summarize(audited_outcome, "Outcome-only design RESCUED by post-hoc manual audit")

print(f"\nOverall corpus: n={len(df)}, mean OVIS={df.OVIS_pct.mean():.1f}%, std={df.OVIS_pct.std():.1f}, "
      f"min={df.OVIS_pct.min():.1f}%, max={df.OVIS_pct.max():.1f}%")

stats = {
    "n_scored": int(len(df)),
    "n_insufficient_evidence_excluded": 11,
    "overall_mean_ovis_pct": round(float(df.OVIS_pct.mean()),1),
    "overall_std_ovis_pct": round(float(df.OVIS_pct.std()),1),
    "outcome_only_mean_MV_pct": round(float(outcome_only.MV.mean()/2*100),1) if len(outcome_only) else None,
    "process_aware_mean_MV_pct": round(float(process_aware.MV.mean()/2*100),1) if len(process_aware) else None,
    "outcome_only_mean_OVIS_pct": round(float(outcome_only.OVIS_pct.mean()),1) if len(outcome_only) else None,
    "process_aware_mean_OVIS_pct": round(float(process_aware.OVIS_pct.mean()),1) if len(process_aware) else None,
    "n_outcome_only": int(len(outcome_only)),
    "n_process_aware": int(len(process_aware)),
    "n_audited_outcome": int(len(audited_outcome)),
}
with open("ovis_summary_stats.json","w") as f:
    json.dump(stats, f, indent=2)
print("\n", json.dumps(stats, indent=2))
