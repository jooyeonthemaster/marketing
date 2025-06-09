import asyncio
from playwright.async_api import async_playwright
import time

async def test_iframe_naver_map():
    """
    블로그에서 찾은 iframe 접근 방식을 테스트
    """
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(
            headless=False,  # 실제 브라우저 창 표시
            slow_mo=2000     # 각 동작 사이 2초 지연
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            print("네이버 지도 접속 중...")
            await page.goto("https://map.naver.com/v5/search", wait_until='domcontentloaded')
            print(f"✓ 페이지 로드 완료: {page.url}")
            
            # 검색창 찾기 - 블로그에서 찾은 선택자 사용
            print("검색창 찾는 중...")
            search_input = await page.wait_for_selector(".input_search", timeout=10000)
            if search_input:
                print("✓ 검색창 발견!")
                
                # 검색어 입력
                await search_input.fill("강남 맛집")
                await page.keyboard.press("Enter")
                print("✓ 검색 실행")
                
                # searchIframe 로드 대기
                print("searchIframe 로드 대기 중...")
                await page.wait_for_selector("#searchIframe", timeout=15000)
                print("✓ searchIframe 발견!")
                
                # iframe으로 전환
                search_frame = page.frame(name="searchIframe") or page.frame(url="**/search**")
                if search_frame:
                    print("✓ searchIframe으로 전환 성공!")
                    
                    # 검색 결과 대기 - 블로그에서 찾은 선택자 사용
                    print("검색 결과 로드 대기 중...")
                    await search_frame.wait_for_selector(".TYaxT", timeout=15000)
                    
                    # 검색 결과 수집
                    places = await search_frame.query_selector_all(".TYaxT")
                    print(f"✓ 검색 결과 {len(places)}개 발견!")
                    
                    # 각 검색 결과의 정보 출력
                    for i, place in enumerate(places[:5]):  # 처음 5개만
                        try:
                            text = await place.text_content()
                            print(f"{i+1}. {text.strip()}")
                        except Exception as e:
                            print(f"{i+1}. 텍스트 추출 실패: {e}")
                            
                else:
                    print("❌ searchIframe 전환 실패")
            else:
                print("❌ 검색창을 찾을 수 없음")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            
        finally:
            print("5초 후 브라우저 종료...")
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_iframe_naver_map()) 