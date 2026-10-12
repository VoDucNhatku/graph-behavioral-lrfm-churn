# Review độc lập sổ tay kiến thức #366956

Ngày: 2026-10-13 · Nguồn review: toàn bộ `docs/vietnamese/01-kien-thuc-nen-tang.md`, paper/source đã đọc đầy đủ, audit và manifest/rerun ngày 12/10. Không sửa file 01; root dựng và kiểm PDF.

**Kết luận: không phát hiện lỗi phương pháp hoặc lỗi số học quan trọng. Bảy worked examples cho kết quả đúng khi tính lại. Có hai điểm P3 cần chỉnh ký hiệu/độ rõ trước khi giao.**

## Findings

1. **P3 — Sai ký hiệu ngày mua cuối ở dòng 99.** `$t_{mathrm{last}}$` thiếu backslash trước `mathrm`; nên là `$t_{\mathrm{last}}$`, thống nhất với dòng 104 và các công thức sau. Hiện renderer có thể đọc “mathrm” thành các chữ biến trong subscript. Đây là typo ký hiệu, không làm sai phép tính L/R trong ví dụ.

2. **P3 — Minh họa 4, dòng 292, mở rộng tập validation mà chưa đặt tên khách mới.** Ban đầu có sáu khách A–F, train A–D và validation E/F. F lại có E và “một khách validation khác trong ví dụ mở rộng”. Arithmetic fallback 0,5 đúng, nhưng người đọc có thể tìm một khách thứ ba không tồn tại trong cohort đã nêu. Nên ghi rõ thêm G thuộc validation hoặc mô tả F không có train neighbour mà không dùng khách mới chưa định nghĩa. Đây là độ rõ của ví dụ, không phải validation-target leakage.

## Tính lại bảy worked examples

Đã chạy script độc lập bằng Python 3.13.5; metrics dùng sklearn trong môi trường ghim. Các checks exit 0.

| Ví dụ | Kết quả tính lại | Verdict |
|---|---|---|
| 1. Midnight boundary | Current obs=[False,False], pred=[True,False]; whole-day obs=[True,False], pred=[False,True] | B không thuộc current cohort; cửa sổ sửa cho label 0 đúng |
| 2. Chín features | F=3, M=120, AOV=40, basket=2, diversity=4, cancel=0,25, L=181, R=30, span=151; gaps59/92, IPT75,5 | Đúng toàn bộ |
| 3. kNN/union | A→B, B→C, C→B, D→C; union AB/BC/CD; degrees1/2/2/1 | Đúng |
| 4. NCR/CCR | Mean train0,5; NCR(E)=1, full NCR(E)=2/3; fallback0,5; CCR(A/B/E)=0,5; LOO A=0/B=1; singleton A=1 | Đúng; cần làm rõ khách mới ở finding2 |
| 5. AUC/AP/threshold | AUC=0,6666667; AP=0,7555556; threshold0,5: TP2/FP1/FN1/TN2, P/R/F1=2/3; threshold0,2: TP3/FP2/FN0/TN1, P=0,6/R=1 | Đúng cả ranking và threshold metrics |
| 6. Correction | Mean0,002; sample variance6,666667e−6; naive SE0,001290994/t1,549193; corrected SE0,001825742/t1,095445 | Đúng với tỷ lệ test/train minh họa1/4 |
| 7. Attribution toy | f(2,2)=4; symmetric φ1=φ2=2; refit g=2x1 cho cùng score trên toàn population x2=x1 | Đúng trong assumptions đã ghi; không phải retail TreeSHAP |

Ví dụ 50 differences trong mục 16 cũng đúng: factor0,27; naive SE0,001414214/t2,121320; corrected SE0,005196152/t0,577350. Các phép phụ đúng: weighted degree1,6; standardized differences đều0,5; independent16-test FWER≈0,559873; balanced class weights≈0,766819/1,436965.

## Phương pháp, assumptions và phạm vi đã kiểm

- **Định nghĩa features/label:** tách invoice rows/customer; cancellations và positive purchase filtering; L code khác first-to-last; IPT invoice-level/median; midnight windows và counts tác động đúng audit. Không gán label bất hoạt thành rời bỏ vĩnh viễn hoặc bất mãn.
- **Graph/NCR/CCR:** outgoing kNN khác union vô hướng; NCR không weighted; graph degree không fixed k; CCR training có self-label; fallback dùng mean train. Số 5.038/33.426, degree10–25 và 23 dummies/38 full features tại k10 khớp evidence.
- **Evaluation:** hai classifier main, 50 folds/configuration và 500 rows; shared pairing, transductive graph preprocessing khác fold-local classifier scaler; random repeated CV khác temporal backtest. NB variance factor và df49 đúng code, có nêu correction là xấp xỉ. Bootstrap resampling assumptions/overlap limitation, Wilcoxon dependence, multiple tests, failure-to-reject khác equivalence đều được giải thích đúng.
- **Metrics:** phân biệt AUC/ranking với confusion matrix/threshold; AP không dùng trapezoid interpolation, đúng [tài liệu sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Prevalence65,2% được dùng đúng phạm vi, không coi churn là lớp positive hiếm.
- **SHAP:** nói rõ raw margin/log-odds của default TreeExplainer cho LightGBM binary, đúng [tài liệu SHAP](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html). Full-data SHAP được giữ như mô tả hợp lệ có giới hạn; không suy ra CV leak, held-out attribution, causal effect hoặc NCR-only contribution. Toy7 có nêu dependence/background và refit.
- **Results/status/novelty:** Table1–3 giữ số nguồn; tách cross-model khỏi feature effect; không gọi null result là zero effect. Actual rerun17m42/cache mới, RAM khác nhẹ, chưa corrected-window fit, chưa Colab run được ghi đúng. Không thổi novelty, detector robustness, .398 reproduction provenance hoặc business validation.

Một chi tiết có thể thêm khi giảng, không phải bug: StandardScaler dùng SD với ddof=0, trong khi sample SD của fold scores/differences dùng ddof=1; source đã không đồng nhất chúng, nên hiện không có mâu thuẫn. [Tài liệu StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).

Review này kiểm nội dung và toán toy, không chạy lại model suite hoặc thay source. Chỉ hai finding P3 cần quyết định chỉnh; sau chỉnh root cập nhật hash/line mapping và render lại PDF tương ứng.
