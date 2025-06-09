"""
스텔스 크롤링을 위한 유틸리티 함수들
네이버 지도의 안티봇 시스템을 우회하기 위한 기능들
"""

import random
import time
from typing import Dict, List
from fake_useragent import UserAgent


class StealthUtils:
    """스텔스 크롤링을 위한 유틸리티 클래스"""
    
    def __init__(self):
        self.ua = UserAgent()
        
    def get_random_user_agent(self) -> str:
        """랜덤 사용자 에이전트 반환"""
        try:
            return self.ua.random
        except:
            # fallback user agents
            fallback_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
            ]
            return random.choice(fallback_agents)
    
    def get_stealth_browser_args(self) -> List[str]:
        """스텔스 브라우저 실행 인수 반환"""
        return [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-dev-shm-usage',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-back-forward-cache',
            '--disable-ipc-flooding-protection',
            '--password-store=basic',
            '--use-mock-keychain',
            '--force-fieldtrials=*BackgroundTracing/default/',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-client-side-phishing-detection',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--mute-audio',
            '--no-default-browser-check',
            '--autoplay-policy=user-gesture-required',
            '--disable-background-mode',
            '--no-first-run',
            '--lang=ko'
        ]
    
    def get_viewport_size(self) -> Dict[str, int]:
        """랜덤 뷰포트 크기 반환"""
        common_resolutions = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 1280, 'height': 720},
        ]
        return random.choice(common_resolutions)
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """랜덤 지연 시간"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_like_typing(self, page, selector: str, text: str) -> None:
        """인간처럼 타이핑하는 함수"""
        element = page.locator(selector)
        element.click()
        
        # 기존 텍스트 지우기
        element.fill('')
        
        # 한 글자씩 타이핑
        for char in text:
            element.type(char)
            time.sleep(random.uniform(0.05, 0.15))  # 타이핑 간격
    
    def random_mouse_movement(self, page) -> None:
        """랜덤 마우스 움직임"""
        viewport = page.viewport_size
        if viewport:
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.3))
    
    def scroll_randomly(self, page) -> None:
        """랜덤 스크롤"""
        # 랜덤 스크롤 거리
        scroll_distance = random.randint(200, 800)
        direction = random.choice([1, -1])  # 위 또는 아래
        
        page.mouse.wheel(0, scroll_distance * direction)
        time.sleep(random.uniform(0.5, 1.5))
    
    def simulate_human_behavior(self, page) -> None:
        """인간의 행동 패턴 시뮬레이션"""
        actions = [
            self.random_mouse_movement,
            self.scroll_randomly,
            lambda p: time.sleep(random.uniform(1, 3))  # 단순 대기
        ]
        
        # 랜덤하게 액션 선택
        action = random.choice(actions)
        action(page)
    
    @staticmethod
    def get_stealth_context_options() -> Dict:
        """스텔스 컨텍스트 옵션 반환"""
        return {
            'user_agent': StealthUtils().get_random_user_agent(),
            'viewport': StealthUtils().get_viewport_size(),
            'locale': 'ko-KR',
            'timezone_id': 'Asia/Seoul',
            'permissions': ['geolocation'],
            'geolocation': {'longitude': 126.9780, 'latitude': 37.5665},  # 서울 좌표
            'java_script_enabled': True,
            'accept_downloads': False,
            'bypass_csp': True,
            'ignore_https_errors': True,
        } 