import asyncio
import json
from playwright.async_api import async_playwright

async def simple_naver_search(query, max_results=10):
    """
    블로그 정보를 바탕으로 한 간단한 네이버 지도 검색
    """
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        results = []
        
        try:
            print(f"🔍 '{query}' 검색 시작...")
            
            # 네이버 지도 접속
            await page.goto("https://map.naver.com/v5/search", wait_until='domcontentloaded')
            print("✅ 네이버 지도 로드 완료")
            
            # 검색창 찾기 및 검색 실행
            search_input = await page.wait_for_selector(".input_search", timeout=10000)
            await search_input.fill(query)
            await page.keyboard.press("Enter")
            print("✅ 검색 실행 완료")
            
            # searchIframe 로드 대기 및 전환
            await page.wait_for_selector("#searchIframe", timeout=15000)
            search_frame = page.frame(name="searchIframe")
            
            if not search_frame:
                # 다른 방법으로 iframe 찾기
                frames = page.frames
                for frame in frames:
                    if "search" in frame.url:
                        search_frame = frame
                        break
            
            if not search_frame:
                raise Exception("searchIframe을 찾을 수 없습니다")
                
            print("✅ searchIframe으로 전환 성공")
            
            # 검색 결과 로드 대기
            await search_frame.wait_for_selector(".TYaxT", timeout=15000)
            places = await search_frame.query_selector_all(".TYaxT")
            print(f"✅ 검색 결과 {len(places)}개 발견")
            
            # 각 장소 정보 수집
            for i, place in enumerate(places[:max_results]):
                try:
                    # 장소명 추출
                    name = await place.text_content()
                    
                    # 부모 요소에서 추가 정보 찾기
                    parent = await place.evaluate_handle("el => el.closest('.CHC5F, .search_item, [data-id]')")
                    
                    address = ""
                    category = ""
                    
                    if parent:
                        # 주소 찾기
                        try:
                            address_elem = await parent.query_selector(".LDgIH, .addr, .jibun")
                            if address_elem:
                                address = await address_elem.text_content()
                        except:
                            pass
                        
                        # 카테고리 찾기
                        try:
                            category_elem = await parent.query_selector(".KCMnt, .category")
                            if category_elem:
                                category = await category_elem.text_content()
                        except:
                            pass
                    
                    result = {
                        'rank': i + 1,
                        'name': name.strip() if name else f"장소 {i+1}",
                        'address': address.strip() if address else "주소 정보 없음",
                        'category': category.strip() if category else "카테고리 없음",
                        'search_query': query
                    }
                    
                    results.append(result)
                    print(f"✅ {i+1}. {result['name']} 수집 완료")
                    
                    # 요청 간 지연
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ {i+1}번째 장소 정보 수집 실패: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            
        finally:
            await browser.close()
            
        return results

async def main():
    """메인 함수"""
    try:
        # 검색 키워드
        queries = ["강남 맛집", "홍대 카페", "서울 관광지"]
        
        all_results = {}
        
        for query in queries:
            print(f"\n{'='*50}")
            print(f"🎯 키워드: {query}")
            print(f"{'='*50}")
            
            results = await simple_naver_search(query, max_results=5)
            all_results[query] = results
            
            print(f"\n📊 '{query}' 검색 결과: {len(results)}개")
            for result in results:
                print(f"  {result['rank']}. {result['name']} - {result['address']}")
            
            # 키워드 간 지연
            await asyncio.sleep(3)
        
        # 결과 저장
        with open('search_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 모든 검색 완료! 결과가 'search_results.json'에 저장되었습니다.")
        
        # 전체 결과 요약
        total_places = sum(len(results) for results in all_results.values())
        print(f"📈 총 수집된 장소: {total_places}개")
        
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")

if __name__ == "__main__":
    print("🗺️ 네이버 지도 크롤링 테스트 시작")
    asyncio.run(main()) 