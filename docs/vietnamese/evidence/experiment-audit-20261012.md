> Ghi chú cập nhật 13/10/2026: bản này lưu audit phương pháp ngày 12/10 trước full model rerun. Các trạng thái chưa fit/runtime ở bên dưới đã được cập nhật trong [báo cáo tổng hợp](../04-bao-cao-tong-hop.md): 10 jobs đã chạy thành công với pinned Python3.13.5. Full-data SHAP là phân tích mô tả hợp lệ; không tự động sai hay chứng minh main CV leakage. Findings phương pháp vẫn được phân biệt với mức diễn giải.

# Audit thực nghiệm — 2026-10-12

## Kết luận và phạm vi

**Các bảng ROC-AUC/PR-AUC chính, kiểm định và k-sweep có artifact thật; fresh tái tính khớp. Tuy nhiên chưa đủ bằng chứng cho mọi câu diễn giải/mọi thành phần framework mà paper gợi ý đã kiểm soát.** Cần sửa định nghĩa cửa sổ và đặc trưng, thu hẹp claim ablation/SHAP, phân biệt classifier effect với feature effect, và bổ sung provenance baseline trước khi coi bản thảo hoàn toàn khớp thực nghiệm.

Áp dụng `code-reviewer`, review read-only source, artifact và dữ liệu. Không sửa source, paper hay results cũ; không fit lại model suite, không gửi dữ liệu khách hàng. Đã đọc `main.tex`, trích text từ `main.pdf`, xem code/log/CSV hiện tại và đối chiếu notes cũ. PDF hiện có cùng các câu đáng chú ý với TeX; đây là bản local, không xác minh nó chính là PDF đã nộp bên ngoài.

Fresh verification hôm nay gồm: (1) đếm hai worksheet XLSX bằng streaming XML và áp dụng filtering/dedup/window như code; (2) tái tính mean, delta, bootstrap CI và Nadeau–Bengio từ toàn bộ folds của main và bốn k; (3) dựng lại riêng kNN trên feature cache; (4) chạy `src/audit_paper.py`. Các mô hình, community partitions, SHAP và seed42 vẫn là artifact tháng 8, không được gọi là rerun tháng 10.

## Claim → bằng chứng → verdict

| Claim/số paper | Bằng chứng hiện tại | Verdict |
|---|---|---|
| 1.067.371 raw rows, hai sheet 525.461 + 541.910 | Fresh `fresh-data-counts.json`, raw `data/online_retail_II.xlsx` | **Đúng**, đã đếm mới |
| 556.212 observation rows; 5.038 customers; churn 65,2% | Fresh raw audit: 556.212, 5.038, 3.285 churners/5.038 = 65,204446% | **Đúng với code**, cửa sổ không đúng mô tả ngày trọn vẹn |
| Observation tới 30/6; prediction 1/7–30/9; “90-day” | `main.tex:238–248`; `significance_test.py:119–126`; fresh raw audit | **Lệch thực thi**: các mốc Timestamp là 00:00; Q3 có 92 ngày |
| L = days between first and last purchase | `main.tex:256`; `significance_test.py:133`; `run_pipeline_v2.py:133` | **Sai định nghĩa**; code là ngày phân tích trừ lần mua đầu |
| k10: 33.426 edges, Louvain20/modularity .8385, Leiden20/.8323 | `full-2026-08-07/run_pipeline_v2.log:44–49`; fresh kNN edges33.426 | **Có log thật**; chỉ edges được dựng lại hôm nay |
| NCR trung bình labels của graph neighbours | `main.tex:279–291`; `significance_test.py:193–199,244–247` | **Không hoàn toàn khớp**; NCR dùng outgoing kNN list, graph là union vô hướng |
| 23 dummies, 38 total features tại k10 | `run_pipeline_v2.py:271–281,483`; log4 KM+19 LV | **Đúng**, 9+23+4+2=38 |
| Main LightGBM means .8066/.8074/.8054/.8044/.8044; p .755/.742/.561/.590 | `significance_folds.csv`, `significance_summary.csv`, fresh arithmetic | **Đúng** toàn bộ trong rounding |
| 16 tier-vs-RFM tests, min p=.144 | Fresh arithmetic từ main summary | **Đúng**: min .144162913 |
| Seed42 gain +.0033, CI[−.0025,+.0099] | `results_rerun/seed42/significance_summary.csv:6` | **Đúng artifact**: delta .003293335; CI[−.002523341,.009937119]; không fit mới |
| Cross-model Table2: delta .0113/.0099/.0078, p .001/.010/.068 | Fresh paired folds | **Đúng**: p .001182776/.010230575/.067887357 |
| k5/10/15/20: edges16902/33426/50054/66652, communities31/20/16/16; p .880/.590/.666/.500 | Bốn raw logs `knn-sweep/*:9`, bốn CSV pair; fresh stats | **Đúng**, có 500 rows/bộ, 50 folds/tier/model |
| SHAP top5:1.087,.560,.250,.224,.215 | `shap_global_v2.csv:2–6` | **Đúng số**; fit full-data có label aggregates, không phải held-out SHAP |
| “removing it costs nothing” | Main only compares six-feature graph block with Seg; `run_pipeline_v2.py:418–430` có static-only nhưng chỉ seed42 | **Chưa có ablation riêng NCR**, không chứng minh cost=0 |
| Baseline “we reproduce .398” | Local `comparison_v2.csv:17`: max-k-cut approx .4771; `compare_methods_v2.py:439` hardcodes .398 reference | **Provenance thiếu**, không phải output comparison CSV hiện tại |
| K-means .219, Louvain −.050; descriptive communities327/.82 và418/.24 | `comparison_v2.csv` k4=.2185/−.0497; `segment_profiles_v2.csv` | **Đúng rounding/descriptive**; .2185→.219 là trường hợp tie rounding |
| All preprocessing/scalers fold-local; both detectors control detector choice | `significance_test.py:185–202,216–227,273–275`; v2Leiden chỉ ở238–249 | **Nói quá**: graph preprocessing transductive; repeated CV chỉ Louvain |

## Tám phát hiện chính

### 1. Important — cửa sổ label khác ngày mô tả và có ảnh hưởng đo được

`pd.Timestamp("2011-06-30")` là midnight; `<=OBS_END` loại giao dịch ban ngày30/6 khỏi observation và `>OBS_END` đưa chúng vào prediction. Tương tự `<=PRED_END` loại giao dịch ban ngày30/9. Fresh kiểm raw xác nhận **1.186** valid rows30/6 bị chuyển sang prediction và **1.451** valid rows30/9 bị bỏ khỏi prediction. Nếu dùng trọn ngày như paper, observation thành **557.398 rows, 5.041 customers**, churn **65,006943%**; trên khách hàng chung **28 labels đổi**. Vì vậy mọi main number đúng cho cách cắt hiện tại nhưng không phải chính xác cho cửa sổ paper viết. Cần chọn mô tả timestamp hiện hữu hoặc sửa half-open windows rồi rerun; không tự thay số trong paper bằng counts mới mà chưa fit lại. Câu “90-day” cũng cần thành Q3/92-day hoặc đổi horizon tương ứng.

### 2. Important — hai định nghĩa feature không khớp

L thực thi = analysis date minus first purchase, tức tuổi quan hệ tính tới mốc phân tích; L trong paper = last minus first. Chúng khác nhau bởi khoảng từ lần mua cuối tới mốc phân tích, không phải khác biệt cách gọi vô hại. NCR cũng khác: code lưu đúng10 outgoing nearest neighbours, còn graph G thêm cạnh union vô hướng. Fresh kNN-only trên cache, với sklearn1.9.0, tái tạo đúng33.426 edges; undirected degree **10–25**, trung bình **13,26955**, **4.498/5.038** nodes có degree>10. Không có self-neighbour trong dữ liệu hiện tại. Cần định nghĩa NCR trên directed kNN sets trong công thức, hoặc đổi code và rerun. Đây là discrepancy phương pháp, không phải bằng chứng validation labels đã leak.

### 3. Important — claim SHAP/ablation mạnh hơn thực nghiệm

NCR/CCR dùng training labels trong CV đúng như tuyên bố kiểm soát labels (`significance_test.py:236–256`); nhưng SHAP đến từ một model khác về cách tạo aggregate: v2:470–509 dùng tất cả labels, fit full data rồi giải thích800 training samples. Paper:471–484 chưa nêu explicit full-data/in-sample này. Có thể giữ SHAP như exploratory description nếu nói rõ; **không gọi main CV metric bị leak vì SHAP**.

Quan trọng hơn, Seg→Graph thêm **bốn static + hai label aggregate** cùng lúc. Chưa có repeated ablation NCR-only/CCR-only hay static-only. Fresh Graph−Seg LightGBM delta AUC **+.00005118**, pNB **.98693**; NB95% interval **[−.00619687,+.00629923]**. Điều này hỗ trợ “không thấy cải thiện có ý nghĩa của block sáu features”, không hỗ trợ “removing NCR costs nothing” hay equivalence. Trong seed42 static-only .8045→full .8098 có gain .0053; đó vẫn là artifact một partition, cũng chưa cô lập NCR.

### 4. Important — cross-model p đúng nhưng không cô lập feature effect; “only” sai phạm vi

LR/raw RFM vs LGBM/Graph p=.0102306 đổi đồng thời classifier và features. Có thể dùng như comparison hai pipelines, không suy ra features dư thừa hoặc capacity bị tiêu vào variance. Matched RFM classifier change p=.067887; matched Graph classifier change p=.00245722 (delta+.0108312); matched B-LRFM p=.0169628, matched Seg p=.0163305. Các p bổ sung là fresh exploratory, chưa điều chỉnh multiple comparisons.

Ngay Table2 đã có **hai** cross-model AUC comparisons p<.05; hàng thứ ba p=.068 không có ý nghĩa. Do vậy abstract/contributions/conclusion “the only significant comparison” và lời dẫn Table2 “comparisons that do reach significance / All of them…” không chính xác literal. Dùng “significant comparisons favour logistic regression” với phạm vi/metric rõ, và giữ p chưa adjusted được ghi rõ. Những diễn giải “signal close to exhausted”/“capacity spent on variance” chưa được chứng minh bởi chênh hai pipelines.

### 5. Important — hai detector chưa thành controlled repeated experiment; preprocessing là transductive

Leiden thực sự đã chạy và có20 communities/.8323 trong main log. Tuy nhiên repeated-CV/sweep chỉ dựng Louvain và dummy Louvain (`significance_test.py:201–227`); v2 cũng chỉ append Louvain. Auxiliary IMP5 có Leiden AUC nhưng global label aggregates trước CV (`improvements_pipeline.py:421–431`), vì vậy không thể dùng như detector comparison có cùng leakage controls. Câu `main.tex:298–299` cần giới hạn “computed two partitions, prediction experiments use Louvain”. Không thiếu chạy detector; thiếu đánh giá detector tương đương.

Classifier scaler fit fold-local đúng. Nhưng graph scaler, KMeans, communities, và IPT median imputation fit/compute trên tất cả customers trước CV (`significance_test.py:153,185–186,201`). Đây là evaluation transductive dùng covariates validation; không thấy validation labels vào CV NCR/CCR. Paper:292 đã thừa nhận graph cố định feature-only, nhưng claim “standardisation … rather than on full matrix”/“controls apply throughout” cần ghi rõ chỉ scaler classifier. CCR trên training rows còn chứa chính label row đó trong community mean; nên leave-one-out hoặc inner cross-fitting để kiểm bias train/validation target-encoding, chưa được thực nghiệm riêng.

### 6. Important — provenance .398 và clustering numbers cần phân tách

`.398` published reference và `.398` reproduced là hai claim khác nhau. Local comparison file k4 max-k-cut approximation là **.4771**, không phải .398; code reference .398 chỉ là hằng số. Root audit thấy parent segmentation manuscript `../results/paper/main.tex:154,228` báo .398, nhưng không có raw numeric CSV trong parent results để đối chiếu. Vì vậy **không kết luận .398 bịa**; kết luận citation/provenance cho “we reproduce” chưa đầy đủ trong artifact set này. Gắn đúng experiment/source khác hoặc bỏ claim local reproduction. Thêm nữa comparison script dùng toàn bộ transaction history (`compare_methods_v2.py:86–98`), còn churn dùng observation window. Cần ghi sampling/window riêng khi đưa silhouette comparison vào cùng paper.

### 7. Important — negative result hợp lệ ở mức failure-to-reject, không phải zero-effect/noise-floor định lượng

Paper discussion:521 đã tự giới hạn “failure to reject” và phân biệt similarity graph với interaction graph; introduction:73–76 đã giải thích non-contractual/inactivity. Đây là hai điểm xử lý reviewer đúng, không liệt kê là thiếu.

Tuy vậy abstract “idea does not hold”, contribution “neither … improve”, section SHAP “They do not matter” mạnh hơn null tests. Scope hợp lý: **không phát hiện improvement có ý nghĩa trên retailer này, model/hyperparameters này, graph family này, k5/10/15/20**. Không có equivalence test/power study để tuyên bố mọi effect<.005 uninformative. Fresh NB intervals cho graph block chứa cả gain khoảng+.0063. k15 đổi sign theo tuning không tự chứng minh noise; một effect thật cũng có thể phụ thuộc k. Library drift claim .0033 có old vs rerun artifact history trong notes, nhưng không có controlled chỉ-đổi-version experiment; auxiliary code còn global label leakage. Đề nghị trình bày .005 là heuristic cân nhắc, không established detection threshold hoặc causal library estimate.

### 8. Minor/Important — reproducibility có nền tốt nhưng automatic audit không đầy đủ

Fresh thống kê kiểm **5 bộ ×500 rows**, không duplicate FoldId/tier/model,50 scores/tier/model. Mean/delta/bootstrap bounds khớp1e−12, max pNB difference **1,23e−15**. Main và k10 folds byte-identical. Có logs thật; country encoding/spectral clustering đã explicit “not implemented” (`main.tex:552–556`), không phải experiments paper lén claim có. K-sweep đã xong, notes tháng8 nói thiếu là stale.

`audit_paper.py` chạy58 checks/57 reported pass, một “mismatch” .219 vs .2185 do binary float tại tolerance. Không coi đây là numerical misconduct. Script hardcodes claims, không parse table hoặc kiểm cross-model/baseline/windows/SHAP provenance; câu “every number” quá rộng. Comment trỏ `src/knn_sweep.py` không có file; sweep khả thi qua env `LRFM_KNN_K` và `LRFM_OUT_SUFFIX`, cần ghi cả hai để giữ headline CSV. Cache CSV không có fingerprint raw/features/window; reuse cache là tiện ích, chưa tự chứng minh cache khớp current source. Python hiện tại3.14.6/SciPy1.18/sklearn1.9 khác reference3.13.5/SciPy1.17.1/sklearn1.8 và thiếu LightGBM/NetworkX/Louvain/Leiden; chưa verify clean install pinned requirements hay laptop runtime hôm nay. Không được nói full suite đã fresh rerun.

## Artifact fresh và kiểm chứng

- `fresh-statistics.json` + `fresh_experiment_check.py`: paired arithmetic, NB intervals, matched classifier comparisons, checksums của TeX/PDF/main folds/summary; hoàn tất exit0.
- `fresh-data-counts.json` + `fresh_data_check.py`: counts/boundary effects từ raw workbook; không chứa customer records; hoàn tất exit0.
- `fresh-knn-check.json`: kNN-only rebuild từ cache, dependency khác reference được ghi rõ; exit0.
- `fresh-number-audit.txt`: output chạy mới existing audit script; exit0 nhưng một rounding tolerance mismatch.
- `main-pdf-text.txt`: extraction PDF local để đối chiếu claims, không phải compilation/rerender mới.

**Done gate:** arithmetic/result integrity chính đạt; method-description integrity và một số explanatory claims chưa đạt. Không có yêu cầu dataset thứ hai để kết luận scoped negative result này; ưu tiên sửa misdescription/overclaim và minh bạch provenance. Nếu sửa code/windows hoặc muốn claim NCR-specific/detector robustness/zero effect, cần thực nghiệm tương ứng, không thể đạt bằng sửa văn bản đơn thuần.
