"""Render translated figures from source labels and unchanged archived fold data."""
from pathlib import Path
import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT/"docs/vietnamese/assets"
MANIFEST = ROOT/"docs/vietnamese/evidence/translation-coverage.json"
if not MANIFEST.exists():
    MANIFEST = ROOT/"notes/vietnamese-docs-20261013/translation-coverage.json"


def setup():
    font = Path("C:/Windows/Fonts/arial.ttf")
    if font.exists():
        font_name = FontProperties(fname=str(font)).get_name()
    else:
        font_name = "DejaVu Sans"
    plt.rcParams.update({"font.family": font_name, "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "text.color": "#203044", "axes.labelcolor": "#203044"})


def pipeline(record):
    fig, ax = plt.subplots(figsize=(9.6, 4.1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    positions = {"data": (.025,.61), "feat": (.36,.61), "graph": (.695,.61),
                 "eval": (.025,.075), "leak": (.36,.075), "comm": (.695,.075)}
    width, height = .28, .31
    for node in record["nodes"]:
        x, y = positions[node["id"]]
        background = "#E7F2EE" if node["id"] == "graph" else "#E8F1F8" if node["id"] in ["leak","eval"] else "#F7F9FA"
        ax.add_patch(FancyBboxPatch((x,y),width,height,boxstyle="round,pad=0.012,rounding_size=0.014",
                                   facecolor=background,edgecolor="#9CB0BF",linewidth=1.2))
        title, *details = node["translated_lines"]
        title = title.replace("Nadeau–Bengio", "Nadeau-Bengio")
        ax.text(x+width/2, y+height*.76, title, ha="center",va="center",fontsize=11.5,fontweight="bold")
        detail_lines = []
        for line in details:
            detail_lines += textwrap.wrap(line.replace("Nadeau–Bengio", "Nadeau-Bengio"), width=33)
        ax.text(x+width/2,y+height*.36,"\n".join(detail_lines),ha="center",va="center",fontsize=10.7,linespacing=1.45)
    for left, right in [("data","feat"),("feat","graph"),("comm","leak"),("leak","eval")]:
        lx, ly = positions[left]
        rx, ry = positions[right]
        start = (lx+width+.012,ly+height/2) if lx<rx else (lx-.012,ly+height/2)
        end = (rx-.014,ry+height/2) if lx<rx else (rx+width+.014,ry+height/2)
        ax.annotate("",xy=end,xytext=start,arrowprops={"arrowstyle":"->","lw":1.8,"color":"#526678"})
    x = positions["graph"][0]+width/2
    ax.annotate("",xy=(x,positions["comm"][1]+height+.015),xytext=(x,positions["graph"][1]-.015),
                arrowprops={"arrowstyle":"->","lw":1.8,"color":"#526678"})
    fig.subplots_adjust(left=.015,right=.985,bottom=.025,top=.98)
    fig.savefig(ASSETS/"pipeline-vi.png",dpi=250,facecolor="white")
    plt.close(fig)


def folds(record):
    data = pd.read_csv(ROOT/"results/significance_folds.csv")
    tiers = record["x_tick_labels"]
    checks = []
    fig = plt.figure(figsize=(9.6, 5.2),facecolor="white")
    ax = fig.add_axes([.12,.20,.76,.54])
    label_map = {r["original"]:r["translated"] for r in record["labels"]}
    title = label_map["Adding features moves nothing; the classifier moves everything"]
    fig.text(.07,.96,"\n".join(textwrap.wrap(title,width=85)),fontsize=14.5,fontweight="bold",va="top")
    subtitle = label_map["Lines are mean ROC-AUC over 50 folds. Shaded bands are the fold-to-fold spread (±1 SD), far wider than any movement along a line."]
    fig.text(.07,.865,"\n".join(textwrap.wrap(subtitle,width=111)),fontsize=10.2,color="#617083",va="top")
    x = np.arange(len(tiers))
    plotted = {}
    for model, color in [("Logistic Regression","#0B725C"),("LightGBM","#32678D")]:
        means, deviations = [], []
        for i, tier in enumerate(tiers):
            scores = data[(data.Model==model)&(data.Tier==tier)].AUC
            mean, sd = float(scores.mean()), float(scores.std(ddof=1))
            expected = record["data_summary"][i]["classifiers"][model]
            assert len(scores)==50 and abs(mean-expected["mean_roc_auc"])<1e-14 and abs(sd-expected["sample_sd"])<1e-14
            means.append(mean)
            deviations.append(sd)
            checks.append({"model":model,"tier":tier,"mean":mean,"sample_sd":sd,"n":50})
        means, deviations = np.array(means),np.array(deviations)
        ax.fill_between(x,means-deviations,means+deviations,color=color,alpha=.16,linewidth=0)
        ax.plot(x,means,"o-",color=color,lw=2.1,markersize=5)
        plotted[model] = means
    ax.set_ylim(.785,.835)
    ax.set_xlim(-.75,4.95)
    ax.set_xticks(x,["RFM","LRFM","B-LRFM","B-LRFM\n+Seg","Graph-\nEnhanced"],fontsize=10.5)
    ax.set_yticks([.79,.80,.81,.82,.83])
    ax.set_ylabel("ROC-AUC trung bình",fontsize=11.5)
    ax.grid(axis="y",color="#D9E2E8",linewidth=.7)
    ax.set_axisbelow(True)
    ax.text(-.65,.8172,"Hồi quy\nlogistic",color="#0B725C",fontweight="bold",ha="left",va="center",fontsize=11)
    ax.text(-.65,.8070,"LightGBM",color="#32678D",fontweight="bold",ha="left",va="center",fontsize=11)
    lo, hi = plotted["LightGBM"][-1],plotted["Logistic Regression"][-1]
    ax.annotate("",xy=(4.20,hi),xytext=(4.20,lo),arrowprops={"arrowstyle":"<->","lw":1.3,"color":"#203044"})
    ax.text(4.28,(lo+hi)/2,"hiệu ứng thực\nsự duy nhất\n≈ 0.010",fontsize=9.7,ha="left",va="center")
    for spine in ["left","bottom"]:
        ax.spines[spine].set_color("#7F8E9C")
    fig.savefig(ASSETS/"folds-vi.png",dpi=250,facecolor="white")
    plt.close(fig)
    return checks


if __name__ == "__main__":
    ASSETS.mkdir(parents=True,exist_ok=True)
    setup()
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pipeline(coverage["figures"][0])
    checks = folds(coverage["figures"][1])
    evidence = {"figures":2,"translated_labels_from":"translation-coverage.json",
                "fold_data_source":"results/significance_folds.csv","fold_checks":checks,
                "annotation_is_auc_difference_not_p_value":True,
                "note":"Source wording retained faithfully; audit qualifications are in separate study documents."}
    path = ROOT/"docs/vietnamese/evidence/translated-figures.json"
    path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"created": ["pipeline-vi.png","folds-vi.png"], "verified_series":len(checks)},indent=2))
