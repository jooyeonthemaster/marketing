"""
네이버 지도 크롤링 메인 실행 파일
2024-2025년 최신 스텔스 기법을 적용한 네이버 플레이스 순위 크롤러
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import sys
import os

# 상위 디렉토리의 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import OUTPUT_SETTINGS, LOG_SETTINGS
from src.crawler.naver_map_crawler import NaverMapCrawler
from src.utils.data_processor import DataProcessor

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_SETTINGS['level']),
    format=LOG_SETTINGS['format'],
    handlers=[
        logging.FileHandler(LOG_SETTINGS['log_file'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """메인 실행 함수"""
    try:
        logger.info("네이버 지도 크롤링 시작")
        
        # 크롤러 초기화
        async with NaverMapCrawler() as crawler:
            
            # 검색 키워드
            keywords = [
                "강남 맛집",
                "홍대 카페", 
                "명동 음식점",
                "서울 관광지"
            ]
            
            logger.info(f"검색 키워드: {keywords}")
            
            # 키워드별 검색 수행
            all_results = await crawler.crawl_keywords(keywords)
            
            # 데이터 처리
            processor = DataProcessor()
            
            # 모든 결과를 하나의 리스트로 합치기
            all_places = []
            for keyword, places in all_results.items():
                all_places.extend(places)
            
            # 중복 제거 및 정리
            processed_data = processor.process_places_data(all_places)
            
            # 결과 저장
            timestamp = datetime.now().strftime(OUTPUT_SETTINGS['timestamp_format'])
            
            # JSON 파일 저장
            json_filename = OUTPUT_SETTINGS['json_filename'].format(timestamp=timestamp)
            json_path = Path(OUTPUT_SETTINGS['output_directory']) / json_filename
            
            # 출력 디렉토리 생성
            json_path.parent.mkdir(exist_ok=True)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_places': len(processed_data),
                    'keywords': keywords,
                    'places': processed_data
                }, f, ensure_ascii=False, indent=2)
            
            # Excel 파일 저장
            excel_filename = OUTPUT_SETTINGS['excel_filename'].format(timestamp=timestamp)
            excel_path = Path(OUTPUT_SETTINGS['output_directory']) / excel_filename
            processor.save_to_excel(processed_data, str(excel_path))
            
            # 결과 요약 출력
            logger.info(f"크롤링 완료!")
            logger.info(f"총 수집된 장소: {len(processed_data)}개")
            logger.info(f"JSON 파일: {json_path}")
            logger.info(f"Excel 파일: {excel_path}")
            
            # 키워드별 결과 요약
            for keyword, places in all_results.items():
                logger.info(f"'{keyword}': {len(places)}개 장소")
                
    except Exception as e:
        logger.error(f"메인 실행 중 오류: {e}")
        raise

# 테스트 함수
async def test_single_search():
    """단일 검색 테스트"""
    try:
        logger.info("단일 검색 테스트 시작")
        
        async with NaverMapCrawler() as crawler:
            results = await crawler.search_places("강남 맛집", max_results=5)
            
            logger.info(f"테스트 결과: {len(results)}개 장소 발견")
            for i, place in enumerate(results, 1):
                logger.info(f"{i}. {place['name']} - {place['address']}")
                
    except Exception as e:
        logger.error(f"테스트 중 오류: {e}")

if __name__ == "__main__":
    # 사용자 선택
    print("실행할 작업을 선택하세요:")
    print("1. 전체 크롤링 실행")
    print("2. 단일 검색 테스트")
    
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        asyncio.run(test_single_search())
    else:
        print("잘못된 선택입니다.") 