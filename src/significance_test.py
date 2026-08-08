"""
significance_test.py
Repeated-CV significance testing for the Graph-Enhanced Behavioral-LRFM ablation.

Why this exists
---------------
`run_pipeline_v2.py` reports a single 5-fold CV point estimate per feature tier
(e.g. RFM AUC 0.8065 -> Graph-Enhanced AUC 0.8098, a +0.0033 gap). A single
point estimate cannot tell whether a gap that small is a real effect or fold
noise. This script answers that question directly:

  * repeated stratified CV (N_REPEATS x N_SPLITS folds),
  * the SAME fold partition is reused by every tier inside a repeat, so the
    per-fold scores are properly PAIRED and deltas are meaningful,
  * three tests on the paired deltas vs the RFM baseline:
      - naive paired t-test          (anti-conservative for repeated CV),
      - Nadeau & Bengio (2003) corrected resampled t-test  <- the one to report,
      - Wilcoxon signed-rank         (distribution-free cross-check),
  * a bootstrap 95% CI on the mean delta.

Leakage handling is copied verbatim from run_pipeline_v2.py:
  FIX-A cancellations restricted to the observation window,
  FIX-B NeighborChurnRate / CommunityChurnRate recomputed per training fold,
  FIX-C StandardScaler inside an sklearn Pipeline,
  FIX-D one-hot encoded segment / community ids.

Feature construction is cached to <OUT>/feat_cache.parquet so only the first run
pays the ~4 min Excel read.

Usage:
    python src/significance_test.py
Environment overrides: LRFM_DATA_DIR, LRFM_OUT_DIR
"""

import warnings, os, glob

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

import numpy as np
import pandas as pd
from scipy import stats

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.base import clone
from sklearn.metrics import roc_auc_score, average_precision_score

import networkx as nx
import community as community_louvain
import lightgbm as lgb

SEED = 42
N_SPLITS = 5
# Graph degree. Default 10 reproduces the main results; the sensitivity sweep
# (src/knn_sweep.py) overrides it to test whether the conclusion depends on k.
KNN_K = int(os.environ.get("LRFM_KNN_K", "10"))
# Suffix keeps a sweep run from overwriting the headline result files.
OUT_SUFFIX = os.environ.get("LRFM_OUT_SUFFIX", "")
# CV partition seeds, one per repeat. Override to reproduce a specific published run,
# e.g. LRFM_CV_SEEDS=42 reproduces the single-split result of run_pipeline_v2.py.
_seed_env = os.environ.get("LRFM_CV_SEEDS", "")
CV_SEEDS = ([int(s) for s in _seed_env.split(",") if s.strip()]
            if _seed_env else [1000 + r for r in range(10)])
N_REPEATS = len(CV_SEEDS)
np.random.seed(SEED)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("LRFM_DATA_DIR", os.path.join(ROOT, "data"))
OUT = os.environ.get("LRFM_OUT_DIR", os.path.join(ROOT, "results"))
os.makedirs(OUT, exist_ok=True)
CACHE = os.path.join(OUT, "feat_cache.csv")  # csv, not parquet: no pyarrow dependency

print("=" * 72)
print(f"REPEATED-CV SIGNIFICANCE TEST  ({N_REPEATS} repeats x {N_SPLITS} folds "
      f"= {N_REPEATS * N_SPLITS} paired folds)")
print("=" * 72)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1-4 (cached): load, preprocess, engineer features, churn label
# ─────────────────────────────────────────────────────────────────────────────
def build_features():
    candidates = glob.glob(os.path.join(DATA_DIR, "online_retail*.xlsx")) \
        or glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
    if not candidates:
        raise SystemExit(f"[ERROR] No .xlsx file found in {DATA_DIR}")
    xlsx_path = candidates[0]
    print(f"\n[1] Reading {os.path.basename(xlsx_path)} (slow, cached afterwards)...")

    df_list = [pd.read_excel(xlsx_path, sheet_name=s, engine="openpyxl")
               for s in pd.ExcelFile(xlsx_path).sheet_names]
    df_raw = pd.concat(df_list, ignore_index=True)
    df_raw.columns = [c.replace(" ", "") for c in df_raw.columns]
    df_raw["InvoiceDate"] = pd.to_datetime(df_raw["InvoiceDate"])
    df_raw = df_raw.dropna(subset=["CustomerID"])

    df_raw["IsCancelled"] = df_raw["Invoice"].astype(str).str.startswith("C")
    df_cancel_all = df_raw[df_raw["IsCancelled"]].copy()
    df_main = df_raw[(~df_raw["IsCancelled"]) &
                     (df_raw["Quantity"] > 0) &
                     (df_raw["Price"] > 0)].copy()
    df_main = df_main.drop_duplicates()
    df_main["TotalPrice"] = df_main["Quantity"] * df_main["Price"]

    OBS_END = pd.Timestamp("2011-06-30")
    PRED_END = pd.Timestamp("2011-09-30")
    ANALYSIS_DATE = OBS_END + pd.Timedelta(days=1)

    df_obs = df_main[df_main["InvoiceDate"] <= OBS_END]
    df_pred = df_main[(df_main["InvoiceDate"] > OBS_END) &
                      (df_main["InvoiceDate"] <= PRED_END)]
    df_cancel_obs = df_cancel_all[df_cancel_all["InvoiceDate"] <= OBS_END]  # FIX-A
    obs_customers = set(df_obs["CustomerID"].unique())

    grp = df_obs.groupby("CustomerID")
    recency = (ANALYSIS_DATE - grp["InvoiceDate"].max()).dt.days.rename("R")
    frequency = grp["Invoice"].nunique().rename("F")
    monetary = grp["TotalPrice"].sum().rename("M")
    length = (ANALYSIS_DATE - grp["InvoiceDate"].min()).dt.days.rename("L")
    aov = (monetary / frequency).rename("AOV")
    basket = (df_obs.groupby(["CustomerID", "Invoice"])["StockCode"].nunique()
              .groupby("CustomerID").mean()).rename("BasketSize")
    diversity = grp["StockCode"].nunique().rename("ProductDiversity")

    cancel_cnt = (df_cancel_obs[df_cancel_obs["CustomerID"].isin(obs_customers)]
                  .groupby("CustomerID")["Invoice"].nunique())
    cancel_rate = (cancel_cnt / (cancel_cnt + frequency)).fillna(0).rename("CancellationRate")

    inv_dates = (df_obs.groupby(["CustomerID", "Invoice"])["InvoiceDate"]
                 .first().reset_index())

    def avg_ipt(s):
        d = s.sort_values().values
        if len(d) < 2:
            return np.nan
        return float(np.diff(d).astype("timedelta64[D]").astype(float).mean())

    ipt_raw = inv_dates.groupby("CustomerID")["InvoiceDate"].apply(avg_ipt)
    ipt = ipt_raw.fillna(ipt_raw.median()).rename("InterpurchaseTime")

    feat = pd.concat([length, recency, frequency, monetary, aov,
                      basket, diversity, cancel_rate, ipt], axis=1).fillna(0)
    feat.index.name = "CustomerID"

    active_in_pred = set(df_pred["CustomerID"].unique())
    feat["Churn"] = feat.index.map(lambda c: 0 if c in active_in_pred else 1)
    return feat


if os.path.exists(CACHE):
    feat = pd.read_csv(CACHE, index_col="CustomerID")
    print(f"\n[1] Loaded cached features: {CACHE}")
else:
    feat = build_features()
    feat.to_csv(CACHE)
    print(f"\n[1] Features cached to {CACHE}")

n = len(feat)
y = feat["Churn"].values
print(f"    Customers: {n:,}  |  Churn rate: {y.mean() * 100:.1f}%")

rfm_cols = ["R", "F", "M"]
lrfm_cols = ["L", "R", "F", "M"]
blrfm_cols = ["L", "R", "F", "M", "AOV", "BasketSize",
              "ProductDiversity", "CancellationRate", "InterpurchaseTime"]

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5-9: graph, communities, static graph features, one-hot ids
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2] Rebuilding k-NN graph + Louvain communities (deterministic, SEED=42)...")
X_blrfm = StandardScaler().fit_transform(feat[blrfm_cols])
feat["KMeans_Seg"] = KMeans(n_clusters=5, random_state=SEED, n_init=10).fit_predict(X_blrfm)

nn = NearestNeighbors(n_neighbors=KNN_K + 1, metric="euclidean").fit(X_blrfm)
distances, indices = nn.kneighbors(X_blrfm)

G = nx.Graph()
G.add_nodes_from(range(n))
neighbor_dict = {i: [] for i in range(n)}
for i in range(n):
    for jj in range(1, KNN_K + 1):
        j = indices[i, jj]
        if not G.has_edge(i, j):
            G.add_edge(i, j, weight=1.0 / (1.0 + distances[i, jj]))
        neighbor_dict[i].append(j)

partition_lou = community_louvain.best_partition(G, weight="weight", random_state=SEED)
louvain_arr = np.array([partition_lou[i] for i in range(n)])
feat["Louvain_Community"] = louvain_arr
print(f"    Nodes: {G.number_of_nodes():,}  Edges: {G.number_of_edges():,}  "
      f"Louvain communities: {len(set(louvain_arr))}")

feat["Degree"] = [G.degree(i) for i in range(n)]
feat["WeightedDeg"] = [G.degree(i, weight="weight") for i in range(n)]
feat["PageRank"] = list(nx.pagerank(G, weight="weight").values())
feat["ClustCoeff"] = list(nx.clustering(G, weight="weight").values())
static_graph_cols = ["Degree", "WeightedDeg", "PageRank", "ClustCoeff"]

kmeans_oh = pd.get_dummies(feat["KMeans_Seg"], prefix="KM", drop_first=True)
louvain_oh = pd.get_dummies(feat["Louvain_Community"], prefix="LV", drop_first=True)
feat = pd.concat([feat, kmeans_oh, louvain_oh], axis=1)
oh_cols = list(kmeans_oh.columns) + list(louvain_oh.columns)

TIERS = {
    "RFM": dict(cols=rfm_cols, graph=False),
    "LRFM": dict(cols=lrfm_cols, graph=False),
    "B-LRFM": dict(cols=blrfm_cols, graph=False),
    "B-LRFM+Seg": dict(cols=blrfm_cols + oh_cols, graph=False),
    "Graph-Enhanced": dict(cols=blrfm_cols + static_graph_cols + oh_cols, graph=True),
}
BASELINE_TIER = "RFM"

churn_rate = y.mean()
MODELS = {
    "LightGBM": lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, max_depth=6,
                                   random_state=SEED, is_unbalance=True, verbose=-1),
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=SEED,
                                              class_weight="balanced"),
}


def fold_features(cols, use_graph, train_idx):
    """Build the fold's design matrix. FIX-B: NCR/CCR use TRAINING labels only."""
    X = feat[cols].values.astype(float)
    if not use_graph:
        return X
    train_set = set(train_idx.tolist())
    train_mean = y[train_idx].mean()

    ncr = np.empty(n)
    for i in range(n):
        nbrs = [nb for nb in neighbor_dict[i] if nb in train_set]
        ncr[i] = np.mean([y[nb] for nb in nbrs]) if nbrs else train_mean

    ccr = np.empty(n)
    in_train = np.zeros(n, dtype=bool)
    in_train[train_idx] = True
    for comm in np.unique(louvain_arr):
        in_comm = louvain_arr == comm
        m = in_comm & in_train
        ccr[in_comm] = y[m].mean() if m.sum() > 0 else train_mean
    return np.column_stack([X, ncr, ccr])


# ─────────────────────────────────────────────────────────────────────────────
# Repeated CV — identical fold partition shared by every tier inside a repeat
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[3] Running {N_REPEATS} x {N_SPLITS}-fold CV over "
      f"{len(TIERS)} tiers x {len(MODELS)} models...")

rows = []
for rep, cv_seed in enumerate(CV_SEEDS):
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=cv_seed)
    for fold, (tr, va) in enumerate(cv.split(feat, y)):
        for tier, cfg in TIERS.items():
            X = fold_features(cfg["cols"], cfg["graph"], tr)
            for mname, proto in MODELS.items():
                pipe = Pipeline([("sc", StandardScaler()), ("clf", clone(proto))])
                pipe.fit(X[tr], y[tr])
                p = pipe.predict_proba(X[va])[:, 1]
                rows.append({
                    "Repeat": rep, "Fold": fold, "FoldId": rep * N_SPLITS + fold,
                    "Tier": tier, "Model": mname,
                    "AUC": roc_auc_score(y[va], p),
                    "PR_AUC": average_precision_score(y[va], p),
                })
    print(f"    repeat {rep + 1}/{N_REPEATS} done")

df = pd.DataFrame(rows)
folds_path = os.path.join(OUT, f"significance_folds{OUT_SUFFIX}.csv")
df.to_csv(folds_path, index=False)
print(f"\n    Per-fold scores -> {folds_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Statistics on the paired deltas
# ─────────────────────────────────────────────────────────────────────────────
def nadeau_bengio_t(d, n_splits):
    """Corrected resampled t-test (Nadeau & Bengio 2003).

    Repeated-CV folds overlap heavily, so the naive t-test underestimates the
    variance of the mean delta. The correction inflates it by
    (1/J + n_test/n_train); for k-fold, n_test/n_train = 1/(k-1).
    """
    d = np.asarray(d, dtype=float)
    J = len(d)
    if J < 2:
        return np.nan, np.nan
    var = d.var(ddof=1)
    if var == 0:
        return np.nan, np.nan
    corrected_var = (1.0 / J + 1.0 / (n_splits - 1)) * var
    t = d.mean() / np.sqrt(corrected_var)
    return t, 2 * stats.t.sf(abs(t), df=J - 1)


def bootstrap_ci(d, n_boot=10000, alpha=0.05, seed=SEED):
    rng = np.random.default_rng(seed)
    d = np.asarray(d, dtype=float)
    means = rng.choice(d, size=(n_boot, len(d)), replace=True).mean(axis=1)
    return np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])


summary = []
for metric in ["AUC", "PR_AUC"]:
    for mname in MODELS:
        sub = df[df["Model"] == mname]
        piv = sub.pivot_table(index="FoldId", columns="Tier", values=metric)
        base = piv[BASELINE_TIER].values
        for tier in TIERS:
            v = piv[tier].values
            d = v - base
            row = {
                "Metric": metric, "Model": mname, "Tier": tier,
                "Mean": v.mean(), "Std": v.std(ddof=1),
                "Delta_vs_RFM": d.mean(),
            }
            if tier != BASELINE_TIER:
                lo, hi = bootstrap_ci(d)
                t_nb, p_nb = nadeau_bengio_t(d, N_SPLITS)
                t_naive, p_naive = stats.ttest_rel(v, base)
                try:
                    _, p_wil = stats.wilcoxon(v, base)
                except ValueError:
                    p_wil = np.nan
                row.update({
                    "CI95_low": lo, "CI95_high": hi,
                    "p_naive_ttest": p_naive,
                    "t_NadeauBengio": t_nb, "p_NadeauBengio": p_nb,
                    "p_wilcoxon": p_wil,
                    "Significant_NB_0.05": (p_nb < 0.05) if not np.isnan(p_nb) else None,
                })
            summary.append(row)

df_sum = pd.DataFrame(summary)
sum_path = os.path.join(OUT, f"significance_summary{OUT_SUFFIX}.csv")
df_sum.to_csv(sum_path, index=False)

pd.set_option("display.width", 200, "display.max_columns", 50)
for metric in ["AUC", "PR_AUC"]:
    for mname in MODELS:
        print(f"\n{'=' * 72}\n{metric} — {mname}  "
              f"({N_REPEATS * N_SPLITS} paired folds, baseline = {BASELINE_TIER})\n{'=' * 72}")
        s = df_sum[(df_sum["Metric"] == metric) & (df_sum["Model"] == mname)]
        cols = ["Tier", "Mean", "Std", "Delta_vs_RFM", "CI95_low", "CI95_high",
                "p_naive_ttest", "p_NadeauBengio", "p_wilcoxon"]
        print(s[cols].to_string(index=False, float_format=lambda x: f"{x:.5f}"))

print(f"\nSummary -> {sum_path}")
print("\nRead the Nadeau-Bengio p-value, not the naive one: repeated-CV folds share "
      "training data, so the naive paired t-test overstates significance.")
