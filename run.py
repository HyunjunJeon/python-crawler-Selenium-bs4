# 인터파크 투어 사이트에서 여행지 입력 후 검색 -> delay -> 결과
# 로그인 시 PC 웹 사이트에서 처리가 어려울 경우 -> 모바일 웹 로그인으로 진입

## 모듈 가져오기
    # pip install selenium 
from selenium import webdriver as wd

from selenium.webdriver.common.by import By
    # 명시적 대기를 위해
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Tour 정보 담을 클래스 호출
from Tour import TourInfo
from bs4 import BeautifulSoup as bs

## 사전에 필요한 정보를 로드 -> DB / Shell / batch 파일에서 인자로 받아서 setting
main_url = 'http://tour.interpark.com/'
SearchKeyword = '로마'
# 상품 정보를 담는 리스트(TourInfo의 리스트)
tour_list = []

## 드라이버 로드
driver = wd.Chrome(executable_path='./utils/chromedriver')
# 옵션 부여하기 (프록시, 에이전트 조작, 이미지 배제)
    # 에이전트 조작 시 PC / 모바일 잘 나눠서 꼭 들어가보고 체크하셈
# 크롤링을 계속하면 -> 임시파일 쌓임 -> temp 비우기

# 사이트 접속(GET Method)
driver.get(main_url)

# 예외처리 : 대기

# 검색창 찾기 id : SearchGNBText // 검색어 입력
driver.find_element_by_id('SearchGNBText').send_keys(SearchKeyword)
    # 수정할 경우 -> send_keys는 뒤에 내용이 붙어버림 -> clear() -> send_keys()

# 검색버튼 클릭
driver.find_element_by_class_name('search-btn').click()
#driver.find_element_by_css_selector('.search-btn')

# 잠시 대기 -> 페이지 로드 후 즉각 데이터 획득 행위 "자제" -> '데이터가 로드 되는데 시간은 천차만별'(평균 10s)
    # 명시적 대기 : 특정 요소가 Located될 때까지 대기
try:
    element = WebDriverWait(driver, 10).until(
        # 지정한 한개 요소가 올라오면 Wait 종료
        EC.presence_of_element_located((By.CLASS_NAME, 'oTravelBox'))
    )
except Exception as e:
    print('오류 발생',e)

    # 묵시적 대기 : DOM이 모두 Ready될 때까지 대기 (먼저 로드되면 바로 실행)
        # 요소를 찾을 특정 시간동안 DOM Pooling을 지시, X초 이내 발견 시 바로 추가코드 진행
    driver.implicitly_wait(10)

    # 절대적 대기 : time.sleep(10) -> CloudFare(DDos 방어 솔루션)
    #time.sleep(10)

# 해외여행 더보기 눌러서 진입 (근데 함수의 특성을 이용해서 가장 처음 나오는 부분을 찾을땐 걍 className으로 해버려)
driver.find_element_by_css_selector('.oTravelBox .boxList .moreBtnWrap .moreBtn').click()

# 게시판에서 데이터를 가져올때 데이터가 많으면 세션이 끊어질 경우 발생 (특히 로그인을 해야 접근 가능한 경우)
    # 특정 단위별로 로그아웃-로그인 계속 시도
    # 특정 게시물이 사라질경우 -> 팝업 발생 (없는 게시글 입니다....) -> 팝업에 대한 예외처리 검토
    # 임계점을 확인할 수 없음

# 게시판 스캔 -> 메타정보 획득 -> Loop화 하여 일괄적으로 접근 후 디테일 내용 획득
# 스크립트 실행 : searchModule.SetCategoryList(2, '')
# 16은 페이징을 넘어갔을 때 예외처리를 위해 확인용.
for page in range(1,2): # 2 -> 16
    try:
        # 자바스크립트 구동하기
        driver.execute_script("searchModule.SetCategoryList(%s, '')" %page)
        print(page,"페이지 이동")
        time.sleep(2)
        ##########################
        # 여러 사이트에서 정보를 수집할 경우, 공통 정보를 정의 (DB Table 때문에)
        # 상품명, 코멘트, 기간1, 기간2, 가격, 평점, 썸네일, 상세정보 링크
        boxItems = driver.find_elements_by_css_selector('.oTravelBox >.boxList >li')
        for li in boxItems:
            #이미지의 링크값을 사용할 것인지, 직접 다운로드해서 우리 서버에 FTP로 업로드 할 것인가?
            print("썸네일:", li.find_element_by_css_selector('img').get_attribute('src'))
            print("상세정보 링크:", li.find_element_by_css_selector('a').get_attribute('onclick'))
            print("상품명:", li.find_element_by_class_name('proTit').text)
            print("코멘트:", li.find_element_by_class_name('proSub').text)
            print("가격:", li.find_element_by_class_name('proPrice').text)
            area = ''
            for info in li.find_elements_by_css_selector('.info-row .proInfo'):
                print(info.text)
            print("="*100)
            # 데이터 모음
            # 데이터가 부족하거나 없을수도 있으므로 직접 인덱스로의 표현은 위험성이 있음
            obj = TourInfo(
                li.find_element_by_class_name('proTit').text,
                li.find_element_by_class_name('proPrice').text,
                li.find_elements_by_css_selector('.info-row .proInfo')[1].text, 
                li.find_element_by_css_selector('a').get_attribute('onclick'),
                li.find_element_by_css_selector('img').get_attribute('src')
            )
            tour_list.append(obj)

    except Exception as e1:
        print("오류",e1)

print(tour_list,len(tour_list))

# 수집한 정보 개수를 루프 -> 페이지 방문 -> 콘텐츠 획득(상품 상세정보) -> DB에 삽입
for tour in tour_list:
    # tour -> TourInfo
    print(type(tour))
    # 링크 데이터에서 실데이터 획득
    # 분해
    arr = tour.link.split(',')
    # 대체
    if arr:
        # 대체
        link = arr[0].replace('searchModule.OnClickDetail(','')
        # 슬라이싱
        detail_url = link[1:-1] # 앞-뒤로 하나씩(') 잘라냄
        # 상세 페이지 이동 : URL 값이 완성된 형태인지 확인해볼 것
        driver.get(detail_url)
        time.sleep(2)

        # 현재 페이지를 BeautifulSoup 의 DOM으로 구성
        soup = bs(driver.page_source,'html.parser')
        # 상세정보 페이지 -> 한눈에 보는 간편일정 획득
        simpleSchedule = soup.select('.schedule-all')
        print(type(simpleSchedule))


# 정돈된 정보를 추출해서 DB에 넣기




# 종료
driver.close()
driver.quit()
import sys
sys.exit()
