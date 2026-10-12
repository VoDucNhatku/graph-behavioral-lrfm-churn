# Review độc lập báo cáo tổng hợp

> Worker: hallucination-guard · Ngày: 2026-10-13 · Phạm vi: `docs/vietnamese/04-bao-cao-tong-hop.md` · Review chỉ đọc, không sửa báo cáo.
>
> SHA256 bản review: `708980a9179a22fb20497cc1039dcab51630e5106d7959ff0f1b09ad4f1a9f80`.

**Không phát hiện lỗi factual, số liệu hoặc suy luận nhân quả cần sửa trong phần nghiên cứu/thực nghiệm. Có một điểm trạng thái bàn giao cần đóng sau khi dựng PDF.**

## Finding cần đóng trước bàn giao

- **P2 — Trạng thái bốn PDF/font còn phụ thuộc bước build.** Dòng 215 ghi “Bốn PDF + Markdown”; dòng 229 ghi font được embed. Tại thời điểm review, listing trực tiếp `docs/vietnamese` có bốn Markdown và script build, chưa có bốn PDF. Đây là kiểm tra bàn giao đang chờ root hoàn tất, không phải lỗi số liệu khoa học. Cách đóng: dựng đủ bốn PDF, xác minh trang và font được nhúng rồi giữ nguyên các câu này; nếu build không hoàn tất, sửa trạng thái về chưa tạo/chưa xác minh. Mức tin cậy: cao đối với trạng thái filesystem lúc review.

## Đã đối chiếu

- Paper gốc đầy đủ 12 trang, `main.tex`, `main.bbl`: tiêu đề, tác giả, ba bảng, phạm vi negative result, hai hàng Table 2 có p<0,05, và các claim bản dịch phải giữ nguyên.
- Đọc trực tiếp CSV raw/RAM và cache-k10 mới: cả năm AUC, pNB, delta và mức sai khác đúng với báo cáo. Hai bộ đều có 16 phép thử với p nhỏ nhất 0,1441629129111896; cách diễn giải failure-to-reject đúng phạm vi.
- Đọc manifest actual-run: 10 jobs đều exit 0, thời gian từng job khớp, 14 dependency đều đúng phiên bản, dấu thời gian tương ứng khoảng 17 phút 42 giây, source/dataset unchanged. Không suy audit exit 0 thành kiểm chứng mọi claim.
- Đọc source thật: định nghĩa L, timestamp boundary, outgoing kNN/union graph, CCR chứa self-label, preprocessing transductive, scaler classifier fold-local và final-fit SHAP đều được mô tả đúng; report phân biệt NCR-only ablation chưa chạy với việc block sáu đặc trưng đã chạy.
- `fresh-data-counts.json` xác nhận 1.186/1.451 giao dịch boundary, 5.041 khách và 28 labels đổi trong cửa sổ ngày trọn vẹn; báo cáo không gọi đó là corrected-window model run.
- Listing source xác nhận sáu script với tổng 2.333 dòng. Notebook thật có 16 cells, 9 code cells; evidence ghi rõ chưa actual Colab run. Các local links của báo cáo đều trỏ tới file tồn tại. Hash PDF thực tế khớp `b3803266…b6bbd2`.

Mức tin cậy: cao cho các số/định nghĩa vừa đối chiếu bằng nguồn và artifact thật; vừa cho nguồn gốc accept/review dựa trên identity evidence đã đọc. Phần chính sách hội nghị ngày 13/10 do root đã browse, không được review này xác minh web độc lập thêm. Báo cáo không đánh đồng Accepted với thanh toán, camera-ready đã nộp hoặc đã xuất bản; không xác nhận track/presenter ngoài bằng chứng hiện có.
