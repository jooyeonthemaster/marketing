import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def extract_detailed_info(frame, place_element, index):
    """상세 정보 추출"""
    try:
        # 기본 장소명
        name = await place_element.text_content()
        
        # 부모 컨테이너 찾기 - 더 넓은 범위에서 정보 찾기
        parent_selectors = [
            "xpath=ancestor::li[1]",
            "xpath=ancestor::div[contains(@class, 'item') or contains(@class, 'place') or contains(@class, 'list')][1]",
            "xpath=ancestor::*[contains(@class, 'CHC5F') or contains(@class, 'search') or @data-id][1]"
        ]
        
        parent = None
        for selector in parent_selectors:
            try:
                parent = await place_element.query_selector(selector)
                if parent:
                    break
            except:
                continue
        
        # 정보 추출
        address = ""
        category = ""
        rating = ""
        review_count = ""
        phone = ""
        
        if parent:
            # 주소 찾기
            address_selectors = [".LDgIH", ".addr", ".jibun", "[class*='addr']", "[class*='address']"]
            for sel in address_selectors:
                try:
                    addr_elem = await parent.query_selector(sel)
                    if addr_elem:
                        address = await addr_elem.text_content()
                        if address and address.strip():
                            break
                except:
                    continue
            
            # 카테고리 찾기
            category_selectors = [".KCMnt", ".category", "[class*='category']", "[class*='type']"]
            for sel in category_selectors:
                try:
                    cat_elem = await parent.query_selector(sel)
                    if cat_elem:
                        category = await cat_elem.text_content()
                        if category and category.strip():
                            break
                except:
                    continue
            
            # 평점 찾기
            rating_selectors = [".orXYY", ".rating", "[class*='rating']", "[class*='star']"]
            for sel in rating_selectors:
                try:
                    rating_elem = await parent.query_selector(sel)
                    if rating_elem:
                        rating = await rating_elem.text_content()
                        if rating and rating.strip():
                            break
                except:
                    continue
            
            # 리뷰 수 찾기
            review_selectors = [".MVx6e", ".review", "[class*='review']", "[class*='count']"]
            for sel in review_selectors:
                try:
                    review_elem = await parent.query_selector(sel)
                    if review_elem:
                        review_count = await review_elem.text_content()
                        if review_count and review_count.strip():
                            break
                except:
                    continue
            
            # 전화번호 찾기
            phone_selectors = [".xlx7Q", ".phone", ".tel", "[class*='phone']", "[class*='tel']"]
            for sel in phone_selectors:
                try:
                    phone_elem = await parent.query_selector(sel)
                    if phone_elem:
                        phone = await phone_elem.text_content()
                        if phone and phone.strip():
                            break
                except:
                    continue
        
        result = {
            'rank': index + 1,
            'name': name.strip() if name else f"장소 {index+1}",
            'address': address.strip() if address else "",
            'category': category.strip() if category else "",
            'rating': rating.strip() if rating else "",
            'review_count': review_count.strip() if review_count else "",
            'phone': phone.strip() if phone else "",
        }
        
        return result
        
    except Exception as e:
        print(f"❌ 상세 정보 추출 실패: {e}")
        return None

async def search_naver_places(query, max_results=20):
    """
    성공한 방식을 기반으로 한 네이버 지도 검색
    """
    async with async_playwright() as p:
        # 브라우저 실행 (성공한 설정 그대로 사용)
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=2000  # 성공한 설정과 동일
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        results = []
        
        try:
            print(f"🔍 네이버 지도에서 '{query}' 검색 중...")
            
            # 네이버 지도 접속 (성공한 방식 그대로)
            await page.goto("https://map.naver.com/v5/search", wait_until='domcontentloaded')
            print(f"✓ 페이지 로드 완료: {page.url}")
            
            # 검색창 찾기 및 검색 실행 (성공한 방식 그대로)
            search_input = await page.wait_for_selector(".input_search", timeout=10000)
            if search_input:
                print("✓ 검색창 발견!")
                
                await search_input.fill(query)
                await page.keyboard.press("Enter")
                print("✓ 검색 실행")
                
                # searchIframe 로드 대기 (성공한 방식 그대로)
                print("searchIframe 로드 대기 중...")
                await page.wait_for_selector("#searchIframe", timeout=15000)
                print("✓ searchIframe 발견!")
                
                # iframe으로 전환 (성공한 방식 그대로)
                search_frame = page.frame(name="searchIframe") or page.frame(url="**/search**")
                if search_frame:
                    print("✓ searchIframe으로 전환 성공!")
                    
                    # 검색 결과 대기 (성공한 방식 그대로)
                    print("검색 결과 로드 대기 중...")
                    await search_frame.wait_for_selector(".TYaxT", timeout=15000)
                    
                    # 검색 결과 수집
                    places = await search_frame.query_selector_all(".TYaxT")
                    print(f"✓ 검색 결과 {len(places)}개 발견!")
                    
                    # 각 검색 결과의 정보 출력 및 상세 정보 추출
                    for i, place in enumerate(places[:max_results]):
                        try:
                            # 기본 정보
                            text = await place.text_content()
                            print(f"{i+1}. {text.strip()}")
                            
                            # 상세 정보 추출
                            detailed_info = await extract_detailed_info(search_frame, place, i)
                            if detailed_info:
                                detailed_info['search_query'] = query
                                results.append(detailed_info)
                                
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
            
        return results

async def main():
    """메인 함수"""
    try:
        print("🗺️ 네이버 지도 크롤링 시작")
        print("="*60)
        
        # 검색 키워드들
        keywords = [
            "강남 맛집",
            "홍대 카페", 
            "명동 음식점",
            "이태원 레스토랑"
        ]
        
        all_results = {}
        
        for keyword in keywords:
            print(f"\n🎯 키워드: '{keyword}' 검색")
            print("="*60)
            
            results = await search_naver_places(keyword, max_results=10)
            all_results[keyword] = results
            
            print(f"\n📊 '{keyword}' 검색 결과: {len(results)}개")
            for result in results:
                print(f"  {result['rank']}. {result['name']}")
                if result['address']:
                    print(f"     📍 {result['address']}")
                if result['category']:
                    print(f"     🏷️ {result['category']}")
                if result['rating']:
                    print(f"     ⭐ {result['rating']}")
                print()
            
            # 키워드 간 지연
            print("다음 검색까지 10초 대기...")
            await asyncio.sleep(10)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"naver_places_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'keywords': keywords,
                'results': all_results,
                'total_places': sum(len(results) for results in all_results.values())
            }, f, ensure_ascii=False, indent=2)
        
        # 최종 요약
        total_places = sum(len(results) for results in all_results.values())
        print(f"\n🎉 크롤링 완료!")
        print(f"📁 파일: {filename}")
        print(f"📊 총 수집된 장소: {total_places}개")
        
        for keyword, results in all_results.items():
            print(f"  • '{keyword}': {len(results)}개")
        
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 