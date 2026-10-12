# Bộ tài liệu tiếng Việt - paper #366956

Biên soạn ngày 13/10/2026 cho thành viên đã biết Python và machine learning cơ bản.

| Tài liệu | Nội dung | PDF | Nguồn editable |
|---|---|---|---|
| 01. Sổ tay kiến thức | Nền tảng, công thức, ví dụ tính toán, cách đọc paper, câu hỏi ôn tập | [Đọc PDF](../../output/pdf/01-kien-thuc-nen-tang-paper.pdf) | [Markdown](01-kien-thuc-nen-tang.md) |
| 02. Quy trình nghiên cứu | Năm chương từ câu hỏi đến thiết kế, phân tích, kết quả và bàn giao | [Đọc PDF](../../output/pdf/02-quy-trinh-nghien-cuu.pdf) | [Markdown](02-quy-trinh-nghien-cuu.md) |
| 03. Dịch toàn bộ paper | Giữ đủ nội dung, công thức, ba bảng, hai hình, citations và 17 references | [Đọc PDF](../../output/pdf/03-ban-dich-paper-tieng-viet.pdf) | [Markdown](03-ban-dich-paper.md) |
| 04. Báo cáo tổng hợp | Hội nghị, accepted identity, code/data, actual rerun, audit và tiến độ | [Đọc PDF](../../output/pdf/04-bao-cao-tong-hop.pdf) | [Markdown](04-bao-cao-tong-hop.md) |

Đọc theo thứ tự **01 → 02 → 03**, dùng **04** để tra trạng thái và giới hạn bằng chứng. Hai tài liệu đầu đều giải thích đề tài, bài toán, mục tiêu/đóng góp, phương pháp nghiên cứu, code/kết quả đã có và việc còn thiếu. Bố cục quy trình tham khảo ảnh mục lục của tác giả, nhưng thay survey/EFA/CFA bằng cohort giao dịch, feature engineering, graph và paired CV phù hợp paper.

Bản dịch là phiên bản accepted gốc, **chưa phải camera-ready đã sửa**. Những phát biểu gốc được dịch trung thành; các điểm lệch mô tả/code và diễn giải mạnh hơn bằng chứng được giải thích trong tài liệu 01/02/04. Full-data SHAP không tự động sai; cần phân biệt descriptive attribution và predictive ablation. Bộ tài liệu này không thay source paper hoặc kết quả khoa học gốc.

[Notebook Colab](../../notebooks/366956-reproduce.ipynb) · [Hướng dẫn chạy](../../notebooks/HUONG_DAN_COLAB.md) · [Aggregate outputs mới](../../results/reproduction-20261012) · [Evidence index](evidence/README.md).

Chạy local 12/10/2026: 10 jobs thành công, 17m42 trên Windows CPU/Python3.13.5. Cached new k10 khớp archived main; first raw/in-memory CV lệch nhẹ, giữ nguyên failure-to-reject finding. Notebook đã validate local; chưa thực chạy Colab. Chưa fit corrected-window models, chưa NCR-only repeated ablation, chưa external/business validation, chưa sửa/nộp camera-ready trong phiên này.

PDF có font tiếng Việt được embed, mục lục và bookmarks. Các ví dụ nhỏ trong sổ tay là minh họa, không phải thêm experiment mới của paper. Thuật ngữ tiếng Anh được giữ để đối chiếu.

## Dựng lại tài liệu

Các PDF dựng bằng Python và ReportLab. Cần `reportlab`, `matplotlib`, `pandas`, `pillow`, `pymupdf`, cùng Arial trên Windows hoặc DejaVu Sans trên Linux.

```bash
python docs/vietnamese/build_figures.py
python docs/vietnamese/build_pdfs.py
python docs/vietnamese/validate_pdfs.py
```

`build_figures.py` dùng translated-label manifest và CSV archived để vẽ hình đúng số. `build_pdfs.py` đọc bốn Markdown và assets; math/cache/render trung gian nằm ở `tmp/pdfs` và không publish. `validate_pdfs.py` kiểm pages, text bounds, glyphs, nội dung prose và tạo contact sheets cho người đọc kiểm bố cục. `collect_evidence.py` là script bảo trì để xuất evidence từ local rerun notes; nó cần notes local, không cần để đọc hoặc dựng lại PDF đã public.

Nguồn chính: [paper gốc](../../paper/main.pdf), [code](../../src), [BibTeX](../../paper/refs.bib), UCI Online Retail II và các nguồn phương pháp/công cụ trực tiếp được trích trong tài liệu. Dữ liệu UCI: Chen (2012), DOI 10.24432/C5CG6D, CC BY 4.0. Không đóng gói raw XLSX, per-customer cache, email riêng hoặc authentication token.
