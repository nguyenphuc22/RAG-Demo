import pandas as pd
from database.NewsCrawlerInterface import NewsCrawlerInterface

class ThanhNienExcelCrawler(NewsCrawlerInterface):
    def __init__(self, base_url='https://thanhnien.vn/'):
        self.base_url = base_url
        self.articles = [
            {
                'title': 'Giá xăng dầu hôm nay 25.8.2023: Trong nước và thế giới cùng tăng',
                'url': 'https://thanhnien.vn/gia-xang-dau-hom-nay-25-8-2023-trong-nuoc-va-the-gioi-cung-tang-185230825065742087.htm',
                'description': 'Giá xăng dầu hôm nay 25.8.2023 trên thị trường thế giới tiếp tục đà tăng từ 2 phiên gần nhất. Trong nước, giá xăng dầu được điều chỉnh tăng từ chiều qua.',
                'content': 'Giá xăng dầu hôm nay 25.8.2023 trên thị trường thế giới ghi nhận lúc 6 giờ 30 phút (giờ Việt Nam), cụ thể như sau: Giá dầu thô WTI đứng ở mức 79,41 USD/thùng, tăng 0,36 USD/thùng tương đương 0,45% so với phiên giao dịch trước đó. Giá dầu Brent ở mức 83,52 USD/thùng, tăng 0,16 USD/thùng tương đương 0,19% so với phiên liền kề.',
                'date': '25/08/2023'
            },
            {
                'title': 'Thủ tướng yêu cầu bảo đảm cung ứng điện những tháng còn lại của năm 2023',
                'url': 'https://thanhnien.vn/thu-tuong-yeu-cau-bao-dam-cung-ung-dien-nhung-thang-con-lai-cua-nam-2023-185230824221943714.htm',
                'description': 'Thủ tướng Phạm Minh Chính vừa ký công điện yêu cầu các bộ, ngành, địa phương tiếp tục thực hiện quyết liệt các giải pháp bảo đảm cung ứng điện cho sản xuất, kinh doanh và sinh hoạt của nhân dân những tháng còn lại của năm 2023 và các năm tiếp theo.',
                'content': 'Ngày 24.8, Thủ tướng Phạm Minh Chính ký công điện số 777/CĐ-TTg yêu cầu các bộ, ngành, địa phương tiếp tục thực hiện quyết liệt các giải pháp bảo đảm cung ứng điện cho sản xuất, kinh doanh và sinh hoạt của nhân dân những tháng còn lại của năm 2023 và các năm tiếp theo.',
                'date': '24/08/2023'
            },
            {
                'title': 'Hà Nội sẽ xây cầu Tứ Liên nối quận Tây Hồ và huyện Đông Anh',
                'url': 'https://thanhnien.vn/ha-noi-se-xay-cau-tu-lien-noi-quan-tay-ho-va-huyen-dong-anh-185230824194555166.htm',
                'description': 'UBND TP.Hà Nội vừa có văn bản chấp thuận chủ trương đầu tư dự án xây dựng cầu Tứ Liên nối quận Tây Hồ và huyện Đông Anh.',
                'content': 'Ngày 24.8, UBND TP.Hà Nội có văn bản chấp thuận chủ trương đầu tư dự án xây dựng cầu Tứ Liên nối quận Tây Hồ và huyện Đông Anh. Theo đó, cầu Tứ Liên sẽ được xây dựng với tổng mức đầu tư khoảng 8.700 tỉ đồng từ ngân sách thành phố.',
                'date': '24/08/2023'
            }
        ]

    def crawl(self, max_articles: int) -> None:
        # Đã có dữ liệu mẫu, không cần crawl thực tế
        pass

    def save_to_excel(self, filename: str = 'thanhnien_articles.xlsx') -> pd.DataFrame:
        df = pd.DataFrame(self.articles)
        df.to_excel(filename, index=False)
        print(f"Saved {len(self.articles)} articles to {filename}")
        return df

    def get_articles(self) -> list[dict]:
        return self.articles