"""
네이버 지도 검색 결과 로딩 확인
더 긴 대기 시간을 통한 동적 로딩 분석
"""

import asyncio
from playwright.async_api import async_playwright


async def test_longer_wait():
    """긴 대기 시간으로 네이버 지도 테스트"""
    try:
        print("🚀 긴 대기 시간 테스트 시작...")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # 네이버 지도로 이동
        search_url = "https://map.naver.com/v5/search/강남%20맛집"
        print(f"📍 URL: {search_url}")
        await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        print("✅ 기본 페이지 로드 완료")
        
        # 단계별로 대기하면서 확인
        wait_times = [3, 5, 10, 15, 20]
        
        for wait_time in wait_times:
            print(f"\n⏰ {wait_time}초 대기 후 확인...")
            await asyncio.sleep(wait_time)
            
            # 다양한 선택자로 검색 결과 확인
            search_selectors = [
                # 2024-2025 네이버 지도 새로운 선택자들
                '[class*="searchItem"]',
                '[class*="SearchItem"]',
                '[class*="place"]',
                '[class*="Place"]',
                '[class*="restaurant"]',
                '[class*="Restaurant"]',
                'li[data-id]',
                'div[data-id]',
                'article[data-id]',
                '[role="listitem"]',
                '[class*="item"]',
                '.UEzoS',  # 네이버 지도 새로운 클래스
                '.CHC5F',  # 검색 결과 컨테이너
                '.Rh6cC',  # 리스트 아이템
                '.YzBgS',  # 카테고리
                '.LDgIH',  # 주소
                '.TYaxT',  # 제목/이름
            ]
            
            found_any = False
            for selector in search_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ '{selector}': {len(elements)}개 요소 발견")
                        found_any = True
                        
                        # 첫 번째 요소의 텍스트 확인
                        if len(elements) > 0:
                            try:
                                first_text = await elements[0].inner_text()
                                if first_text and len(first_text.strip()) > 2:
                                    print(f"   📝 첫 번째 요소 텍스트: {first_text.strip()[:50]}...")
                            except:
                                pass
                except Exception as e:
                    continue
            
            if not found_any:
                print("❌ 검색 결과 요소를 찾지 못함")
                
                # 현재 페이지의 body 내용 일부 확인
                try:
                    body_text = await page.locator('body').inner_text()
                    if "맛집" in body_text:
                        print("🔍 페이지에 '맛집' 텍스트는 존재함")
                    else:
                        print("❌ 페이지에 '맛집' 텍스트가 없음")
                except:
                    pass
            
            # 스크롤해서 더 많은 결과 로드 시도
            if wait_time >= 10:
                print("📜 스크롤 시도...")
                await page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(2)
        
        # 마지막에 스크린샷 저장
        await page.screenshot(path='output/naver_map_final.png')
        print("📸 최종 스크린샷 저장: output/naver_map_final.png")
        
        # 페이지 최종 HTML 저장
        final_html = await page.content()
        with open('output/naver_map_final.html', 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("📄 최종 HTML 저장: output/naver_map_final.html")
        
        await browser.close()
        await playwright.stop()
        print("✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_longer_wait()) 