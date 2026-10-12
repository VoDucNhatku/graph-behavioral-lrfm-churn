# Review độc lập tài liệu quy trình nghiên cứu

Paper #366956 · Tài liệu: `docs/vietnamese/02-quy-trinh-nghien-cuu.md` · Reviewer: `knowledge_handbook` · Ngày: 2026-10-13 · Chỉ đọc, không sửa source02.

## Kết luận

**Không phát hiện lỗi P1/P2 về phương pháp, số liệu hoặc mức độ mạnh của kết luận trong bản được review. Tài liệu có thể chuyển sang dựng PDF và visual QA.** Những chỗ paper nói mạnh hơn bằng chứng được tài liệu nhận diện đúng, không được sao chép như kết luận đã xác nhận. Có ba điểm làm rõ P3 tùy chọn ở cuối report; chúng không phải điều kiện chặn hoàn tất.

Độ tin cậy: **cao** cho đối chiếu paper/code và trạng thái artifact đã được kiểm; **vừa** cho các suy luận về triển khai/ngữ nghĩa rộng hơn. Review này không chạy lại model, không xác minh một lần Colab mới, không deep-read lại toàn văn mọi bài trong bibliography và không chứng minh novelty ngoài phạm vi search hiện có.

## Phạm vi và bằng chứng đọc

- Đã đọc toàn bộ source02; các đoạn bị tool output cắt giữa Chương 3 được đọc lại theo range, gồm 3.2–3.5.
- Kế thừa full fresh reading trong cùng phiên: toàn bộ `paper/main.tex`, PDF `paper/main.pdf` 12/12 trang và 17 entries `paper/refs.bib`.
- Đối chiếu implementation đã đọc: `src/run_pipeline_v2.py`, toàn `src/significance_test.py`, các đoạn liên quan của `src/compare_methods_v2.py` và `src/improvements_pipeline.py`.
- Đối chiếu `notes/reproduce-20261012/report.md`, `comparison.json`, `run-manifest.json`, cùng `notes/fisat-2026-audit/experiment-audit.md`. Report/manifest rerun cập nhật các facts chạy model mà audit trước đó chưa có; findings phương pháp không được coi là đã resolved.
- Đọc và áp dụng `hallucination-guard` mode scan/source-check; không có claim khoa học bị xác định là fabricated trong source02.

SHA256 source02 tại thời điểm review: `170428cf5dbf702d14ff39ddc8a28e7dc52878651fcae13defefe650c5a0217f`.

## Các hạng mục đạt

| Hạng mục | Đánh giá | Bằng chứng trong source02 |
|---|---|---|
| Chủ đề, đơn vị, nhãn | Đạt | Lời mở đầu; 1.1–1.4; 3.2–3.5 |
| EFA/CFA và mẫu khảo sát | Đạt | Dòng 35 phủ định đã dùng khảo sát/EFA/CFA/SEM; Phụ lục B là chuyển chức năng mục lục |
| Giả thuyết và preregistration | Đạt | Dòng 101 gọi rõ là tái dựng vận hành, không đăng ký trước; bảng chỉ ra NCR-only chưa làm |
| Novelty scope | Đạt | Dòng 37: công cụ đã có, targeted search, không priority/algorithm/improvement claim |
| Date/L/NCR discrepancies | Đạt | 3.4–3.8 giữ cả paper và code, counts sửa chỉ là kiểm đếm chưa fit |
| Covariates/target scopes | Đạt | 1.4, 3.5–3.9: graph transductive, classifier scaler fold-local, CCR self-label còn tồn tại |
| Tables 1–3 | Đạt | Chương 4 giữ đúng số paper, với context cached/archived và raw first-run riêng |
| SHAP và causality | Đạt | 3.12/4.4: full-data descriptive, không NCR-only ablation, không attribution→AUC claim |
| Cross-model inference | Đạt | 4.2: hai p<.05; đổi cả model/features; không cô lập graph effect |
| Null/equivalence | Đạt | 2.3, 4.1, 5.2: failure-to-reject; không zero-effect/noise-floor guarantee |
| Reproducibility status | Đạt | 10 jobs CPU/17m42; RAM/cache phân biệt; cửa sổ sửa và full Colab chưa chạy |
| Baseline/business | Đạt | 4.4/5.1: .398 provenance thiếu; silhouette khác space; profiles chưa campaign validation |

### EFA/CFA replacement

Việc đổi cấu trúc năm chương sang ML là phù hợp. Tài liệu không dùng EFA/CFA như bằng chứng đã kiểm định một thang đo và không gọi dummy/communities là latent constructs. Phụ lục B thay vai trò của phần kiểm định trong một quy trình khảo sát bằng kiểm feature construction, tier comparisons và paired CV; đây là thích ứng mục lục, không là tương đương toán học giữa các phép kiểm định. Lời mở đầu và Chương 2 đã nêu giới hạn đủ rõ. Không cần thêm EFA/CFA vào thí nghiệm để “đủ mẫu chương”.

### Number/status checks

Table 1 khớp main archived/cached k10: mean AUC `.8066/.8074/.8054/.8044/.8044`, pNB `.755/.742/.561/.590`, delta graph `−.0021`. Table 2 khớp paper `.0113/.0099/.0078`, p `.001/.010/.068`; hai hàng đầu significant chưa điều chỉnh, hàng thứ ba không. Table 3 giữ đúng edges `16902/33426/50054/66652`, communities `31/20/16/16`, delta/p của bốn k.

Source02 cũng giữ riêng Graph raw/RAM `.804533`, delta `−.002021`, p `.606129` với cached `.804422`, delta `−.002130`, p `.590480`. Đây khớp các trường `headline_means` và `cached_k10_means` của `comparison.json` đã mở lại trong review. `main_min_pNB=.144162912911...`, cohort `5038`, churners `3285`, rate `.652044462...` cũng khớp. Không thấy đem whole-day corrected counts thay vào bảng AUC chưa fit.

Các số SHAP `1.087/0.560/0.250/0.224/0.215` được trình bày đúng bản chất model full-data. Claim “bỏ NCR cost=0” đã được thu hẹp đúng thành chưa thấy gain của graph block. Baseline .398 là published reference, .4771 là local approximation khác provenance; tài liệu không gọi .398 là fabricated.

## Điểm làm rõ P3 tùy chọn

| Vị trí source02 | Điều có thể làm rõ | Cách sửa nhỏ nếu chọn |
|---|---|---|
| Dòng 227, 3.8 | “training IDs” có thể bị đọc là CustomerID raw; graph/code thực dùng vị trí dòng | Ghi T là tập chỉ số dòng/node 0…n−1, với mapping sang CustomerID |
| Dòng 269/307 | Câu multiple comparisons đang nhấn exploratory bổ sung; các p main/Table 2 cũng chưa family-adjusted | Ghi rõ pNB đã hiệu chỉnh overlap, chưa hiệu chỉnh họ nhiều phép so sánh |
| Dòng 275/322 | Số mean absolute SHAP lớn hơn 1 không thuộc probability scale | Thêm một câu raw margin/log-odds hoặc dẫn §18 sổ tay kiến thức |

Đây là làm rõ để phần quy trình đứng độc lập hơn; không phát hiện source02 đang tuyên bố ngược lại. Phần availability của labels NCR/CCR khi triển khai prospective đã được giải thích chi tiết ở sổ tay kiến thức; có thể cross-reference, không cần mở một thí nghiệm mới chỉ để hoàn thiện prose này.

## Kiểm tra kỹ thuật mới sau khi đọc

Đã chạy `.tmp/review_process_check.py` bằng Python 3.13.5 reference; exit 0. Source02 có 7.937 từ whitespace; 35 biểu thức toán parse được bằng matplotlib mathtext, **0 lỗi toán**; **0 link nội bộ thiếu**. Source02 không bị sửa. Root thực hiện PDF rendering/visual QA; kiểm text/math này không thay thế visual QA.
