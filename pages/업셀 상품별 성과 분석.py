import streamlit as st
import pandas as pd

# 제목 설정
st.title('업셀 상품 구매 성과 분석')

# 파일 업로더 생성
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

if uploaded_file is not None:
    # 데이터 읽기
    data = pd.read_csv(uploaded_file)

    # 업셀 상품 필터링
    upsell_data = data[data['일반/업셀 구분'] == '업셀 상품']
    
    if not upsell_data.empty:
        # 각 행의 매출 계산
        upsell_data['합계 매출'] = upsell_data['구매 수량'] * upsell_data['상품 단가']
        
        # 상품 코드, 상품명, 구매 수량 합계, 첫 단가, 합계 매출을 기준으로 요약
        upsell_summary = upsell_data.groupby(['상품 코드', '상품명'], as_index=False).agg({
            '구매 수량': 'sum',
            '상품 단가': 'first',  # 첫 번째 단가 표시
            '합계 매출': 'sum'      # 합계 매출 합산
        })

        # 요약 결과 표시
        st.write("### 업셀 상품 구매 성과 요약")
        st.write(upsell_summary)

        # 선택 옵션: 데이터 다운로드 제공
        csv_data = upsell_summary.to_csv(index=False).encode('utf-8')
        st.download_button("CSV 파일로 다운로드", csv_data, "upsell_performance_summary.csv", "text/csv")
    else:
        st.write("업로드된 데이터에 업셀 상품이 없습니다.")
else:
    st.write("CSV 파일을 업로드하여 업셀 상품의 성과를 분석해보세요.")
