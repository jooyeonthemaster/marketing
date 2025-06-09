import asyncio
from playwright.async_api import async_playwright

async def quick_test():
    """빠른 테스트"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            test_keywords = ["강남 카페", "홍대 맛집", "서울 향수공방"]
            
            for keyword in test_keywords:
                print(f"\n🔍 '{keyword}' 테스트 중...")
                print("="*50)
                
                await page.goto("https://map.naver.com/v5/search", wait_until='domcontentloaded')
                
                search_input = await page.wait_for_selector(".input_search", timeout=10000)
                await search_input.fill(keyword)
                await page.keyboard.press("Enter")
                
                await page.wait_for_selector("#searchIframe", timeout=15000)
                search_frame = page.frame(name="searchIframe") or page.frame(url="**/search**")
                
                if search_frame:
                    # .TYaxT 선택자 확인
                    try:
                        await search_frame.wait_for_selector(".TYaxT", timeout=10000)
                        places = await search_frame.query_selector_all(".TYaxT")
                        print(f"✅ '{keyword}': .TYaxT 선택자로 {len(places)}개 발견!")
                        
                        for i, place in enumerate(places[:3]):
                            text = await place.text_content()
                            print(f"   {i+1}. {text.strip()}")
                            
                    except Exception as e:
                        print(f"❌ '{keyword}': .TYaxT 선택자 실패")
                        
                        # 다른 선택자들 시도
                        alternative_selectors = ["._3XamX", ".CHC5F", "[data-id]", "li"]
                        for selector in alternative_selectors:
                            try:
                                await search_frame.wait_for_selector(selector, timeout=3000)
                                elements = await search_frame.query_selector_all(selector)
                                if len(elements) > 0:
                                    print(f"✅ '{keyword}': {selector} 선택자로 {len(elements)}개 발견!")
                                    break
                            except:
                                continue
                        else:
                            print(f"❌ '{keyword}': 검색 결과 없음")
                
                await asyncio.sleep(3)  # 키워드 간 대기
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            
        finally:
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(quick_test()) 