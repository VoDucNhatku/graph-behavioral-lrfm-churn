# Khi các đặc trưng lân cận suy ra từ đồ thị không giúp ích: Đánh giá có kiểm soát rò rỉ dữ liệu đối với dự báo khách hàng rời bỏ bằng Behavioural-LRFM trong bán lẻ phi hợp đồng

> id: 366956 · nguồn: `paper/main.pdf` và `paper/main.tex` · worker: vi-translate · ngôn ngữ đích: vi · ngày: 2026-10-13
>
> Bản dịch trung thành, đầy đủ của phiên bản đã nộp và được chấp nhận; đây chưa phải bản camera-ready đã chỉnh sửa. Các khẳng định khoa học, định nghĩa, số liệu và trích dẫn được giữ theo bản nguồn. Khuyến nghị kiểm toán được trình bày trong tài liệu riêng. Bảng thuật ngữ ở cuối là phần bổ sung của người dịch, nằm ngoài nội dung bài báo gốc.

**Duc Nhat Vo**

FPT University, Thành phố Hồ Chí Minh, Việt Nam
voducnhat242006@gmail.com

## Tóm tắt

Đồ thị tương đồng khách hàng (customer similarity graph) là một thành phần bổ sung hấp dẫn cho các mô hình khách hàng rời bỏ (churn) theo kiểu RFM. Nếu sự rời bỏ lan truyền trong các nhóm khách hàng tương đồng về hành vi, tỷ lệ rời bỏ trong số những khách hàng lân cận gần nhất của một khách hàng sẽ giúp dự báo sự rời bỏ của chính khách hàng đó. Chúng tôi kiểm tra ý tưởng này trên bộ dữ liệu Online Retail II với hai biện pháp kiểm soát. Thứ nhất, tỷ lệ rời bỏ của nhóm lân cận và của cộng đồng được tính lại bên trong từng phần huấn luyện (training fold), để không có nhãn kiểm tra nào đi vào ma trận đặc trưng. Thứ hai, mỗi phép so sánh được thực hiện qua mười lần lặp của kiểm định chéo năm phần (five-fold cross-validation) và được đánh giá bằng kiểm định $t$ lấy mẫu lại có hiệu chỉnh (corrected resampled $t$-test), thay vì bằng một lần chia dữ liệu. Với các biện pháp kiểm soát này, ý tưởng đó không đứng vững. Không tầng đặc trưng (feature tier) nào vượt qua mô hình cơ sở (baseline) RFM đơn giản với ba biến, xét theo ROC-AUC hay PR-AUC, với bất kỳ bộ phân loại (classifier) nào trong hai bộ phân loại. Phát hiện này vẫn đúng khi bậc đồ thị (graph degree) thay đổi từ 5 đến 20. Tầng tăng cường đồ thị đạt mức tăng $+0.0033$ ROC-AUC trên một cách chia các phần dữ liệu và đổi dấu khi xét qua mười lần chia. Phép so sánh duy nhất có ý nghĩa thống kê lại chỉ theo hướng ngược lại: hồi quy logistic (logistic regression) trên ba biến RFM thô vượt qua mô hình tăng cường gradient dùng đặc trưng đồ thị (gradient-boosted) với 38 đặc trưng ($p = 0.010$). Việc quy gán đóng góp (attribution) và đóng góp thực tế cũng tách rời nhau, vì tỷ lệ rời bỏ của nhóm lân cận đứng thứ ba theo SHAP nhưng việc loại bỏ nó không làm mất đi hiệu quả dự báo. Chúng tôi báo cáo quy trình (pipeline), các biện pháp kiểm soát và kết quả âm tính (negative result), đồng thời lập luận rằng đánh giá bằng một lần chia dữ liệu không thể tách một hiệu ứng nhỏ như vậy khỏi nhiễu do cách chia các phần dữ liệu (fold noise).

**Từ khóa:** Dự báo khách hàng rời bỏ · RFM · Đồ thị tương đồng khách hàng · Phát hiện cộng đồng (community detection) · Kiểm định chéo lặp lại (repeated cross-validation) · Kết quả âm tính.

## 1 Giới thiệu

Bán lẻ phi hợp đồng (non-contractual retail) không cung cấp tín hiệu hủy bỏ quan hệ. Một khách hàng ngừng mua hàng không thông báo điều đó, nên sự rời bỏ phải được định nghĩa bằng việc không hoạt động trong một khoảng thời gian đã chọn, và nhiệm vụ mô hình hóa là dự báo sự không hoạt động đó từ lịch sử mua hàng. Biểu diễn RFM — độ gần đây (recency), tần suất (frequency), giá trị tiền tệ (monetary value) — đã là hệ khái niệm làm việc của bài toán này trong nhiều thập niên, và một khối lượng lớn tài liệu ứng dụng mở rộng nó: thêm độ dài quan hệ (relationship length), thêm các thuộc tính nhân khẩu học (demographic attributes) [9], hoặc triển khai bộ ba này theo thời gian [14].

Một hướng nghiên cứu gần đây hơn xem tập khách hàng là một đồ thị thay vì một bảng. Corrêa Vianna Filho và cộng sự phát biểu bài toán phân khúc RFM thành bài toán lát cắt $k$ cực đại (maximum $k$-cut) trên đồ thị khách hàng, trong đó các vectơ điểm giống nhau được gộp thành siêu đỉnh (super-vertex), và kích thước đồ thị rút gọn có giới hạn không phụ thuộc vào số lượng khách hàng [6]. Khi khách hàng đã là các đỉnh, bước tiếp theo tự xuất hiện: nếu có thể xây dựng một đồ thị tương đồng, thì phát hiện cộng đồng [1, 17] có thể phân hoạch đồ thị đó, và các đại lượng suy ra từ đồ thị — bậc, độ trung tâm (centrality), đặc biệt là tỷ lệ rời bỏ quan sát được trong số các khách hàng lân cận của một khách hàng — có thể được thêm vào ma trận đặc trưng của mô hình dự báo rời bỏ có giám sát (supervised churn model). Giả thuyết nền tảng là giả thuyết lan truyền (contagion): rủi ro rời bỏ một phần là thuộc tính của nhóm lân cận về hành vi, chứ không chỉ của từng cá nhân.

Bài báo này kiểm tra giả thuyết đó và không tìm được bằng chứng ủng hộ. Chúng tôi xây dựng quy trình mà giả thuyết này đòi hỏi — một phiên bản mở rộng RFM theo hành vi với chín chiều, đồ thị tương đồng khách hàng dựa trên $k$ láng giềng gần nhất ($k$-nearest-neighbour), các cộng đồng Louvain và Leiden, cùng các đặc trưng nút đồ thị bao gồm tỷ lệ rời bỏ của khách hàng lân cận và của cộng đồng — và đánh giá nó so với các tập đặc trưng đơn giản dần. Đóng góp nằm ở phần đánh giá. Hai biện pháp kiểm soát hóa ra có tính quyết định:

1. **Tính lại các đặc trưng lân cận trong từng phần huấn luyện.** Cả hai đều là các đại lượng tổng hợp của biến đích (target), nên tính chúng một lần trên toàn bộ dữ liệu sẽ đưa nhãn kiểm tra vào các đặc trưng huấn luyện. Chúng tôi tính lại chúng bên trong từng phần huấn luyện, chỉ từ nhãn huấn luyện.
2. **Kiểm định chéo lặp lại với một kiểm định có hiệu chỉnh phương sai (variance-corrected test).** Một lần chia dữ liệu cho một ước lượng điểm (point estimate) mà không kèm độ bất định (uncertainty). Chúng tôi dùng mười lần lặp trên các cách chia phần dùng chung và báo cáo kiểm định $t$ lấy mẫu lại có hiệu chỉnh của Nadeau và Bengio [15], kiểm định này điều chỉnh cho sự chồng lấn của các tập huấn luyện khiến kiểm định ghép cặp thông thường kém bảo thủ (anti-conservative) [8, 2].

Khi có cả hai biện pháp kiểm soát, hiệu ứng mà quy trình được xây dựng để chứng minh biến mất. Chúng tôi trình bày các đóng góp một cách thận trọng:

- Một kết quả âm tính, được báo cáo đúng với bản chất đó: cả phần mở rộng hành vi lẫn các đặc trưng đồ thị đều không cải thiện khả năng phân biệt (discrimination) so với mô hình cơ sở RFM ba biến, ở bất kỳ bậc đồ thị nào đã kiểm tra, và phép so sánh duy nhất có ý nghĩa thống kê ưu tiên mô hình đơn giản nhất trong nghiên cứu.
- Một giao thức đánh giá (evaluation protocol) cho lĩnh vực ứng dụng này, cùng quan sát rằng các chênh lệch nhỏ hơn khoảng $0.005$ ROC-AUC trên bộ dữ liệu này không thể phân biệt được với nhiễu do cách chia phần dữ liệu hay với sự dịch chuyển do phiên bản thư viện (library-version drift).
- Sự tách rời giữa thứ hạng quy gán đóng góp SHAP và đóng góp dự báo, được chúng tôi nêu rõ vì thứ hạng độ quan trọng của đặc trưng (feature importance) thường được xem là bằng chứng về tính hữu ích.

## 2 Công trình liên quan

Ba hướng nghiên cứu gặp nhau trong bài toán này, và sự căng thẳng giữa chúng là điều khiến một kết quả âm tính cung cấp thông tin thay vì chỉ gây thất vọng.

Hướng **biểu diễn (representation)** hỏi nên đo lường điều gì về một khách hàng. RFM vẫn tồn tại vì chi phí thấp và dễ diễn giải (interpretable), còn các phần mở rộng đi theo nó thường thêm chiều thay vì thay thế ý tưởng: độ dài quan hệ bên cạnh ba chiều ban đầu, các thuộc tính nhân khẩu học [9], hoặc triển khai theo thời gian để bộ ba RFM trở thành một chuỗi thay vì một điểm [14]. Điều các phần mở rộng này cùng chia sẻ là khẳng định ngầm rằng các chiều bổ sung chứa thông tin mà ba chiều ban đầu không có. Khẳng định đó có thể kiểm tra được, và là một trong những điều chúng tôi kiểm tra.

Hướng **cấu trúc (structural)** hỏi liệu có nên mô hình hóa các khách hàng cùng nhau thay vì độc lập. Vianna Filho và cộng sự đưa ra hình thức mạnh nhất của lập luận này đối với phân khúc: bằng cách diễn đạt lại phân khúc RFM thành lát cắt $k$ cực đại trên một đồ thị khách hàng, mục tiêu phân khúc trở thành một đại lượng đồ thị tường minh thay vì sản phẩm phụ của một phương pháp heuristic phân cụm dựa trên khoảng cách (distance-based clustering heuristic) [6]. Công trình của họ là điểm xuất phát của chúng tôi, nhưng dừng ở phân khúc và không đề cập dự báo có giám sát. Phát hiện cộng đồng cung cấp công cụ cho một phần mở rộng có giám sát: phân hoạch dựa trên độ mô-đun (modularity) [16, 1] và phiên bản cải tiến bảo đảm các cộng đồng có kết nối tốt [17] đều là những phương pháp chuẩn, được triển khai tốt và áp dụng trực tiếp được cho đồ thị tương đồng giữa các khách hàng. Bước từ đó đến việc thêm tỷ lệ rời bỏ của nhóm lân cận làm một đặc trưng là ngắn, và chính vì vậy nó đáng được xem xét kỹ: đặc trưng ấy là một đại lượng tổng hợp của nhãn, còn các đặc trưng thuộc loại này là phương tiện điển hình dẫn đến rò rỉ biến đích (target leakage).

Bản thân đặc trưng tỷ lệ rời bỏ của nhóm lân cận không mới, và các bối cảnh mà nó đã có tác dụng cung cấp thông tin đáng chú ý. Các nghiên cứu viễn thông xây dựng nó từ bản ghi chi tiết cuộc gọi (call-detail record), trong đó một cạnh có nghĩa là hai thuê bao đã thực sự nói chuyện, và báo cáo rằng rủi ro của một thuê bao tăng theo số lượng khách hàng lân cận đã rời bỏ [11]; các công trình gần đây hơn xem đồ thị xã hội là một đối tượng biến thiên theo thời gian và dự báo sự rời bỏ từ cách đồ thị tiến triển [12]. Điều phân biệt các bối cảnh đó với bối cảnh của chúng tôi là ý nghĩa của một cạnh. Cạnh của họ ghi nhận một tương tác tồn tại độc lập với ma trận đặc trưng của mô hình; cạnh của chúng tôi ghi nhận sự gần nhau trong chính không gian đặc trưng (feature space) mà bộ phân loại đã quan sát. Khác biệt đó hóa ra có ý nghĩa, và Mục 9.2 sẽ trở lại vấn đề này.

Hướng **đánh giá (evaluation)** là nơi tài liệu ứng dụng yếu nhất và cũng là nơi tài liệu phương pháp luận đã có lời giải từ lâu. Các tập huấn luyện được lấy mẫu lại và có chồng lấn làm gia tăng sai lầm loại I (Type I error) trong những kiểm định thường dùng để so sánh các thuật toán học [8]; phép hiệu chỉnh phương sai khắc phục kiểm định ghép cặp cho đúng trường hợp này đã có từ hai thập niên [15], cùng bằng chứng về khả năng lặp lại của những kiểm định như vậy trong thực tiễn [2, 7]. Dẫu vậy, các nghiên cứu ứng dụng về khách hàng rời bỏ, kể cả báo cáo trước đây của chính chúng tôi về quy trình hiện tại, vẫn xếp hạng các cấu hình theo một ước lượng điểm duy nhất từ kiểm định chéo. Với các chênh lệch ở mức $10^{-3}$ ROC-AUC, cách đó không thể tách một hiệu ứng khỏi một cách chia phần dữ liệu. Kết quả của chúng tôi là một trường hợp của khoảng cách giữa hai hướng nghiên cứu này, không phải sự phê phán một nghiên cứu cá biệt nào.

Cây tăng cường gradient (gradient-boosted tree) [5, 10] và quy gán đóng góp đặc trưng theo dạng cộng (additive feature attribution) [13] được sử dụng ở đây như những công cụ chuẩn, không phải đối tượng nghiên cứu.

## 3 Tổng quan quy trình

Hình 1 thể hiện các giai đoạn và vị trí của hai biện pháp kiểm soát. Hàng trên, đọc từ trái sang phải, xây dựng biểu diễn; hàng dưới, đọc từ phải sang trái, đưa biểu diễn qua các biện pháp kiểm soát vào bước đánh giá. Hai giai đoạn có tô nền là những giai đoạn quyết định kết quả: kiểm soát rò rỉ giữ các đặc trưng suy ra từ nhãn bên trong phần huấn luyện, và đánh giá lặp lại gắn độ bất định với mỗi phép so sánh.

![Hình 1. Quy trình phân tích. Các giai đoạn có tô nền là hai biện pháp kiểm soát quyết định kết quả: các đặc trưng lân cận suy ra từ nhãn được tính lại bên trong từng phần huấn luyện, và mỗi phép so sánh được thực hiện qua mười lần lặp của kiểm định chéo năm phần với một kiểm định ý nghĩa thống kê có hiệu chỉnh phương sai.](assets/pipeline-vi.png)

## 4 Dữ liệu và xây dựng đặc trưng

### 4.1 Bộ dữ liệu và các cửa sổ thời gian

Chúng tôi dùng Online Retail II, nhật ký giao dịch của một nhà bán lẻ không có cửa hàng đặt tại Vương quốc Anh, bao phủ từ tháng 12 năm 2009 đến tháng 12 năm 2011, được phân phối qua UCI Machine Learning Repository [3] và được giới thiệu trong nghiên cứu phân khúc RFM của Chen và cộng sự [4]. Tệp thô chứa $1{,}067{,}371$ dòng giao dịch trên hai trang tính ($525{,}461$ và $541{,}910$); con số $541{,}000$ thường được trích dẫn cho bộ dữ liệu này chỉ là trang tính thứ hai.

Đặc trưng và nhãn được tách biệt theo thời gian. Cửa sổ quan sát (observation window) chạy từ 2009-12-01 đến 2011-06-30 và là khoảng thời gian duy nhất dùng để tính đặc trưng. Cửa sổ dự báo (prediction window) chạy từ 2011-07-01 đến 2011-09-30; một khách hàng hoạt động trong cửa sổ quan sát được gán nhãn là người rời bỏ (churner) nếu không xuất hiện lần mua hàng nào trong cửa sổ dự báo. Sau khi lọc các giao dịch hợp lệ trong cửa sổ quan sát ($556{,}212$ dòng) và tổng hợp ở cấp khách hàng, ma trận làm việc chứa $5{,}038$ khách hàng. Tỷ lệ rời bỏ là $65.2\%$.

Con số cuối cùng đó cần được nhấn mạnh, vì nó đảo ngược một giả định thường được đưa vào bài toán này. Khách hàng rời bỏ là lớp **đa số (majority class)** ở đây, không phải những trường hợp dương tính hiếm cần được cứu bằng lấy mẫu lại (resampling). Một khoảng thời gian không hoạt động 90 ngày, áp dụng cho một nhà bán lẻ có khoảng cách dài giữa các lần mua, gán nhãn rời bỏ cho phần lớn tập khách hàng. Điều này khiến PR-AUC ít cung cấp thông tin hơn so với trong tình huống mất cân bằng thực sự (imbalance), và chúng tôi báo cáo nó bên cạnh ROC-AUC thay vì coi là thước đo chính.

### 4.2 Các đặc trưng Behavioural-LRFM

Chín đặc trưng cấp khách hàng được tính trong cửa sổ quan sát: độ dài $L$ (số ngày giữa lần mua đầu tiên và lần mua cuối cùng), độ gần đây $R$, tần suất $F$ (các hóa đơn khác nhau), giá trị tiền tệ $M$, giá trị đơn hàng trung bình (average order value), kích thước giỏ hàng (basket size), độ đa dạng sản phẩm (product diversity), tỷ lệ hủy (cancellation rate), và thời gian trung bình giữa các lần mua (mean interpurchase time). Tỷ lệ hủy được giới hạn ở những lần hủy có ngày nằm trong cửa sổ quan sát; một phiên bản trước của quy trình này đã tính nó trên toàn bộ nhật ký, cho phép các lần hủy sau cửa sổ đi vào một đặc trưng của thời điểm trước cửa sổ.

## 5 Xây dựng đồ thị và phát hiện cộng đồng

Chín đặc trưng được chuẩn hóa (standardisation), và một đồ thị $k$ láng giềng gần nhất được xây dựng trên các khách hàng với $k = 10$ và khoảng cách Euclid (Euclidean distance), có trọng số cạnh (edge weight) $w(i,j) = 1/(1 + d(i,j))$. Đồ thị thu được có $5{,}038$ nút và $33{,}426$ cạnh. Louvain [1] tạo ra 20 cộng đồng với độ mô-đun $0.8385$; Leiden [17] tạo ra 20 cộng đồng với độ mô-đun $0.8323$.

Không nên diễn giải quá mức độ mô-đun cao: một đồ thị $k$-NN với $k$ cố định áp đặt bậc gần như đồng đều và sự phân cụm cục bộ mạnh ngay từ cách xây dựng, nên một giá trị trên $0.8$ phản ánh cách đồ thị được xây dựng ít nhất cũng nhiều ngang với bất kỳ cấu trúc nào trong tập khách hàng.

Sáu đặc trưng suy ra từ đồ thị được thêm vào: bậc (degree), bậc có trọng số (weighted degree), PageRank, hệ số phân cụm (clustering coefficient), và hai đại lượng tổng hợp lân cận tạo động lực cho thiết kế — tỷ lệ rời bỏ của khách hàng lân cận (neighbour churn rate; nhãn trung bình trong số các khách hàng lân cận của một khách hàng trên đồ thị) và tỷ lệ rời bỏ của cộng đồng (community churn rate; nhãn trung bình trong cộng đồng Louvain của khách hàng).

## 6 Các biện pháp kiểm soát rò rỉ

Cả hai đại lượng tổng hợp lân cận đều là hàm của biến đích. Tính một trong hai trên toàn bộ dữ liệu trước khi kiểm định chéo cho phép nhãn của một khách hàng kiểm tra tác động đến các đặc trưng huấn luyện của các khách hàng lân cận của họ, và sự lạc quan trong kết quả thu được có thể đáng kể. Vì vậy, chúng tôi tính lại cả hai bên trong từng phần huấn luyện: đối với khách hàng $i$, tỷ lệ rời bỏ của khách hàng lân cận lấy trung bình các nhãn trên $\mathcal{N}(i) \cap \mathcal{T}$, trong đó $\mathcal{T}$ là tập chỉ số huấn luyện, và dùng tỷ lệ nền (base rate) của phần huấn luyện khi giao đó rỗng; tỷ lệ rời bỏ của cộng đồng được tính theo cùng cách trong từng cộng đồng Louvain. Bản thân đồ thị và các cộng đồng chỉ được xây dựng từ đặc trưng, không bao giờ từ nhãn, và do đó được giữ cố định qua các phần dữ liệu.

Ba biện pháp kiểm soát nữa được áp dụng xuyên suốt: phép chuẩn hóa được khớp bên trong quy trình kiểm định chéo thay vì trên toàn bộ ma trận; định danh cụm K-means và Louvain được mã hóa one-hot (one-hot encoding) thay vì truyền dưới dạng số nguyên; và cả Louvain lẫn Leiden đều được chạy, để lựa chọn bộ phát hiện cộng đồng không trở thành một bậc tự do ẩn.

## 7 Giao thức đánh giá

### 7.1 Các tầng đặc trưng

Năm tầng lồng nhau tách biệt đóng góp của từng lớp mô hình hóa: **RFM** ($R, F, M$); **LRFM** (thêm $L$); **B-LRFM** (chín đặc trưng hành vi); **B-LRFM+Seg** (thêm 23 biến chỉ báo one-hot cho phân khúc và cộng đồng); và **Graph-Enhanced**, ma trận đầy đủ với 38 đặc trưng, bổ sung bốn đặc trưng đồ thị tĩnh và hai đại lượng tổng hợp lân cận được tính riêng cho từng phần huấn luyện. Hai bộ phân loại được đánh giá trên mỗi tầng: LightGBM [10] làm mô hình chính và hồi quy logistic với chính quy hóa $\ell_2$ ($\ell_2$ regularisation) làm mô hình tham chiếu dễ diễn giải.

### 7.2 Kiểm định chéo lặp lại và ý nghĩa thống kê

Chúng tôi chạy mười lần lặp kiểm định chéo năm phần có phân tầng (stratified five-fold cross-validation), tạo thành 50 phần dữ liệu. Trong một lần lặp, cả năm tầng và hai bộ phân loại đều dùng **cùng** một cách chia phần dữ liệu, nên các chênh lệch theo từng phần được ghép cặp đúng cách. Với các chênh lệch $d_1, \dots, d_n$ trên $n = 50$ phần dữ liệu, chúng tôi báo cáo thống kê $t$ lấy mẫu lại có hiệu chỉnh [15]:

$$
t = \frac{\bar{d}}
{\sqrt{\hat{\sigma}^{2}\left(\dfrac{1}{n} + \dfrac{n_{2}}{n_{1}}\right)}},
\qquad \frac{n_{2}}{n_{1}} = \frac{1}{4},
$$

(1)

trong đó $n_{2}/n_{1}$ là tỷ số giữa kích thước tập kiểm tra và tập huấn luyện; với kiểm định chéo năm phần, tỷ số này là $1/4$. Chúng tôi chỉ báo cáo $p_{\mathrm{NB}}$ từ thống kê này. Các khoảng tin cậy bootstrap (bootstrap confidence interval) trên 50 chênh lệch được đưa ra để thể hiện độ lớn hiệu ứng (effect magnitude), nhưng chúng tôi lưu ý không nên đọc chúng như các tuyên bố về ý nghĩa thống kê: bootstrap lấy mẫu lại các chênh lệch như thể chúng độc lập, trong khi các phần dữ liệu lặp lại dùng chung dữ liệu huấn luyện, nên các khoảng đó hẹp hơn mức mà cấu trúc tương quan cho phép. Đây chính là sự chồng lấn khiến kiểm định $t$ ghép cặp thông thường kém bảo thủ [8].

Khi chạy với cùng một giá trị khởi tạo ngẫu nhiên (seed) mà quy trình gốc sử dụng, bộ chương trình kiểm định ý nghĩa thống kê tái lập ROC-AUC theo từng tầng của quy trình đó đến bốn chữ số thập phân ở cả năm tầng; vì vậy, mọi sai khác bên dưới có thể quy cho cách chia phần dữ liệu thay vì cho khác biệt trong việc triển khai lại.

## 8 Kết quả

### 8.1 Một lần chia cho thấy điều ngược lại so với mười lần

Bảng 1 đặt hai cách đánh giá cạnh nhau, và sự tương phản đó là kết quả của bài báo này. Trên lần chia kiểm định chéo năm phần có phân tầng duy nhất mà quy trình này báo cáo ban đầu, Graph-Enhanced là tầng tốt nhất, cao hơn RFM $+0.0033$ ROC-AUC. Qua mười lần lặp, nó đồng hạng thấp nhất, thấp hơn RFM $-0.0021$. Không điều gì về mô hình thay đổi giữa hai cột đó; chỉ cách chia phần dữ liệu thay đổi. Ngay cả ở seed tạo ra nó, khoảng cách $+0.0033$ có khoảng bootstrap 95% là $[-0.0025, +0.0099]$, chứa giá trị không.

**Bảng 1.** LightGBM trên năm tầng đặc trưng. Cột một lần chia là đánh giá với seed-42 mà quy trình này báo cáo đầu tiên; các cột còn lại là mười lần lặp của cùng giao thức. $p_{\mathrm{NB}}$ là kiểm định $t$ lấy mẫu lại có hiệu chỉnh so với RFM (Mục 7.2); không tầng nào đạt ý nghĩa thống kê. Nguyên nhân cột một lần chia gây hiểu lầm được bàn trong Mục 9.

| Tầng đặc trưng | Một lần chia: ROC-AUC | CV lặp lại ($10 \times 5$ phần, ghép cặp): ROC-AUC | CV lặp lại: $\Delta$ so với RFM | CV lặp lại: $p_{\mathrm{NB}}$ |
|---|---:|---:|---:|---:|
| RFM (mô hình cơ sở) | 0.8065 | 0.8066 | — | — |
| LRFM | 0.8071 | 0.8074 | $+0.0009$ | 0.755 |
| B-LRFM | 0.8067 | 0.8054 | $-0.0012$ | 0.742 |
| B-LRFM+Seg | 0.8073 | 0.8044 | $-0.0022$ | 0.561 |
| Graph-Enhanced | **0.8098** | 0.8044 | $-0.0021$ | 0.590 |

Không tầng nào khác biệt có ý nghĩa thống kê so với mô hình cơ sở RFM, và ba trong bốn chênh lệch điểm là âm. Điều tương tự cũng đúng với PR-AUC và khi dùng hồi quy logistic làm bộ phân loại: trên bốn tổ hợp thước đo–bộ phân loại — mười sáu phép so sánh tầng với mô hình cơ sở — $p_{\mathrm{NB}}$ nhỏ nhất là $0.144$. Trên lần chia duy nhất, các thước đo khác cũng đồng thuận với ROC-AUC, trong đó Graph-Enhanced dẫn đầu về PR-AUC ($0.8689$), F1 ($0.8108$) và recall ($0.8009$); sự đồng thuận đó khiến một lần chia có sức thuyết phục và chính là lý do nó không đủ.

### 8.2 Hiệu ứng duy nhất có ý nghĩa thống kê

Bảng 2 báo cáo những phép so sánh thực sự đạt ý nghĩa thống kê. Tất cả đều nghiêng về hồi quy logistic so với mô hình tăng cường gradient dùng đặc trưng đồ thị.

**Bảng 2.** Các phép so sánh giữa mô hình trên cùng 50 phần dữ liệu ghép cặp. Các khoảng là khoảng bootstrap và chỉ được đưa ra để thể hiện độ lớn; ý nghĩa thống kê được đọc từ $p_{\mathrm{NB}}$, vì lý do trình bày ở Mục 7.2.

| Phép so sánh | $\Delta$ ROC-AUC | Khoảng tin cậy 95% (95% CI) | $p_{\mathrm{NB}}$ |
|---|---:|---:|---:|
| LogReg / B-LRFM so với LGBM / Graph-Enh. | $+0.0113$ | $[+0.0096, +0.0130]$ | **0.001** |
| LogReg / RFM so với LGBM / Graph-Enh. | $+0.0099$ | $[+0.0080, +0.0119]$ | **0.010** |
| LogReg / RFM so với LGBM / RFM | $+0.0078$ | $[+0.0056, +0.0100]$ | 0.068 |

Một mô hình tuyến tính (linear model) ba biến vượt qua một mô hình tăng cường gradient với 38 đặc trưng được xây dựng trên đồ thị tương đồng khách hàng. Biên chênh lệch xấp xỉ ba lần khoảng cách $+0.0033$ mà đánh giá một lần chia báo cáo là mức cải thiện của quy trình, và có độ lớn lớn hơn mọi chênh lệch giữa các tầng đặc trưng. Chúng tôi rút ra kết luận trong phạm vi hẹp: trên bộ dữ liệu này, ở cỡ mẫu này, với định nghĩa rời bỏ này, tín hiệu phân biệt (discriminative signal) gần như đã được khai thác hết bởi độ gần đây, tần suất và giá trị tiền tệ, còn năng lực bổ sung của mô hình (model capacity) được sử dụng cho phương sai thay vì tín hiệu.

Hình 2 thể hiện toàn bộ kết quả trong một hình. Mỗi đường đều phẳng: di chuyển dọc theo nó — thêm thời gian duy trì quan hệ (tenure), rồi hành vi, rồi phân khúc, rồi đồ thị — không tạo ra thay đổi nào có thể thấy được. Khoảng cách theo chiều dọc giữa hai đường, vốn chỉ là thay đổi bộ phân loại, là hiệu ứng thực sự duy nhất. Các dải tô nền cho thấy lý do một lần chia không thể quyết định vấn đề này: độ phân tán giữa các phần dữ liệu có độ lệch chuẩn (standard deviation) khoảng $0.014$, lớn hơn một bậc độ lớn so với mọi chênh lệch giữa các tầng.

![Hình 2. ROC-AUC trung bình trên năm tầng đặc trưng cho cả hai bộ phân loại. Các dải thể hiện ±1 độ lệch chuẩn của 50 điểm số theo phần dữ liệu, tức là độ phân tán mà một lần chia riêng lẻ được lấy từ đó. Độ bất định của chính các chênh lệch ghép cặp nằm trong Bảng 1 và Bảng 2.](assets/folds-vi.png)

### 8.3 Kết quả không phụ thuộc vào bậc đồ thị

Một kết quả âm tính về đồ thị dẫn đến câu hỏi hiển nhiên rằng liệu đó có phải là kết quả về một đồ thị cụ thể hay không. Vì vậy, chúng tôi xây dựng lại từ đầu đồ thị, các cộng đồng và các đặc trưng riêng cho từng phần huấn luyện tại $k \in \{5, 10, 15, 20\}$, rồi chạy lại toàn bộ giao thức CV lặp lại ở mỗi thiết lập. Bảng 3 báo cáo kết quả.

**Bảng 3.** Graph-Enhanced so với mô hình cơ sở RFM khi bậc đồ thị thay đổi. LightGBM, $10 \times 5$ phần dữ liệu ghép cặp ở mỗi thiết lập; đồ thị, các cộng đồng Louvain và các đặc trưng riêng cho từng phần huấn luyện được xây dựng lại cho mỗi $k$.

| $k$ | Số cạnh | Số cộng đồng | $\Delta$ so với RFM | $p_{\mathrm{NB}}$ |
|---:|---:|---:|---:|---:|
| 5 | 16,902 | 31 | $-0.0006$ | 0.880 |
| 10 | 33,426 | 20 | $-0.0021$ | 0.590 |
| 15 | 50,054 | 16 | $+0.0017$ | 0.666 |
| 20 | 66,652 | 16 | $-0.0027$ | 0.500 |

Tăng số cạnh lên bốn lần và giảm số cộng đồng xuống một nửa làm thay đổi đồ thị đáng kể nhưng hoàn toàn không thay đổi kết luận: không thiết lập nào đạt ý nghĩa thống kê, và ngay cả dấu của chênh lệch cũng không ổn định, chuyển sang dương tại $k = 15$ và âm ở ba thiết lập còn lại. Một đại lượng mà dấu của nó phụ thuộc vào một tham số điều chỉnh (tuning parameter) mà lẽ ra nó không nên phụ thuộc đang biểu hiện giống nhiễu; đây chính là điều các giá trị $p$ trực tiếp cho biết.

### 8.4 Quy gán đóng góp không phải là đóng góp thực tế

Các giá trị SHAP toàn cục (global SHAP value) [13] trên mô hình tăng cường đồ thị xếp độ gần đây thứ nhất ($1.087$) và giá trị tiền tệ thứ hai ($0.560$), tiếp theo là tỷ lệ rời bỏ của khách hàng lân cận ($0.250$), thời gian giữa các lần mua ($0.224$) và tỷ lệ rời bỏ của cộng đồng ($0.215$). Khi được đọc như một thứ hạng độ quan trọng, điều này dường như xác nhận rằng các đại lượng tổng hợp lân cận có tác dụng: hai trong năm đặc trưng đứng đầu được suy ra từ đồ thị.

Chúng không có tác dụng đối với khả năng phân biệt: tầng không có chúng (B-LRFM+Seg, $0.8044$) và tầng có chúng (Graph-Enhanced, $0.8044$) không thể phân biệt được. Đây là vấn đề về định nghĩa, không phải mâu thuẫn. SHAP quy gán cách một mô hình **đã được khớp** phân bổ công trạng cho các đặc trưng được cung cấp, nên một đặc trưng tương quan với cả biến đích và phần còn lại của tập đặc trưng sẽ nhận phần quy gán đóng góp dù không bổ sung điều gì mà các đặc trưng khác chưa chứa. Thứ hạng quy gán đóng góp trả lời “mô hình này đang sử dụng điều gì?”; chỉ một phân tích loại bỏ thành phần (ablation) mới trả lời “loại bỏ nó có làm mất đi điều gì không?”, và ở đây câu trả lời là không.

### 8.5 Quan hệ với mô hình cơ sở phân khúc

Điểm xuất phát của chúng tôi [6] phân khúc khách hàng trên các điểm RFM rời rạc từ 1–5 trong ba chiều; công trình hiện tại dự báo sự rời bỏ trong không gian liên tục chín chiều. Không thể so sánh điểm silhouette (silhouette score) giữa các không gian đặc trưng khác nhau — một không gian rời rạc ít chiều tạo ra các cụm chặt hơn như một thuộc tính của chính không gian đó — nên chúng tôi không đưa ra khẳng định đối đầu trực tiếp về chất lượng phân cụm. Để tham khảo, trong chính không gian chấm điểm của nó, mô hình cơ sở đạt silhouette $0.398$ tại $k = 4$ như đã công bố, và chúng tôi tái lập được ở mức $0.398$; K-means trên không gian chín chiều của chúng tôi đạt $0.219$ và Louvain đạt $-0.050$ theo cùng thước đo. Quan hệ giữa hai công trình là mở rộng phạm vi, không phải cải thiện. Các cộng đồng vẫn có thể dùng để xác định ưu tiên dù chúng không cải thiện dự báo: khi xếp hạng theo xác suất rời bỏ nhân với giá trị tiền tệ, chúng tách một nhóm có giá trị cao đang có rủi ro ($327$ khách hàng, $82\%$ rời bỏ) khỏi một nhóm trung thành có giá trị cao ($418$ khách hàng, $24\%$ rời bỏ). Vì dữ liệu không có nhãn phản hồi chiến dịch (campaign-response label), đây chỉ là một đầu ra mô tả.

## 9 Thảo luận

### 9.1 Các độ lớn hiệu ứng dưới ngưỡng nhiễu

Hai nguồn biến thiên độc lập có cùng độ lớn với các hiệu ứng mà quy trình được xây dựng để phát hiện. Cách chia phần dữ liệu đóng góp khoảng $0.003$ ROC-AUC, như sự đảo dấu ở trên cho thấy. Phiên bản thư viện đóng góp tương đương: chạy lại quy trình cải thiện phụ trợ với các thư viện mới hơn đã làm cấu hình tốt nhất của nó dịch chuyển $-0.0033$ ROC-AUC và số cộng đồng Leiden thay đổi từ $20$ sang $21$. Vì vậy, chúng tôi coi các chênh lệch nhỏ hơn khoảng $0.005$ ROC-AUC trên bộ dữ liệu này là không cung cấp thông tin, và đề xuất các phép so sánh ở đây hoặc báo cáo một kiểm định có hiệu chỉnh phương sai, hoặc tránh xếp hạng cấu hình trong dải đó.

### 9.2 Vì sao giả thuyết lan truyền vẫn có thể đúng

Kết quả của chúng tôi là việc không bác bỏ được giả thuyết không (null hypothesis) trên một bộ dữ liệu với một cách xây dựng đồ thị, chứ không phải chứng minh rằng các hiệu ứng từ những khách hàng tương đồng về hành vi không tồn tại. Lời giải thích có khả năng nhất là chúng tôi đã xây dựng sai đồ thị: các cạnh của nó mã hóa sự gần nhau trong một không gian đặc trưng suy ra từ cùng lịch sử mua hàng đã được đưa vào bộ phân loại, nên tỷ lệ rời bỏ của khách hàng lân cận có thể là một cách diễn đạt lại đã được làm trơn (smoothed restatement) của những gì mô hình có, thay vì thông tin mới. Cách đọc này phù hợp với các bối cảnh mà đặc trưng đó thực sự có tác dụng. Các kết quả viễn thông và đồ thị xã hội được trích dẫn ở Mục 2 được xây dựng trên tương tác đã ghi nhận — ai gọi cho ai, ai chơi cùng ai — chứ không trên độ tương đồng tính từ chính các đầu vào của mô hình [11, 12]. Một đồ thị bán lẻ được xây dựng từ tín hiệu tương tác chưa có trong ma trận đặc trưng — giỏ hàng chung, danh mục chung, liên kết giới thiệu hoặc hộ gia đình — sẽ là một phép kiểm tra thực sự khác, và là thí nghiệm tiếp theo chúng tôi sẽ thực hiện. Hai cách đọc yếu hơn cũng phù hợp: nhãn không hoạt động 90 ngày trên tập khách hàng với đa số đã rời bỏ có thể quá thô để các hiệu ứng lân cận xuất hiện; và khi mọi tầng đều ở gần $0.81$ ROC-AUC, ràng buộc giới hạn có thể nằm ở biểu diễn thay vì lớp mô hình (model class).

## 10 Các mối đe dọa đối với tính hợp lệ

**Một bộ dữ liệu duy nhất.** Mọi kết quả đều đến từ một nhà bán lẻ trong hai năm. Chúng tôi không đưa ra khẳng định về các lĩnh vực hay khoảng thời gian dự báo khác; ngưỡng độ lớn hiệu ứng mà chúng tôi báo cáo chỉ dành cho bộ dữ liệu và cỡ mẫu này.

**Một họ đồ thị duy nhất.** Phép khảo sát bậc ở Mục 8 cho thấy kết quả không phải là hệ quả giả tạo của $k$, nhưng mỗi thiết lập vẫn là một đồ thị $k$ láng giềng gần nhất trên các đặc trưng Behavioural-LRFM đã chuẩn hóa với cùng khoảng cách và cùng cách gán trọng số. Một họ đồ thị khác — xây dựng từ việc cùng mua hàng (co-purchase), chồng lấn danh mục (category overlap) hoặc liên kết hộ gia đình — chưa được kiểm tra ở đây, và là nơi chúng tôi kỳ vọng giả thuyết sẽ được xem xét công bằng hơn.

**Các thành phần dự kiến chưa được triển khai.** Hai thành phần được mô tả trong thiết kế nghiên cứu chưa được triển khai và không thuộc bất kỳ kết quả nào báo cáo ở đây: mã hóa biến phân loại theo quốc gia xuất xứ (country-of-origin categorical encoding), và phân cụm phổ (spectral clustering) làm thuật toán phát hiện cộng đồng thứ ba. Chúng tôi liệt kê chúng để khoảng cách giữa thiết kế và thực hiện được nhìn thấy rõ.

**Lựa chọn thước đo.** Khi khách hàng rời bỏ thuộc lớp đa số, PR-AUC không mang cách diễn giải thông thường của nó. Chúng tôi báo cáo cả hai thước đo và không dựa bất kỳ kết luận nào chỉ vào PR-AUC.

**Tìm kiếm tài liệu có mục tiêu, không toàn diện.** Chúng tôi tìm các công trình trước đây sử dụng đặc trưng tỷ lệ rời bỏ của nhóm lân cận và xác định được các công trình về viễn thông và đồ thị xã hội được thảo luận trong Mục 2, vốn dùng đồ thị tương tác (interaction graph) thay vì đồ thị tương đồng. Chúng tôi không tìm thấy biến thể đồ thị tương đồng trong bán lẻ được kiểm tra ở đây, nhưng việc tìm kiếm có mục tiêu thay vì có hệ thống, và chúng tôi không đưa ra bất kỳ khẳng định nào về tính tiên phong.

**Không có kiểm chứng nghiệp vụ.** Giá trị giữ chân kỳ vọng (expected retention value) xếp hạng khách hàng theo một đại lượng của mô hình, không phải theo phản hồi chiến dịch quan sát được. Giá trị thực tiễn của nó chưa được kiểm tra.

## 11 Kết luận

Chúng tôi xây dựng quy trình mà giả thuyết hiệu ứng từ khách hàng tương đồng về hành vi đòi hỏi và đánh giá nó với việc tính lại các đặc trưng suy ra từ nhãn bên trong từng phần huấn luyện, cùng kiểm định chéo lặp lại với một kiểm định có hiệu chỉnh. Giả thuyết không được ủng hộ trên bộ dữ liệu này ở bất kỳ bậc đồ thị nào đã kiểm tra, và phép so sánh duy nhất có ý nghĩa thống kê ưu tiên hồi quy logistic trên ba biến RFM thô so với mô hình đồ thị đầy đủ ($p = 0.010$).

Luận điểm phương pháp luận có khả năng khái quát rộng hơn kết quả âm tính. Một cách đánh giá báo cáo một con số kiểm định chéo cho mỗi cấu hình không thể phân biệt chênh lệch $0.003$ ROC-AUC với cách chia dữ liệu đã tạo ra nó, và những chênh lệch ở độ lớn đó chính là điều các nghiên cứu xây dựng đặc trưng (feature engineering) trong lĩnh vực này thường báo cáo. Các biện pháp kiểm soát dùng ở đây có chi phí thấp — mười lần lặp kiểm định chéo năm phần trên $5{,}038$ khách hàng chỉ là chuyện vài phút — và chúng tôi cho rằng chúng nên nằm trong giao thức mặc định thay vì trong phụ lục.

#### Khả năng tái lập

Mã nguồn, điểm số theo từng phần dữ liệu, các bảng tóm tắt ý nghĩa thống kê và nhật ký chạy thô có tại [https://github.com/VoDucNhatku/graph-behavioral-lrfm-churn](https://github.com/VoDucNhatku/graph-behavioral-lrfm-churn), với thẻ `v1.0-submission`. Các phiên bản thư viện được ghim theo môi trường đã tạo ra mọi con số báo cáo, và hình kết quả được tạo từ điểm số theo từng phần dữ liệu đã được commit, nên nó không thể sai khác với các bảng. Toàn bộ quy trình chạy trong chưa đến mười phút trên máy tính xách tay không có GPU.

#### Tuyên bố về AI tạo sinh

Trong quá trình chuẩn bị công trình này, tác giả đã dùng một mô hình ngôn ngữ lớn (large language model; Claude, Anthropic) để soạn thảo và sửa bản thảo, triển khai một phần mã đánh giá và mã tạo hình, cũng như đối chiếu các con số báo cáo với các tệp kết quả. Tác giả đã kiểm chứng mọi con số báo cáo với các lần chạy được lưu trữ và chịu hoàn toàn trách nhiệm về nội dung.

## Tài liệu tham khảo

[1] Blondel, V.D., Guillaume, J.L., Lambiotte, R., Lefebvre, E.: Fast unfolding of communities in large networks. Journal of Statistical Mechanics: Theory and Experiment **2008**(10), P10008 (2008). https://doi.org/10.1088/1742-5468/2008/10/P10008

[2] Bouckaert, R.R., Frank, E.: Evaluating the replicability of significance tests for comparing learning algorithms. In: Advances in Knowledge Discovery and Data Mining (PAKDD 2004). Lecture Notes in Computer Science, vol. 3056, pp. 3–12 (2004). https://doi.org/10.1007/978-3-540-24775-3_3

[3] Chen, D.: Online retail II. UCI Machine Learning Repository (2019). https://doi.org/10.24432/C5CG6D, https://archive.ics.uci.edu/dataset/502/online+retail+ii

[4] Chen, D., Sain, S.L., Guo, K.: Data mining for the online retail industry: A case study of RFM model-based customer segmentation using data mining. Journal of Database Marketing & Customer Strategy Management **19**(3), 197–208 (2012). https://doi.org/10.1057/dbm.2012.17

[5] Chen, T., Guestrin, C.: XGBoost: A scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. pp. 785–794 (2016). https://doi.org/10.1145/2939672.2939785

[6] Corrêa Vianna Filho, A.L., de Lima, L., Kleina, M.: RFM model customer segmentation from a graph theory perspective. Quality & Quantity (2026). https://doi.org/10.1007/s11135-026-02784-0

[7] Demšar, J.: Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research **7**, 1–30 (2006), https://www.jmlr.org/papers/v7/demsar06a.html

[8] Dietterich, T.G.: Approximate statistical tests for comparing supervised classification learning algorithms. Neural Computation **10**(7), 1895–1923 (1998). https://doi.org/10.1162/089976698300017197

[9] Ho, T., Nguyen, S., Nguyen, H., Nguyen, N., Man, D.S., Le, T.G.: An extended RFM model for customer behaviour and demographic analysis in retail industry. Business Systems Research Journal **14**(1) (2023). https://doi.org/10.2478/bsrj-2023-0002

[10] Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., Liu, T.Y.: LightGBM: A highly efficient gradient boosting decision tree. In: Advances in Neural Information Processing Systems 30 (NIPS 2017). pp. 3146–3154 (2017)

[11] Kostić, S.M., Simić, M.I., Kostić, M.V.: Social network analysis and churn prediction in telecommunications using graph theory. Entropy **22**(7), 753 (2020). https://doi.org/10.3390/e22070753

[12] Lee, M., Woo, J.: TempODEGraphNet: predicting user churn using dynamic social graphs and neural ODEs. PLOS One **20**, e0321560 (2025). https://doi.org/10.1371/journal.pone.0321560

[13] Lundberg, S.M., Lee, S.I.: A unified approach to interpreting model predictions. In: Advances in Neural Information Processing Systems 30 (NIPS 2017). pp. 4765–4774 (2017)

[14] Mena, G., Coussement, K., De Bock, K.W., De Caigny, A., Lessmann, S.: Exploiting time-varying RFM measures for customer churn prediction with deep neural networks. Annals of Operations Research **339** (2023). https://doi.org/10.1007/s10479-023-05259-9

[15] Nadeau, C., Bengio, Y.: Inference for the generalization error. Machine Learning **52**(3), 239–281 (2003). https://doi.org/10.1023/A:1024068626366

[16] Newman, M.E.J., Girvan, M.: Finding and evaluating community structure in networks. Physical Review E **69**(2), 026113 (2004). https://doi.org/10.1103/PhysRevE.69.026113

[17] Traag, V.A., Waltman, L., van Eck, N.J.: From Louvain to Leiden: guaranteeing well-connected communities. Scientific Reports **9**, 5233 (2019). https://doi.org/10.1038/s41598-019-41695-z

## Thuật ngữ (Glossary)

*Phần bổ sung của người dịch; không thuộc bài báo gốc.*

| Original | Bản dịch | Giải thích ngắn |
|---|---|---|
| churn | khách hàng rời bỏ; sự rời bỏ | Trong bài này, không mua hàng trong cửa sổ dự báo. |
| churn prediction | dự báo khách hàng rời bỏ | Dự báo nhãn rời bỏ từ lịch sử khách hàng. |
| churner | khách hàng rời bỏ | Khách hàng mang nhãn rời bỏ. |
| non-contractual retail | bán lẻ phi hợp đồng | Bối cảnh không có tín hiệu hủy hợp đồng trực tiếp. |
| RFM | RFM | Biểu diễn bằng recency, frequency và monetary value. |
| recency | độ gần đây | Đại lượng phản ánh mức gần đây của lần mua. |
| frequency | tần suất | Số hóa đơn khác nhau theo định nghĩa trong bài. |
| monetary value | giá trị tiền tệ | Giá trị giao dịch tiền tệ của khách hàng. |
| relationship length | độ dài quan hệ | Chiều thời gian quan hệ được thêm vào RFM. |
| tenure | thời gian duy trì quan hệ | Thời gian quan hệ với nhà bán lẻ. |
| Behavioural-LRFM | Behavioural-LRFM | Tên biểu diễn gồm chín đặc trưng hành vi của bài. |
| average order value | giá trị đơn hàng trung bình | Giá trị trung bình của một đơn hàng. |
| basket size | kích thước giỏ hàng | Đại lượng mô tả kích thước giỏ; trong code là số loại sản phẩm khác nhau trung bình mỗi hóa đơn. |
| product diversity | độ đa dạng sản phẩm | Mức đa dạng sản phẩm mua. |
| cancellation rate | tỷ lệ hủy | Đại lượng về các giao dịch hủy. |
| mean interpurchase time | thời gian trung bình giữa các lần mua | Khoảng thời gian trung bình giữa các lần mua. |
| demographic attributes | thuộc tính nhân khẩu học | Những thuộc tính mô tả nhân khẩu học khách hàng. |
| customer similarity graph | đồ thị tương đồng khách hàng | Đồ thị nối các khách hàng theo độ tương đồng. |
| vertex; node | đỉnh; nút | Đối tượng khách hàng trong đồ thị. |
| edge | cạnh | Liên kết giữa hai nút đồ thị. |
| edge weight | trọng số cạnh | Giá trị gắn với một cạnh. |
| degree; graph degree | bậc; bậc đồ thị | Số liên kết của nút hoặc mức bậc đang khảo sát. |
| weighted degree | bậc có trọng số | Bậc có tính đến trọng số các cạnh. |
| centrality | độ trung tâm | Đại lượng mô tả vị trí của nút trong đồ thị. |
| clustering coefficient | hệ số phân cụm | Đại lượng về kết nối cục bộ quanh nút. |
| maximum k-cut | lát cắt k cực đại | Bài toán phân hoạch đồ thị nêu trong công trình cơ sở. |
| super-vertex | siêu đỉnh | Đỉnh thu được khi gộp các vectơ điểm giống nhau. |
| k-nearest-neighbour; k-NN | k láng giềng gần nhất; k-NN | Quy tắc chọn những khách hàng gần nhất để xây dựng đồ thị. |
| Euclidean distance | khoảng cách Euclid | Khoảng cách được dùng cho đồ thị trong bài. |
| community detection | phát hiện cộng đồng | Phân chia đồ thị thành các cộng đồng. |
| modularity | độ mô-đun | Thước đo cấu trúc cộng đồng được báo cáo. |
| neighbour churn rate; NCR | tỷ lệ rời bỏ của khách hàng lân cận; NCR | Nhãn trung bình trong tập khách hàng lân cận được dùng. |
| community churn rate; CCR | tỷ lệ rời bỏ của cộng đồng; CCR | Nhãn trung bình trong cộng đồng được dùng. |
| contagion | lan truyền | Giả thuyết rủi ro rời bỏ có liên quan đến nhóm lân cận. |
| call-detail record | bản ghi chi tiết cuộc gọi | Nguồn tương tác dùng trong nghiên cứu viễn thông. |
| interaction graph | đồ thị tương tác | Đồ thị có cạnh biểu diễn tương tác được ghi nhận. |
| co-purchase | cùng mua hàng | Tín hiệu mua hàng chung được nêu cho đồ thị khác. |
| category overlap | chồng lấn danh mục | Sự trùng lặp danh mục được nêu cho đồ thị khác. |
| supervised churn model | mô hình dự báo rời bỏ có giám sát | Mô hình học từ đặc trưng và nhãn rời bỏ. |
| representation | biểu diễn | Cách mô tả khách hàng bằng các đại lượng. |
| feature space | không gian đặc trưng | Không gian của các biến đầu vào. |
| feature tier | tầng đặc trưng | Một tập đặc trưng trong năm cấu hình lồng nhau. |
| baseline | mô hình cơ sở | Cấu hình dùng làm mốc so sánh. |
| target | biến đích | Nhãn cần được dự báo. |
| target leakage | rò rỉ biến đích | Thông tin nhãn kiểm tra đi vào đặc trưng huấn luyện. |
| training fold | phần huấn luyện | Tập huấn luyện của một lần chia trong kiểm định chéo. |
| fold-local recomputation | tính lại trong từng phần huấn luyện | Tính đại lượng từ nhãn huấn luyện của riêng phần đó. |
| base rate | tỷ lệ nền | Tỷ lệ lớp rời bỏ trong tập huấn luyện. |
| standardisation | chuẩn hóa | Biến đổi đặc trưng theo tham số được khớp. |
| one-hot encoding | mã hóa one-hot | Biểu diễn nhóm bằng các biến chỉ báo. |
| classifier | bộ phân loại | Mô hình dự báo lớp. |
| logistic regression | hồi quy logistic | Bộ phân loại tham chiếu của bài. |
| gradient-boosted tree | cây tăng cường gradient | Họ mô hình cây được dùng như công cụ chuẩn. |
| linear model | mô hình tuyến tính | Mô hình ba biến được so sánh trong phần kết quả. |
| model capacity | năng lực mô hình | Khả năng biểu diễn của mô hình. |
| model class | lớp mô hình | Họ mô hình đang xét. |
| l2 regularisation | chính quy hóa l2 | Cơ chế chính quy hóa của hồi quy logistic. |
| cross-validation; CV | kiểm định chéo; CV | Giao thức đánh giá qua các phần dữ liệu. |
| stratified five-fold cross-validation | kiểm định chéo năm phần có phân tầng | Giữ phân bố lớp khi chia năm phần. |
| repeated cross-validation | kiểm định chéo lặp lại | Lặp lại nhiều cách chia kiểm định chéo. |
| corrected resampled t-test | kiểm định t lấy mẫu lại có hiệu chỉnh | Kiểm định có hiệu chỉnh cho sự chồng lấn tập huấn luyện. |
| variance-corrected test | kiểm định có hiệu chỉnh phương sai | Kiểm định sử dụng phương sai đã điều chỉnh. |
| anti-conservative | kém bảo thủ | Có thể đánh giá ý nghĩa thống kê quá lạc quan. |
| Type I error | sai lầm loại I | Bác bỏ giả thuyết không khi giả thuyết đó đúng. |
| null hypothesis | giả thuyết không | Giả thuyết dùng làm mốc của kiểm định thống kê. |
| point estimate | ước lượng điểm | Một giá trị ước lượng đơn lẻ. |
| bootstrap confidence interval | khoảng tin cậy bootstrap | Khoảng suy ra bằng lấy mẫu lại bootstrap. |
| effect magnitude; effect size | độ lớn hiệu ứng | Độ lớn của chênh lệch được so sánh. |
| uncertainty | độ bất định | Sự không chắc chắn của ước lượng. |
| standard deviation; SD | độ lệch chuẩn; SD | Thước đo độ phân tán. |
| resampling | lấy mẫu lại | Tạo các mẫu từ dữ liệu hoặc các chênh lệch. |
| fold noise | nhiễu do cách chia phần dữ liệu | Biến thiên do lựa chọn cách chia các phần. |
| library-version drift | dịch chuyển do phiên bản thư viện | Biến thiên kết quả khi phiên bản thư viện thay đổi. |
| seed | giá trị khởi tạo ngẫu nhiên | Giá trị điều khiển lựa chọn ngẫu nhiên. |
| tuning parameter | tham số điều chỉnh | Tham số được thay đổi trong khảo sát. |
| observation window | cửa sổ quan sát | Khoảng thời gian dùng để tính đặc trưng. |
| prediction window | cửa sổ dự báo | Khoảng thời gian dùng để xác định nhãn. |
| majority class | lớp đa số | Lớp chiếm nhiều khách hàng hơn trong dữ liệu. |
| imbalance | mất cân bằng | Phân bố lớp không đều. |
| discrimination | khả năng phân biệt | Khả năng phân biệt các lớp theo điểm dự báo. |
| discriminative signal | tín hiệu phân biệt | Thông tin hữu ích cho phân biệt lớp. |
| feature importance | độ quan trọng của đặc trưng | Thứ hạng hoặc giá trị được gán cho đặc trưng. |
| attribution | quy gán đóng góp | Phân bổ công trạng trong một mô hình đã khớp. |
| additive feature attribution | quy gán đóng góp đặc trưng theo dạng cộng | Cách quy gán có các phần đóng góp cộng lại. |
| global SHAP value | giá trị SHAP toàn cục | Giá trị SHAP được tổng hợp để xếp hạng đặc trưng. |
| ablation | phân tích loại bỏ thành phần | Đánh giá khi loại bỏ một thành phần hoặc đặc trưng. |
| silhouette score | điểm silhouette | Thước đo chất lượng phân cụm được nêu trong bài. |
| distance-based clustering heuristic | heuristic phân cụm dựa trên khoảng cách | Phương pháp phân cụm heuristic dùng khoảng cách. |
| spectral clustering | phân cụm phổ | Thành phần dự kiến nhưng chưa triển khai. |
| country-of-origin categorical encoding | mã hóa biến phân loại theo quốc gia xuất xứ | Thành phần dự kiến nhưng chưa triển khai. |
| expected retention value | giá trị giữ chân kỳ vọng | Đại lượng mô hình dùng để xếp hạng ưu tiên. |
| campaign-response label | nhãn phản hồi chiến dịch | Nhãn phản hồi thực tế mà dữ liệu không có. |
| negative result | kết quả âm tính | Kết quả không ủng hộ giả thuyết đang kiểm tra. |
| feature engineering | xây dựng đặc trưng | Tạo hoặc bổ sung đặc trưng đầu vào. |
| reproducibility | khả năng tái lập | Khả năng chạy lại công trình theo tài nguyên đã cung cấp. |
| large language model | mô hình ngôn ngữ lớn | Loại mô hình AI được nêu trong tuyên bố. |
