"""
간단한 Playwright 테스트 스크립트
네이버 지도 크롤링 문제 디버깅용
"""

import asyncio
from playwright.async_api import async_playwright


async def test_simple_crawler():
    """간단한 크롤링 테스트"""
    try:
        print("🚀 Playwright 테스트 시작...")
        
        # Playwright 시작
        playwright = await async_playwright().start()
        print("✅ Playwright 시작 완료")
        
        # 브라우저 실행
        browser = await playwright.chromium.launch(headless=False)
        print("✅ 브라우저 실행 완료")
        
        # 컨텍스트 생성
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        print("✅ 컨텍스트 생성 완료")
        
        # 페이지 생성
        page = await context.new_page()
        print("✅ 페이지 생성 완료")
        
        # 간단한 사이트로 테스트
        print("🌐 구글 페이지로 이동 중...")
        await page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=30000)
        print("✅ 구글 페이지 로드 완료")
        
        # 네이버 지도로 이동 테스트
        print("🗺️ 네이버 지도로 이동 중...")
        search_url = "https://map.naver.com/v5/search/강남 맛집"
        response = await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        print(f"✅ 네이버 지도 로드 완료. Status: {response.status}")
        
        # 5초 대기
        await asyncio.sleep(5)
        
        # 페이지 제목 확인
        title = await page.title()
        print(f"📄 페이지 제목: {title}")
        
        # 몇 가지 선택자 테스트
        selectors_to_test = [
            '.place_bluelink',
            '.CHC5F',
            '[data-id]',
            '.PlaceItem',
            '.search_item'
        ]
        
        for selector in selectors_to_test:
            try:
                elements = await page.query_selector_all(selector)
                print(f"🔍 선택자 '{selector}': {len(elements)}개 요소 발견")
            except Exception as e:
                print(f"❌ 선택자 '{selector}' 오류: {str(e)}")
        
        # 스크린샷 저장
        await page.screenshot(path='output/naver_map_test.png')
        print("📸 스크린샷 저장 완료: output/naver_map_test.png")
        
        # 브라우저 종료
        await browser.close()
        await playwright.stop()
        print("✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_crawler()) 