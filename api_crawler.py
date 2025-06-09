import asyncio
import aiohttp
import json
from typing import List, Dict

async def search_naver_api(query: str, longitude: float = 127.0378515499566, latitude: float = 37.4774550570593) -> List[Dict]:
    """
    네이버 지도 allSearch API 직접 호출 방식
    블로그에서 찾은 정보를 바탕으로 구현
    """
    search_coord = f"{longitude};{latitude}"
    boundary = f"{longitude};{latitude};{longitude};{latitude}"
    
    url = "https://map.naver.com/p/api/search/allSearch"
    
    headers = {
        "authority": "map.naver.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "referer": f"https://map.naver.com/p/search/{query}?c=15.00,0,0,0,dh",
    }
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for page in range(1, 6):  # 5페이지까지 수집
            params = {
                "query": query,
                "type": "all",
                "searchCoord": search_coord,
                "boundary": boundary,
                "page": str(page)
            }
            
            try:
                print(f"🔍 '{query}' 페이지 {page} 요청 중...")
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "result" in data and "place" in data["result"] and "list" in data["result"]["place"]:
                            place_list = data["result"]["place"]["list"]
                            
                            if not place_list:
                                print(f"❌ 페이지 {page}: 검색 결과 없음")
                                break
                            
                            print(f"✅ 페이지 {page}: {len(place_list)}개 장소 발견")
                            
                            for i, place in enumerate(place_list):
                                result = {
                                    'rank': len(results) + 1,
                                    'name': place.get('name', 'N/A'),
                                    'address': place.get('address', 'N/A'),
                                    'road_address': place.get('roadAddress', 'N/A'),
                                    'category': place.get('category', 'N/A'),
                                    'phone': place.get('tel', 'N/A'),
                                    'longitude': place.get('x', 'N/A'),
                                    'latitude': place.get('y', 'N/A'),
                                    'naver_id': place.get('id', 'N/A'),
                                    'search_query': query,
                                    'page': page
                                }
                                results.append(result)
                                print(f"  {result['rank']}. {result['name']} - {result['address']}")
                        else:
                            print(f"❌ 페이지 {page}: 예상치 못한 응답 구조")
                            break
                            
                    elif response.status == 403:
                        print(f"❌ 페이지 {page}: 접근 거부 (403) - 헤더나 파라미터 문제")
                        break
                    else:
                        print(f"❌ 페이지 {page}: HTTP {response.status}")
                        break
                        
                # 페이지 간 지연
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ 페이지 {page} 요청 실패: {e}")
                break
    
    return results

async def search_multiple_locations(query: str) -> List[Dict]:
    """
    여러 지역에서 검색하여 더 많은 결과 수집
    """
    # 주요 도시 좌표
    locations = [
        {"name": "서울 강남", "longitude": 127.0378515499566, "latitude": 37.4774550570593},
        {"name": "서울 홍대", "longitude": 126.9225103, "latitude": 37.5564147},
        {"name": "서울 명동", "longitude": 126.9816468, "latitude": 37.563692},
        {"name": "부산 서면", "longitude": 129.0584861, "latitude": 35.1576312},
        {"name": "대구 동성로", "longitude": 128.5963242, "latitude": 35.8682327},
    ]
    
    all_results = []
    seen_places = set()  # 중복 제거용
    
    for location in locations:
        print(f"\n{'='*60}")
        print(f"📍 지역: {location['name']}")
        print(f"{'='*60}")
        
        results = await search_naver_api(
            query, 
            longitude=location['longitude'], 
            latitude=location['latitude']
        )
        
        # 중복 제거하면서 추가
        for result in results:
            place_key = f"{result['name']}_{result['address']}"
            if place_key not in seen_places:
                result['search_location'] = location['name']
                all_results.append(result)
                seen_places.add(place_key)
        
        print(f"📊 {location['name']} 결과: {len(results)}개 (중복 제거 후 총 {len(all_results)}개)")
        
        # 지역 간 지연
        await asyncio.sleep(3)
    
    return all_results

async def main():
    """메인 함수"""
    try:
        print("🗺️ 네이버 지도 API 크롤링 시작")
        print("="*70)
        
        # 검색할 키워드들
        queries = ["맛집", "카페", "치킨", "중국집"]
        
        all_results = {}
        
        for query in queries:
            print(f"\n🎯 키워드: '{query}' 검색 시작")
            print("="*70)
            
            results = await search_multiple_locations(query)
            all_results[query] = results
            
            print(f"\n📈 '{query}' 최종 결과: {len(results)}개 장소")
            
            # 상위 10개 출력
            for i, result in enumerate(results[:10], 1):
                print(f"  {i}. {result['name']} ({result['category']}) - {result['search_location']}")
            
            # 키워드 간 지연
            await asyncio.sleep(5)
        
        # 전체 결과 저장
        filename = "naver_api_results.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 최종 요약
        total_places = sum(len(results) for results in all_results.values())
        print(f"\n🎉 크롤링 완료!")
        print(f"📁 파일: {filename}")
        print(f"📊 총 수집된 장소: {total_places}개")
        
        for query, results in all_results.items():
            print(f"  • '{query}': {len(results)}개")
        
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 