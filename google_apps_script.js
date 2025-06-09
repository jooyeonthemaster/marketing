/**
 * 네이버 지도 크롤링 데이터를 Google Sheets에 저장하는 Apps Script
 */

// 설정
const CONFIG = {
  API_URL: 'http://localhost:8000/search',  // 백엔드 API URL
  SHEET_NAME: 'marketing',  // 데이터를 저장할 시트명
  MAX_RESULTS: 10  // 최대 검색 결과 수
};

/**
 * 메뉴 추가 (스프레드시트 열릴 때 자동 실행)
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔍 네이버 지도 크롤링')
    .addItem('검색하기', 'showSearchDialog')
    .addItem('데이터 지우기', 'clearData')
    .addToUi();
}

/**
 * 검색 다이얼로그 표시
 */
function showSearchDialog() {
  const html = HtmlService.createHtmlOutput(`
    <div style="padding: 20px; font-family: Arial;">
      <h3>🗺️ 네이버 지도 크롤링</h3>
      <p><strong>검색 키워드:</strong></p>
      <input type="text" id="keyword" placeholder="예: 강남맛집, 향수공방" style="width: 100%; padding: 8px; margin-bottom: 10px;">
      
      <p><strong>최대 결과 수:</strong></p>
      <select id="maxResults" style="width: 100%; padding: 8px; margin-bottom: 15px;">
        <option value="5">5개</option>
        <option value="10" selected>10개</option>
        <option value="15">15개</option>
        <option value="20">20개</option>
      </select>
      
      <button onclick="searchPlaces()" style="width: 100%; padding: 10px; background: #4285f4; color: white; border: none; cursor: pointer;">
        🔍 검색 시작
      </button>
      
      <div id="status" style="margin-top: 15px; font-size: 12px; color: #666;"></div>
    </div>
    
    <script>
      function searchPlaces() {
        const keyword = document.getElementById('keyword').value.trim();
        const maxResults = parseInt(document.getElementById('maxResults').value);
        const status = document.getElementById('status');
        
        if (!keyword) {
          status.innerHTML = '❌ 검색 키워드를 입력해주세요!';
          return;
        }
        
        status.innerHTML = '🔄 크롤링 중... 잠시만 기다려주세요.';
        
        google.script.run
          .withSuccessHandler(function(result) {
            if (result.success) {
              status.innerHTML = '✅ 성공! ' + result.count + '개 데이터 저장됨';
              setTimeout(() => google.script.host.close(), 2000);
            } else {
              status.innerHTML = '❌ 실패: ' + result.error;
            }
          })
          .withFailureHandler(function(error) {
            status.innerHTML = '❌ 오류 발생: ' + error.toString();
          })
          .crawlNaverMap(keyword, maxResults);
      }
    </script>
  `).setWidth(400).setHeight(300);
  
  SpreadsheetApp.getUi().showModalDialog(html, '네이버 지도 크롤링');
}

/**
 * 네이버 지도 크롤링 실행
 */
function crawlNaverMap(keyword, maxResults = 10) {
  try {
    console.log(`크롤링 시작: ${keyword} (최대 ${maxResults}개)`);
    
    // API 요청
    const payload = {
      query: keyword,
      max_results: maxResults
    };
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      payload: JSON.stringify(payload)
    };
    
    console.log('API 요청 중...');
    const response = UrlFetchApp.fetch(CONFIG.API_URL, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      throw new Error(`API 오류: ${responseCode} - ${response.getContentText()}`);
    }
    
    const data = JSON.parse(response.getContentText());
    console.log(`API 응답 받음: ${data.places.length}개 결과`);
    
    // 스프레드시트에 저장
    const count = saveToSheet(data);
    
    return {
      success: true,
      count: count,
      keyword: keyword
    };
    
  } catch (error) {
    console.error('크롤링 오류:', error);
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * 데이터를 스프레드시트에 저장
 */
function saveToSheet(data) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = spreadsheet.getSheetByName(CONFIG.SHEET_NAME);
  
  // 시트가 없으면 생성
  if (!sheet) {
    sheet = spreadsheet.insertSheet(CONFIG.SHEET_NAME);
  }
  
  // 기존 데이터 지우기
  sheet.clear();
  
  // 헤더 작성
  const headers = [
    '순위', '장소명', '카테고리', '주소', '영업상태', '리뷰수', '평점', 
    '전화번호', '네이버페이', '예약가능', '검색키워드', '수집일시'
  ];
  
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  
  // 헤더 스타일 적용
  const headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setBackground('#4285f4');
  headerRange.setFontColor('white');
  headerRange.setFontWeight('bold');
  headerRange.setHorizontalAlignment('center');
  
  // 데이터 파싱 및 저장
  const now = new Date();
  const rows = [];
  
  data.places.forEach((place, index) => {
    const parsedData = parseNaverPlaceData(place.name, index + 1);
    rows.push([
      parsedData.rank,
      parsedData.name,
      parsedData.category || '',
      parsedData.address || '',
      parsedData.status || '',
      parsedData.reviewCount || '',
      parsedData.rating || '',
      parsedData.phone || '',
      parsedData.naverPay ? 'O' : '',
      parsedData.reservation ? 'O' : '',
      data.query,
      Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss')
    ]);
  });
  
  // 데이터 입력
  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
    
    // 자동 폭 조정
    sheet.autoResizeColumns(1, headers.length);
    
    // 테두리 추가
    const dataRange = sheet.getRange(1, 1, rows.length + 1, headers.length);
    dataRange.setBorder(true, true, true, true, true, true);
  }
  
  console.log(`${rows.length}개 데이터 저장 완료`);
  return rows.length;
}

/**
 * 네이버 지도 크롤링 데이터 파싱
 */
function parseNaverPlaceData(rawText, rank) {
  const result = {
    rank: rank,
    name: '',
    category: '',
    address: '',
    status: '',
    reviewCount: '',
    rating: '',
    phone: '',
    naverPay: false,
    reservation: false
  };
  
  try {
    // 기본 장소명 추출 (첫 번째 단어들)
    let remainingText = rawText;
    
    // 네이버페이 확인
    if (remainingText.includes('네이버페이')) {
      result.naverPay = true;
      remainingText = remainingText.replace('네이버페이', '');
    }
    
    // 예약 확인
    if (remainingText.includes('예약') || remainingText.includes('톡톡')) {
      result.reservation = true;
      remainingText = remainingText.replace(/예약|톡톡/g, '');
    }
    
    // 영업상태 추출
    const statusMatches = remainingText.match(/(영업\s*(중|종료)|광고|새로오픈)/);
    if (statusMatches) {
      result.status = statusMatches[0];
      remainingText = remainingText.replace(statusMatches[0], '');
    }
    
    // 시간 정보 제거
    remainingText = remainingText.replace(/\d{1,2}:\d{2}에\s*(영업\s*(시작|종료))/g, '');
    
    // 리뷰 수 추출
    const reviewMatches = remainingText.match(/리뷰\s*(\d+|999\+)/);
    if (reviewMatches) {
      result.reviewCount = reviewMatches[1];
      remainingText = remainingText.replace(reviewMatches[0], '');
    }
    
    // 평점 추출
    const ratingMatches = remainingText.match(/별점(\d+\.\d+)/);
    if (ratingMatches) {
      result.rating = ratingMatches[1];
      remainingText = remainingText.replace(ratingMatches[0], '');
    }
    
    // 주소 추출 (서울 ~동 패턴)
    const addressMatches = remainingText.match(/서울\s*[가-힣]+구\s*[가-힣]+동/);
    if (addressMatches) {
      result.address = addressMatches[0];
      remainingText = remainingText.replace(addressMatches[0], '');
    }
    
    // 카테고리 추출 (한글 단어들)
    const categoryMatches = remainingText.match(/[가-힣]{2,}/);
    if (categoryMatches && categoryMatches.length > 1) {
      result.category = categoryMatches[1]; // 두 번째 매치가 보통 카테고리
    }
    
    // 장소명 추출 (정제된 첫 번째 부분)
    const nameMatches = rawText.match(/^[^\d가-힣]*?([가-힣\w\s]+)/);
    if (nameMatches) {
      result.name = nameMatches[1].trim();
    } else {
      // 백업: 첫 20자 사용
      result.name = rawText.substring(0, 20).replace(/[^\w가-힣\s]/g, '').trim();
    }
    
  } catch (error) {
    console.error('파싱 오류:', error);
    result.name = rawText.substring(0, 30); // 백업으로 원본 텍스트 일부 사용
  }
  
  return result;
}

/**
 * 데이터 지우기
 */
function clearData() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert('확인', '정말로 모든 데이터를 지우시겠습니까?', ui.ButtonSet.YES_NO);
  
  if (response === ui.Button.YES) {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName(CONFIG.SHEET_NAME);
    
    if (sheet) {
      sheet.clear();
      ui.alert('완료', '데이터가 삭제되었습니다.', ui.ButtonSet.OK);
    }
  }
}

/**
 * 테스트 함수
 */
function testCrawling() {
  const result = crawlNaverMap('강남맛집', 5);
  console.log('테스트 결과:', result);
} 