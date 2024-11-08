import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import itertools

def run_product_analysis():
    st.title('상품 연관성 분석 v1.3')

    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

    if uploaded_file is not None:
        # 데이터 읽기 및 전처리
        data = pd.read_csv(uploaded_file)
        data['총 주문 금액'] = pd.to_numeric(data['총 주문 금액'], errors='coerce')
        data['구매 수량'] = pd.to_numeric(data['구매 수량'], errors='coerce')
        data = data[data['총 주문 금액'] > 0]
        data = data.sort_values(by=['일반/업셀 구분'], ascending=False)
        
        if '상품 옵션' not in data.columns:
            data['상품 옵션'] = ''
        else:
            data['상품 옵션'] = data['상품 옵션'].fillna('')
        
        # 상품명과 상품 옵션으로 그룹화하여 데이터 집계
        aggregated_data = data.groupby(['상품명', '상품 옵션']).agg({
            '총 주문 금액': 'sum',
            '일반/업셀 구분': 'first',
            '주문번호': 'count',
            '구매 수량': 'sum'  # 총 구매 수량 추가
        }).reset_index()

        # 단가 계산 (총 주문 금액 / 총 구매 수량) 및 반올림
        aggregated_data['단가'] = (aggregated_data['총 주문 금액'] / aggregated_data['구매 수량']).round().astype(int)

        # 상품 식별자 생성 (상품명과 옵션 조합)
        aggregated_data['상품_식별자'] = aggregated_data['상품명'] + ' - ' + aggregated_data['상품 옵션']

        # 상품 식별자와 표시 이름 생성 (단가 포함)
        product_display_names = {
            row['상품_식별자']: f"{row['상품명']} ({row['상품 옵션']}) - {row['단가']:,}원" if row['상품 옵션'] else f"{row['상품명']} - {row['단가']:,}원"
            for _, row in aggregated_data.iterrows()
        }

        # 상품명을 기준으로 정렬
        sorted_product_display_names = dict(sorted(product_display_names.items(), key=lambda x: x[1]))

        dropdown_options = list(sorted_product_display_names.values())

        # 검색 기능 추가
        search_term = st.text_input("상품 검색:", "")
        filtered_options = [option for option in dropdown_options if search_term.lower() in option.lower()]

        selected_product_display_name = st.selectbox("상품을 선택하세요:", filtered_options)

        selected_product_identifier = next(
            (identifier for identifier, display_name in sorted_product_display_names.items()
            if display_name == selected_product_display_name),
            None
        )

        # 1. 선택한 상품의 상품명과 단가 표시
        if selected_product_identifier:
            selected_product = aggregated_data[aggregated_data['상품_식별자'] == selected_product_identifier].iloc[0]
            st.write(f"선택한 상품: {selected_product['상품명']}")
            st.write(f"단가: {selected_product['단가']:,}원")
            st.write(f"총 구매 수량: {selected_product['구매 수량']:,}개")  # 총 구매 수량 추가

        # 2. 상품 단가와 총 구매 수량을 오른쪽 끝에 추가
        st.header("상품 목록")
        display_data = aggregated_data[['상품명', '상품 옵션', '단가', '구매 수량']].copy()
        display_data['단가'] = display_data['단가'].apply(lambda x: f"{x:,}원")
        display_data['구매 수량'] = display_data['구매 수량'].apply(lambda x: f"{x:,}개")
        
        # 3. 선택한 상품의 단가와 다른 상품들의 단가 합계 계산
        if selected_product_identifier:
            selected_price = selected_product['단가']
            display_data['합계 단가'] = aggregated_data['단가'] + selected_price
            display_data['합계 단가'] = display_data['합계 단가'].apply(lambda x: f"{x:,}원")

        st.dataframe(display_data)

    else:
        st.write("CSV 파일을 업로드해주세요.")

if __name__ == "__main__":
    run_product_analysis()