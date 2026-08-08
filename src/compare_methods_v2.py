"""
compare_methods_v2.py
Direct comparison: Vianna Filho et al. (2026) vs Our Proposal

Fixes applied:
  FIX-1: CancellationRate — separate cancellations BEFORE filtering Qty>0/Price>0
  FIX-2: G' edge weight  — multiply by count_i * count_j (per VF2026 Procedure 1)
  FIX-3: Louvain         — run ONCE outside k loop; merge smallest for fair k comparison
  FIX-4: Cross-space     — each method evaluated on own space (clearly labeled) AND
                           all labels also evaluated on common 3D-RFM reference space
  FIX-5: Path handling   — explicit error if .xlsx not found; warn if multiple files
"""

import warnings, os, sys, glob

# Windows consoles default to cp1252, which cannot encode the box-drawing and arrow
# characters used in the progress output; without this the script dies with
# UnicodeEncodeError partway through and writes no results.
import sys
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import networkx as nx
import community as community_louvain
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                              calinski_harabasz_score)

SEED = 42
np.random.seed(SEED)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.environ.get("LRFM_OUT_DIR", os.path.join(ROOT, "results"))
os.makedirs(OUT, exist_ok=True)

print("=" * 70)
print("METHOD COMPARISON v2 — Vianna Filho (2026) vs Our Proposal")
print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# FIX-5: Safe file loading
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = os.environ.get("LRFM_DATA_DIR", os.path.join(ROOT, "data"))
xlsx_files = glob.glob(os.path.join(DATA_DIR, "online_retail*.xlsx"))
if not xlsx_files:
    xlsx_files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
if not xlsx_files:
    sys.exit("[ERROR] No .xlsx file found in " + DATA_DIR)
if len(xlsx_files) > 1:
    print(f"[WARN] Multiple .xlsx files found, using: {os.path.basename(xlsx_files[0])}")
xlsx = xlsx_files[0]
print(f"\n[1] Loading: {os.path.basename(xlsx)}")

sheets = pd.read_excel(xlsx, sheet_name=None, engine="openpyxl")
df_raw = pd.concat(sheets.values(), ignore_index=True)
df_raw.columns = [c.replace(" ", "") for c in df_raw.columns]
df_raw["InvoiceDate"] = pd.to_datetime(df_raw["InvoiceDate"])
df_raw = df_raw.dropna(subset=["CustomerID"])

# ─────────────────────────────────────────────────────────────────────────────
# FIX-1: Separate cancellations BEFORE filtering Quantity/Price
# ─────────────────────────────────────────────────────────────────────────────
df_raw["IsCancelled"] = df_raw["Invoice"].astype(str).str.startswith("C")
df_cancel = df_raw[df_raw["IsCancelled"]].copy()           # keep for CancellationRate
df_main   = df_raw[
    (~df_raw["IsCancelled"]) &
    (df_raw["Quantity"] > 0) &
    (df_raw["Price"]    > 0)
].copy()
df_main = df_main.drop_duplicates()
df_main["TotalPrice"] = df_main["Quantity"] * df_main["Price"]

ANALYSIS_DATE = df_main["InvoiceDate"].max() + pd.Timedelta(days=1)
grp = df_main.groupby("CustomerID")

print(f"  Total customers:       {df_main['CustomerID'].nunique():,}")
print(f"  Cancellation records:  {len(df_cancel):,}")

# ─────────────────────────────────────────────────────────────────────────────
# Feature engineering
# ─────────────────────────────────────────────────────────────────────────────
R_raw = (ANALYSIS_DATE - grp["InvoiceDate"].max()).dt.days
F_raw = grp["Invoice"].nunique()
M_raw = grp["TotalPrice"].sum()
L_raw = (ANALYSIS_DATE - grp["InvoiceDate"].min()).dt.days
AOV   = (M_raw / F_raw)
basket = (df_main.groupby(["CustomerID","Invoice"])["StockCode"].nunique()
                .groupby("CustomerID").mean())
div    = grp["StockCode"].nunique()

# CancellationRate — correct: use df_cancel (not filtered df_main)
cancel_cnt = (df_cancel[df_cancel["CustomerID"].isin(grp.groups)]
              .groupby("CustomerID")["Invoice"].nunique())
# CancellationRate = cancels / (cancels + normals) → always in [0, 1]
cancel_rate = (cancel_cnt / (cancel_cnt + F_raw)).fillna(0)

# Verify: max must be <= 1.0 and distribution must be meaningful
n_nonzero = (cancel_rate > 0).sum()
cr_max    = cancel_rate.max()
print(f"  Customers with CancellationRate > 0: {n_nonzero:,} "
      f"({n_nonzero/len(cancel_rate)*100:.1f}%)  max={cr_max:.3f}  [FIX-1 check, must be ≤1.0]")

# FIX-6: Compute IPT on invoice-level dates (one date per invoice, not per item)
# One customer may have 10 items in one invoice → all same InvoiceDate → unique() was OK
# but if two invoices on same day, unique() collapses them → invoice-level is more precise
inv_dates_df = (df_main
                .groupby(["CustomerID", "Invoice"])["InvoiceDate"]
                .first()
                .reset_index())

def avg_ipt_invoice(dates_series):
    """FIX-6+7: invoice-level IPT; NaN for single purchasers (not 0)."""
    sorted_dates = dates_series.sort_values().values
    if len(sorted_dates) < 2:
        return np.nan           # FIX-7: undefined, not 0 (0 would mean "buys every day")
    gaps = np.diff(sorted_dates).astype("timedelta64[D]").astype(float)
    return float(gaps.mean())

ipt_raw = inv_dates_df.groupby("CustomerID")["InvoiceDate"].apply(avg_ipt_invoice)

# FIX-7: Impute single-purchase customers with population median (neutral estimate)
ipt_median = ipt_raw.median()
ipt = ipt_raw.fillna(ipt_median)
print(f"  IPT: {(ipt_raw.isna()).sum()} single-purchasers imputed with median={ipt_median:.1f} days")

feat = pd.concat([
    L_raw.rename("L"), R_raw.rename("R"), F_raw.rename("F"), M_raw.rename("M"),
    AOV.rename("AOV"), basket.rename("BasketSize"),
    div.rename("ProductDiversity"), cancel_rate.rename("CancellationRate"),
    ipt.rename("InterpurchaseTime")
], axis=1).fillna(0)

n_customers = len(feat)

# ─────────────────────────────────────────────────────────────────────────────
# Feature matrices
# ─────────────────────────────────────────────────────────────────────────────
sc = StandardScaler()

X_rfm_raw   = sc.fit_transform(feat[["R","F","M"]].values)          # 3D continuous
X_lrfm      = sc.fit_transform(feat[["L","R","F","M"]].values)       # 4D continuous
X_blrfm     = sc.fit_transform(feat[["L","R","F","M","AOV","BasketSize",
                                      "ProductDiversity","CancellationRate",
                                      "InterpurchaseTime"]].values)   # 9D continuous

# VF2026: RFM quintile scores 1–5
def score_quintile(series, invert=False):
    """
    FIX-5: Use pd.qcut on raw values (not rank(method='first')).
    rank('first') breaks ties arbitrarily by row order → same value = different score.
    pd.qcut on values with duplicates='drop' gives tied values the SAME bin → stable.
    """
    labels = [5,4,3,2,1] if invert else [1,2,3,4,5]
    try:
        return pd.qcut(series, q=5, labels=labels, duplicates="drop").astype(int)
    except Exception:
        # Fallback if too many ties to form 5 bins: use rank-based with average
        try:
            return pd.qcut(series.rank(method="average"), q=5,
                           labels=labels, duplicates="drop").astype(int)
        except Exception:
            return pd.Series(3, index=series.index)

R_sc = score_quintile(feat["R"], invert=True)
F_sc = score_quintile(feat["F"], invert=False)
M_sc = score_quintile(feat["M"], invert=False)
rfm_scores = pd.DataFrame({"R":R_sc,"F":F_sc,"M":M_sc}).fillna(3).astype(int)
X_scores   = rfm_scores.values.astype(float)          # 3D discrete 1-5

# ── Common reference space (FIX-4): standardized 3D RFM ──────────────────
# All cluster labels will be re-evaluated on this common space
# so that Silhouette numbers become directly comparable.
X_common = X_rfm_raw     # standardized continuous R, F, M
print("\n  Feature spaces summary:")
print(f"    X_scores  (VF2026): discrete 1–5, 3 dims, range [{X_scores.min():.0f},{X_scores.max():.0f}]")
print(f"    X_rfm_raw (Ours):   continuous standardized, 3 dims")
print(f"    X_lrfm    (Ours):   continuous standardized, 4 dims")
print(f"    X_blrfm   (Ours):   continuous standardized, 9 dims")
print(f"    X_common  (ref):    = X_rfm_raw — used for cross-method fair comparison")

# ─────────────────────────────────────────────────────────────────────────────
# FIX-2: Build G' with correct edge weights (count_i × count_j × distance)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2] Building VF2026 graph G' (FIX-2: weighted by customer counts)...")

score_arr               = rfm_scores[["R","F","M"]].values
unique_scores, inverse  = np.unique(score_arr, axis=0, return_inverse=True)
n_prime                 = len(unique_scores)

# Count customers in each unique score group
score_counts = np.bincount(inverse)   # score_counts[i] = # customers with score unique_scores[i]

print(f"  G  (original): {n_customers:,} nodes")
print(f"  G' (reduced):  {n_prime} score-groups  (max 5^3=125)")
print(f"  Customer counts per score group: min={score_counts.min()}  "
      f"max={score_counts.max()}  mean={score_counts.mean():.1f}")

G_prime = nx.Graph()
G_prime.add_nodes_from(range(n_prime))
for i in range(n_prime):
    for j in range(i+1, n_prime):
        dist = int(abs(unique_scores[i,0]-unique_scores[j,0]) +
                   abs(unique_scores[i,1]-unique_scores[j,1]) +
                   abs(unique_scores[i,2]-unique_scores[j,2]))
        if dist > 0:
            # FIX-2: weight = count_i * count_j * distance (per VF2026 Procedure 1)
            w = int(score_counts[i] * score_counts[j] * dist)
            G_prime.add_edge(i, j, weight=w)

print(f"  G' edges: {G_prime.number_of_edges()}")

# Max-k-cut local search (on G')
def max_k_cut_local_search(G, k, n_restarts=8, max_iter=400):
    nodes = list(G.nodes())
    adj   = {v:{} for v in nodes}
    for u,v,d in G.edges(data=True):
        adj[u][v] = d.get("weight",1)
        adj[v][u] = d.get("weight",1)

    def objective(labels):
        return sum(d.get("weight",1)
                   for u,v,d in G.edges(data=True) if labels[u]!=labels[v])

    best_obj, best_labels = -np.inf, None
    for _ in range(n_restarts):
        labels = {v: np.random.randint(0,k) for v in nodes}
        improved, it = True, 0
        while improved and it < max_iter:
            improved = False; it += 1
            for v in np.random.permutation(nodes):
                cur  = sum(adj[v].get(u,0) for u in adj[v] if labels[u]!=labels[v])
                best_g, best_c = cur, labels[v]
                for c in range(k):
                    if c == labels[v]: continue
                    g = sum(adj[v].get(u,0) for u in adj[v] if labels[u]!=c)
                    if g > best_g: best_g, best_c = g, c
                if best_c != labels[v]:
                    labels[v] = best_c; improved = True
        obj = objective(labels)
        if obj > best_obj: best_obj, best_labels = obj, labels.copy()
    full = np.array([best_labels[inverse[i]] for i in range(n_customers)])
    return full, best_obj

# ─────────────────────────────────────────────────────────────────────────────
# FIX-3: Louvain — run ONCE, then merge to match each k
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3] Running Louvain ONCE (FIX-3), then merging to k=2..6...")

nn_g = NearestNeighbors(n_neighbors=11, metric="euclidean")
nn_g.fit(X_blrfm)
dists_g, idxs_g = nn_g.kneighbors(X_blrfm)

G_ours = nx.Graph()
G_ours.add_nodes_from(range(n_customers))
for i in range(n_customers):
    for jj in range(1, 11):
        j = idxs_g[i,jj]
        w = 1.0 / (1.0 + dists_g[i,jj])
        if not G_ours.has_edge(i,j):
            G_ours.add_edge(i, j, weight=w)

partition_full = community_louvain.best_partition(
    G_ours, weight="weight", random_state=SEED)
louvain_labels_full = np.array([partition_full[i] for i in range(n_customers)])
n_louvain = len(set(louvain_labels_full))
print(f"  Louvain found {n_louvain} communities (auto-k)")

def merge_to_k(labels, k):
    """Merge smallest communities iteratively until exactly k communities remain."""
    labels = labels.copy()
    while len(set(labels)) > k:
        unique, counts = np.unique(labels, return_counts=True)
        if len(unique) <= k:
            break
        # Find the two smallest communities and merge them
        sorted_idx = np.argsort(counts)
        smallest   = unique[sorted_idx[0]]
        second     = unique[sorted_idx[1]]
        labels[labels == smallest] = second
    # Remap to 0..k-1
    mapping = {v: i for i, v in enumerate(np.unique(labels))}
    return np.array([mapping[v] for v in labels])

# Pre-compute Louvain labels merged to each k
louvain_at_k = {}
for k_target in [2, 3, 4, 5, 6]:
    if n_louvain >= k_target:
        louvain_at_k[k_target] = merge_to_k(louvain_labels_full, k_target)
    else:
        louvain_at_k[k_target] = louvain_labels_full.copy()
    n_actual = len(set(louvain_at_k[k_target]))
    print(f"  Louvain merged to k={k_target}: actual communities = {n_actual}")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP: k = 2..6
# FIX-4: Each method evaluated on (a) its OWN feature space
#         AND (b) common 3D-RFM reference space
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4] Running all methods k=2..6 ...")
print("    Each method evaluated on OWN space AND common 3D-RFM space")

K_RANGE = [2, 3, 4, 5, 6]
results  = []

def eval_labels(labels, own_X, common_X, method_name, k, space_own_name):
    """Evaluate labels on own space and common reference space."""
    n_actual = len(set(labels))
    if n_actual < 2:
        return

    # (a) Own feature space
    sil_own = silhouette_score(own_X, labels)
    dbi_own = davies_bouldin_score(own_X, labels)
    chi_own = calinski_harabasz_score(own_X, labels)

    # (b) Common 3D-RFM reference space (FIX-4)
    sil_ref = silhouette_score(common_X, labels)
    dbi_ref = davies_bouldin_score(common_X, labels)
    chi_ref = calinski_harabasz_score(common_X, labels)

    results.append({
        "k":          k,
        "Method":     method_name,
        "OwnSpace":   space_own_name,
        # Own space metrics — NOT directly comparable across methods
        "Sil_own":    round(sil_own, 4),
        "DBI_own":    round(dbi_own, 4),
        "CHI_own":    round(chi_own, 1),
        # Common space metrics — DIRECTLY COMPARABLE across methods
        "Sil_ref":    round(sil_ref, 4),
        "DBI_ref":    round(dbi_ref, 4),
        "CHI_ref":    round(chi_ref, 1),
    })
    return sil_own, sil_ref

for k in K_RANGE:
    print(f"\n  k={k}")

    # ── A1: VF2026 K-means on RFM scores ──────────────────────────────────
    lbl = KMeans(n_clusters=k, random_state=SEED, n_init=20).fit_predict(X_scores)
    r = eval_labels(lbl, X_scores, X_common,
                    "[VF2026] K-means (score 1-5)", k, "3D-score-1-5")
    if r: print(f"    VF K-means (scores):     Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}")

    # ── A2: VF2026 Max-k-cut approx ───────────────────────────────────────
    lbl, obj = max_k_cut_local_search(G_prime, k, n_restarts=5, max_iter=300)
    k_actual = len(set(lbl))
    # FIX-8: check actual cluster count; report degeneracy if k_actual != k
    if k_actual >= 2:
        note = "" if k_actual == k else f"  [WARN: got {k_actual} clusters, not {k}]"
        r = eval_labels(lbl, X_scores, X_common,
                        "[VF2026] Max-k-cut approx", k, "3D-score-1-5")
        if r: print(f"    VF Max-k-cut (approx):   Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}  Obj={obj:.0f}{note}")

    # ── A3: VF2026 GMM on RFM scores ──────────────────────────────────────
    lbl = GaussianMixture(n_components=k, random_state=SEED, n_init=5).fit_predict(X_scores)
    if len(set(lbl)) >= 2:
        r = eval_labels(lbl, X_scores, X_common,
                        "[VF2026] GMM (score 1-5)", k, "3D-score-1-5")
        if r: print(f"    VF GMM (scores):         Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}")

    # ── B1: Ours K-means raw RFM ──────────────────────────────────────────
    lbl = KMeans(n_clusters=k, random_state=SEED, n_init=20).fit_predict(X_rfm_raw)
    r = eval_labels(lbl, X_rfm_raw, X_common,
                    "[Ours] K-means raw RFM", k, "3D-continuous")
    if r: print(f"    Ours K-means (raw RFM):  Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}")

    # ── B2: Ours K-means LRFM ─────────────────────────────────────────────
    lbl = KMeans(n_clusters=k, random_state=SEED, n_init=20).fit_predict(X_lrfm)
    r = eval_labels(lbl, X_lrfm, X_common,
                    "[Ours] K-means LRFM", k, "4D-continuous")
    if r: print(f"    Ours K-means (LRFM):     Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}")

    # ── B3: Ours K-means B-LRFM ───────────────────────────────────────────
    lbl = KMeans(n_clusters=k, random_state=SEED, n_init=20).fit_predict(X_blrfm)
    r = eval_labels(lbl, X_blrfm, X_common,
                    "[Ours] K-means B-LRFM", k, "9D-continuous")
    if r: print(f"    Ours K-means (B-LRFM):   Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}")

    # ── B4: Ours Louvain (merged to k) ────────────────────────────────────
    lbl = louvain_at_k[k]
    if len(set(lbl)) >= 2:
        r = eval_labels(lbl, X_blrfm, X_common,
                        "[Ours] Louvain B-LRFM", k, "9D-continuous")
        if r: print(f"    Ours Louvain (B-LRFM):   Sil_own={r[0]:.4f}  Sil_ref={r[1]:.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY TABLES
# ─────────────────────────────────────────────────────────────────────────────
df_res = pd.DataFrame(results)

print("\n" + "=" * 70)
print("RESULTS — TWO TABLES (FIX-4)")
print("=" * 70)

# ── Table A: Own-space Silhouette (NOT cross-comparable) ──────────────────
print("""
╔══════════════════════════════════════════════════════════════════════╗
║  TABLE A: Silhouette on OWN feature space                           ║
║  ⚠ Numbers NOT directly comparable across rows (different spaces)   ║
╚══════════════════════════════════════════════════════════════════════╝""")

tA = df_res.pivot_table(index=["Method","OwnSpace"], columns="k",
                         values="Sil_own", aggfunc="first")
print(tA.to_string())

# ── Table B: Common-space Silhouette (DIRECTLY comparable) ───────────────
print("""
╔══════════════════════════════════════════════════════════════════════╗
║  TABLE B: Silhouette on COMMON 3D standardized RFM space            ║
║  ✅ Numbers ARE directly comparable across all methods               ║
║  (all labels re-evaluated on same X = standardized R,F,M)           ║
╚══════════════════════════════════════════════════════════════════════╝""")

tB = df_res.pivot_table(index="Method", columns="k",
                         values="Sil_ref", aggfunc="first")
# Sort by mean Silhouette_ref
tB["mean"] = tB.mean(axis=1)
tB = tB.sort_values("mean", ascending=False).drop(columns="mean")
print(tB.to_string())

# ── Paper reference values ────────────────────────────────────────────────
print("\nPaper reference (Vianna Filho 2026, exact max-k-cut):")
ref = pd.DataFrame({
    "k":        [2,     3,     4,     5,     6    ],
    "Sil(paper)":[0.4569,0.3545,0.3980,0.3542,0.2900],
})
print(ref.to_string(index=False))
print("(Paper uses own score-space evaluation — comparable with Table A VF rows)")

# ── At k=4: clear ranking ────────────────────────────────────────────────
print("\nAt k=4 — Fair ranking on COMMON space (Sil_ref):")
k4 = df_res[df_res["k"]==4][["Method","OwnSpace","Sil_own","Sil_ref"]].copy()
k4 = k4.sort_values("Sil_ref", ascending=False)
print(k4.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# PLOT
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

methods_cfg = [
    ("[VF2026] Max-k-cut approx",  "red",    "o-",  "VF2026 Max-k-cut approx"),
    ("[VF2026] K-means (score 1-5)","blue",  "^--", "VF2026 K-means (scores)"),
    ("[Ours] K-means raw RFM",     "purple", "D-",  "Ours K-means raw RFM"),
    ("[Ours] K-means LRFM",        "orange", "s-",  "Ours K-means LRFM"),
    ("[Ours] K-means B-LRFM",      "brown",  "P-",  "Ours K-means B-LRFM"),
    ("[Ours] Louvain B-LRFM",      "green",  "h--", "Ours Louvain B-LRFM"),
]

# Left: Own-space (with explicit disclaimer)
ax = axes[0]
for mth, col, sty, lbl in methods_cfg:
    sub = df_res[df_res["Method"]==mth].sort_values("k")
    if len(sub):
        ax.plot(sub["k"], sub["Sil_own"], sty, color=col,
                label=lbl, linewidth=1.8, markersize=7)
ax.plot([2,3,4,5,6], [0.4569,0.3545,0.3980,0.3542,0.2900],
        "r*-", lw=2.5, ms=10, label="VF2026 max-k-cut EXACT (paper)")
ax.set_title("Silhouette — OWN space\n⚠ NOT cross-comparable (different spaces)",
             fontsize=10)
ax.set_xlabel("k"); ax.set_ylabel("Silhouette (own space)")
ax.legend(fontsize=7); ax.grid(alpha=0.3); ax.set_xticks(K_RANGE)

# Right: Common-space (fair comparison)
ax2 = axes[1]
for mth, col, sty, lbl in methods_cfg:
    sub = df_res[df_res["Method"]==mth].sort_values("k")
    if len(sub):
        ax2.plot(sub["k"], sub["Sil_ref"], sty, color=col,
                 label=lbl, linewidth=1.8, markersize=7)
ax2.set_title("Silhouette — COMMON 3D-RFM space\n✅ Fair cross-method comparison",
              fontsize=10)
ax2.set_xlabel("k"); ax2.set_ylabel("Silhouette (common space)")
ax2.legend(fontsize=7); ax2.grid(alpha=0.3); ax2.set_xticks(K_RANGE)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "comparison_v2.png"), dpi=150)
plt.close()
print(f"\n[OUTPUT] results/comparison_v2.png")

df_res.to_csv(os.path.join(OUT, "comparison_v2.csv"), index=False)
print(f"[OUTPUT] results/comparison_v2.csv")
print("\nDone.")
