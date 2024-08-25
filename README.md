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