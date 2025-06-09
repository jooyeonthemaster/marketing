/**
 * 네이버 지도 크롤링 결과를 Google Sheets에 저장하는 Google Apps Script
 * 2024년 최신 버전 - CORS 및 안정성 개선
 */

// 스프레드시트 ID (새로운 스프레드시트를 만들고 URL에서 ID를 복사하세요)
const SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'; // 여기에 실제 스프레드시트 ID를 입력하세요

/**
 * POST 요청 처리 함수
 */
function doPost(e) {
  try {
    // CORS 헤더 설정
    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json'
    };
    
    // 파라미터에서 데이터 가져오기
    let data;
    if (e.parameter.data) {
      data = JSON.parse(e.parameter.data);
    } else if (e.postData && e.postData.contents) {
      data = JSON.parse(e.postData.contents);
    } else {
      throw new Error('데이터가 없습니다');
    }
    
    console.log('받은 데이터:', data);
    
    // 스프레드시트에 저장
    const result = saveToSheet(data);
    
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: '데이터가 성공적으로 저장되었습니다',
        rowsAdded: result.rowsAdded,
        sheetName: result.sheetName
      }))
      .setMimeType(ContentService.MimeType.JSON)
      .setHeaders(headers);
      
  } catch (error) {
    console.error('오류 발생:', error);
    
    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json'
    };
    
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON)
      .setHeaders(headers);
  }
}

/**
 * GET 요청 처리 함수 (테스트용)
 */
function doGet(e) {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
  
  return ContentService
    .createTextOutput(JSON.stringify({
      message: '네이버 지도 크롤러 Google Apps Script가 정상 작동 중입니다!',
      timestamp: new Date().toISOString()
    }))
    .setMimeType(ContentService.MimeType.JSON)
    .setHeaders(headers);
}

/**
 * 스프레드시트에 데이터 저장
 */
function saveToSheet(data) {
  try {
    // 스프레드시트 열기
    const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
    
    // 현재 날짜로 시트명 생성
    const today = new Date();
    const sheetName = `네이버지도_${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    
    // 시트 가져오기 또는 생성
    let sheet = spreadsheet.getSheetByName(sheetName);
    if (!sheet) {
      sheet = spreadsheet.insertSheet(sheetName);
      
      // 헤더 추가
      const headers = [
        '순위', '업체명', '카테고리', '주소', '영업상태', 
        '리뷰수', '별점', '네이버페이', '예약가능', '원본텍스트'
      ];
      
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      
      // 헤더 스타일링
      const headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setBackground('#4285f4');
      headerRange.setFontColor('white');
      headerRange.setFontWeight('bold');
      headerRange.setBorder(true, true, true, true, true, true);
    }
    
    // 데이터 준비
    const rows = [];
    
    data.results.forEach((place, index) => {
      // 상세 정보 파싱
      const details = parseDetailedInfo(place.raw_text);
      
      const row = [
        place.rank || (index + 1),           // 순위
        place.name || '',                    // 업체명
        details.category || '',              // 카테고리
        details.address || '',               // 주소
        details.businessStatus || '',        // 영업상태
        details.reviewCount || '',           // 리뷰수
        details.rating || '',                // 별점
        details.naverPay || '',              // 네이버페이
        details.reservationAvailable || '',  // 예약가능
        place.raw_text || ''                 // 원본텍스트
      ];
      
      rows.push(row);
    });
    
    // 데이터 추가
    if (rows.length > 0) {
      const lastRow = sheet.getLastRow();
      const startRow = lastRow + 1;
      
      sheet.getRange(startRow, 1, rows.length, 10).setValues(rows);
      
      // 데이터 스타일링
      const dataRange = sheet.getRange(startRow, 1, rows.length, 10);
      dataRange.setBorder(true, true, true, true, true, true);
      
      // 자동 열 폭 조정
      sheet.autoResizeColumns(1, 10);
    }
    
    console.log(`${rows.length}개 행이 ${sheetName} 시트에 저장됨`);
    
    return {
      rowsAdded: rows.length,
      sheetName: sheetName
    };
    
  } catch (error) {
    console.error('시트 저장 오류:', error);
    throw error;
  }
}

/**
 * 원본 텍스트에서 상세 정보 파싱
 */
function parseDetailedInfo(rawText) {
  if (!rawText) return {};
  
  const details = {};
  
  // 카테고리 추출 (일반적으로 업체명 다음에 나옴)
  const categoryMatch = rawText.match(/(?:네이버페이|예약|톡톡)?\s*([가-힣]+(?:점|관|원|샵|카페|식당|병원|약국|마트|편의점)?)\s*(?:광고|영업|리뷰)/);
  if (categoryMatch) {
    details.category = categoryMatch[1];
  }
  
  // 주소 추출
  const addressMatch = rawText.match(/(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s+[가-힣구시군\s]+[동면읍로길]\s*[\d-]*[번지호실]?/);
  if (addressMatch) {
    details.address = addressMatch[0];
  }
  
  // 영업상태 추출
  if (rawText.includes('영업 종료')) {
    details.businessStatus = '영업 종료';
  } else if (rawText.includes('영업 시작')) {
    details.businessStatus = '영업 시작';
  } else if (rawText.includes('영업중')) {
    details.businessStatus = '영업중';
  }
  
  // 리뷰수 추출
  const reviewMatch = rawText.match(/리뷰\s+(\d+(?:,\d+)*|\d+\+?)/);
  if (reviewMatch) {
    details.reviewCount = reviewMatch[1];
  }
  
  // 별점 추출
  const ratingMatch = rawText.match(/별점?\s*([0-9.]+)/);
  if (ratingMatch) {
    details.rating = ratingMatch[1];
  }
  
  // 네이버페이 확인
  if (rawText.includes('네이버페이')) {
    details.naverPay = 'O';
  }
  
  // 예약 가능 확인
  if (rawText.includes('예약')) {
    details.reservationAvailable = 'O';
  }
  
  return details;
} 