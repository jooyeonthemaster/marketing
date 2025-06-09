/**
 * 네이버 지도 크롤링 결과를 Google Sheets에 저장하는 Web App
 * 
 * 사용법:
 * 1. Google Apps Script 프로젝트를 생성
 * 2. 이 코드를 붙여넣기
 * 3. 웹 앱으로 배포 (Execute as: Me, Who has access: Anyone)
 * 4. 생성된 Web App URL을 프론트엔드에 설정
 */

// OPTIONS 요청 처리 (CORS preflight)
function doOptions() {
  return ContentService
    .createTextOutput('')
    .setMimeType(ContentService.MimeType.TEXT);
}

// GET 요청 처리 (테스트용)
function doGet() {
  const response = {
    status: 'success',
    message: '네이버 지도 크롤링 결과 저장 API가 정상 작동 중입니다.',
    timestamp: new Date().toISOString()
  };
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

// POST 요청 처리 (실제 데이터 저장)
function doPost(e) {
  try {
    console.log('요청 수신:', e);
    console.log('postData:', e.postData);
    
    // FormData 방식으로 전송된 데이터 파싱 - 더 안정적인 처리
    let keyword, results;
    
    console.log('=== 상세 디버깅 정보 ===');
    console.log('e 타입:', typeof e);
    console.log('e.parameters 존재여부:', !!e.parameters);
    console.log('e.parameters 타입:', typeof e.parameters);
    console.log('e.parameters:', e.parameters);
    
    if (e.parameters && Object.keys(e.parameters).length > 0) {
      console.log('parameters 키들:', Object.keys(e.parameters));
      
      // FormData에서 keyword 추출 (배열 형태일 수 있음)
      if (e.parameters.keyword) {
        keyword = Array.isArray(e.parameters.keyword) ? e.parameters.keyword[0] : e.parameters.keyword;
        console.log('추출된 키워드:', keyword, '(타입:', typeof keyword, ')');
      } else {
        console.log('keyword 파라미터 없음');
        keyword = '알 수 없음';
      }
      
      // FormData에서 results JSON 문자열 추출 및 파싱 (배열 형태일 수 있음)
      if (e.parameters.results) {
        try {
          const resultsString = Array.isArray(e.parameters.results) ? e.parameters.results[0] : e.parameters.results;
          console.log('results 문자열 타입:', typeof resultsString);
          console.log('results 문자열 길이:', resultsString.length);
          console.log('results 문자열 처음 200자:', resultsString.substring(0, 200));
          
          results = JSON.parse(resultsString);
          console.log('파싱 성공! results 타입:', typeof results);
          console.log('파싱 성공! results 길이:', Array.isArray(results) ? results.length : '배열이 아님');
          
          if (Array.isArray(results) && results.length > 0) {
            console.log('첫 번째 결과의 키들:', Object.keys(results[0]));
            console.log('첫 번째 결과 샘플:', JSON.stringify(results[0]).substring(0, 200));
          }
        } catch (parseError) {
          console.error('results JSON 파싱 실패:', parseError.message);
          console.error('파싱 실패한 원본 데이터:', e.parameters.results);
          results = [];
        }
      } else {
        console.log('results 파라미터가 없음');
        results = [];
      }
    } else {
      console.error('parameters가 비어있거나 없음');
      console.log('e.postData도 확인:', e.postData);
      throw new Error('요청 데이터가 없습니다. parameters: ' + JSON.stringify(e.parameters));
    }
    
    console.log('최종 키워드:', keyword);
    console.log('최종 결과 개수:', Array.isArray(results) ? results.length : 'Array가 아님');
    
    if (!Array.isArray(results) || results.length === 0) {
      console.error('검색 결과 데이터가 없음:', results);
      throw new Error('검색 결과 데이터가 없습니다. 키워드: ' + keyword + ', results: ' + JSON.stringify(results));
    }
    
    // Google Sheets 접근
    const sheetName = `네이버지도_${keyword}_${new Date().toLocaleDateString('ko-KR').replace(/\./g, '-')}`;
    const spreadsheet = SpreadsheetApp.create(sheetName);
    const sheet = spreadsheet.getActiveSheet();
    
    // 헤더 설정
    const headers = [
      '순위', '장소명', '카테고리', '주소', '영업상태', 
      '영업시간', '평점', '리뷰수', '네이버페이', '예약가능', 
      '기타정보', '검색키워드', '크롤링시간'
    ];
    
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    
    // 헤더 스타일링
    const headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setBackground('#4285f4');
    headerRange.setFontColor('#ffffff');
    headerRange.setFontWeight('bold');
    headerRange.setHorizontalAlignment('center');
    
    // 데이터 파싱 및 저장
    const timestamp = new Date().toLocaleString('ko-KR');
    const rows = [];
    
    results.forEach((result, index) => {
      const text = result.text || result.name || '';
      
      // 텍스트에서 정보 추출
      const rank = index + 1;
      const placeName = extractPlaceName(text);
      const category = extractCategory(text);
      const address = extractAddress(text);
      const businessStatus = extractBusinessStatus(text);
      const businessHours = extractBusinessHours(text);
      const rating = extractRating(text);
      const reviewCount = extractReviewCount(text);
      const naverPay = text.includes('네이버페이') ? 'O' : '';
      const reservation = text.includes('예약') || text.includes('톡톡') ? 'O' : '';
      const otherInfo = extractOtherInfo(text);
      
      rows.push([
        rank, placeName, category, address, businessStatus,
        businessHours, rating, reviewCount, naverPay, reservation,
        otherInfo, keyword, timestamp
      ]);
    });
    
    // 데이터 행 추가
    if (rows.length > 0) {
      const dataRange = sheet.getRange(2, 1, rows.length, headers.length);
      dataRange.setValues(rows);
      
      // 자동 폭 조정
      sheet.autoResizeColumns(1, headers.length);
      
      // 교대로 색상 적용
      for (let i = 0; i < rows.length; i++) {
        if (i % 2 === 1) {
          sheet.getRange(i + 2, 1, 1, headers.length).setBackground('#f8f9fa');
        }
      }
    }
    
    // 성공 응답
    const response = {
      status: 'success',
      message: `${results.length}개의 검색 결과가 성공적으로 저장되었습니다.`,
      sheetName: sheetName,
      sheetUrl: spreadsheet.getUrl(),
      itemCount: results.length,
      timestamp: timestamp
    };
    
    console.log('응답 데이터:', response);
    
    return ContentService
      .createTextOutput(JSON.stringify(response))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    console.error('처리 오류:', error);
    
    const errorResponse = {
      status: 'error',
      message: error.message || '알 수 없는 오류가 발생했습니다.',
      timestamp: new Date().toISOString()
    };
    
    return ContentService
      .createTextOutput(JSON.stringify(errorResponse))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// 텍스트에서 장소명 추출
function extractPlaceName(text) {
  // 첫 번째 단어들을 장소명으로 추정
  const matches = text.match(/^[^가-힣]*([가-힣\s\w\-\.]+)/);
  if (matches && matches[1]) {
    return matches[1].trim().split(/\s+(예약|네이버페이|톡톡|광고|영업|별점|리뷰)/)[0];
  }
  return text.substring(0, 20);
}

// 카테고리 추출
function extractCategory(text) {
  const categories = ['한식', '중식', '일식', '양식', '카페', '베이커리', '치킨', '피자', '분식', '냉면', '갈비', '삼겹살', 
                     '스테이크', '이자카야', '술집', '바', '공방', '미용실', '병원', '약국', '은행'];
  
  for (const category of categories) {
    if (text.includes(category)) {
      return category;
    }
  }
  
  // 특정 패턴으로 카테고리 추출
  const categoryMatch = text.match(/(한식|중식|일식|양식|카페|음식|요리|[가-힣]+점|[가-힣]+집)/);
  return categoryMatch ? categoryMatch[1] : '';
}

// 주소 추출
function extractAddress(text) {
  const addressMatch = text.match(/(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s+[가-힣\s\d]+/);
  return addressMatch ? addressMatch[0] : '';
}

// 영업 상태 추출
function extractBusinessStatus(text) {
  if (text.includes('영업 중')) return '영업 중';
  if (text.includes('영업 종료')) return '영업 종료';
  if (text.includes('휴무')) return '휴무';
  return '';
}

// 영업 시간 추출
function extractBusinessHours(text) {
  const hoursMatch = text.match(/(\d{1,2}:\d{2}에 영업 [시작종료])/);
  return hoursMatch ? hoursMatch[1] : '';
}

// 평점 추출
function extractRating(text) {
  const ratingMatch = text.match(/별점(\d+\.?\d*)/);
  return ratingMatch ? ratingMatch[1] : '';
}

// 리뷰 수 추출
function extractReviewCount(text) {
  const reviewMatch = text.match(/리뷰\s*(\d+\+?|\d+)/);
  return reviewMatch ? reviewMatch[1] : '';
}

// 기타 정보 추출
function extractOtherInfo(text) {
  const info = [];
  if (text.includes('미쉐린')) info.push('미쉐린');
  if (text.includes('광고')) info.push('광고');
  if (text.includes('새로오픈')) info.push('새로오픈');
  return info.join(', ');
}

// 시트에 데이터 저장
function saveToSheet(data) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet()
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    const sheetName = `네이버검색_${data.keyword}_${timestamp}`
    
    // 새 시트 생성
    const sheet = ss.insertSheet(sheetName)
    
    // 헤더 설정 (더 상세한 정보)
    const headers = [
      '순위', '업체명', '카테고리', '주소', '영업상태', '리뷰수', '별점', 
      '네이버페이', '예약가능', '원본텍스트'
    ]
    sheet.getRange(1, 1, 1, headers.length).setValues([headers])
    
    // 헤더 스타일링
    const headerRange = sheet.getRange(1, 1, 1, headers.length)
    headerRange.setBackground('#4285f4')
    headerRange.setFontColor('white')
    headerRange.setFontWeight('bold')
    headerRange.setHorizontalAlignment('center')
    
    // 데이터 행 추가
    if (data.results && data.results.length > 0) {
      const rows = data.results.map(result => [
        result.rank || '',
        result.name || '',
        result.category || '',
        result.address || '',
        result.status || '',
        result.reviews || '',
        result.rating || '',
        result.naverPay || '',
        result.reservation || '',
        result.raw_text || ''
      ])
      
      sheet.getRange(2, 1, rows.length, headers.length).setValues(rows)
      
      // 데이터 영역 스타일링
      const dataRange = sheet.getRange(2, 1, rows.length, headers.length)
      dataRange.setBorder(true, true, true, true, true, true)
      
      // 순위 열 가운데 정렬
      sheet.getRange(2, 1, rows.length, 1).setHorizontalAlignment('center')
      
      // 네이버페이, 예약가능 열 가운데 정렬
      sheet.getRange(2, 8, rows.length, 2).setHorizontalAlignment('center')
    }
    
    // 열 너비 자동 조정
    for (let i = 1; i <= headers.length; i++) {
      sheet.autoResizeColumn(i)
      
      // 원본텍스트 열은 좀 더 넓게
      if (i === headers.length) {
        sheet.setColumnWidth(i, 300)
      }
    }
    
    return {
      success: true,
      sheetName: sheetName,
      url: ss.getUrl(),
      dataCount: data.results?.length || 0
    }
    
  } catch (error) {
    Logger.log('시트 저장 오류: ' + error.toString())
    throw error
  }
} 