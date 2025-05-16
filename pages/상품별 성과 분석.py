import streamlit as st
import pandas as pd

# 제목 설정
st.title('상품 구매 성과 분석')

# 파일 업로더 생성
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

if uploaded_file is not None:
    # 데이터 읽기
    data = pd.read_csv(uploaded_file)

    # 드롭다운 메뉴 생성
    filter_option = st.selectbox("보고 싶은 데이터를 선택하세요:", ["전체 상품", "일반 상품", "업셀 상품"])

    # 필터링 조건 설정
    if filter_option == "일반 상품":
        filtered_data = data[data['일반/업셀 구분'] == '일반 상품']
    elif filter_option == "업셀 상품":
        filtered_data = data[data['일반/업셀 구분'] == '업셀 상품']
    else:
        filtered_data = data  # 전체 상품

    if not filtered_data.empty:
        # 각 행의 매출 계산
        filtered_data['합계 매출'] = filtered_data['구매 수량'] * filtered_data['상품 단가']

        # 상품 코드, 상품명별로 구매 수량 합계, 단가 목록, 합계 매출을 기준으로 요약
        summary = filtered_data.groupby(['상품 코드', '상품명'], as_index=False).agg({
            '구매 수량': 'sum',
            '상품 단가': lambda x: ', '.join(map(str, sorted(x.unique()))),  # 단가 목록 표시
            '합계 매출': 'sum'  # 합계 매출 합산
        })

        # 요약 결과 표시
        st.write(f"### {filter_option} 구매 성과 요약")
        st.write(summary)

        # 선택 옵션: 데이터 다운로드 제공
        csv_data = summary.to_csv(index=False).encode('utf-8')
        st.download_button("CSV 파일로 다운로드", csv_data, "purchase_performance_summary.csv", "text/csv")
    else:
        st.write(f"{filter_option} 데이터가 없습니다.")
else:
    st.write("CSV 파일을 업로드하여 데이터를 분석해보세요.")
