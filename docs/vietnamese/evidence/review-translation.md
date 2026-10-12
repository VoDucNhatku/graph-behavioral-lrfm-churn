# Review độc lập bản dịch paper #366956

Ngày: 2026-10-13 · Phạm vi: fidelity của `docs/vietnamese/03-ban-dich-paper.md` và `translation-coverage.json` so với toàn bộ `paper/main.tex`, PDF 12 trang, bibliography/BBl. Không sửa nguồn bản dịch. Không đánh giá lại tính đúng của mọi claim khoa học trong paper.

**Kết luận: không phát hiện lỗi dịch quan trọng làm đổi số, đổi kết luận hoặc bỏ nội dung. Bản dịch giữ đủ cấu trúc và nội dung chính của paper. Hai gợi ý P3 bên dưới là chỉnh rõ thuật ngữ/glossary, không phải lỗi số liệu hay thiếu đoạn.**

## Findings

1. **P3 — Cụm “mô hình đồ thị tăng cường gradient” có thể làm người đọc hiểu sai đối tượng được boosting.** Ở dòng 14 và 125, nguồn viết “gradient-boosted graph model”, trong ngữ cảnh là classifier tăng cường gradient dùng biểu diễn đồ thị. Bản dịch hiện vẫn giữ referent nhưng tiếng Việt dễ được đọc thành thuật toán tăng cường chính graph. Có thể đổi cụm này thành “mô hình tăng cường gradient sử dụng đặc trưng đồ thị”; không thay model, số 38 features hoặc claim nguồn. Dòng 135 đã diễn đạt rõ hơn theo hướng đó.

2. **P3 — Glossary “basket size” chưa rõ loại lượng được đo.** Dòng 258 bổ sung “Đại lượng về lượng hàng trong giỏ”, có thể được hiểu là tổng quantity. Paper chỉ nêu tên biến, còn implementation tính trung bình số StockCode khác nhau trong mỗi invoice. Vì glossary là phần bổ sung đã được đánh dấu, có thể viết “Đại lượng mô tả kích thước giỏ; trong implementation là số loại sản phẩm khác nhau trung bình mỗi hóa đơn.” Không cần chèn định nghĩa mới vào nội dung dịch trung thành của Section 4.2.

## Các phần đã đối chiếu và đạt

- **Table 1:** đủ năm rows, single-seed/repeated columns, mọi dấu delta, pNB và bold 0.8098 khớp nguồn. Không đưa các số raw/RAM rerun tháng 10 vào bảng nguồn.
- **Table 2:** ba cặp model/feature, deltas +0.0113/+0.0099/+0.0078, ba CI và p 0.001/0.010/0.068 khớp; hai p đầu giữ bold đúng nguồn.
- **Table 3:** bốn k, edge/community counts, dấu delta và p đều khớp. Đoạn giải thích sweep và đổi dấu được dịch đủ.
- **Equation (1):** LaTeX khớp source sau chuẩn hóa whitespace; giữ variance correction, n=50, tỷ lệ test/train 1/4, vị trí số phương trình và toàn bộ lời giải thích bootstrap dependence.
- **Citations:** đối chiếu bằng script toàn bộ 28 nhóm citation trong body và riêng từng 52 prose/list units; số và thứ tự đều khớp `\cite` → thứ tự `\bibitem` thực của BBl. Bibliography đủ [1]–[17], đúng thứ tự/key; tên/metadata, DOI và các nguồn không có DOI được giữ theo nguồn.
- **Limits:** đủ sáu mục Single dataset, One graph family, Planned components not implemented, Metric choice, Targeted literature search, No business validation. Không âm thầm biến Country/SpectralClustering thành đã triển khai.
- **Conclusion/repro/declaration:** đủ hai đoạn kết luận, repository/tag, versions, nguồn fold figure, claim dưới mười phút/no GPU, và tuyên bố Claude/Anthropic cùng trách nhiệm tác giả. Không bỏ disclaimer “failure to reject a null” ở Discussion 9.2.
- **Figures:** đã xem cả hai PNG. Figure 1 giữ hướng luồng hai hàng, các nhãn và số; Figure 2 giữ model/tier labels, mean/bands ±1 SD và annotation ≈0.010 là gap AUC, không biến thành p-value.

## Lưu ý về fidelity và manifest

Các câu mạnh về “only significant comparison”, “removing it costs nothing”, L first-to-last, “we reproduce .398”, kiểm soát preprocessing/Leiden, noise floor và runtime được giữ như original. Chúng là vấn đề của bản nguồn đã ghi trong audit, **không phải lỗi dịch cần sửa trong một bản dịch trung thành**. Version note và glossary đã được tách khỏi body.

Các gloss tiếng Anh tạo thêm spans math ở P001/P003/P004/P027 (t, k, l2); không thấy mất hay đổi công thức nguồn. Do đó `per_unit_inline_math_preserved` nên được hiểu là giữ công thức nguồn, không phải số lượng spans inline bằng nhau tuyệt đối.

Fresh verification: hashes của năm source files trong manifest khớp current files; equation/citation/table checks exit 0; hai assets tồn tại và đã xem. Review không sửa Markdown/coverage/assets và không build PDF. Root giữ quyền quyết định hai chỉnh thuật ngữ tùy chọn rồi cập nhật line/hash manifest nếu áp dụng.
