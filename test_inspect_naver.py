"""
네이버 지도 HTML 구조 분석 스크립트
실제 선택자를 찾기 위한 디버깅용
"""

import asyncio
from playwright.async_api import async_playwright


async def inspect_naver_map():
    """네이버 지도 HTML 구조 분석"""
    try:
        print("🚀 네이버 지도 구조 분석 시작...")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # 네이버 지도로 이동
        search_url = "https://map.naver.com/v5/search/강남 맛집"
        await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        print("✅ 네이버 지도 로드 완료")
        
        # 충분히 대기
        await asyncio.sleep(10)
        
        # 페이지의 전체 HTML을 파일로 저장
        html_content = await page.content()
        with open('output/naver_map_html.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("📄 HTML 내용 저장 완료: output/naver_map_html.html")
        
        # 검색 결과 관련 클래스들을 찾아보자
        potential_selectors = [
            # 기본 선택자들
            'div[class*="place"]',
            'div[class*="search"]', 
            'div[class*="list"]',
            'div[class*="item"]',
            'div[class*="result"]',
            'li[class*="place"]',
            'li[class*="search"]',
            'li[class*="item"]',
            # 새로운 네이버 지도 선택자들 (2024-2025)
            'div[class*="Place"]',
            'div[class*="PLACE"]',
            'div[class*="Result"]',
            'div[class*="List"]',
            '[data-*]',
            'article',
            'section',
            '[role="listitem"]',
            '[role="button"]',
        ]
        
        print("🔍 검색 결과 요소 탐색 중...")
        found_elements = {}
        
        for selector in potential_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    found_elements[selector] = len(elements)
                    print(f"✅ '{selector}': {len(elements)}개 요소 발견")
            except Exception as e:
                continue
        
        if found_elements:
            print(f"\n📋 발견된 선택자들:")
            for selector, count in found_elements.items():
                print(f"  - {selector}: {count}개")
        else:
            print("❌ 적절한 선택자를 찾지 못했습니다.")
        
        # 이제 더 구체적으로 텍스트 검색 시도
        print("\n🔍 텍스트 기반 요소 검색...")
        try:
            # "맛집"이라는 텍스트가 포함된 요소 찾기
            elements_with_text = await page.query_selector_all('*:has-text("맛집")')
            print(f"📝 '맛집' 텍스트 포함 요소: {len(elements_with_text)}개")
            
            # 첫 번째 요소의 부모들을 확인
            if elements_with_text:
                first_element = elements_with_text[0]
                parent = await first_element.query_selector('..')
                if parent:
                    parent_class = await parent.get_attribute('class')
                    print(f"🔼 첫 번째 요소 부모 클래스: {parent_class}")
                    
        except Exception as e:
            print(f"텍스트 검색 오류: {str(e)}")
        
        # JavaScript로 동적으로 로드된 내용 확인
        print("\n🔍 JavaScript 실행 후 재검색...")
        await page.evaluate("() => { window.scrollBy(0, 100); }")
        await asyncio.sleep(3)
        
        # 다시 검색
        updated_selectors = [
            'div[class*="place"]',
            'div[class*="item"]',
            'a[class*="place"]',
            'a[class*="link"]',
        ]
        
        for selector in updated_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"🔄 '{selector}': {len(elements)}개 요소 발견 (업데이트됨)")
                    
                    # 첫 번째 요소의 텍스트 확인
                    if elements:
                        first_text = await elements[0].inner_text()
                        print(f"   첫 번째 요소 텍스트: {first_text[:100]}...")
                        
            except Exception as e:
                continue
        
        # 브라우저 종료
        await browser.close()
        await playwright.stop()
        print("✅ 분석 완료!")
        
    except Exception as e:
        print(f"❌ 분석 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(inspect_naver_map()) 