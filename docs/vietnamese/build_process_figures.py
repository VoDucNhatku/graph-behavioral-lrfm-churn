"""Build Vietnamese research-process diagrams from the archived code contract."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import fontManager

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent/"assets"
font = Path("C:/Windows/Fonts/arial.ttf")
if font.exists():
    fontManager.addfont(str(font))
plt.rcParams.update({"font.family": "Arial" if font.exists() else "DejaVu Sans",
                     "font.size": 12, "text.color": "#203044"})


def box(ax, x, y, w, h, title, body, fill="#EDF5F3", stroke="#14736A"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.035",
                              facecolor=fill, edgecolor=stroke, linewidth=1.2))
    ax.text(x+w/2, y+h-.13, title, ha="center", va="top", weight="bold", fontsize=12)
    ax.text(x+w/2, y+h-.43, body, ha="center", va="top", fontsize=11.5, linespacing=1.45)


def arrow(ax, start, end, color="#14736A"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13,
                                linewidth=1.5, color=color, connectionstyle="arc3"))


def save(fig, name):
    path=ASSETS/name
    fig.savefig(path, dpi=260, facecolor="white", bbox_inches="tight", pad_inches=.16)
    plt.close(fig)
    return path.relative_to(ROOT).as_posix()


def pipeline():
    fig, ax=plt.subplots(figsize=(8, 5.8))
    ax.set(xlim=(0, 8.25), ylim=(0, 6)); ax.axis("off")
    for x,y,title,body in [
        (.15,4.45,"1. Dữ liệu và cohort","Hai sheet → giao dịch hợp lệ\nCửa sổ quan sát và tương lai\n5.038 khách; nhãn churn"),
        (4.4,4.45,"2. Biểu diễn cá nhân","Chín biến Behavioural-LRFM\nChỉ lịch sử quan sát\nRFM làm baseline"),
        (.15,2.4,"3. Cấu trúc từ covariates","Chuẩn hóa → kNN → Louvain\nKMeans, one-hot và static graph\nChưa dùng nhãn để dựng graph"),
        (4.4,2.4,"4. Đánh giá ghép cặp","NCR/CCR chỉ từ nhãn training\n5 tier × 2 classifier × 50 fold\nScaler classifier fit training"),
        (.15,.35,"5. Hiệu số và độ nhạy","Cùng FoldId → ΔAUC và pNB\nk = 5, 10, 15, 20\nKết luận trong phạm vi đã thử"),
        (4.4,.35,"Nhánh mô tả riêng","Full fit → SHAP và profiles\nMô tả model/cohort hiện có\nChưa xác nhận hiệu quả giữ chân"),
    ]:
        box(ax,x,y,3.45,1.4,title,body,fill="#F4F6F8" if title.startswith("Nhánh") else "#EDF5F3")
    arrow(ax,(3.63,5.16),(4.36,5.16))
    arrow(ax,(5.4,4.43),(3.5,3.82))
    arrow(ax,(3.63,3.1),(4.36,3.1))
    arrow(ax,(5.3,2.38),(3.5,1.77))
    # The descriptive branch draws covariates/labels from the same cohort,
    # rather than being a held-out continuation of the statistical branch.
    ax.plot([7.87,8.09,8.09],[5.16,5.16,1.07],color="#617083",linewidth=1.5)
    arrow(ax,(8.09,1.07),(7.87,1.07),color="#617083")
    return save(fig,"process-pipeline-vi.png")


def fold_scope():
    fig,ax=plt.subplots(figsize=(8,5.1))
    ax.set(xlim=(0,8),ylim=(0,5.2));ax.axis("off")
    box(ax,.2,3.4,3.5,1.4,"Training T: A, B, C, D","Được dùng yA, yB, yC, yD\nBase rate = (1+0+1+0)/4\nNhãn training để fit classifier")
    box(ax,4.3,3.4,3.5,1.4,"Validation V: E, F, G, H","Chỉ dùng covariates để dự báo\nGiấu yE, yF, yG, yH\nMở nhãn khi chấm metrics",fill="#FFF4ED",stroke="#AF6B35")
    box(ax,.2,1.5,3.5,1.3,"NCR của E","Outgoing: {A, C, F}\nGiao với T: {A, C}\nNCR(E) = (1+1)/2 = 1")
    box(ax,4.3,1.5,3.5,1.3,"CCR của E","Community: {A, B, E, F}\nGiao với T: {A, B}\nCCR(E) = (1+0)/2 = 0,5")
    arrow(ax,(1.95,3.37),(1.95,2.83))
    arrow(ax,(2.9,3.37),(5.25,2.83))
    ax.text(4,.8,"Cả NCR và CCR của E đều không đọc yE hoặc yF.",ha="center",weight="bold",fontsize=12)
    ax.text(4,.36,"Ví dụ giả định 8 khách, k=3; thực nghiệm chính dùng 5.038 khách, k=10.",ha="center",fontsize=11)
    return save(fig,"process-fold-scope-vi.png")


def timeline():
    fig,ax=plt.subplots(figsize=(8,4.4))
    ax.set(xlim=(0,8),ylim=(0,4.8));ax.axis("off")
    box(ax,.2,2.8,3.5,1.5,"Mô tả theo paper","Quan sát: đến hết 30/06/2011\nTương lai: 01/07-30/09/2011\nGiao dịch ngày 30/06 → features")
    box(ax,4.3,2.8,3.5,1.5,"Thực thi archived","OBS_END: 30/06 lúc 00:00\nPRED_END: 30/09 lúc 00:00\n30/06 ban ngày → prediction",fill="#FFF4ED",stroke="#AF6B35")
    arrow(ax,(3.73,3.55),(4.27,3.55),color="#617083")
    box(ax,.2,.55,7.6,1.65,"Kết quả kiểm đếm khi chuyển sang ngày trọn vẹn","Observation: 556.212 → 557.398 dòng; cohort: 5.038 → 5.041\n28 nhãn đổi trong tập khách chung\nChưa fit models với cửa sổ sửa; AUC cũ vẫn thuộc archived windows")
    arrow(ax,(6.1,2.77),(6.1,2.24),color="#617083")
    return save(fig,"process-windows-vi.png")


if __name__=="__main__":
    ASSETS.mkdir(parents=True,exist_ok=True)
    files=[pipeline(),fold_scope(),timeline()]
    print(json.dumps({"figures":files,"kind":"Source-grounded diagrams; hypothetical fold explicitly labelled"},indent=2))
