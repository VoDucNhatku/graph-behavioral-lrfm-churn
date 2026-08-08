"""
run_pipeline_v2.py
Graph-Enhanced Behavioral-LRFM Framework for Explainable Churn Prediction
in Non-Contractual E-Commerce — CORRECTED VERSION

Fixes vs run_pipeline.py:
  FIX-A: CancellationRate filtered to InvoiceDate <= OBS_END (no future leakage)
  FIX-B: NCR/CCR recomputed per CV fold on training labels only (no target leakage)
  FIX-C: StandardScaler inside sklearn Pipeline (no preprocessing leakage)
  FIX-D: KMeans_Segment / Louvain_Community one-hot encoded (not treated as ordinal)
  FIX-E: Leiden community detection added alongside Louvain
  FIX-F: Per-community SHAP analysis added
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
from datetime import datetime

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                             calinski_harabasz_score,
                             roc_auc_score, f1_score, recall_score,
                             precision_score, average_precision_score)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.base import clone

import xgboost as xgb
import lightgbm as lgb
import networkx as nx
import community as community_louvain
import shap

try:
    import leidenalg, igraph as ig
    HAS_LEIDEN = True
except ImportError:
    HAS_LEIDEN = False
    print("[Note] leidenalg not installed — Leiden step skipped")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
np.random.seed(SEED)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("LRFM_DATA_DIR", os.path.join(ROOT, "data"))
OUT  = os.environ.get("LRFM_OUT_DIR", os.path.join(ROOT, "results"))
os.makedirs(OUT, exist_ok=True)

print("=" * 70)
print("GRAPH-ENHANCED BEHAVIORAL-LRFM PIPELINE v2 (all leakages fixed)")
print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: LOAD DATASET
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 1] Loading Online Retail II...")

candidates = glob.glob(os.path.join(DATA_DIR, "online_retail*.xlsx"))
if not candidates:
    candidates = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
if not candidates:
    sys_exit_msg = f"[ERROR] No .xlsx file found in {DATA_DIR}"
    raise SystemExit(sys_exit_msg)
xlsx_path = candidates[0]

df_list = [pd.read_excel(xlsx_path, sheet_name=s, engine="openpyxl")
           for s in pd.ExcelFile(xlsx_path).sheet_names]
df_raw = pd.concat(df_list, ignore_index=True)
df_raw.columns = [c.replace(" ", "") for c in df_raw.columns]
df_raw["InvoiceDate"] = pd.to_datetime(df_raw["InvoiceDate"])
df_raw = df_raw.dropna(subset=["CustomerID"])

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: PREPROCESSING
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 2] Preprocessing...")

df_raw["IsCancelled"] = df_raw["Invoice"].astype(str).str.startswith("C")
df_cancel_all = df_raw[df_raw["IsCancelled"]].copy()
df_main       = df_raw[(~df_raw["IsCancelled"]) &
                        (df_raw["Quantity"] > 0) &
                        (df_raw["Price"]    > 0)].copy()
df_main = df_main.drop_duplicates()
df_main["TotalPrice"] = df_main["Quantity"] * df_main["Price"]

OBS_END  = pd.Timestamp("2011-06-30")
PRED_END = pd.Timestamp("2011-09-30")
ANALYSIS_DATE = OBS_END + pd.Timedelta(days=1)

df_obs  = df_main[df_main["InvoiceDate"] <= OBS_END]
df_pred = df_main[(df_main["InvoiceDate"] > OBS_END) &
                  (df_main["InvoiceDate"] <= PRED_END)]

# FIX-A: restrict cancellations to observation window only
df_cancel_obs = df_cancel_all[df_cancel_all["InvoiceDate"] <= OBS_END]

obs_customers = set(df_obs["CustomerID"].unique())
print(f"  Valid transactions (obs): {len(df_obs):,}")
print(f"  Observation customers:    {len(obs_customers):,}")
print(f"  Cancellation records (obs window only): {len(df_cancel_obs):,}  [FIX-A]")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 3] Feature engineering (Behavioral-LRFM)...")

grp = df_obs.groupby("CustomerID")

recency   = (ANALYSIS_DATE - grp["InvoiceDate"].max()).dt.days.rename("R")
frequency = grp["Invoice"].nunique().rename("F")
monetary  = grp["TotalPrice"].sum().rename("M")
length    = (ANALYSIS_DATE - grp["InvoiceDate"].min()).dt.days.rename("L")
aov       = (monetary / frequency).rename("AOV")
basket    = (df_obs.groupby(["CustomerID","Invoice"])["StockCode"].nunique()
                   .groupby("CustomerID").mean()).rename("BasketSize")
diversity = grp["StockCode"].nunique().rename("ProductDiversity")

# FIX-A: use df_cancel_obs (obs-window only), not full df_cancel_all
cancel_cnt   = (df_cancel_obs[df_cancel_obs["CustomerID"].isin(obs_customers)]
                .groupby("CustomerID")["Invoice"].nunique())
cancel_rate  = (cancel_cnt / (cancel_cnt + frequency)).fillna(0).rename("CancellationRate")

# IPT: invoice-level, median-impute single purchasers
inv_dates = (df_obs.groupby(["CustomerID","Invoice"])["InvoiceDate"]
             .first().reset_index())
def avg_ipt(s):
    d = s.sort_values().values
    if len(d) < 2: return np.nan
    return float(np.diff(d).astype("timedelta64[D]").astype(float).mean())
ipt_raw    = inv_dates.groupby("CustomerID")["InvoiceDate"].apply(avg_ipt)
ipt_median = ipt_raw.median()
ipt        = ipt_raw.fillna(ipt_median).rename("InterpurchaseTime")

feat = pd.concat([length, recency, frequency, monetary, aov,
                  basket, diversity, cancel_rate, ipt], axis=1).fillna(0)
feat.index.name = "CustomerID"

print(f"  Feature matrix: {feat.shape}")
print(feat.describe().round(2))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: CHURN LABEL
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 4] Churn label (90-day prediction window)...")

active_in_pred = set(df_pred["CustomerID"].unique())
feat["Churn"]  = feat.index.map(lambda c: 0 if c in active_in_pred else 1)
churn_rate     = feat["Churn"].mean()
print(f"  Customers: {len(feat):,}  |  Churn rate: {churn_rate*100:.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: BASELINE CLUSTERING
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 5] Baseline clustering...")

rfm_cols   = ["R","F","M"]
lrfm_cols  = ["L","R","F","M"]
blrfm_cols = ["L","R","F","M","AOV","BasketSize",
              "ProductDiversity","CancellationRate","InterpurchaseTime"]

scaler_clust = StandardScaler()
X_blrfm = scaler_clust.fit_transform(feat[blrfm_cols])

for name, cols in [("RFM",rfm_cols),("LRFM",lrfm_cols),("B-LRFM",blrfm_cols)]:
    X = StandardScaler().fit_transform(feat[cols])
    km = KMeans(n_clusters=5, random_state=SEED, n_init=10)
    lbl = km.fit_predict(X)
    sil = silhouette_score(X, lbl)
    dbi = davies_bouldin_score(X, lbl)
    print(f"  {name:10s} K-means k=5: Sil={sil:.4f}  DBI={dbi:.4f}")

# Best K-means segmentation for FIX-D one-hot
km5 = KMeans(n_clusters=5, random_state=SEED, n_init=10)
feat["KMeans_Seg"] = km5.fit_predict(X_blrfm)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: CUSTOMER SIMILARITY GRAPH
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 6] Building k-NN customer similarity graph (k=10)...")

from sklearn.neighbors import NearestNeighbors
n = len(feat)
cust_ids = feat.index.tolist()

nn = NearestNeighbors(n_neighbors=11, metric="euclidean")
nn.fit(X_blrfm)
distances, indices = nn.kneighbors(X_blrfm)

G = nx.Graph()
G.add_nodes_from(range(n))
# Store neighbor dict for FIX-B
neighbor_dict = {i: [] for i in range(n)}

for i in range(n):
    for jj in range(1, 11):
        j = indices[i, jj]
        w = 1.0 / (1.0 + distances[i, jj])
        if not G.has_edge(i, j):
            G.add_edge(i, j, weight=w)
        neighbor_dict[i].append(j)

print(f"  Nodes: {G.number_of_nodes():,}  |  Edges: {G.number_of_edges():,}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7: COMMUNITY DETECTION — Louvain + Leiden (FIX-E)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 7] Community detection — Louvain + Leiden (FIX-E)...")

# Louvain
partition_lou = community_louvain.best_partition(G, weight="weight", random_state=SEED)
louvain_arr   = np.array([partition_lou[i] for i in range(n)])
feat["Louvain_Community"] = louvain_arr
n_lou = len(set(louvain_arr))
mod_lou = community_louvain.modularity(partition_lou, G, weight="weight")
print(f"  Louvain:  {n_lou} communities  Modularity={mod_lou:.4f}")

# Leiden (FIX-E)
if HAS_LEIDEN:
    ig_g = ig.Graph(n=n, edges=list(G.edges()))
    ig_g.es["weight"] = [G[u][v]["weight"] for u,v in G.edges()]
    leiden_part = leidenalg.find_partition(
        ig_g, leidenalg.ModularityVertexPartition,
        weights="weight", n_iterations=10, seed=SEED)
    leiden_arr = np.array(leiden_part.membership)
    feat["Leiden_Community"] = leiden_arr
    n_lei = len(set(leiden_arr))
    mod_lei = leiden_part.modularity
    print(f"  Leiden:   {n_lei} communities  Modularity={mod_lei:.4f}")
else:
    leiden_arr = louvain_arr.copy()
    feat["Leiden_Community"] = leiden_arr
    n_lei = n_lou
    print("  Leiden: skipped (using Louvain labels as fallback)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8: STATIC GRAPH FEATURES (no churn label needed)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 8] Static graph features (degree, PageRank, clustering coeff)...")

feat["Degree"]      = [G.degree(i) for i in range(n)]
feat["WeightedDeg"] = [G.degree(i, weight="weight") for i in range(n)]
feat["PageRank"]    = list(nx.pagerank(G, weight="weight").values())
feat["ClustCoeff"]  = list(nx.clustering(G, weight="weight").values())

# NOTE: NeighborChurnRate and CommunityChurnRate are NOT added here.
# They will be recomputed inside each CV fold to avoid target leakage (FIX-B).
static_graph_cols = ["Degree","WeightedDeg","PageRank","ClustCoeff"]
print(f"  Static graph features: {static_graph_cols}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9: FIX-D — One-Hot Encode categorical cluster IDs
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 9] One-hot encoding categorical segment/community IDs (FIX-D)...")

# KMeans segment: 5 categories → 4 dummies (drop_first)
kmeans_dummies  = pd.get_dummies(feat["KMeans_Seg"],
                                  prefix="KM", drop_first=True)
louvain_dummies = pd.get_dummies(feat["Louvain_Community"],
                                  prefix="LV", drop_first=True)

kmeans_oh_cols  = list(kmeans_dummies.columns)
louvain_oh_cols = list(louvain_dummies.columns)

feat = pd.concat([feat, kmeans_dummies, louvain_dummies], axis=1)

print(f"  KMeans one-hot: {len(kmeans_oh_cols)} cols")
print(f"  Louvain one-hot: {len(louvain_oh_cols)} cols")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 10: CUSTOM CV FUNCTION — FIX-B (NCR/CCR per fold) + FIX-C (Pipeline)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 10] Churn prediction with leak-free CV (FIX-B + FIX-C)...")

y = feat["Churn"].values

def custom_cv_with_graph(feat_df, y, base_feature_cols, neighbor_dict,
                          community_arr, models_dict, n_splits=5, seed=42):
    """
    Correct CV for graph-enhanced churn prediction.
    FIX-B: NCR and CCR recomputed on training fold labels only.
    FIX-C: StandardScaler wrapped in Pipeline — fit on train, transform on val.
    """
    cv     = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    all_rows = []

    for fold, (train_idx, val_idx) in enumerate(cv.split(feat_df, y)):
        y_train = y[train_idx]
        y_val   = y[val_idx]
        train_set = set(train_idx)

        # ── FIX-B: NCR on training labels only ──────────────────────────────
        ncr = np.zeros(n)
        for i in range(n):
            train_nbrs = [nb for nb in neighbor_dict.get(i, []) if nb in train_set]
            ncr[i] = np.mean([y[nb] for nb in train_nbrs]) if train_nbrs else y_train.mean()

        # ── FIX-B: CCR on training labels only ──────────────────────────────
        ccr = np.zeros(n)
        for comm in np.unique(community_arr):
            in_comm   = community_arr == comm
            in_train  = np.zeros(n, dtype=bool); in_train[train_idx] = True
            tc_mask   = in_comm & in_train
            ccr[in_comm] = y[tc_mask].mean() if tc_mask.sum() > 0 else y_train.mean()

        # Build full feature matrix: base + NCR + CCR
        X_base = feat_df[base_feature_cols].values
        X_full = np.column_stack([X_base,
                                   ncr.reshape(-1, 1),
                                   ccr.reshape(-1, 1)])

        X_train, X_val = X_full[train_idx], X_full[val_idx]

        for mdl_name, mdl_proto in models_dict.items():
            # FIX-C: scaler inside pipeline
            pipe = Pipeline([("sc", StandardScaler()),
                              ("clf", clone(mdl_proto))])
            pipe.fit(X_train, y_train)
            y_prob = pipe.predict_proba(X_val)[:, 1]
            y_pred = (y_prob >= 0.5).astype(int)

            all_rows.append({
                "Fold": fold,
                "Model": mdl_name,
                "AUC":    roc_auc_score(y_val, y_prob),
                "PR_AUC": average_precision_score(y_val, y_prob),
                "F1":     f1_score(y_val, y_pred),
                "Recall": recall_score(y_val, y_pred),
            })

    df_folds = pd.DataFrame(all_rows)
    return df_folds.groupby("Model")[["AUC","PR_AUC","F1","Recall"]].mean().round(4)


def standard_cv(feat_df, y, feature_cols, models_dict, n_splits=5, seed=42):
    """Standard CV for feature sets without NCR/CCR (FIX-C: scaler in pipeline)."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    rows = []
    for fold, (train_idx, val_idx) in enumerate(cv.split(feat_df, y)):
        X = feat_df[feature_cols].values
        X_tr, X_va = X[train_idx], X[val_idx]
        y_tr, y_va = y[train_idx],  y[val_idx]
        for mdl_name, mdl_proto in models_dict.items():
            pipe = Pipeline([("sc", StandardScaler()), ("clf", clone(mdl_proto))])
            pipe.fit(X_tr, y_tr)
            yp = pipe.predict_proba(X_va)[:,1]
            rows.append({
                "Fold": fold, "Model": mdl_name,
                "AUC":    roc_auc_score(y_va, yp),
                "PR_AUC": average_precision_score(y_va, yp),
                "F1":     f1_score(y_va, (yp>=0.5).astype(int)),
                "Recall": recall_score(y_va, (yp>=0.5).astype(int)),
            })
    df = pd.DataFrame(rows)
    return df.groupby("Model")[["AUC","PR_AUC","F1","Recall"]].mean().round(4)


models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced"),
    "Decision Tree":       DecisionTreeClassifier(max_depth=6, random_state=SEED, class_weight="balanced"),
    "Random Forest":       RandomForestClassifier(n_estimators=200, random_state=SEED,
                                                   class_weight="balanced", n_jobs=-1),
    "XGBoost":             xgb.XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6,
                                              use_label_encoder=False, eval_metric="logloss",
                                              random_state=SEED,
                                              scale_pos_weight=(1-churn_rate)/churn_rate),
    "LightGBM":            lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, max_depth=6,
                                               random_state=SEED, is_unbalance=True, verbose=-1),
}

all_results = {}

# Experiment 1: RFM (no graph)
print("\n  [EXP 1] RFM...")
r = standard_cv(feat, y, rfm_cols, models)
all_results["RFM"] = r
print(r)

# Experiment 2: LRFM
print("\n  [EXP 2] LRFM...")
r = standard_cv(feat, y, lrfm_cols, models)
all_results["LRFM"] = r
print(r)

# Experiment 3: Behavioral-LRFM
print("\n  [EXP 3] Behavioral-LRFM...")
r = standard_cv(feat, y, blrfm_cols, models)
all_results["B-LRFM"] = r
print(r)

# Experiment 4: B-LRFM + Segment labels (one-hot, FIX-D)
seg_cols = blrfm_cols + kmeans_oh_cols + louvain_oh_cols
print("\n  [EXP 4] B-LRFM + Segment (one-hot, FIX-D)...")
r = standard_cv(feat, y, seg_cols, models)
all_results["B-LRFM+Seg"] = r
print(r)

# Experiment 5: B-LRFM + Static graph features (no leakage)
static_cols = blrfm_cols + static_graph_cols + kmeans_oh_cols + louvain_oh_cols
print("\n  [EXP 5] B-LRFM + Static graph features...")
r = standard_cv(feat, y, static_cols, models)
all_results["B-LRFM+StaticGraph"] = r
print(r)

# Experiment 6: Graph-Enhanced (FIX-B: NCR/CCR computed per fold)
base_for_graph = blrfm_cols + static_graph_cols + kmeans_oh_cols + louvain_oh_cols
print("\n  [EXP 6] Graph-Enhanced (NCR+CCR leak-free, FIX-B+C)...")
r_graph = custom_cv_with_graph(feat, y, base_for_graph,
                                neighbor_dict, louvain_arr, models)
all_results["Graph-Enhanced (leak-free)"] = r_graph
print(r_graph)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 11: COMPARISON TABLE
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("FINAL RESULTS — AUC (5-fold CV, all leakage-free)")
print("=" * 70)

best_model_per_exp = {}
for exp_name, res_df in all_results.items():
    best_mdl = res_df["AUC"].idxmax()
    best_auc = res_df["AUC"].max()
    best_model_per_exp[exp_name] = (best_mdl, best_auc,
                                     res_df.loc[best_mdl,"F1"],
                                     res_df.loc[best_mdl,"Recall"],
                                     res_df.loc[best_mdl,"PR_AUC"])

summary = pd.DataFrame(best_model_per_exp,
                        index=["Best Model","ROC-AUC","F1","Recall","PR-AUC"]).T
print(summary.to_string())

# LightGBM cross-exp comparison
print("\n[LightGBM across all feature sets]")
lgbm_rows = {}
for exp_name, res_df in all_results.items():
    if "LightGBM" in res_df.index:
        lgbm_rows[exp_name] = res_df.loc["LightGBM"]
lgbm_table = pd.DataFrame(lgbm_rows).T
print(lgbm_table.to_string())

# Save
lgbm_table.to_csv(os.path.join(OUT, "churn_results_v2.csv"))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 12: TRAIN BEST MODEL + COMPUTE NCR/CCR ON FULL DATA FOR REPORTING
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 12] Training best model on full data for SHAP/reporting...")

# Compute NCR/CCR on full data (for reporting only, not for CV evaluation)
churn_map = feat["Churn"].to_dict()
ncr_full  = np.array([
    np.mean([churn_map[cust_ids[nb]] for nb in neighbor_dict[i]])
    if neighbor_dict[i] else churn_rate
    for i in range(n)
])
comm_rate_map = feat.groupby("Louvain_Community")["Churn"].mean().to_dict()
ccr_full = feat["Louvain_Community"].map(comm_rate_map).values

feat["NeighborChurnRate"]  = ncr_full
feat["CommunityChurnRate"] = ccr_full

full_feature_cols = base_for_graph + ["NeighborChurnRate", "CommunityChurnRate"]
X_full = feat[full_feature_cols].values
sc_full = StandardScaler()
X_full_scaled = sc_full.fit_transform(X_full)

best_mdl_final = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05,
                                      max_depth=6, random_state=SEED,
                                      is_unbalance=True, verbose=-1)
best_mdl_final.fit(X_full_scaled, y)
y_prob_full = best_mdl_final.predict_proba(X_full_scaled)[:, 1]
feat["ChurnProbability"]  = y_prob_full
feat["ExpectedRetention"] = y_prob_full * feat["M"]

top10_idx  = np.argsort(y_prob_full)[::-1][:int(n*0.1)]
top10_cap  = y[top10_idx].sum() / y.sum()
lift       = y[top10_idx].mean() / y.mean()
print(f"  Top-10% capture rate: {top10_cap*100:.1f}%")
print(f"  Lift@10%: {lift:.2f}x")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 13: GLOBAL SHAP + PER-COMMUNITY SHAP (FIX-F)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 13] SHAP — global + per-community (FIX-F)...")

explainer = shap.TreeExplainer(best_mdl_final)
sample_idx = np.random.choice(n, min(800, n), replace=False)
sv = explainer.shap_values(X_full_scaled[sample_idx])
if isinstance(sv, list): sv = sv[1]

# Global SHAP
shap_global = pd.DataFrame({
    "Feature": full_feature_cols,
    "Mean|SHAP|": np.abs(sv).mean(axis=0).round(5)
}).sort_values("Mean|SHAP|", ascending=False)
print("\n  Global SHAP (Top 12):")
print(shap_global.head(12).to_string(index=False))
shap_global.to_csv(os.path.join(OUT, "shap_global_v2.csv"), index=False)

# Global SHAP plot
plt.figure(figsize=(10, 7))
shap.summary_plot(sv, X_full_scaled[sample_idx],
                  feature_names=full_feature_cols, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "shap_global_v2.png"), dpi=150)
plt.close()

# FIX-F: Per-community SHAP
print("\n  Per-community SHAP (top 3 features per community)...")
communities = sorted(feat["Louvain_Community"].unique())
comm_shap_rows = []

for comm in communities:
    comm_mask_sample = np.array([
        feat["Louvain_Community"].iloc[sample_idx[ii]] == comm
        for ii in range(len(sample_idx))])
    if comm_mask_sample.sum() < 5:
        continue
    sv_comm = sv[comm_mask_sample]
    top3_idx = np.abs(sv_comm).mean(axis=0).argsort()[::-1][:3]
    top3     = [(full_feature_cols[i], round(float(np.abs(sv_comm[:,i]).mean()),5))
                for i in top3_idx]
    comm_size  = (feat["Louvain_Community"] == comm).sum()
    comm_churn = feat.loc[feat["Louvain_Community"]==comm, "Churn"].mean()
    comm_shap_rows.append({
        "Community": comm,
        "N": comm_size,
        "Churn%": round(comm_churn*100,1),
        "Top1_feature": top3[0][0], "Top1_shap": top3[0][1],
        "Top2_feature": top3[1][0], "Top2_shap": top3[1][1],
        "Top3_feature": top3[2][0], "Top3_shap": top3[2][1],
    })

df_comm_shap = pd.DataFrame(comm_shap_rows)
print(df_comm_shap[["Community","N","Churn%","Top1_feature","Top2_feature","Top3_feature"]]
      .to_string(index=False))
df_comm_shap.to_csv(os.path.join(OUT, "shap_per_community_v2.csv"), index=False)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 14: SEGMENT PROFILES + RETENTION STRATEGY
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 14] Segment profiles and retention strategy...")

seg = feat.groupby("Louvain_Community").agg(
    N             = ("Churn","count"),
    ChurnRate     = ("Churn","mean"),
    AvgMonetary   = ("M","mean"),
    AvgRecency    = ("R","mean"),
    AvgChurnProb  = ("ChurnProbability","mean"),
    AvgERV        = ("ExpectedRetention","mean"),
).round(2)

def label_seg(row):
    if row["AvgMonetary"] > feat["M"].quantile(0.75):
        return "High-value at-risk" if row["ChurnRate"]>0.5 else "High-value loyal"
    elif row["ChurnRate"] > 0.7:
        return "Low-value dormant"
    else:
        return "Moderate active"

STRATEGY = {
    "High-value loyal":   "Loyalty reward / VIP program",
    "High-value at-risk": "Urgent personalized retention voucher",
    "Moderate active":    "Bundle offer / upsell campaign",
    "Low-value dormant":  "Low-cost reactivation email",
}

seg["Label"]    = seg.apply(label_seg, axis=1)
seg["Strategy"] = seg["Label"].map(STRATEGY)
print(seg[["N","ChurnRate","AvgMonetary","AvgChurnProb","Label","Strategy"]].to_string())
seg.to_csv(os.path.join(OUT, "segment_profiles_v2.csv"))

print(f"\n[OUTPUT] results/churn_results_v2.csv")
print(f"[OUTPUT] results/shap_global_v2.csv + shap_global_v2.png")
print(f"[OUTPUT] results/shap_per_community_v2.csv  [FIX-F]")
print(f"[OUTPUT] results/segment_profiles_v2.csv")
print("\nDone.")
