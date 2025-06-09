"""
네이버 지도 크롤링 프로젝트 설정 파일
2024-2025년 최신 스텔스 기법 적용
"""

# 브라우저 설정 (Patchright 최적화)
BROWSER_SETTINGS = {
    'headless': False,  # False로 설정하여 브라우저 UI 표시 (디버깅용)
    'viewport': {'width': 1920, 'height': 1080},
    'timeout': 60000,  # 60초로 타임아웃 증가
    'channel': 'chrome',  # Patchright 권장 설정
    'no_viewport': True,  # Patchright 권장 설정
    'args': [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-ipc-flooding-protection',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-background-timer-throttling',
        '--disable-background-media-hang-monitor',
        '--disable-client-side-phishing-detection',
        '--disable-default-apps',
        '--disable-hang-monitor',
        '--disable-prompt-on-repost',
        '--disable-sync',
        '--disable-translate',
        '--metrics-recording-only',
        '--no-first-run',
        '--disable-session-crashed-bubble',
        '--disable-logging',
        '--no-default-browser-check',
        '--disable-notifications',
        '--disable-popup-blocking',
    ]
}

# 네이버 지도 URL 및 선택자 (2024-2025년 최신)
NAVER_MAP = {
    'base_url': 'https://map.naver.com/v5/search/',
    'place_list_selector': '.place_bluelink, .CHC5F, [data-id], .PlaceItem',
    'place_name_selector': '.place_bluelink > .title_link, .CHC5F .TYaxT, [data-id] .TYaxT',
    'place_address_selector': '.addr, .LDgIH, .jibun',
    'place_category_selector': '.category, .YzBgS',
    'place_rating_selector': '.rating, .orXYY',
    'place_review_count_selector': '.review_count, .MVx6e',
    'search_results_selector': '.search_listview, .Rh6cC, [role="tabpanel"]',
    'loading_selector': '.loading, .spinner, [class*="loading"]',
}

# 크롤링 설정 (개선된 안정성)
CRAWLING_SETTINGS = {
    'delay_between_requests': 3,  # 요청 간 지연 시간 증가 (초)
    'max_retries': 5,  # 최대 재시도 횟수 증가
    'max_places_per_search': 30,  # 검색당 최대 장소 수 (안정성 우선)
    'enable_stealth': True,
    'wait_for_selector_timeout': 30000,  # 선택자 대기 시간 (30초)
    'navigation_timeout': 60000,  # 네비게이션 타임아웃 (60초)
    'page_load_strategy': 'domcontentloaded',  # networkidle 대신 domcontentloaded 사용
    'scroll_delay': 2,  # 스크롤 간 지연
    'random_delay_range': (1, 3),  # 랜덤 지연 범위
}

# 스텔스 설정 (Patchright 최적화)
STEALTH_SETTINGS = {
    'user_agent_rotation': True,
    'viewport_randomization': True,
    'webgl_randomization': True,
    'canvas_randomization': True,
    'audio_context_randomization': True,
    'timezone_randomization': True,
    'language_randomization': True,
    'memory_randomization': True,
    'isolated_context': True,  # Patchright 권장
}

# 검색 키워드 (테스트용)
SEARCH_KEYWORDS = [
    '강남 맛집',
    '홍대 카페', 
    '명동 쇼핑',
    '여의도 레스토랑',
    '서면 치킨'
]

# 출력 설정
OUTPUT_SETTINGS = {
    'output_directory': 'output',
    'excel_filename': 'naver_places_{timestamp}.xlsx',
    'csv_filename': 'naver_places_{timestamp}.csv',
    'json_filename': 'naver_places_{timestamp}.json',
    'log_filename': 'crawler.log',
    'timestamp_format': '%Y%m%d_%H%M%S',
}

# 로깅 설정
LOG_SETTINGS = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_handler': True,
    'console_handler': True,
    'log_file': 'output/crawler.log',
}

# Patchright 전용 설정
PATCHRIGHT_SETTINGS = {
    'use_persistent_context': True,
    'user_data_dir': 'output/browser_data',
    'channel': 'chrome',
    'bypass_csp': True,
    'ignore_https_errors': True,
} 