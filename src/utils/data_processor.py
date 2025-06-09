"""
크롤링된 데이터 처리 및 저장 유틸리티
Excel, CSV, JSON 형식으로 데이터 저장 기능
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
import sys

# 상위 디렉토리의 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import OUTPUT_SETTINGS


class DataProcessor:
    """데이터 처리 및 저장 클래스"""
    
    def __init__(self):
        self.setup_logging()
        self.ensure_output_directory()
    
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger(__name__)
    
    def ensure_output_directory(self):
        """출력 디렉토리 생성"""
        output_dir = OUTPUT_SETTINGS['output_directory']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.logger.info(f"출력 디렉토리 생성: {output_dir}")
    
    def process_crawling_results(self, results: Dict[str, List[Dict]]) -> pd.DataFrame:
        """크롤링 결과를 DataFrame으로 변환"""
        try:
            all_data = []
            
            for keyword, places in results.items():
                for place in places:
                    # 기본 정보에 키워드 추가
                    place_data = place.copy()
                    place_data['search_keyword'] = keyword
                    place_data['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 데이터 정제
                    place_data = self.clean_place_data(place_data)
                    all_data.append(place_data)
            
            # DataFrame 생성
            df = pd.DataFrame(all_data)
            
            if not df.empty:
                # 컬럼 순서 정리
                column_order = [
                    'search_keyword', 'rank', 'name', 'address', 'category',
                    'rating', 'review_count', 'phone', 'url', 'crawled_at'
                ]
                
                # 존재하는 컬럼만 선택
                available_columns = [col for col in column_order if col in df.columns]
                df = df[available_columns]
                
                # 정렬
                df = df.sort_values(['search_keyword', 'rank']).reset_index(drop=True)
            
            self.logger.info(f"데이터 처리 완료: {len(df)} 건")
            return df
            
        except Exception as e:
            self.logger.error(f"데이터 처리 실패: {e}")
            return pd.DataFrame()
    
    def clean_place_data(self, place_data: Dict) -> Dict:
        """장소 데이터 정제"""
        try:
            # 텍스트 정제
            for key, value in place_data.items():
                if isinstance(value, str):
                    # 불필요한 공백 제거
                    value = value.strip()
                    # 개행문자 제거
                    value = value.replace('\n', ' ').replace('\r', ' ')
                    # 연속된 공백 제거
                    value = ' '.join(value.split())
                    place_data[key] = value
            
            # 평점 숫자 추출
            if place_data.get('rating'):
                rating_text = place_data['rating']
                # 숫자 부분만 추출 (예: "4.5점" -> "4.5")
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    place_data['rating'] = rating_match.group(1)
            
            # 리뷰 수 숫자 추출
            if place_data.get('review_count'):
                review_text = place_data['review_count']
                # 숫자 부분만 추출 (예: "리뷰 125개" -> "125")
                import re
                review_match = re.search(r'(\d+)', review_text.replace(',', ''))
                if review_match:
                    place_data['review_count'] = review_match.group(1)
            
            return place_data
            
        except Exception as e:
            self.logger.warning(f"데이터 정제 실패: {e}")
            return place_data
    
    def save_to_excel(self, df: pd.DataFrame, filename: Optional[str] = None) -> str:
        """Excel 파일로 저장"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"naver_places_ranking_{timestamp}.xlsx"
            
            output_path = os.path.join(OUTPUT_SETTINGS['output_directory'], filename)
            
            # Excel 저장 (여러 시트로 구성)
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 전체 데이터
                df.to_excel(writer, sheet_name='전체_데이터', index=False)
                
                # 키워드별 시트 생성
                if 'search_keyword' in df.columns:
                    for keyword in df['search_keyword'].unique():
                        keyword_df = df[df['search_keyword'] == keyword]
                        sheet_name = keyword[:30]  # 시트명 길이 제한
                        keyword_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 요약 통계
                if not df.empty:
                    summary_data = self.create_summary_stats(df)
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='요약_통계', index=False)
            
            self.logger.info(f"Excel 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Excel 저장 실패: {e}")
            return ""
    
    def save_to_csv(self, df: pd.DataFrame, filename: Optional[str] = None) -> str:
        """CSV 파일로 저장"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"naver_places_ranking_{timestamp}.csv"
            
            output_path = os.path.join(OUTPUT_SETTINGS['output_directory'], filename)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"CSV 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"CSV 저장 실패: {e}")
            return ""
    
    def save_to_json(self, results: Dict[str, List[Dict]], filename: Optional[str] = None) -> str:
        """JSON 파일로 저장"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"naver_places_ranking_{timestamp}.json"
            
            output_path = os.path.join(OUTPUT_SETTINGS['output_directory'], filename)
            
            # 메타데이터 추가
            output_data = {
                'metadata': {
                    'crawled_at': datetime.now().isoformat(),
                    'total_keywords': len(results),
                    'total_places': sum(len(places) for places in results.values())
                },
                'data': results
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"JSON 저장 실패: {e}")
            return ""
    
    def create_summary_stats(self, df: pd.DataFrame) -> List[Dict]:
        """요약 통계 생성"""
        try:
            summary_data = []
            
            if 'search_keyword' in df.columns:
                for keyword in df['search_keyword'].unique():
                    keyword_df = df[df['search_keyword'] == keyword]
                    
                    stats = {
                        '검색_키워드': keyword,
                        '총_장소_수': len(keyword_df),
                        '평균_평점': '',
                        '평균_리뷰_수': '',
                        '카테고리_수': ''
                    }
                    
                    # 평점 통계
                    if 'rating' in keyword_df.columns:
                        try:
                            numeric_ratings = pd.to_numeric(keyword_df['rating'], errors='coerce')
                            if not numeric_ratings.isna().all():
                                stats['평균_평점'] = f"{numeric_ratings.mean():.2f}"
                        except:
                            pass
                    
                    # 리뷰 수 통계
                    if 'review_count' in keyword_df.columns:
                        try:
                            numeric_reviews = pd.to_numeric(keyword_df['review_count'], errors='coerce')
                            if not numeric_reviews.isna().all():
                                stats['평균_리뷰_수'] = f"{numeric_reviews.mean():.0f}"
                        except:
                            pass
                    
                    # 카테고리 통계
                    if 'category' in keyword_df.columns:
                        unique_categories = keyword_df['category'].nunique()
                        stats['카테고리_수'] = unique_categories
                    
                    summary_data.append(stats)
            
            return summary_data
            
        except Exception as e:
            self.logger.error(f"요약 통계 생성 실패: {e}")
            return []
    
    def save_all_formats(self, results: Dict[str, List[Dict]]) -> Dict[str, str]:
        """모든 형식으로 저장"""
        saved_files = {}
        
        try:
            # DataFrame 생성
            df = self.process_crawling_results(results)
            
            if not df.empty:
                # Excel 저장
                excel_path = self.save_to_excel(df)
                if excel_path:
                    saved_files['excel'] = excel_path
                
                # CSV 저장
                csv_path = self.save_to_csv(df)
                if csv_path:
                    saved_files['csv'] = csv_path
            
            # JSON 저장 (원본 데이터)
            json_path = self.save_to_json(results)
            if json_path:
                saved_files['json'] = json_path
            
            self.logger.info(f"모든 형식 저장 완료: {list(saved_files.keys())}")
            return saved_files
            
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {e}")
            return saved_files
    
    def print_summary(self, results: Dict[str, List[Dict]]) -> None:
        """크롤링 결과 요약 출력"""
        try:
            print("\n" + "="*60)
            print("네이버 지도 크롤링 결과 요약")
            print("="*60)
            
            total_places = 0
            for keyword, places in results.items():
                print(f"\n🔍 키워드: {keyword}")
                print(f"   └─ 수집된 장소: {len(places)}개")
                total_places += len(places)
                
                if places:
                    # 상위 3개 장소 미리보기
                    print("   └─ 상위 장소:")
                    for i, place in enumerate(places[:3], 1):
                        name = place.get('name', '이름 없음')
                        rating = place.get('rating', 'N/A')
                        print(f"      {i}. {name} (평점: {rating})")
            
            print(f"\n📊 전체 통계:")
            print(f"   • 총 키워드 수: {len(results)}개")
            print(f"   • 총 수집 장소: {total_places}개")
            print(f"   • 평균 장소/키워드: {total_places/len(results):.1f}개")
            
            print("\n" + "="*60)
            
        except Exception as e:
            self.logger.error(f"요약 출력 실패: {e}") 