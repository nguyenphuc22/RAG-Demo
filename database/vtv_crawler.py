import pandas as pd
from database.NewsCrawlerInterface import NewsCrawlerInterface

class VTVExcelCrawler(NewsCrawlerInterface):
    def __init__(self, base_url='https://vtv.vn/'):
        self.base_url = base_url
        self.articles = [
            {
                'title': 'Giá vàng hôm nay 25-8: Vàng SJC giảm 200.000 đồng/lượng',
                'url': 'https://tuoitre.vn/gia-vang-hom-nay-25-8-vang-sjc-giam-200-000-dong-luong-20230825085817684.htm',
                'description': 'Sáng 25-8, giá vàng SJC giảm 200.000 đồng/lượng so với chốt phiên hôm qua.',
                'content': 'Công ty Vàng bạc Đá quý Sài Gòn niêm yết giá vàng SJC mua vào bán ra là 66,8 triệu - 67,5 triệu đồng/lượng, giảm 200.000 đồng/lượng ở chiều mua vào và giảm 100.000 đồng/lượng ở chiều bán ra so với chốt phiên ngày 24-8.',
                'date': '25/08/2023'
            },
            {
                'title': 'Doanh nghiệp Việt Nam đầu tư vào nước ngoài tăng mạnh',
                'url': 'https://tuoitre.vn/doanh-nghiep-viet-nam-dau-tu-vao-nuoc-ngoai-tang-manh-20230825090532564.htm',
                'description': 'Trong 8 tháng đầu năm 2023, tổng vốn đầu tư của Việt Nam ra nước ngoài đạt gần 400 triệu USD, tăng 2,5 lần so với cùng kỳ năm ngoái.',
                'content': 'Theo số liệu của Cục Đầu tư nước ngoài (Bộ Kế hoạch và Đầu tư), tính đến ngày 20-8, tổng vốn đầu tư của Việt Nam ra nước ngoài (bao gồm vốn cấp mới và tăng thêm) đạt 398,3 triệu USD, tăng 2,5 lần so với cùng kỳ năm 2022.',
                'date': '25/08/2023'
            },
            {
                'title': 'Bão Saola mạnh cấp 13 hướng vào Biển Đông',
                'url': 'https://tuoitre.vn/bao-saola-manh-cap-13-huong-vao-bien-dong-20230825080123056.htm',
                'description': 'Sáng 25-8, bão Saola đang hoạt động ở phía đông Philippines với sức gió mạnh nhất vùng gần tâm bão mạnh cấp 13.',
                'content': 'Theo Trung tâm Dự báo khí tượng thủy văn quốc gia, hồi 7h ngày 25-8, vị trí tâm bão ở khoảng 19,8 độ vĩ bắc; 127,5 độ kinh đông, cách đảo Lu-dông (Philippines) khoảng 470km về phía đông đông bắc. Sức gió mạnh nhất vùng gần tâm bão mạnh cấp 13 (134-149km/giờ), giật cấp 16.',
                'date': '25/08/2023'
            }
        ]

    def crawl(self, max_articles: int) -> None:
        # Nhớ cài đặt lại nhé các bạn
        pass

    def save_to_excel(self, filename: str = 'tuoitre_articles.xlsx') -> pd.DataFrame:
        df = pd.DataFrame(self.articles)
        df.to_excel(filename, index=False)
        print(f"Saved {len(self.articles)} articles to {filename}")
        return df

    def get_articles(self) -> list[dict]:
        return self.articles