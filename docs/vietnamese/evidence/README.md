# Bằng chứng cho bộ tài liệu tiếng Việt

Đối chiếu nguồn và thực nghiệm ngày 12/10/2026, tài liệu biên soạn ngày 13/10/2026.

- `reproduction-manifest.json`: actual local CPU run, input/source hashes, đúng dependency ghim, 10 jobs và thời gian/exit codes. Đây là bản public bỏ đường dẫn máy cá nhân.
- `source-identity.json`: 43 tracked files được đối chiếu với remote tree tại commit `fdbbccf`. Con số này là snapshot trước khi thêm bộ tài liệu, không phải tổng số file repo sau publication.
- `paper-identity.json`: PDF author cung cấp có nội dung trùng local 12 trang, chỉ thêm một byte CR. Nguồn gốc submission file theo author; chưa tải Confy lại.
- `uci-download-verification.json`: XLSX tải trực tiếp từ UCI cùng SHA256 với raw local.
- `comparison.json`, `paper-vs-rerun.csv`, `archive-vs-rerun.csv`: kiểm tra số paper và archived outputs. Initial raw/RAM main lệch nhẹ; cached new k10 exact archived main.
- `notebook-verification.json`: nbformat, code-cell compile, helper comparison/data hash/export checks; không phải actual Colab run.
- `aggregate-output-hashes.json`: hashes các CSV được public từ fresh run ở `results/reproduction-20261012`.
- Coverage manifests đi kèm ghi sections, concepts và translation units được đọc/biên soạn; chúng là traceability của tài liệu, không thay model evidence.

Raw XLSX, per-customer feature cache, email riêng và authentication token không nằm trong package. Các file bằng chứng không sửa kết luận của paper gốc hoặc chứng minh các experiments chưa chạy. Xem báo cáo tổng hợp cho method discrepancies, reviewer feedback và trạng thái camera-ready.
