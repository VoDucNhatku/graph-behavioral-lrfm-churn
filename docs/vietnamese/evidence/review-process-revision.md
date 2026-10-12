# Rà soát bản quy trình mở rộng và sửa PDF

Paper #366956 · 13/10/2026 · Người thực hiện: root/editor. Đây là rà soát của người sửa, không phải một review độc lập mới hoặc một lượt train mới.

## Phản hồi và lỗi đã xác định

Người dùng chỉ ra sơ đồ hiện mã Mermaid, chữ bị cắt và nội dung quy trình chưa đủ sâu. Bản cũ coi mọi fenced block là code; mỗi dòng được vẽ bằng một Paragraph có background và padding. Background của dòng sau đè lên phần glyph của dòng trước. Kiểm text extraction, bounds và source paragraph coverage trước đó không phát hiện được vì glyph vẫn tồn tại trong PDF. Rà hình trước đó đã bỏ sót lỗi; không giữ kết luận rằng bản cũ không có lỗi bố cục.

Kiểm paint order mới phát hiện **15 trường hợp opaque vector fill che text** trong PDF quy trình ở commit `901aaf8`. Bản mới không còn trường hợp này. Mermaid bị từ chối trong PDF builder nếu chưa chuyển thành hình. CodeBlock mới vẽ một background trước toàn bộ text, tính wrap theo font width, chia đoạn dài theo line và giữ đoạn ngắn cùng trang. Sơ đồ quy trình/fold/windows được dựng sẵn với nhãn tiếng Việt; đường nối nhánh mô tả đi ngoài các hộp để không che nội dung.

## Nội dung được mở rộng

- Hướng dẫn đọc và câu trả lời trực tiếp cho chủ đề, bài toán, mục tiêu/đóng góp, phương pháp và tiến độ.
- Hợp đồng so sánh: biến thay đổi, yếu tố giữ cố định, cùng-classifier versus cross-model, 16 main comparisons và giới hạn inference.
- Từ điển tám cột raw, quy tắc làm sạch và ví dụ invoice/cancellation.
- Windows/cohort và sơ đồ ranh giới timestamp; phân biệt temporal label construction với temporal model validation.
- Từ điển chín features và tính tay một khách: L/R/F/M/AOV/basket/diversity/cancellation/IPT.
- Graph distance/weights, outgoing-versus-union, static features/dummies/row mapping và scope transductive.
- Training estimators/solver iterations, 500 fits/main, FoldId/pairing và điều kiện nhận per-fold CSV.
- Ví dụ tám khách tính NCR/CCR, self-label CCR, dự báo giả định và AUC/AP/F1/accuracy; điều kiện label availability khi triển khai.
- Ví dụ standard error Nadeau–Bengio, pseudocode có scope covariates/labels và artifact contract.
- Cách đọc số làm tròn, phân tầng bằng chứng, reviewer/correction decision table, tiến độ và quy trình bàn giao nhóm.
- Phụ lục chạy local/Colab, checkout tham chiếu đúng commit, mười job có thời gian thực, artifact lookup, mẫu trình bày và mười câu hỏi có đáp án.

## Các kiểm tra

`check_process_revision.py` kiểm links, Mermaid guard, feature/date/IPT arithmetic, tám NCR values, AUC/AP/F1/accuracy, ví dụ SE và mười durations từ manifest. Một probe 90 rows ép wrapping/pagination giữ mỗi ID đúng một lần trên hai trang và không có opaque overpaint. Kiểm tra này không train model.

`validate_pdfs.py` kiểm cả bốn PDF: glyphs, bounds, source paragraphs, bookmarks, paint order và không có raw `flowchart TD`; tạo contact sheets để đọc bố cục. Bản quy trình mới có 34 trang, 64 bookmarks và 185 prose snippets khớp. Bằng chứng số/hash chi tiết nằm trong `pdf-validation.json` và `process-revision-checks.json`. Root xem lại toàn bộ 34 trang final qua contact sheets và xem cỡ lớn các sơ đồ, code blocks, ví dụ/bảng cần thiết.

## Fidelity và giới hạn

Bảng kết quả paper và evidence khoa học được giữ nguyên. Counts corrected-window vẫn chỉ là kiểm đếm; chưa có model fit mới. Mọi tính tay đều gắn nhãn giả định. Khác biệt RAM/cache vẫn chưa được cô lập nguyên nhân. Chưa có Colab execution, NCR-only ablation, temporal/external/business validation hoặc camera-ready mới trong đợt sửa tài liệu này.

Ba PDF còn lại giữ nguyên byte; ZIP bộ tài liệu được cập nhật bằng bản quy trình mới. Bộ bốn PDF hiện là 23/34/18/11 trang, tổng 86. Tài liệu này ghi trạng thái kiểm bản sửa, không thay review độc lập lịch sử `review-process.md`.
