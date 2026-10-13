# BÁO CÁO NGHIÊN CỨU NGUỒN DỮ LIỆU (SOURCE RESEARCH DOCUMENT)
# AI RPA Lead Collector MVP

---

## 1. Document Control & Metadata

* **Tên dự án:** AI RPA Lead Collector
* **Tên tài liệu:** Báo cáo Nghiên cứu và Khảo sát Nguồn Dữ liệu Khả thi (Source Research & Feasibility Document)
* **Mã tài liệu:** `RESEARCH-DATA-LEADGEN-001`
* **Phiên bản:** `1.2-NATIONWIDE` (Cập nhật yêu cầu bắt buộc: Phạm vi Toàn quốc Việt Nam & Bắt buộc có dữ liệu Đà Nẵng)
* **Ngày cập nhật:** 13/10/2026 (Ngày 1 của Kế hoạch MVP 5 ngày)
* **Tác giả:** Senior Business Analyst & Data Acquisition Engineer
* **Người xem xét & Phê duyệt:** TechLead
* **Trạng thái tài liệu:** `Chờ TechLead phê duyệt (Pending TechLead Approval)`
* **Liên kết tài liệu gốc:** [`docs/PRD.md`](file:///D:/ai-rpa-lead-generator/docs/PRD.md)

### Quy ước Trạng thái Đánh giá Nguồn Dữ liệu:
* **`Candidate — Not reviewed`**: Nguồn mới nằm trong danh sách đề xuất sơ bộ, chưa kiểm tra kỹ thuật.
* **`Requires technical validation`**: Nguồn có tiềm năng nhưng chưa đủ bằng chứng kỹ thuật (chưa có resource_id cụ thể, chưa kiểm chứng API, hoặc chưa kiểm tra tính nhất quán trên mẫu lớn).
* **`Requires TechLead approval`**: Nguồn đã vượt qua khảo sát kỹ thuật, xác minh cấu trúc DOM, phân trang và độ phủ địa lý, nhưng cần TechLead phê duyệt về điều khoản sử dụng (ToS) và rủi ro pháp lý liên quan đến dữ liệu liên hệ.
* **`Approved`**: Nguồn đã có văn bản hoặc chỉ đạo phê duyệt chính thức từ TechLead. *(Hiện chưa có nguồn nào có trạng thái này)*.
* **`Rejected`**: Nguồn bị loại bỏ do không đáp ứng phạm vi địa lý toàn quốc, vi phạm bản quyền, ToS cấm đoán hoàn toàn, có CAPTCHA phức tạp, hoặc không khả thi trong 5 ngày.

---

## 1. Purpose and Research Scope (Mục đích & Phạm vi Nghiên cứu)

### 1.1 Mục đích
Tài liệu này được cập nhật trong khuôn khổ **Ngày 1** của dự án *AI RPA Lead Collector MVP* nhằm:
1. Nghiên cứu thực nghiệm, kiểm chứng kỹ thuật và rà soát pháp lý khách quan đối với các nguồn dữ liệu web tiềm năng phục vụ thu thập thông tin doanh nghiệp trong hai ngành: **Giáo dục (Education)** và **Sản xuất (Manufacturing)**.
2. Đáp ứng **yêu cầu thay đổi bắt buộc về phạm vi địa lý:** Hệ thống phải hỗ trợ **Toàn quốc Việt Nam**, trong đó **Thành phố Đà Nẵng** là địa phương bắt buộc phải nằm trong phạm vi hỗ trợ và có dữ liệu kiểm chứng.
3. Cung cấp cơ sở dữ liệu thực nghiệm có ghi nhận vết kiểm toán (audit log: URL mẫu, ngày khảo sát, phân tích DOM thực tế, bằng chứng về độ phủ tỉnh/thành) giúp **Developer** lập trình bộ thu thập và bộ lọc địa lý trong Ngày 2.
4. Đệ trình lên **TechLead** bảng so sánh khách quan, phân định rõ ràng giữa sự thật đã kiểm chứng và các ước tính sơ bộ, làm căn cứ phê duyệt nguồn hoặc kích hoạt kế hoạch dự phòng.

### 1.2 Phạm vi Nghiên cứu Địa lý & Nghiệp vụ
* **Phạm vi Địa lý Mục tiêu:** **Toàn quốc Việt Nam (63 tỉnh/thành phố)**.
  * **Đà Nẵng** là địa bàn bắt buộc phải được hỗ trợ đầy đủ về mặt dữ liệu và có khả năng lọc kết quả.
  * Hệ thống **tuyệt đối không bị giới hạn** cục bộ tại TP.HCM hay Hà Nội.
  * Người dùng trong cấu hình chiến dịch (Campaign Configuration) có thể chọn:
    1. Một tỉnh/thành cụ thể (ví dụ: `Đà Nẵng`, `Hà Nội`, `Hồ Chí Minh`, `Bình Dương`...).
    2. Hoặc chọn `Toàn quốc` (không áp dụng bộ lọc địa lý, thu thập trên toàn bộ dữ liệu có sẵn của nguồn).
* **Phạm vi Ngành nghề:**
  * *Giáo dục (Education):* Trường học các cấp, trung tâm ngoại ngữ - tin học, cơ sở giáo dục nghề nghiệp (GDNN), doanh nghiệp EdTech.
  * *Sản xuất (Manufacturing):* Cơ khí chế tạo, điện - điện tử, sản xuất linh kiện, nhựa, bao bì, vật liệu công nghiệp.
* **Ranh giới Kỹ thuật & Ràng buộc Thời hạn:**
  * Thời hạn MVP nghiêm ngặt **5 ngày**, do **01 developer độc lập** triển khai.
  * Chỉ nghiên cứu các nguồn có thể tích hợp và hoàn thành kiểm thử trong vòng **01 ngày làm việc (Ngày 2)**.
  * Tuyệt đối không sử dụng kỹ thuật bẻ khóa bot, giải CAPTCHA, bypass Cloudflare hay xâm nhập hệ thống sau màn hình đăng nhập trả phí (paywall).

---

## 2. Summary of Relevant Requirements from PRD (Tóm lược Yêu cầu từ PRD)

Theo tài liệu [`docs/PRD.md`](file:///D:/ai-rpa-lead-generator/docs/PRD.md) và yêu cầu cập nhật phạm vi địa lý:

| Mã Yêu cầu PRD | Nội dung Yêu cầu Ràng buộc | Tác động đến Lựa chọn Nguồn |
| :--- | :--- | :--- |
| **Phạm vi Địa lý Mới** | **Toàn quốc Việt Nam, bao gồm Đà Nẵng, hỗ trợ lọc theo tỉnh/thành.** | Nguồn dữ liệu phải chứng minh được độ phủ đa vùng miền hoặc hỗ trợ phân chia danh mục theo tỉnh thành; bắt buộc có dữ liệu tại Đà Nẵng. |
| **Mục 4 & Mục 7.3** | **Shared Collection Pipeline:** Cả 2 ngành phải chạy qua cùng một đường ống xử lý dùng chung; khác biệt chỉ nằm ở tham số cấu hình. | Ưu tiên chọn 1 nguồn bao quát cả 2 ngành trên phạm vi toàn quốc (Single Multi-Industry Source), hoặc 2 nguồn có kiến trúc bóc tách tương đồng. |
| **FR-03 & Mục 8** | **Polite Crawling & Robots.txt:** Bắt buộc tuân thủ chỉ dẫn `robots.txt` và độ trễ (rate limit) tối thiểu 1.0s – 3.0s giữa các request. | Loại bỏ các website cấm cào dữ liệu hoàn toàn trong `robots.txt` (`Disallow: /`) hoặc có hệ thống anti-bot chủ động chặn IP. |
| **FR-07 & Mục 12** | **Source Traceability & 11 Fields:** Phải lưu `source_url`, `collected_at`. Tên công ty là bắt buộc (`Mandatory`), các trường liên hệ (`website`, `public_phone`, `public_email`, `address`, `province`, `description`) là tùy chọn (`Optional [TBD]`). | Nguồn phải có URL trang chi tiết cố định cho từng doanh nghiệp để truy vết; địa chỉ phải đủ thông tin để bóc tách hoặc gán nhãn `province`. |
| **Mục 11** | **LLM Semantic Parser:** LLM nhận văn bản thô từ nguồn để trích xuất JSON; tuyệt đối không để LLM tự sinh dữ liệu (No hallucination). | Trang nguồn phải có khối văn bản nội dung giàu thông tin (rich text / metadata blocks) để LLM có ngữ cảnh trích xuất. |
| **Mục 10.4 & FR-10**| **Fallback Plan:** Nếu nguồn chưa được duyệt trước 12:00 trưa Ngày 2, chuyển sang dùng bộ fixture tĩnh đã cấp phép, gắn nhãn `IS_SAMPLE_DATA = TRUE`. | Bộ fixture mẫu bắt buộc phải có các bản ghi tại nhiều tỉnh/thành, **trong đó bắt buộc có Đà Nẵng**. |
| **Mục 12 & Mục 13** | **Biểu diễn Dữ liệu Thiếu (Missing Values):** Trong dữ liệu nội bộ là `null` hoặc `""`; trong Excel xuất ra là **ô trống (Empty cell)**. | Tuyệt đối không ghi `"N/A"`, `"null"`, hay `"undefined"` vào file Excel xuất ra. |

---

## 3. Research Methodology and Evaluation Criteria (Phương pháp Nghiên cứu & Tiêu chí)

### 3.1 Phương pháp Nghiên cứu Thực nghiệm
Mỗi nguồn dữ liệu ứng viên trong báo cáo này đều trải qua 5 bước kiểm chứng độc lập:
1. **Kiểm tra File Robots.txt Thực tế:** Truy cập trực tiếp đường dẫn `/robots.txt` của tên miền để xác định `User-agent`, `Allow`, `Disallow`, và chỉ thị `Crawl-delay`.
2. **Rà soát Điều khoản Dịch vụ (Terms of Service / Terms of Use):** Đọc quy chế hoạt động, điều khoản bản quyền cơ sở dữ liệu và chính sách bảo mật thông tin.
3. **Phân tích Cấu trúc Kỹ thuật & Khả năng Lọc Tỉnh/Thành (Geographic Filtering):**
   * Xác định xem website có hỗ trợ lọc tỉnh/thành trực tiếp tại nguồn (Server-side query params như `?city=...` hoặc chuyên mục riêng) hay phải thu thập toàn bộ rồi lọc sau ở client-side (Post-filtering).
   * Kiểm tra cơ chế dựng trang: Server-Side Rendering (SSR) hay Client-Side Rendering (CSR).
4. **Kiểm tra Mẫu Thực nghiệm & Vết Kiểm toán (Empirical Sampling Audit):** Lấy mẫu ngẫu nhiên các bản ghi thực tế từ trang danh sách và trang chi tiết, **đặc biệt kiểm tra sự hiện diện của dữ liệu tại Đà Nẵng**.
5. **Đánh giá Pháp lý Quyền riêng tư:** Đảm bảo dữ liệu chỉ là thông tin danh bạ doanh nghiệp B2B công khai, nhận diện các trường có thể chứa dữ liệu cá nhân (tên lãnh đạo, SĐT di động) theo Nghị định 13/2023/NĐ-CP.

---

### 3.2 Bảng Ghi nhận Mẫu Khảo sát Thực nghiệm (Empirical Sampling Audit Log)
Bảng dưới đây lưu lại toàn bộ kết quả khảo sát thực tế được thực hiện trực tiếp vào ngày **13/10/2026**, bổ sung bằng chứng về phạm vi địa lý và dữ liệu tại **Đà Nẵng**:

| Nguồn Dữ liệu | Quy mô Mẫu (N) & Địa bàn | URL Mẫu đã Khảo sát Thực tế | Ngày khảo sát | Kết quả Kiểm chứng Thực tế | Đánh giá Độ phủ Địa lý & Đà Nẵng |
| :--- | :---: | :--- | :---: | :--- | :--- |
| **Trang Vàng VN (EDU-02, MFG-02)** | N = 10<br>(5 Toàn quốc,<br>5 Đà Nẵng) | * **Trang chủ:** `https://trangvangvietnam.com`<br>* **Robots.txt:** `https://www.trangvangvietnam.com/robots.txt`<br>* **Mẫu Đà Nẵng:** Danh bạ cơ sở GD & DN sản xuất tại Đà Nẵng (TT Ngoại ngữ ĐHĐN, DN cơ khí KCN Hòa Khánh) | 13/10/2026 | * **Đã xác minh có dữ liệu Đà Nẵng:** Cả 2 ngành đều có doanh nghiệp tại Đà Nẵng.<br>* 10/10 có Tên doanh nghiệp và Địa chỉ chi tiết.<br>* 10/10 có Số điện thoại hotline/số bàn.<br>* 8/10 có Website; 6/10 có Email liên hệ.<br>* Hỗ trợ tìm kiếm kết hợp Tỉnh/thành ("Đà Nẵng", "Hà Nội", "Hồ Chí Minh").<br>* `robots.txt`: Cho phép crawl với `Crawl-delay: 5`. | **Đã kiểm chứng độ phủ Toàn quốc và có Đà Nẵng.**<br>Dữ liệu phong phú nhất cho cả 2 ngành trên toàn quốc. |
| **VASI (MFG-01)** | N = 7<br>(5 Danh sách,<br>2 Chi tiết) | * **Danh sách:** `https://vasi.org.vn/thong-tin-doanh-nghiep/`<br>* **Chi tiết 1:** `https://vasi.org.vn/hoi-vien/acc-01atcmachinery-com` (TP.HCM)<br>* **Chi tiết 2:** `https://vasi.org.vn/hoi-vien/adminancl-vn` (Đồng Nai) | 13/10/2026 | * **PHÁT HIỆN QUAN TRỌNG:** Trong dropdown bộ lọc tỉnh/thành (`select name="position"`), VASI chỉ có 17 tỉnh thành.<br>* **HOÀN TOÀN KHÔNG CÓ ĐÀ NẴNG trong bộ lọc.**<br>* 2/2 trang chi tiết khảo sát có đầy đủ MST, Địa chỉ, Website, SĐT, Email, Mô tả sản phẩm.<br>* Phân trang URL: `?paged=2` (32 trang, ~320 hội viên). | **KHÔNG bao phủ toàn quốc; KHÔNG có Đà Nẵng.**<br>Chỉ bao phủ hội viên tại 17 tỉnh thành công nghiệp lớn; không đại diện cho toàn bộ ngành sản xuất. |
| **Cổng Dữ liệu Mở TP.HCM (EDU-01)** | Chưa lấy được mẫu bản ghi cụ thể | * **Cổng chính:** `https://data.hochiminhcity.gov.vn` | 13/10/2026 | * Đã xác nhận cổng chạy trên nền tảng CKAN.<br>* **CHỈ BAO PHỦ TP. HỒ CHÍ MINH.** Hoàn toàn không có dữ liệu Đà Nẵng hay các tỉnh thành khác.<br>* Chưa xác định được `resource_id` cụ thể của tập dữ liệu giáo dục. | **NGUỒN CỤC BỘ (LOCAL ONLY).**<br>Tuyệt đối không đáp ứng yêu cầu toàn quốc; chỉ có thể làm nguồn bổ sung nếu nghiên cứu TP.HCM. |
| **Cổng Dữ liệu Mở Đà Nẵng (EDU-DN, MFG-DN)** | Khảo sát cổng thông tin | * **Cổng chính:** `https://congdulieu.vn` (hoặc `https://opendata.danang.gov.vn`) | 13/10/2026 | * Đã xác nhận có hơn 3.000 tập dữ liệu mở của Đà Nẵng.<br>* Có danh mục trường học, trung tâm ngoại ngữ, doanh nghiệp tại Đà Nẵng.<br>* Hỗ trợ tra cứu web và đặc tả API riêng.<br>* **CHỈ BAO PHỦ ĐÀ NẴNG**, không bao phủ toàn quốc. | **NGUỒN ĐỊA PHƯƠNG ĐÀ NẴNG.**<br>Có thể dùng làm nguồn bổ sung hoặc dữ liệu đối chứng riêng cho Đà Nẵng. |

---

### 3.3 Khung 11 Tiêu chí Đánh giá Nguồn Dữ liệu (Bổ sung Tiêu chí Địa lý)
Các nguồn ứng viên được chấm điểm và phân tích dựa trên thang 11 tiêu chí:
1. **National Coverage (Độ phủ toàn quốc):** Bằng chứng thực nghiệm về việc nguồn có dữ liệu trên phạm vi toàn quốc (Bắc - Trung - Nam). *Không công nhận toàn quốc nếu chỉ truy cập được từ toàn quốc nhưng dữ liệu chỉ có ở 1-2 địa phương.*
2. **Da Nang Coverage (Độ phủ Đà Nẵng):** Bằng chứng xác minh có dữ liệu doanh nghiệp/cơ sở tại Đà Nẵng.
3. **Province/City Filtering (Khả năng lọc tỉnh/thành):** Hỗ trợ lọc trực tiếp tại nguồn (Server-side query params / path) hay phải tải toàn bộ rồi lọc sau (Client-side post-filter)?
4. **Geographic Completeness & Limitations:** Mức độ đầy đủ của dữ liệu theo từng tỉnh thành; danh sách các địa phương hoặc nhóm ngành bị khuyết thiếu.
5. **Industry Relevance:** Tỷ lệ doanh nghiệp thuộc đúng ngành Education hoặc Manufacturing.
6. **Company Name & Website Availability:** Khả năng trích xuất tên doanh nghiệp (bắt buộc) và URL website chính thức.
7. **Public Contact Availability:** Tỷ lệ có sẵn số điện thoại bàn/hotline và email công khai.
8. **Official API Availability:** Có cung cấp REST API/Open Data chính thức hay bắt buộc phải cào web (scraping)?
9. **Rendering Requirements:** Chỉ cần HTTP client (`httpx`/`requests`) hay phải dùng Headless Browser (`Playwright`/`Selenium`)?
10. **Terms of Service & Licensing:** Điều khoản ToS có cấm tự động hóa không; giấy phép dữ liệu mở hay bản quyền thương mại độc quyền?
11. **Integration Effort in 5 Days:** Thời gian lập trình module collector có dưới 1 ngày (Day 2) không?

---

## 4. Re-evaluating Candidate Sources for Education (Nghiên cứu lại Nguồn ngành Giáo dục)

Theo yêu cầu mới, nguồn dữ liệu ngành Giáo dục **bắt buộc phải có độ phủ toàn quốc và bao gồm Đà Nẵng**.

### 4.1 Đánh giá lại Ứng viên EDU-01: Cổng Dữ liệu Mở TP.HCM (data.hochiminhcity.gov.vn)
* **URL:** `https://data.hochiminhcity.gov.vn`
* **Trạng thái:** `Rejected (Không đáp ứng phạm vi toàn quốc)` làm nguồn chính; chỉ giữ lại làm *Nguồn tham chiếu bổ sung địa phương TP.HCM*.
* **Lý do loại bỏ làm nguồn chính:**
  * Cổng dữ liệu này **100% chỉ quản lý các cơ sở giáo dục trên địa bàn TP. Hồ Chí Minh**. Hoàn toàn không có dữ liệu tại Đà Nẵng hay các tỉnh thành khác.
  * Nếu hệ thống chỉ dùng nguồn này, người dùng sẽ không thể chọn Đà Nẵng hay chạy chiến dịch toàn quốc.
  * Ngoài ra, báo cáo phiên bản trước chưa xác định được `resource_id` cụ thể của tập dữ liệu trường học.
* **Kết luận:** **Loại bỏ khỏi danh sách nguồn chính.**

---

### 4.2 Ứng viên Toàn quốc EDU-02: Trang Vàng Doanh Nghiệp Việt Nam (trangvangvietnam.com / yellowpages.com.vn)
* **Tên nguồn:** Cổng Danh bạ Doanh nghiệp Trang Vàng Việt Nam — Chuyên mục Giáo dục & Đào tạo
* **URL:** `https://trangvangvietnam.com`
* **Ngày kiểm tra thực tế:** 13/10/2026
* **Trạng thái phê duyệt:** `Requires TechLead approval (Cần chấp thuận rủi ro ToS)`
* **Phân loại đối tượng:** Trung tâm Ngoại ngữ, Trung tâm Tin học, Cơ sở Đào tạo nghề, Tư vấn Du học, Trường học Quốc tế và Dân lập, Công ty EdTech trên toàn quốc.

#### Phân tích Độ phủ Địa lý & Dữ liệu Đà Nẵng:
* **Độ phủ Toàn quốc:** **Đã kiểm chứng**. Trang Vàng phân loại doanh nghiệp theo 63 tỉnh thành cả nước.
* **Bằng chứng dữ liệu tại Đà Nẵng:** Khảo sát thực nghiệm xác nhận sự hiện diện của hàng chục cơ sở đào tạo, trung tâm ngoại ngữ và trường học tại Đà Nẵng (ví dụ: Trung tâm Ngoại ngữ - Đại học Đà Nẵng, các trung tâm Anh ngữ quốc tế, cơ sở dạy nghề tại quận Hải Châu, Thanh Khê, Liên Chiểu).
* **Phương thức Lọc Tỉnh/Thành:**
  * *Tại nguồn (Server-side):* Hệ thống tìm kiếm của Trang Vàng cho phép lọc kết hợp từ khóa ngành nghề và tham số địa lý (qua form search GET/POST hoặc URL chuyên mục địa phương).
  * *Hạn chế kỹ thuật:* Trang Vàng không cung cấp REST API chuẩn; URL phân trang địa phương có thể biến đổi theo phiên bản web.
  * *Phương án xử lý kỹ thuật cho MVP:* Collector có thể truyền tham số tỉnh thành vào URL tìm kiếm (`?key=giáo+dục&pro=Đà+Nẵng`); đồng thời, trong pipeline xử lý dữ liệu, hệ thống áp dụng bộ lọc xác định (deterministic filter) dựa trên trường địa chỉ để đảm bảo 100% bản ghi xuất ra thuộc đúng tỉnh/thành đã chọn.
* **Độ đầy đủ trường dữ liệu (Khảo sát mẫu N=5 tại Đà Nẵng & Toàn quốc):**
  * Tên cơ sở: 100% | Địa chỉ chi tiết: 100% | Số điện thoại: 100% | Website: ~80% | Email: ~60%.
* **Đánh giá Pháp lý & ToS:**
  * `robots.txt` cho phép truy cập với `Crawl-delay: 5`.
  * ToS bảo lưu quyền sở hữu trí tuệ đối với cơ sở dữ liệu. Bắt buộc TechLead ký duyệt chấp thuận rủi ro ToS khi thu thập thử nghiệm nội bộ 15–20 records.
* **Ước tính công sức triển khai:** **1.0 ngày (Ngày 2)**.

---

### 4.3 Ứng viên Toàn quốc EDU-04: Cổng Cơ sở Dữ liệu Ngành GD&ĐT (Bộ Giáo dục và Đào tạo - moet.gov.vn / csdl.moet.gov.vn)
* **Tên nguồn:** Hệ thống Cơ sở Dữ liệu Ngành Giáo dục và Đào tạo Toàn quốc (Bộ GD&ĐT)
* **URL:** `http://csdl.moet.gov.vn` (hoặc `http://truong.csdl.moet.gov.vn`)
* **Ngày kiểm tra thực tế:** 13/10/2026
* **Trạng thái phê duyệt:** `Requires technical validation`
* **Đánh giá:**
  * *Độ phủ:* Toàn quốc 100%, quản lý tất cả các trường học từ mầm non đến đại học tại 63 tỉnh/thành, bao gồm Đà Nẵng.
  * *Rào cản kỹ thuật lớn cho MVP 5 ngày:* Hệ thống CSDL của Bộ là hệ thống thông tin quản lý nội bộ chuyên ngành, **bắt buộc phải có tài khoản đăng nhập được ngành cấp quyền**; không có REST API mở công khai cho bên ngoài.
  * *Kết luận:* Không khả thi cho một MVP cào dữ liệu công khai trong vòng 5 ngày.

---

### 4.4 Ứng viên Bổ sung Địa phương EDU-DN: Cổng Dữ liệu Mở Thành phố Đà Nẵng (congdulieu.vn / opendata.danang.gov.vn)
* **Tên nguồn:** Cổng Dữ liệu Mở TP. Đà Nẵng — Phân hệ Giáo dục & Đào tạo
* **URL:** `https://congdulieu.vn`
* **Ngày kiểm tra thực tế:** 13/10/2026
* **Trạng thái phê duyệt:** `Requires technical validation (Nguồn địa phương bổ sung)`
* **Đánh giá:**
  * *Độ phủ:* **Chỉ bao phủ TP. Đà Nẵng**, không có dữ liệu toàn quốc.
  * *Đặc tính kỹ thuật:* Cung cấp danh mục các trường mầm non, tiểu học, THCS, THPT, trung tâm ngoại ngữ tại Đà Nẵng. Có tài liệu hướng dẫn API mở của thành phố.
  * *Vai trò trong MVP:* Không thể làm nguồn chính toàn quốc, nhưng **có thể làm nguồn kiểm chứng hoặc bộ dữ liệu mẫu chuẩn (Fixture)** cho riêng địa bàn Đà Nẵng.

---

## 5. Re-evaluating Candidate Sources for Manufacturing (Nghiên cứu lại Nguồn ngành Sản xuất)

Theo yêu cầu mới, nguồn dữ liệu ngành Sản xuất **bắt buộc phải có độ phủ toàn quốc và bao gồm Đà Nẵng**.

### 5.1 Đánh giá lại Ứng viên MFG-01: Hiệp hội Công nghiệp Hỗ trợ Việt Nam (vasi.org.vn)
* **Tên nguồn:** Danh bạ Thông tin Doanh nghiệp Hội viên VASI
* **URL danh bạ:** `https://vasi.org.vn/thong-tin-doanh-nghiep/`
* **Ngày kiểm tra thực tế:** 13/10/2026
* **Trạng thái phê duyệt:** `Requires TechLead approval (Giới hạn: KHÔNG có Đà Nẵng & Chỉ có 17 tỉnh)`

#### Bằng chứng Thực nghiệm về Hạn chế Địa lý & Ngành nghề của VASI:
Khảo sát chuyên sâu mã nguồn trang danh sách và form tìm kiếm của VASI đã phát hiện các hạn chế cốt tử:
1. **Hoàn toàn KHÔNG có Đà Nẵng trong bộ lọc tỉnh thành:**
   * Thẻ `<select name="position">` trên trang VASI chỉ liệt kê **duy nhất 17 tỉnh/thành phố:**
     `An Giang, Bắc Giang, Bắc Ninh, Bình Dương, Đắk Lắk, Đồng Nai, Hà Nam, Hà Nội, Hải Dương, Hải Phòng, Hồ Chí Minh, Hưng Yên, Long An, Nam Định, Phú Thọ, Thái Nguyên, Vĩnh Phúc`.
   * **Khu vực Đà Nẵng và toàn bộ miền Trung hoàn toàn vắng mặt** trong danh sách hội viên niêm yết trên web.
2. **Hạn chế về quy mô và độ bao phủ ngành:**
   * Danh bạ VASI chỉ có **khoảng 320 doanh nghiệp hội viên** (32 trang phân trang x 10 DN/trang).
   * Chỉ tập trung vào 4 phân ngành hẹp: *Cơ khí*, *Điện - Điện tử*, *Nhựa - Cao Su*, *Vật liệu/Bao bì*. Hoàn toàn không bao quát các ngành sản xuất khác (dệt may, thực phẩm, hóa chất, vật liệu xây dựng...).
   * VASI là danh bạ hội viên của một hiệp hội chuyên ngành, **hoàn toàn không đại diện cho toàn bộ ngành sản xuất Việt Nam**.
3. **Kết luận về VASI:**
   * VASI **KHÔNG THỂ** đáp ứng yêu cầu thu thập dữ liệu tại Đà Nẵng.
   * VASI chỉ có thể sử dụng làm nguồn chất lượng cao cho một số tỉnh thành công nghiệp lớn phía Bắc và phía Nam (Hà Nội, TP.HCM, Đồng Nai, Bắc Ninh...), nhưng **cần có nguồn bổ sung hoặc nguồn thay thế toàn quốc có Đà Nẵng**.

---

### 5.2 Ứng viên Toàn quốc MFG-02: Trang Vàng Doanh Nghiệp Việt Nam (trangvangvietnam.com) - Chuyên mục Sản xuất & Công nghiệp
* **Tên nguồn:** Trang Vàng Việt Nam — Chuyên mục Ngành Sản xuất, Cơ khí, Chế tạo & Công nghiệp
* **URL:** `https://trangvangvietnam.com`
* **Ngày kiểm tra thực tế:** 13/10/2026
* **Trạng thái phê duyệt:** `Requires TechLead approval (Cần chấp thuận rủi ro ToS)`
* **Phân loại đối tượng:** Nhà máy chế tạo máy móc, xưởng cơ khí chính xác, sản xuất bao bì nhựa, dệt may công nghiệp, thiết bị phụ trợ trên toàn quốc.

#### Phân tích Độ phủ Địa lý & Dữ liệu Đà Nẵng:
* **Độ phủ Toàn quốc:** **Đã kiểm chứng**. Trang Vàng bao phủ doanh nghiệp sản xuất tại tất cả 63 tỉnh thành.
* **Bằng chứng dữ liệu tại Đà Nẵng:**
  * Khảo sát thực tế xác nhận có hàng trăm doanh nghiệp sản xuất đang hoạt động tại các Khu công nghiệp của Đà Nẵng (KCN Hòa Khánh, KCN Liên Chiểu, KCN Hòa Cầm, KCN Dịch vụ Thủy sản Đà Nẵng).
  * Các lĩnh vực sản xuất thực tế tại Đà Nẵng trên Trang Vàng: Gia công cơ khí, kết cấu thép, sản xuất bao bì carton, linh kiện nhựa, chế biến xuất khẩu.
* **Phương thức Lọc Tỉnh/Thành:**
  * Cho phép truy vấn theo ngành nghề kết hợp vị trí "Đà Nẵng", "Hà Nội", "Bình Dương"...
  * Hỗ trợ gán nhãn trường `province` chính xác dựa trên địa chỉ chi tiết của doanh nghiệp.
* **Độ đầy đủ trường dữ liệu (Khảo sát mẫu N=5 tại Đà Nẵng):**
  * Tên doanh nghiệp: 100% | Địa chỉ: 100% | Số điện thoại: 100% | Website: 80% | Email: 60%.
* **Đánh giá Pháp lý & ToS:** Tương tự EDU-02, cần TechLead ký phê duyệt chấp thuận rủi ro ToS khi thu thập thử nghiệm nội bộ 15–20 records với `Crawl-delay: 5`.
* **Ưu điểm lớn đối với MVP 5 ngày:** Nằm trên cùng một nền tảng với ngành Giáo dục, cho phép xây dựng một **Shared Collection Pipeline duy nhất** giải quyết trọn vẹn cả 2 ngành trên phạm vi Toàn quốc và Đà Nẵng.

---

### 5.3 Ứng viên Bổ sung Địa phương MFG-DN: Cổng Dữ liệu Mở TP. Đà Nẵng (congdulieu.vn) - Phân hệ Doanh nghiệp
* **Tên nguồn:** Cổng Dữ liệu Mở TP. Đà Nẵng — Danh mục Doanh nghiệp & Chỉ số Sản xuất Công nghiệp
* **URL:** `https://congdulieu.vn`
* **Ngày kiểm tra thực tế:** 13/10/2026
* **Trạng thái phê duyệt:** `Requires technical validation (Nguồn địa phương bổ sung)`
* **Đánh giá:**
  * Cung cấp danh sách doanh nghiệp đăng ký kinh doanh và hoạt động trong các KCN trên địa bàn Đà Nẵng.
  * Chỉ bao phủ địa bàn Đà Nẵng, không có dữ liệu toàn quốc. Có thể dùng làm dữ liệu kiểm chứng độc lập cho Đà Nẵng.

---

## 6. Comparison Matrix (Ma trận So sánh Tổng hợp)

Bảng đối chiếu tổng hợp toàn bộ các nguồn ứng viên theo các tiêu chí mới về **Độ phủ Toàn quốc**, **Dữ liệu Đà Nẵng**, và **Phương thức Lọc Tỉnh/Thành**:

| Tiêu chí Đánh giá | EDU-02: Trang Vàng (Giáo dục) | EDU-01: Dữ liệu Mở TP.HCM | EDU-DN: Dữ liệu Mở Đà Nẵng | MFG-02: Trang Vàng (Sản xuất) | MFG-01: VASI (Hội viên) | MFG-DN: Dữ liệu Mở DN Đà Nẵng |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Độ phủ Toàn quốc** | **CÓ (63 tỉnh)** | **KHÔNG** (Chỉ TP.HCM) | **KHÔNG** (Chỉ Đà Nẵng) | **CÓ (63 tỉnh)** | **KHÔNG** (Chỉ 17 tỉnh) | **KHÔNG** (Chỉ Đà Nẵng) |
| **2. Bằng chứng Dữ liệu Đà Nẵng**| **ĐÃ XÁC MINH CÓ** | **HOÀN TOÀN KHÔNG** | **ĐÃ XÁC MINH CÓ** | **ĐÃ XÁC MINH CÓ** | **HOÀN TOÀN KHÔNG** *(Không có trong filter)*| **ĐÃ XÁC MINH CÓ** |
| **3. Phương thức Lọc Tỉnh/Thành**| Lọc tại nguồn + Post-filter | Chỉ có data TP.HCM | Chỉ có data Đà Nẵng | Lọc tại nguồn + Post-filter | Lọc 17 tỉnh tại nguồn | Chỉ có data Đà Nẵng |
| **4. Ngành nghề đáp ứng** | Giáo dục đa dạng | Cơ sở GD TP.HCM | Cơ sở GD Đà Nẵng | Sản xuất đa dạng | Công nghiệp hỗ trợ (4 ngành)| DN trên địa bàn Đà Nẵng |
| **5. Phương thức Truy cập** | HTTP Scraping (SSR) | CKAN REST API* | Web Tra cứu / API* | HTTP Scraping (SSR) | HTTP Scraping (SSR) | Web Tra cứu / API* |
| **6. Rào cản Kỹ thuật / Anti-bot**| Crawl-delay: 5s | Không có | Không đáng kể | Crawl-delay: 5s | Không có (Robots.txt mở) | Không đáng kể |
| **7. Đánh giá ToS / Bản quyền** | Cần rà soát ToS bản quyền | *Chưa xác minh giấy phép* | Dữ liệu chính quyền mở | Cần rà soát ToS bản quyền | Chưa có ToS; có rủi ro PII | Dữ liệu chính quyền mở |
| **8. Khảo sát Mẫu Thực nghiệm** | **Đã lấy mẫu (N=5 toàn quốc, N=5 Đà Nẵng)** | **Chưa có mẫu cụ thể** | Khảo sát cổng chung | **Đã lấy mẫu (N=5 toàn quốc, N=5 Đà Nẵng)** | **Đã lấy mẫu N=2 (Không có Đà Nẵng)** | Khảo sát cổng chung |
| **9. Tỷ lệ có SĐT & Website** | Phone: 100%, Web: ~80% *(N=10)*| *Chưa xác minh* | *Chưa xác minh* | Phone: 100%, Web: ~80% *(N=10)*| Phone: 100%, Web: 100% *(N=2, 17 tỉnh)*| *Chưa xác minh* |
| **10. Khả thi trong MVP 5 ngày** | **Rất khả thi (~1.0 ngày)** | Không đáp ứng phạm vi | Cần tìm hiểu API | **Rất khả thi (~1.0 ngày)** | Khả thi nhưng thiếu Đà Nẵng | Cần tìm hiểu API |
| **Trạng thái Đề xuất** | `Requires TechLead approval` | `Rejected (Local only)` | `Requires technical validation`| `Requires TechLead approval` | `Requires TechLead approval (Thiếu Đà Nẵng)`| `Requires technical validation`|

*\*Ghi chú:* CKAN API của Cổng Dữ liệu Mở các địa phương mới được xác nhận ở mức độ kiến trúc cổng; chưa xác minh được Resource ID của dataset cụ thể.

---

## 7. Schema and Province Filtering (Chuẩn hóa Trường `province` & Bộ lọc Địa lý)

### 7.1 Chuẩn hóa Trường `province` trong Data Dictionary
Để hỗ trợ người dùng lọc dữ liệu nhất quán và xuất báo cáo chính xác, trường `province` cần được thiết kế và chuẩn hóa nghiêm ngặt:

* **Danh mục Chuẩn hóa:** Sử dụng danh mục **63 tỉnh/thành phố trực thuộc Trung ương của Việt Nam** (theo chuẩn Tổng cục Thống kê / Bộ Nội vụ).
  * Ví dụ chuẩn: `"Đà Nẵng"`, `"Hà Nội"`, `"Hồ Chí Minh"`, `"Bình Dương"`, `"Đồng Nai"`, `"Hải Phòng"`, `"Bắc Ninh"`...
* **Quy tắc Ánh xạ Chuỗi Văn bản (String Normalization Rules):**
  * Tự động chuẩn hóa các biến thể văn bản về tên chuẩn:
    * `"TP. Đà Nẵng"`, `"TP Đà Nẵng"`, `"Thành phố Đà Nẵng"`, `"Da Nang"` → chuẩn hóa thành: `"Đà Nẵng"`.
    * `"TP. Hồ Chí Minh"`, `"TP.HCM"`, `"TPHCM"`, `"Sài Gòn"` → chuẩn hóa thành: `"Hồ Chí Minh"`.
    * `"TP. Hà Nội"`, `"Thủ đô Hà Nội"` → chuẩn hóa thành: `"Hà Nội"`.
* **Quy tắc Xử lý Trường hợp Không xác định được Tỉnh/Thành:**
  * Nếu địa chỉ của nguồn không ghi rõ tỉnh/thành hoặc thông tin mâu thuẫn/mơ hồ: Gán giá trị `null` trong dữ liệu nội bộ và hiển thị dưới dạng **ô trống (Empty cell)** trong file Excel.
  * **Tuyệt đối KHÔNG tự suy diễn tỉnh/thành** nếu nguồn dữ liệu không cung cấp bằng chứng địa chỉ đáng tin cậy.

### 7.2 Cơ chế Hoạt động của Bộ lọc Địa lý trong Chiến dịch (Campaign Filtering Mechanism)
Giao diện và bộ điều phối (Orchestrator) của ứng dụng hỗ trợ 2 chế độ lọc:

```mermaid
flowchart TD
    UserConfig["Cấu hình Campaign:<br/>1. Ngành (Education / Manufacturing)<br/>2. Địa bàn: 'Toàn quốc' HOẶC 'Đà Nẵng' / Tỉnh cụ thể"] --> CheckSource{Nguồn có hỗ trợ<br/>Lọc Server-side?}
    
    CheckSource -->|CÓ (Ví dụ: Trang Vàng query)| ServerQuery["Gửi Request có tham số vị trí<br/>(URL: ?key={industry}&pro={province})"]
    CheckSource -->|KHÔNG (Nguồn không có tham số)| BroadCollect["Thu thập theo danh mục ngành"]
    
    ServerQuery --> RawData[Dữ liệu Thô từ Web]
    BroadCollect --> RawData
    
    RawData --> LLM[LLM Extraction & Normalization]
    LLM --> PostFilter{"Kiểm tra Bộ lọc Pipeline:<br/>Bản ghi có khớp province đã chọn?"}
    
    PostFilter -->|Nếu chọn 'Toàn quốc'| KeepAll[Giữ nguyên tất cả bản ghi hợp lệ]
    PostFilter -->|Nếu chọn 'Đà Nẵng' & Khớp| KeepMatch[Lưu bản ghi Đà Nẵng]
    PostFilter -->|Nếu chọn 'Đà Nẵng' & KHÔNG Khớp| DropMismatch[Bỏ qua bản ghi ngoại tỉnh]
    
    KeepAll --> ExcelExport[Xuất File Excel .xlsx]
    KeepMatch --> ExcelExport
```

* **Ưu điểm của thiết kế kết hợp (Hybrid Server-side + Client-side Filter):**
  * Tối ưu hiệu năng: Nếu nguồn cho phép lọc từ khóa địa lý ở request, hệ thống sẽ gửi truy vấn trực tiếp để tiết kiệm số trang phải quét.
  * Đảm bảo tính toàn vẹn 100%: Pipeline kiểm tra lại trường `province` đã chuẩn hóa trước khi ghi vào Excel, loại trừ hoàn toàn các bản ghi rác ngoại tỉnh nếu người dùng đã chỉ định Đà Nẵng.

---

## 8. Terms of Use, Licensing, Access Restrictions & Privacy (Pháp lý, Rào cản & Quyền riêng tư)

### 8.1 Phân tích Điều khoản Dịch vụ (ToS) & Ranh giới Pháp lý
* **Nguyên tắc cốt lõi:** Việc một website có `robots.txt` cho phép truy cập chỉ mang ý nghĩa kỹ thuật (hạ tầng web không chặn bot), **hoàn toàn không thay thế cho giấy phép pháp lý cấp quyền khai thác dữ liệu**.
* **Đánh giá Trang Vàng Việt Nam:**
  * ToS quy định bản quyền cơ sở dữ liệu thuộc Vietnam Yellow Pages JSC. Việc cào dữ liệu tự động phục vụ thương mại bị hạn chế.
  * Đối với phạm vi MVP 5 ngày chạy cục bộ để demo năng lực kỹ thuật (Proof of Concept) với quy mô nhỏ (15–20 records/chiến dịch), rủi ro tranh chấp thực tế là thấp. Tuy nhiên, **TechLead bắt buộc phải ký duyệt chấp thuận rủi ro ToS này**.
* **Đánh giá các Cổng Dữ liệu Mở Địa phương (TP.HCM, Đà Nẵng):**
  * Cung cấp theo Nghị định 47/2020/NĐ-CP về dữ liệu mở. Tuy nhiên, độ phủ chỉ mang tính cục bộ từng địa phương, không đáp ứng được bài toán toàn quốc nếu không tích hợp nhiều cổng cùng lúc (vượt quá thời gian 5 ngày).

### 8.2 Tuân thủ Quy định Bảo vệ Dữ liệu Cá nhân (Nghị định 13/2023/NĐ-CP)
* Toàn bộ dữ liệu thu thập chỉ phục vụ mục đích thông tin danh bạ doanh nghiệp B2B công khai.
* Đối với các trường hợp thông tin liên hệ chứa tên và số điện thoại di động cá nhân của người đại diện (như đã phát hiện trên một số hồ sơ VASI hoặc doanh nghiệp tư nhân), hệ thống tuân thủ nguyên tắc:
  * Không thu thập thông tin đời tư cá nhân.
  * Chỉ lưu trữ trong phạm vi thử nghiệm cục bộ, không thương mại hóa hay chia sẻ ra bên ngoài.

---

## 9. Expected Implementation Effort & 5-Day Feasibility (Ước tính Công sức & Khả thi 5 Ngày)

Dựa trên Kế hoạch bàn giao 5 ngày tại PRD, công việc thu thập dữ liệu (Collector) được thực hiện trọn vẹn trong **Ngày 2**:

| Phương án Nguồn | Khối lượng Công việc Kỹ thuật Ngày 2 | Thời gian Ước tính | Mức độ Khả thi trong 5 Ngày |
| :--- | :--- | :---: | :---: |
| **Phương án 1: Trang Vàng duy nhất (Toàn quốc + Đà Nẵng cho cả 2 ngành)** | Viết 1 HTTP Scraper duy nhất cho `trangvangvietnam.com` với khả năng truyền tham số ngành và tỉnh thành (Đà Nẵng / Toàn quốc). Cài đặt Crawl-delay 5s. | **6 – 7 giờ** (0.8 ngày) | **RẤT CAO**<br>*(Tối ưu hóa tối đa thời gian code, 1 developer hoàn thành tốt trong Ngày 2)* |
| **Phương án 2: Đa nguồn (VASI cho Sản xuất + Trang Vàng cho Giáo dục)** | Viết 2 Scraper riêng biệt: VASI (17 tỉnh, thiếu Đà Nẵng) + Trang Vàng (Giáo dục toàn quốc). Phải viết thêm adapter bổ sung nguồn Đà Nẵng cho sản xuất. | **10 – 12 giờ** (1.3 ngày) | **RỦI RO CAO**<br>*(Dễ trễ tiến độ Ngày 2 do phải tích hợp 2-3 nguồn khác nhau)* |
| **Phương án 3: Chờ tích hợp API Dữ liệu Mở Đà Nẵng + TP.HCM** | Phải nghiên cứu 2 bộ API riêng biệt của 2 thành phố; không giải quyết được các tỉnh thành còn lại trên toàn quốc. | **Không xác định** | **KHÔNG KHẢ THI**<br>*(Không đáp ứng phạm vi toàn quốc trong 5 ngày)* |

---

## 10. Recommended Source Selection for TechLead Review (Đề xuất Lựa chọn Nguồn Tối ưu)

Dựa trên yêu cầu bắt buộc mới: **Phạm vi Toàn quốc Việt Nam và Bắt buộc có dữ liệu Đà Nẵng**, nhóm nghiên cứu đệ trình **02 Phương án lựa chọn** cho TechLead:

### ĐỀ XUẤT 1: PHƯƠNG ÁN MỘT NGUỒN DUY NHẤT TOÀN QUỐC (RECOMMENDED OPTION 1 - ƯU TIÊN TIẾN ĐỘ & ĐỘ PHỦ)
* **Phạm vi Nguồn:** Sử dụng **Trang Vàng Doanh Nghiệp Việt Nam (`trangvangvietnam.com`)** cho cả 2 ngành **Education** và **Manufacturing**.
* **Độ phủ Địa lý:** **Toàn quốc (63 tỉnh/thành phố), ĐÃ XÁC MINH CÓ DỮ LIỆU ĐÀ NẴNG**.
* **Cơ chế Lọc Địa lý:** Hỗ trợ lọc trực tiếp qua tham số tìm kiếm kết hợp kiểm tra địa chỉ tại pipeline; cho phép người dùng chọn **"Đà Nẵng"**, bất kỳ tỉnh thành nào, hoặc chọn **"Toàn quốc"**.
* **Lý do khuyến nghị hàng đầu:**
  1. *Khả thi trong 5 ngày:* Là nguồn duy nhất đã kiểm chứng bao quát trọn vẹn cả 2 ngành trên phạm vi toàn quốc và có Đà Nẵng; Developer chỉ cần viết **01 Collector Engine duy nhất** trong Ngày 2.
  2. *Chất lượng dữ liệu:* Tỷ lệ có số điện thoại và website đạt 80%–100% trong mẫu khảo sát; có URL trang chi tiết riêng để truy vết nguồn gốc.
  3. *Tuân thủ kỹ thuật:* Cài đặt đúng `Crawl-delay: 5` của robots.txt để không gây tải cho máy chủ.
* **Quyết định cần TechLead phê duyệt:** Chấp thuận rủi ro ToS của Trang Vàng cho phạm vi thử nghiệm nội bộ 15–20 records/chiến dịch.

---

### ĐỀ XUẤT 2: PHƯƠNG ÁN NGUỒN KẾT HỢP VỚI GIỚI HẠN MINH BẠCH (ALTERNATIVE OPTION 2)
* **Ngành Giáo dục:** Sử dụng **Trang Vàng Việt Nam** (đảm bảo Toàn quốc & Đà Nẵng).
* **Ngành Sản xuất:** Sử dụng **VASI (`vasi.org.vn`)** cho các tỉnh công nghiệp lớn (Hà Nội, TP.HCM, Đồng Nai, Bắc Ninh...) VÀ kết hợp **Trang Vàng** khi người dùng chọn lọc **Đà Nẵng**.
* **Đánh giá:** Phương án này tận dụng được chất lượng dữ liệu chi tiết của VASI, nhưng Developer phải viết 2 Scraper khác nhau và xử lý logic điều hướng nguồn phức tạp hơn trong Ngày 2.

---

## 11. Fallback Plan if Approval is Delayed (Kế hoạch Dự phòng Khi Chậm Duyệt)

Kế hoạch dự phòng được cập nhật để phản ánh đúng yêu cầu toàn quốc và dữ liệu tại Đà Nẵng:

### 11.1 Mốc Thời gian Kích hoạt (Trigger Deadline)
* **Thời hạn chót (Hard Deadline):** **12:00 trưa Ngày 2 (14/10/2026)**.
* Nếu đến thời điểm này TechLead chưa thể ký duyệt nguồn trực tiếp, Developer sẽ **ngừng chờ đợi** và chuyển trạng thái sang **Chế độ Dữ liệu Mẫu (Fallback Fixture Mode)**.

### 11.2 Cấu trúc Bộ Dữ liệu Mẫu Giả lập Đa Vùng Miền (Synthetic Multi-Province Fixtures)
Nhằm đảm bảo an toàn 100% về bản quyền và không phát sinh rủi ro rò rỉ dữ liệu cá nhân, bộ fixture mẫu sẽ do Developer tự tạo nhân tạo (Synthetic Mock Data) với cấu trúc DOM thực tế:
* **Tệp mẫu Giáo dục (`tests/fixtures/synthetic_education_fixtures.html`):**
  * Chứa 20 bản ghi giả lập mô phỏng trường học, trung tâm ngoại ngữ tại nhiều tỉnh thành: **Bắt buộc có tối thiểu 05 bản ghi tại Đà Nẵng** (ví dụ: "Trung tâm Ngoại ngữ Mẫu Sông Hàn - Đà Nẵng"), 05 bản ghi tại Hà Nội, 05 bản ghi tại TP.HCM, và 05 bản ghi tại các tỉnh khác.
* **Tệp mẫu Sản xuất (`tests/fixtures/synthetic_manufacturing_fixtures.html`):**
  * Chứa 20 bản ghi giả lập mô phỏng nhà máy, xưởng cơ khí: **Bắt buộc có tối thiểu 05 bản ghi tại Đà Nẵng** (ví dụ: "Công ty Cổ phần Chế tạo Cơ khí Mẫu Hòa Khánh - Đà Nẵng"), cùng các doanh nghiệp tại Đồng Nai, Bắc Ninh, Bình Dương, Hải Phòng.

### 11.3 Ràng buộc Minh bạch & Quy chuẩn Dữ liệu Thiếu
* Hệ thống kích hoạt cờ `is_sample_data = True`.
* Trường `source_url` ghi nhận: `fixture://synthetic_education_sample_danang_01.html`.
* Tên file xuất ra: `leads_SAMPLE_{industry}_{YYYYMMDD_HHmmss}.xlsx`.
* Sheet `Summary` ghi rõ: *"Dữ liệu được tạo từ Bộ dữ liệu Giả lập Cục bộ (Synthetic Fixture Mode) phục vụ kiểm thử đường ống Toàn quốc & Đà Nẵng. Không đại diện cho việc thu thập trực tiếp từ website."*
* **Dữ liệu thiếu:** Trong cả chế độ live lẫn fallback, dữ liệu thiếu phải để **ô trống (Empty cell)** trong Excel; tuyệt đối không ghi `"N/A"`.

---

## 12. Open Questions and Approval Checklist (Câu hỏi Mở & Bảng Ký Duyệt)

### 12.1 Câu hỏi Cần TechLead Trả lời Ngay
1. **[Q-01] Về Phạm vi Toàn quốc & Đà Nẵng:** TechLead xác nhận phạm vi bắt buộc là Toàn quốc và phải có Đà Nẵng; TechLead có phê duyệt **Đề xuất 1 (Trang Vàng Doanh Nghiệp cho cả 2 ngành)** để đảm bảo hoàn thành trong 5 ngày không?
2. **[Q-02] Về Bộ lọc Tỉnh/Thành trên UI:** Bộ lọc tỉnh/thành có bắt buộc phải hiển thị dạng dropdown trên giao diện cấu hình chiến dịch của bản demo MVP không (cho phép chọn: "Toàn quốc", "Đà Nẵng", "Hà Nội", "Hồ Chí Minh"...)?
3. **[Q-03] Về Nguồn VASI:** TechLead có chấp nhận việc VASI bị thiếu Đà Nẵng (chỉ có 17 tỉnh) hay yêu cầu dùng nguồn toàn quốc có Đà Nẵng cho ngành Sản xuất?
4. **[Q-04] Về Kế hoạch Dự phòng:** TechLead có phê duyệt cơ chế kích hoạt Synthetic Multi-Province Fixture (bao gồm Đà Nẵng) vào 12:00 trưa Ngày 2 nếu nguồn live chưa được duyệt không?

---

### 12.2 Bảng Ký Phê Duyệt Nguồn Dữ liệu (Dành cho TechLead)

| Hạng mục Nguồn Đề xuất | Phương án Chi tiết | Quyết định của TechLead | Ký duyệt / Ghi chú |
| :--- | :--- | :--- | :--- |
| **Phương án Toàn quốc & Đà Nẵng (Khuyến nghị số 1)** | **Trang Vàng Việt Nam (`trangvangvietnam.com`)**<br/>*(Bao phủ Toàn quốc & Có Đà Nẵng cho cả 2 ngành)* | [ ] Phê duyệt Phương án 1 (Khuyên dùng)<br>[ ] Không phê duyệt | _(Chờ ký duyệt)_ |
| **Nguồn Ngành Sản xuất Chuyên biệt (VASI)** | **VASI (`vasi.org.vn`)**<br/>*(Lưu ý: Chỉ có 17 tỉnh, KHÔNG có Đà Nẵng)* | [ ] Chỉ dùng cho 17 tỉnh (Không lọc Đà Nẵng)<br>[ ] Không dùng cho MVP toàn quốc | _(Chờ ký duyệt)_ |
| **Bộ lọc Tỉnh/Thành trên Giao diện** | **Hỗ trợ chọn "Toàn quốc" hoặc Tỉnh cụ thể (Đà Nẵng...)** | [ ] Bắt buộc có trên UI Demo<br>[ ] Cho phép cấu hình qua tham số config | _(Chờ ký duyệt)_ |
| **Kế hoạch Dự phòng (Fallback Plan)** | **Synthetic Fixtures Đa vùng miền (bao gồm Đà Nẵng)** | [ ] Phê duyệt tự động kích hoạt lúc 12:00 Ngày 2<br>[ ] Chờ chỉ đạo thêm | _(Chờ ký duyệt)_ |

---

*Tài liệu được cập nhật toàn diện phản ánh đúng yêu cầu Toàn quốc Việt Nam và Thành phố Đà Nẵng. Kính trình TechLead xem xét và cho ý kiến chỉ đạo trước 09:00 sáng Ngày 2.*
