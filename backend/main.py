import sys
import os
import re
from pathlib import Path

# 상위 디렉토리를 Python 경로에 추가 (src 폴더에 접근하기 위해)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import List, Optional
from src.crawler.naver_map_crawler import crawl_naver_map

app = FastAPI(title="네이버 지도 크롤러 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://script.google.com",
        "https://docs.google.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_business_name(raw_text: str) -> str:
    """원시 텍스트에서 업체명만 추출"""
    if not raw_text:
        return ""
    
    # 일반적인 구분 키워드들
    keywords = [
        "예약", "광고", "영업", "리뷰", "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
        "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
        "네이버페이", "톡톡", "별점", "현재", "위치", "거리", "출발", "도착", "상세주소", "저장", "더보기"
    ]
    
    # 키워드 중 가장 먼저 나오는 위치 찾기
    first_keyword_pos = len(raw_text)
    for keyword in keywords:
        pos = raw_text.find(keyword)
        if pos != -1 and pos < first_keyword_pos:
            first_keyword_pos = pos
    
    # 키워드 전까지의 텍스트 추출
    business_name = raw_text[:first_keyword_pos].strip()
    
    # 혹시 너무 짧거나 비어있으면 첫 10글자까지만 사용
    if len(business_name) < 2:
        business_name = raw_text[:10].strip()
    
    return business_name

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class PlaceResult(BaseModel):
    name: str
    rank: int
    raw_text: str  # 전체 원시 텍스트

class SearchResponse(BaseModel):
    query: str
    results: List[PlaceResult]
    total_count: int

@app.post("/search", response_model=SearchResponse)
async def search_places(request: SearchRequest):
    """네이버 지도에서 장소 검색"""
    print(f"📋 검색 요청: '{request.query}' (최대 {request.limit}개)")
    
    try:
        # 크롤러 직접 호출 (max_results 파라미터 사용)
        raw_results = await crawl_naver_map(request.query, request.limit)
        
        # PlaceResult 형식으로 변환
        results = []
        for item in raw_results:
            place_result = PlaceResult(
                rank=item.get('rank', 0),
                name=item.get('name', ''),
                raw_text=item.get('raw_text', '')
            )
            results.append(place_result)
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_count=len(results)
        )
        
    except Exception as e:
        print(f"❌ 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "🗺️ 네이버 지도 크롤러 API가 실행 중입니다!"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 네이버 지도 크롤러 API 서버 시작!")
    uvicorn.run(app, host="0.0.0.0", port=8001) 