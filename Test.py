from underthesea import word_tokenize

from search.vector_search import preprocess_text

print(preprocess_text("Trước khi chuyển thành vector, các đoạn văn sẽ được tiền xử lý bằng cách tokenize và loại bỏ các từ không mang nhiều ngữ nghĩa. Điều này giúp việc truy vấn sau này tập trung vào ngữ nghĩa của đoạn văn hơn và thực hiện nhanh hơn."))