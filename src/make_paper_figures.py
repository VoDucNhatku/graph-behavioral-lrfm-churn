"""
make_paper_figures.py

Builds the result figure used in paper/main.tex directly from the committed
result files. Nothing here recomputes a model; the figure is a rendering of
results/significance_folds.csv and results/significance_summary.csv, so a figure
can never drift away from the numbers in the tables.

Figures are authored at the LNCS text width (4.8 in) so that
\\includegraphics[width=\\textwidth] does no scaling. Drawing them wider and
letting LaTeX shrink them is what made the labels too small to read.

Output (vector PDF, so it stays sharp at print size):
    paper/figures/fig_folds.pdf    tier means per classifier, with fold spread

Run:  python src/make_paper_figures.py
"""

import os
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get("LRFM_OUT_DIR", os.path.join(ROOT, "results"))
FIG = os.path.join(ROOT, "paper", "figures")
os.makedirs(FIG, exist_ok=True)

TEXT_WIDTH_IN = 4.8               # LNCS text block width

TIERS = ["RFM", "LRFM", "B-LRFM", "B-LRFM+Seg", "Graph-Enhanced"]
MODELS = ["LightGBM", "Logistic Regression"]

INK = "#1f2933"
MUTED = "#7b8794"
NEUTRAL = "#52606d"
HIGHLIGHT = "#0b6e4f"             # only for effects that clear the corrected test
GRID = "#d8dee4"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "font.size": 7.4,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": NEUTRAL,
    "ytick.color": NEUTRAL,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 200,
})


folds = pd.read_csv(os.path.join(RES, "significance_folds.csv"))
pivot = folds.pivot_table(index=["Repeat", "Fold"], columns=["Model", "Tier"], values="AUC")

# ── The one result figure: tier means per classifier, with fold spread ───────────
fig, ax = plt.subplots(figsize=(TEXT_WIDTH_IN, 3.0))
fig.subplots_adjust(left=0.135, right=0.985, top=0.715, bottom=0.165)

face = {"LightGBM": "#c6d4e1", "Logistic Regression": "#bcd9c9"}
edge = {"LightGBM": "#2c5d8a", "Logistic Regression": HIGHLIGHT}

x = np.arange(len(TIERS))
for model in MODELS:
    means = np.array([pivot[(model, t)].mean() for t in TIERS])
    sds = np.array([pivot[(model, t)].std(ddof=1) for t in TIERS])
    # ribbon = fold-to-fold spread, so the flatness of the line can be judged
    # against the noise it sits in
    ax.fill_between(x, means - sds, means + sds, color=face[model], alpha=0.55,
                    lw=0, zorder=1)
    ax.plot(x, means, "-o", color=edge[model], lw=1.7, ms=4.2, zorder=3)

lg = np.array([pivot[("Logistic Regression", t)].mean() for t in TIERS])
lgbm = np.array([pivot[("LightGBM", t)].mean() for t in TIERS])

for model, arr, txt in (("Logistic Regression", lg, "Logistic\nregression"),
                        ("LightGBM", lgbm, "LightGBM")):
    ax.text(-0.26, arr[0], txt, color=edge[model], fontsize=7.2, fontweight="bold",
            ha="right", va="center", linespacing=1.35)

ax.annotate("", xy=(4.30, lg[-1]), xytext=(4.30, lgbm[-1]),
            arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
ax.text(4.40, (lg[-1] + lgbm[-1]) / 2, "the only\nreal effect\n$\\approx$ 0.010",
        fontsize=6.9, color=INK, va="center", linespacing=1.4)

ax.set_xlim(-1.65, 5.30)
ax.set_xticks(x)
ax.set_xticklabels(["RFM", "LRFM", "B-LRFM", "B-LRFM\n+Seg", "Graph-\nEnhanced"],
                   fontsize=7.2)
ax.set_ylabel("Mean ROC-AUC", fontsize=7.3)
ax.set_ylim(0.7855, 0.8325)
ax.grid(axis="y", color=GRID, lw=0.6, alpha=0.7)
ax.set_axisbelow(True)

fig.text(0.022, 0.978, "Adding features moves nothing; the classifier moves everything",
         fontsize=8.4, fontweight="bold", color=INK, va="top")
fig.text(0.022, 0.938, "Lines are mean ROC-AUC over 50 folds. Shaded bands are the fold-to-fold "
                       "spread ($\\pm$1 SD),\nfar wider than any movement along a line.",
         fontsize=6.9, color=MUTED, va="top", linespacing=1.5)

out2 = os.path.join(FIG, "fig_folds.pdf")
fig.savefig(out2)
plt.close(fig)
print(f"[OUTPUT] {out2}")

# ── Console cross-check so the figure can be audited against the tables ─────
print()
print("Tier means rendered in fig_folds.pdf (cross-check against Table 1):")
for t in TIERS:
    print(f"  {t:<16s} LightGBM={pivot[('LightGBM', t)].mean():.5f}  "
          f"LogReg={pivot[('Logistic Regression', t)].mean():.5f}")
