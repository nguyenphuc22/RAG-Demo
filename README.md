# RAG Chatbot with VnExpress Articles

Dự án này triển khai chatbot Retrieval-Augmented Generation (RAG) sử dụng Streamlit, MongoDB và mô hình AI Gemini của Google. Chatbot thu thập các bài viết từ VnExpress,tuoitre,thanhnien,phapluat... và sử dụng chúng để trả lời các truy vấn của người dùng.
## Prerequisites

- Python 3.7+
- MongoDB
- Gemini API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/rag-chatbot.git
   cd rag-chatbot
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. MongoDB Connection:
   - mongodb+srv://phuc:pBWtKzGm3jHnMxsr@cluster0.llq9qnt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   - Viên và chị Nhi dùng collection này nhé: `collection_name` = `vien_articles`
   - Khang và Minh dùng collection này nhé: `collection_name` = `minh_articles`
2. Gemini API Key:
   - Get Key free đi nhé mọi người :D : https://aistudio.google.com/app/apikey

## Running the Application

1. Khởi động ứng dụng Streamlit:
   ```
   streamlit run ChatBot.py
   ```

2. Ứng dụng sẽ mở trong trình duyệt web mặc định của bạn. Nếu không, hãy điều hướng đến URL hiển thị trong terminal (thường là `http://localhost:8501`).

3. Trong thanh bên:
   - Nhập khóa API Gemini của bạn
   - Nhập chuỗi kết nối MongoDB của bạn
   - Chọn trình thu thập tin tức mong muốn (ví dụ: VnExpress, Tuổi Trẻ, v.v.)
   - Đặt số lượng bài viết tối đa để thu thập

4. Nhấp vào nút "Crawl New Articles" để tìm và xử lý bài viết mới. (Không crawl cũng được, thường dữ liệu cũ sẽ được lưu trên db)

5. Sau khi quá trình thu thập dữ liệu hoàn tất, bạn có thể bắt đầu trò chuyện với bot trong giao diện trò chuyện chính.

## Planing

### Triển khai các crawler thu thập dữ liệu từ các trang báo lớn như VnExpress, Tuổi Trẻ, Thanh Niên, Pháp Luật, v.v.
- [x] Crawler VnExpress
- [ ] Crawler Tuổi Trẻ (Viên)
- [ ] Crawler Thanh Niên (Viên)
- [ ] Crawler Pháp Luật (Viên)
- [ ] Crawler Dân Trí (Khang)
- [ ] Crawler Thư Viện Pháp Luật (Khang)
- [ ] Crawler Báo Mới (Khang)

### Trả lời các câu hỏi thường gặp của người dùng (FAQ). (Phuc)
### Hỗ trợ người dùng tìm kiếm thông tin trên website. (Phuc)
### Thu thập và lưu trữ phản hồi của người dùng để cải thiện dịch vụ. (Phuc)
### Có khả năng học hỏi và cải thiện qua thời gian bằng cách sử dụng dữ liệu tương tác của người dùng. (Phuc)

---
Từ phần này trở đi em chưa biết mọi người sẽ làm gì nên chưa dựng teamplate. Có gì mọi người nghiên cứu thi xong Triết báo lại nhé.
### Có tích hợp tính năng gợi ý câu hỏi để hướng dẫn người dùng. (Minh)

### Nguồn Dữ liệu huấn luyện: (Minh và Nhi phần này focus nhiều hên 2 người thảo luận nhé)
- Sinh viên cần xác định các nguồn dữ liệu sẽ được sử dụng để huấn luyện mô hình, bao gồm các dataset công khai hoặc thông qua các API có sẵn để khai thác các
trang web đã được yêu cầu.

### Nguồn Dữ liệu kiểm thử: (Minh và Nhi)
- Sinh viên cần xây dựng tập đánh giá hoặc quy trình đánh giá để thể hiện chất lượng hệ thống đã xây dựng. Điểm cộng dành cho các nhóm đề xuất quy trình tạo ra tập kiểm thử tự động hoặc bán tự động với ít sự can thiệp thủ công nhất có thể. Thông tin về quá trình này cần được trình bày chi tiết để có thể đạt phần điểm cộng này.
### Mô hình cơ sở: (Minh và Nhi)
- Sinh viên cần xây dựng giải pháp cơ sở nhằm làm căn cứ đánh giá sơ bộ về kết quả đạt được.
### Mô hình đề xuất: (Minh và Nhi)
- Dựa trên mô hình cơ sở đã xây dựng, nhóm sinh viên được yêu cầu phân tích các kết quả đầu ra trên tập kiểm thử và đề xuất các giải pháp cải tiến hệ thống.45