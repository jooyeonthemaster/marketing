"""
네이버 지도 크롤링 메인 클래스
2024-2025년 최신 안티 탐지 기법을 적용한 네이버 플레이스 순위 크롤러
Playwright 기반으로 개선된 크롤링
"""

import asyncio
import logging
import time
import random
import json
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import sys
import os
from urllib.parse import quote
# from .stealth_utils import setup_stealth_page

# 상위 디렉토리의 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import (
    BROWSER_SETTINGS, NAVER_MAP, CRAWLING_SETTINGS, 
    STEALTH_SETTINGS
)
from src.crawler.stealth_utils import StealthUtils


class NaverMapCrawler:
    """네이버 지도 크롤러 (iframe 방식)"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None 
        self.page: Optional[Page] = None
        self.playwright = None
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger('NaverMapCrawler')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def init_browser(self):
        """브라우저 초기화 (환경에 따라 headless 모드 자동 설정)"""
        try:
            # 환경 감지: Railway/production 환경에서는 headless=True
            is_production = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT")
            headless_mode = True if is_production else False
            
            self.logger.info(f"환경 감지: {'Production (headless)' if is_production else 'Development (GUI)'}")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=headless_mode,  # 환경에 따라 자동 설정
                slow_mo=1000 if not is_production else 0,   # production에서는 빠르게
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=TranslateUI',
                    '--disable-extensions',
                    # Production 환경 추가 설정
                    '--single-process',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
            
            # 컨텍스트 생성
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 페이지 생성
            self.page = await self.context.new_page()
            
            self.logger.info("브라우저 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"브라우저 초기화 실패: {str(e)}")
            raise
    
    def extract_business_name(self, raw_text: str) -> str:
        """원시 텍스트에서 업체명만 추출"""
        if not raw_text:
            return ""
        
        # 일반적인 구분 키워드들
        keywords = [
            "예약", "광고", "영업", "리뷰", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
            "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
            "네이버페이", "톡톡", "별점", "현재", "위치", "거리", "출발", "도착", "상세주소", "저장", "더보기"
        ]
        
        # 키워드 중 가장 먼저 나오는 위치 찾기
        first_keyword_pos = len(raw_text)
        for keyword in keywords:
            pos = raw_text.find(keyword)
            if pos != -1 and pos < first_keyword_pos:
                first_keyword_pos = pos
        
        # 업체명 추출 (키워드 전까지, 최대 30자)
        name = raw_text[:first_keyword_pos].strip()
        if len(name) > 30:
            name = name[:30] + "..."
            
        return name if name else raw_text[:20] + "..." if len(raw_text) > 20 else raw_text
        
    async def search_places(self, query: str, max_results: int = 10) -> List[Dict]:
        """네이버 지도에서 장소 검색"""
        if not self.browser:
            await self.init_browser()
            
        results = []
        
        try:
            print("네이버 지도 접속 중...")
            await self.page.goto("https://map.naver.com/p?c=15.00,0,0,0,dh", wait_until='domcontentloaded', timeout=30000)
            print("✓ 페이지 로드 완료: https://map.naver.com/p?c=15.00,0,0,0,dh")
            
            # 검색창 찾기
            print("검색창 찾는 중...")
            search_input = await self.page.wait_for_selector(".input_search", timeout=10000)
            print("✓ 검색창 발견!")
            
            # 검색 실행
            await search_input.fill(query)
            await self.page.keyboard.press("Enter")
            print("✓ 검색 실행")
            
            # searchIframe 로드 대기 및 안정적인 접근
            print("searchIframe 로드 대기 중...")
            
            # iframe이 완전히 로드될 때까지 더 오래 기다리기
            try:
                # iframe 요소가 나타날 때까지 대기
                await self.page.wait_for_selector("#searchIframe", timeout=15000)
                print("✓ searchIframe 요소 발견!")
                
                # iframe이 완전히 로드될 때까지 추가 대기
                await asyncio.sleep(3)
                
                # iframe 로드 상태 확인
                iframe_element = await self.page.query_selector("#searchIframe")
                if iframe_element:
                    # iframe의 src 속성 확인
                    src = await iframe_element.get_attribute("src")
                    print(f"iframe src: {src}")
                    
                    # iframe이 완전히 로드될 때까지 대기
                    await iframe_element.wait_for_element_state("visible")
                    
            except Exception as e:
                print(f"❌ searchIframe 로드 실패: {e}")
                return []
            
            # iframe으로 전환 - 여러 방법 시도
            search_frame = None
            
            # 방법 1: name으로 접근
            try:
                search_frame = self.page.frame(name="searchIframe")
                if search_frame:
                    print("✓ 방법1(name) - searchIframe 접근 성공!")
            except Exception as e:
                print(f"방법1(name) 실패: {e}")
            
            # 방법 2: url로 접근
            if not search_frame:
                try:
                    frames = self.page.frames
                    for frame in frames:
                        frame_url = frame.url
                        if "search" in frame_url.lower() or "place" in frame_url.lower():
                            search_frame = frame
                            print(f"✓ 방법2(url) - searchIframe 접근 성공! URL: {frame_url}")
                            break
                except Exception as e:
                    print(f"방법2(url) 실패: {e}")
            
            # 방법 3: 선택자로 접근
            if not search_frame:
                try:
                    iframe_element = await self.page.query_selector("#searchIframe")
                    if iframe_element:
                        search_frame = await iframe_element.content_frame()
                        if search_frame:
                            print("✓ 방법3(selector) - searchIframe 접근 성공!")
                except Exception as e:
                    print(f"방법3(selector) 실패: {e}")
            
            if not search_frame:
                print("❌ 모든 방법으로 searchIframe 프레임 접근 실패")
                # 디버깅을 위해 현재 프레임들 확인
                frames = self.page.frames
                print(f"현재 페이지의 프레임 개수: {len(frames)}")
                for i, frame in enumerate(frames):
                    print(f"  프레임 {i}: name='{frame.name}', url='{frame.url}'")
                return []
            
            print("✓ searchIframe으로 전환 성공!")
            
            # 검색 결과 로드 대기 및 선택자 시도
            print("검색 결과 로드 대기 중...")
            
            # 더 오래 기다려서 모든 결과가 로드되도록 함
            await asyncio.sleep(5)
            
            # DOM 구조 분석을 위한 디버깅 추가
            print("🔍 iframe 내부 DOM 구조 분석 중...")
            try:
                # iframe 내의 모든 HTML을 가져와서 분석
                html_content = await search_frame.content()
                print(f"HTML 길이: {len(html_content)} 문자")
                
                # HTML을 파일로 저장해서 분석
                import os
                debug_dir = "debug_html"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                
                with open(f"{debug_dir}/naver_map_iframe.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"✓ HTML 저장됨: {debug_dir}/naver_map_iframe.html")
                
                # 더 많은 선택자들로 테스트
                debug_selectors = [
                    "li", "ul li", "ol li", "div", "span", "a",
                    "._3XamX", ".TYaxT", ".CHC5F", ".YwYLL", 
                    "[data-id]", "[data-place-id]", "[data-sid]",
                    ".place_bluelink", ".item_name", ".item", ".result",
                    ".search_item", ".list_item", ".place_item",
                    "[role='listitem']", "[class*='item']", "[class*='place']",
                    "[class*='search']", "[class*='result']"
                ]
                
                for debug_selector in debug_selectors:
                    try:
                        debug_elements = await search_frame.query_selector_all(debug_selector)
                        count = len(debug_elements)
                        if count > 0:
                            print(f"   선택자 '{debug_selector}': {count}개")
                            # 3개보다 많은 결과가 있으면 첫 번째 요소의 클래스 확인
                            if count > 3:
                                try:
                                    first_element = debug_elements[0]
                                    classes = await first_element.get_attribute("class")
                                    data_attrs = {}
                                    for attr in ["data-id", "data-place-id", "data-sid"]:
                                        val = await first_element.get_attribute(attr)
                                        if val:
                                            data_attrs[attr] = val
                                    print(f"      → 첫 번째 요소 클래스: {classes}")
                                    if data_attrs:
                                        print(f"      → 데이터 속성: {data_attrs}")
                                except:
                                    pass
                    except:
                        pass
                        
            except Exception as e:
                print(f"DOM 분석 실패: {e}")
            
            # 여러 선택자를 순서대로 시도 
            selectors = [
                "ul li", "li", ".YwYLL", "._3XamX", ".TYaxT", ".CHC5F", 
                "[data-id]", "div[data-place-id]", ".place_bluelink", 
                ".item_name", ".item", ".result"
            ]
            places = []
            used_selector = None
            
            for selector in selectors:
                try:
                    await search_frame.wait_for_selector(selector, timeout=3000)
                    places = await search_frame.query_selector_all(selector)
                    if places and len(places) > 3:  # 3개보다 많은 결과를 가진 선택자를 우선
                        used_selector = selector
                        print(f"✓ 선택자 '{selector}' 발견! ({len(places)}개)")
                        break
                    elif places and len(places) > 0:
                        if not used_selector:  # 백업용으로 저장
                            used_selector = selector
                            print(f"⚠ 선택자 '{selector}' 발견 (백업용: {len(places)}개)")
                except:
                    print(f"   선택자 '{selector}' 시도 실패")
                    continue
            
            if not places:
                print("❌ 검색 결과를 찾을 수 없음")
                return []
            
            print(f"✓ 검색 결과 {len(places)}개 발견! (선택자: {used_selector})")
            
            # 더 많은 결과가 필요한 경우 스크롤을 통해 추가 로드
            if len(places) < max_results:
                print(f"더 많은 결과 로드 중... (현재: {len(places)}개, 목표: {max_results}개)")
                
                # 스크롤을 통해 더 많은 결과 로드 시도
                for scroll_attempt in range(5):  # 최대 5번 스크롤 시도
                    try:
                        # 검색 결과 영역에서 스크롤
                        await search_frame.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)  # 로딩 대기
                        
                        # 새로운 결과 확인
                        new_places = await search_frame.query_selector_all(used_selector)
                        print(f"   스크롤 {scroll_attempt + 1}회 후: {len(new_places)}개")
                        
                        if len(new_places) >= max_results:
                            places = new_places
                            print(f"✓ 목표 개수 달성: {len(places)}개")
                            break
                        elif len(new_places) == len(places):
                            print(f"   더 이상 새로운 결과가 없습니다.")
                            break
                        else:
                            places = new_places
                            
                    except Exception as e:
                        print(f"   스크롤 {scroll_attempt + 1}회 실패: {e}")
                        break
            
            print(f"최종 검색 결과: {len(places)}개")
            
            # 결과 수집
            for i, place in enumerate(places[:max_results]):
                try:
                    # 전체 텍스트 가져오기
                    raw_text = await place.text_content()
                    if not raw_text or raw_text.strip() == "":
                        continue
                    
                    # 업체명 파싱
                    business_name = self.extract_business_name(raw_text.strip())
                    
                    # 결과 구성
                    result = {
                        'rank': i + 1,
                        'name': business_name,
                        'raw_text': raw_text.strip()
                    }
                    
                    results.append(result)
                    print(f"{i+1}. {business_name}")
                    
                except Exception as e:
                    print(f"❌ {i+1}번째 장소 처리 실패: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ 크롤링 오류: {e}")
        
        finally:
            print("브라우저 종료...")
            await self.close()
            
        return results
    
    async def close(self):
        """리소스 정리"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"종료 중 오류: {e}")


# 전역 함수로 간단한 인터페이스 제공
async def crawl_naver_map(query: str, max_results: int = 10) -> List[Dict]:
    """네이버 지도 크롤링 간단 인터페이스"""
    crawler = NaverMapCrawler()
    try:
        return await crawler.search_places(query, max_results)
    except Exception as e:
        print(f"크롤링 실패: {e}")
        return []
    finally:
        await crawler.close() 