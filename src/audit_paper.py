"""Audit the manuscript: layout overflows from the log, and every reported number
cross-checked against the result files it claims to come from."""
import io
import os
import re

BASE = (r"d:\DAP\lrfm-max-k-cut-segmentation-main (2)\lrfm-max-k-cut-segmentation-main"
        r"\LRFM Churn PREDICT")
PAPER = os.path.join(BASE, "paper")
RES = os.path.join(BASE, "results")
BS = chr(92)

log = io.open(os.path.join(PAPER, "main.log"), encoding="utf8", errors="ignore").read()
tex = io.open(os.path.join(PAPER, "main.tex"), encoding="utf8").read()

print("=" * 72)
print("A. LAYOUT — overfull / underfull boxes (these never appear as 'LaTeX Warning')")
print("=" * 72)
pat_over = re.compile(r"Overfull " + re.escape(BS) + r"([hv])box \(([\d.]+)pt too (?:wide|high)\)"
                      r"[^\n]*\n((?:[^\n]*\n){0,2})")
hits = list(pat_over.finditer(log))
over_h = [m for m in hits if m.group(1) == "h"]
print(f"Overfull hbox : {len(over_h)}")
print(f"Overfull vbox : {len([m for m in hits if m.group(1) == 'v'])}")
print(f"Underfull hbox: {len(re.findall('Underfull ' + re.escape(BS) + 'hbox', log))}")
print(f"LaTeX Warning : {len(re.findall('LaTeX Warning:', log))}")
print()
for m in sorted(over_h, key=lambda m: -float(m.group(2))):
    ctx = m.group(3).replace("\n", " ")[:88].strip()
    print(f"  {float(m.group(2)):7.1f}pt too wide  |  {ctx}")

print()
print("=" * 72)
print("B. NUMBERS — every figure quoted in the paper vs its source file")
print("=" * 72)


def read_csv(name):
    import csv
    with io.open(os.path.join(RES, name), encoding="utf8") as fh:
        return list(csv.DictReader(fh))


checks = []


def check(label, claimed, actual, tol=5e-5):
    ok = abs(float(claimed) - float(actual)) <= tol
    checks.append((ok, label, claimed, actual))


# --- repeated-CV table (Table 1) and abstract, from significance_summary.csv ---
summ = {(r["Metric"], r["Model"], r["Tier"]): r for r in read_csv("significance_summary.csv")}
TABLE1 = {"RFM": ("0.8066", None, None), "LRFM": ("0.8074", "+0.0009", "0.755"),
          "B-LRFM": ("0.8054", "-0.0012", "0.742"),
          "B-LRFM+Seg": ("0.8044", "-0.0022", "0.561"),
          "Graph-Enhanced": ("0.8044", "-0.0021", "0.590")}
for tier, (mean, delta, p) in TABLE1.items():
    row = summ[("AUC", "LightGBM", tier)]
    check(f"Table 1 {tier} mean", mean, row["Mean"], tol=5e-5)
    if delta is not None:
        check(f"Table 1 {tier} delta", delta, row["Delta_vs_RFM"], tol=5e-5)
        check(f"Table 1 {tier} p_NB", p, row["p_NadeauBengio"], tol=5e-4)

# --- single-split table (Table 2), from churn_results_v2.csv ---
single = {r[""]: r for r in read_csv("churn_results_v2.csv")}
TABLE2 = {"RFM": ("0.8065", "0.8685", "0.7927", "0.7610"),
          "LRFM": ("0.8071", "0.8673", "0.8011", "0.7775"),
          "B-LRFM": ("0.8067", "0.8679", "0.8036", "0.7857"),
          "B-LRFM+Seg": ("0.8073", "0.8687", "0.8044", "0.7881"),
          "Graph-Enhanced (leak-free)": ("0.8098", "0.8689", "0.8108", "0.8009")}
for tier, vals in TABLE2.items():
    row = single[tier]
    for key, claimed in zip(["AUC", "PR_AUC", "F1", "Recall"], vals):
        check(f"Table 2 {tier} {key}", claimed, row[key], tol=5e-5)

# --- SHAP top-5 ---
shap = {r["Feature"]: r["Mean|SHAP|"] for r in read_csv("shap_global_v2.csv")}
for feat, claimed in [("R", "1.087"), ("M", "0.560"), ("NeighborChurnRate", "0.250"),
                      ("InterpurchaseTime", "0.224"), ("CommunityChurnRate", "0.215")]:
    check(f"SHAP {feat}", claimed, shap[feat], tol=5e-4)

# --- segment profiles ---
seg = {r["Louvain_Community"]: r for r in read_csv("segment_profiles_v2.csv")}
check("ERV community 0 N", "327", seg["0"]["N"], tol=0)
check("ERV community 0 churn", "0.82", seg["0"]["ChurnRate"], tol=5e-3)
check("ERV community 0 monetary", "2397", seg["0"]["AvgMonetary"], tol=0.5)
check("ERV community 0 ERV", "1348", seg["0"]["AvgERV"], tol=0.5)
check("ERV community 9 N", "418", seg["9"]["N"], tol=0)
check("ERV community 9 churn", "0.24", seg["9"]["ChurnRate"], tol=5e-3)
check("ERV community 9 monetary", "13916", seg["9"]["AvgMonetary"], tol=0.5)

# --- silhouette (comparison_v2.csv), k = 4 ---
comp = [r for r in read_csv("comparison_v2.csv") if r["k"] == "4"]
byname = {r["Method"]: r for r in comp}
check("Silhouette ours K-means B-LRFM", "0.219", byname["[Ours] K-means B-LRFM"]["Sil_own"], tol=5e-4)
check("Silhouette ours Louvain B-LRFM", "-0.050", byname["[Ours] Louvain B-LRFM"]["Sil_own"], tol=5e-4)

# --- k-NN sweep table: every row against its own run ---
SWEEP = {5: ("-0.0006", "0.880"), 10: ("-0.0021", "0.590"),
         15: ("+0.0017", "0.666"), 20: ("-0.0027", "0.500")}
for k, (delta, p) in SWEEP.items():
    rows_k = read_csv(f"significance_summary_k{k}.csv")
    row = next(r for r in rows_k if r["Metric"] == "AUC" and r["Model"] == "LightGBM"
               and r["Tier"] == "Graph-Enhanced")
    check(f"sweep k={k} delta", delta, row["Delta_vs_RFM"], tol=5e-5)
    check(f"sweep k={k} p_NB", p, row["p_NadeauBengio"], tol=5e-4)

# the paper argues the sign is unstable across k; verify that is actually true
signs = {k: float(next(r for r in read_csv(f"significance_summary_k{k}.csv")
                       if r["Metric"] == "AUC" and r["Model"] == "LightGBM"
                       and r["Tier"] == "Graph-Enhanced")["Delta_vs_RFM"]) > 0
         for k in SWEEP}
checks.append((len(set(signs.values())) == 2, "sweep sign is unstable across k",
               "mixed", "positive at k=15 only" if signs == {5: False, 10: False, 15: True, 20: False}
               else str(signs)))

# --- min p across the 16 tier comparisons (claim in Sect. 8.1) ---
ps = [float(r["p_NadeauBengio"]) for r in read_csv("significance_summary.csv")
      if r["Tier"] != "RFM" and r["p_NadeauBengio"]]
check("min p_NB over 16 tier comparisons", "0.144", min(ps), tol=5e-4)
if len(ps) != 16:
    checks.append((False, "count of tier comparisons", "16", str(len(ps))))
else:
    checks.append((True, "count of tier comparisons", "16", "16"))

bad = [c for c in checks if not c[0]]
print(f"checked {len(checks)} figures — {len(checks) - len(bad)} match, {len(bad)} MISMATCH")
print()
for ok, label, claimed, actual in checks:
    if not ok:
        print(f"  MISMATCH  {label:<42s} paper={claimed:>10s}  source={actual}")
if not bad:
    print("  every number in the manuscript matches its source file")

print()
print("=" * 72)
print("C. INTERNAL CONSISTENCY")
print("=" * 72)
for label, pattern, expect in [
    ("38-feature claim", r"38-feature", 2),
    ("1,067,371 raw rows", r"1\{,\}067\{,\}371", 1),
    ("5,038 customers", r"5\{,\}038", 4),
    ("65.2% churn", r"65\.2", 2),
    ("33,426 edges", r"33\{,\}426", 1),
]:
    n = len(re.findall(pattern, tex))
    print(f"  {label:<24s} appears {n}x   (expected ~{expect})")

nfeat = 9 + 4 + 23 + 2
print(f"\n  feature arithmetic: 9 B-LRFM + 4 static graph + 23 one-hot + 2 fold-local = {nfeat}")
print(f"  paper says 38 -> {'CONSISTENT' if nfeat == 38 else 'INCONSISTENT'}")

words = len(re.findall(r"[A-Za-z][A-Za-z'-]+", re.sub(r"\\[a-zA-Z]+", " ", tex)))
print(f"\n  approximate word count of main.tex prose: {words}")
