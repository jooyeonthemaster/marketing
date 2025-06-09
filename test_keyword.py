import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def extract_detailed_info(frame, place_element, index):
    """상세 정보 추출"""
    try:
        # 기본 장소명
        name = await place_element.text_content()
        
        # 부모 컨테이너 찾기
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

async def test_single_keyword(keyword, max_results=10):
    """단일 키워드 테스트"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=2000
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        results = []
        
        try:
            print(f"🔍 네이버 지도에서 '{keyword}' 검색 중...")
            print("="*60)
            
            # 네이버 지도 접속
            await page.goto("https://map.naver.com/v5/search", wait_until='domcontentloaded')
            print(f"✓ 페이지 로드 완료: {page.url}")
            
            # 검색창 찾기 및 검색 실행
            search_input = await page.wait_for_selector(".input_search", timeout=10000)
            if search_input:
                print("✓ 검색창 발견!")
                
                await search_input.fill(keyword)
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
                    
                    # 검색 결과 대기 (결과가 없을 수도 있음)
                    print("검색 결과 로드 대기 중...")
                    try:
                        await search_frame.wait_for_selector(".TYaxT", timeout=15000)
                    except Exception as timeout_error:
                        print("⚠️ 검색 결과를 찾을 수 없습니다. 다른 선택자들을 시도해보겠습니다...")
                        
                                                                         # 대안 선택자들 시도
                        alternative_selectors = [
                            "li",       # 가장 확실한 대안 (향수공방 등에서 작동)
                            "._3XamX",  # 다른 가능한 선택자
                            ".CHC5F",   # 기존에 사용하던 선택자
                            "[data-id]", # data-id 속성이 있는 요소
                            ".item",    # 일반적인 아이템 클래스
                            ".result"   # 결과 클래스
                        ]
                        
                        found_selector = None
                        for selector in alternative_selectors:
                            try:
                                await search_frame.wait_for_selector(selector, timeout=3000)
                                found_selector = selector
                                print(f"✓ 대안 선택자 '{selector}' 발견!")
                                break
                            except:
                                continue
                        
                        if not found_selector:
                            print("❌ 어떤 검색 결과도 찾을 수 없습니다. 검색어를 확인해주세요.")
                            return results
                    
                    # 검색 결과 수집 (성공한 선택자 또는 대안 선택자 사용)
                    selector_to_use = found_selector if 'found_selector' in locals() and found_selector else ".TYaxT"
                    places = await search_frame.query_selector_all(selector_to_use)
                    print(f"✓ 검색 결과 {len(places)}개 발견!")
                    print("="*60)
                    
                    # 각 검색 결과 출력 및 상세 정보 추출
                    for i, place in enumerate(places[:max_results]):
                        try:
                            # 기본 정보
                            text = await place.text_content()
                            print(f"🏪 {i+1}. {text.strip()}")
                            
                            # 상세 정보 추출
                            detailed_info = await extract_detailed_info(search_frame, place, i)
                            if detailed_info:
                                detailed_info['search_query'] = keyword
                                results.append(detailed_info)
                                
                                # 추가 정보 출력
                                if detailed_info['category']:
                                    print(f"   🏷️ 카테고리: {detailed_info['category']}")
                                if detailed_info['rating']:
                                    print(f"   ⭐ 평점: {detailed_info['rating']}")
                                if detailed_info['address']:
                                    print(f"   📍 주소: {detailed_info['address']}")
                                if detailed_info['phone']:
                                    print(f"   📞 전화: {detailed_info['phone']}")
                                    
                            print()  # 빈 줄 추가
                                
                        except Exception as e:
                            print(f"❌ {i+1}. 정보 추출 실패: {e}")
                            print()
                            
                else:
                    print("❌ searchIframe 전환 실패")
            else:
                print("❌ 검색창을 찾을 수 없음")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            
        finally:
            print("="*60)
            print("5초 후 브라우저 종료...")
            await asyncio.sleep(5)
            await browser.close()
            
        return results

def main():
    """메인 함수 - 키워드 입력받기"""
    print("🗺️ 네이버 지도 키워드 테스트")
    print("="*60)
    
    # 키워드 입력받기
    keyword = input("🔍 검색할 키워드를 입력하세요: ").strip()
    
    if not keyword:
        print("❌ 키워드를 입력해주세요!")
        return
    
    # 결과 개수 입력받기 (선택사항)
    max_results_input = input("📊 가져올 결과 개수 (기본값: 10개): ").strip()
    try:
        max_results = int(max_results_input) if max_results_input else 10
        max_results = max(1, min(max_results, 50))  # 1~50개 제한
    except ValueError:
        max_results = 10
        print("⚠️ 잘못된 숫자입니다. 기본값 10개로 설정합니다.")
    
    print(f"\n🎯 '{keyword}' (최대 {max_results}개) 검색 시작!")
    print("="*60)
    
    # 크롤링 실행
    try:
        results = asyncio.run(test_single_keyword(keyword, max_results))
        
        # 결과 저장
        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_{keyword.replace(' ', '_')}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'keyword': keyword,
                    'timestamp': timestamp,
                    'total_count': len(results),
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"🎉 테스트 완료!")
            print(f"📁 결과 파일: {filename}")
            print(f"📊 수집된 장소: {len(results)}개")
        else:
            print("❌ 검색 결과가 없습니다.")
            
    except KeyboardInterrupt:
        print("\n🛑 사용자가 중단했습니다.")
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")

if __name__ == "__main__":
    main() 