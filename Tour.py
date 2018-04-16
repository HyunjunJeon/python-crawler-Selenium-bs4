# 상품 정보를 담는 클래스
class TourInfo:
    # 멤버변수 (실제 컬럼보다는 작게 셋팅됌 - 연습용이라서)
    title = ''
    price = ''
    area = ''
    link = ''
    img = ''
    # 생성자
    def __init__(self,title,price,area,link,img):
        self.title = title
        self.price = price
        self.area = area
        self.link = link
        self.img = img
