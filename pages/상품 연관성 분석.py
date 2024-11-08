import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import itertools

def run_product_analysis():
    st.title('상품 연관성 분석 v1.1')

    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

    if uploaded_file is not None:
        # 데이터 읽기 및 전처리
        data = pd.read_csv(uploaded_file)
        data['총 주문 금액'] = pd.to_numeric(data['총 주문 금액'], errors='coerce')
        data = data[data['총 주문 금액'] > 0]
        data = data.sort_values(by=['일반/업셀 구분'], ascending=False)
        
        if '상품 옵션' not in data.columns:
            data['상품 옵션'] = ''
        else:
            data['상품 옵션'] = data['상품 옵션'].fillna('')
        
        # '상품_식별자' 컬럼 생성
        data['상품_식별자'] = data['상품명'] + ' - ' + data['상품 옵션']

        # 상품명과 상품 옵션으로 그룹화하여 데이터 집계
        aggregated_data = data.groupby(['상품명', '상품 옵션']).agg({
            '총 주문 금액': 'sum',
            '일반/업셀 구분': 'first'  # 각 그룹의 첫 번째 값 사용
        }).reset_index()

        # 상품 식별자 생성 (상품명과 옵션 조합)
        aggregated_data['상품_식별자'] = aggregated_data['상품명'] + ' - ' + aggregated_data['상품 옵션']

        # 상품 식별자와 표시 이름 생성
        product_display_names = {
            row['상품_식별자']: f"{row['상품명']} ({row['상품 옵션']})" if row['상품 옵션'] else row['상품명']
            for _, row in aggregated_data.iterrows()
        }

        # 나머지 코드는 그대로 유지...

        # 2. 업셀 상품 분석
        st.header("2. 업셀 상품 분석")

        order_groups_upsell = data.groupby('주문번호').apply(lambda x: {
            'general': x[x['일반/업셀 구분'] == '일반 상품']['상품_식별자'].tolist(),
            'upsell': x[x['일반/업셀 구분'] == '업셀 상품']['상품_식별자'].tolist()
        }).reset_index(name='products')

        # 나머지 코드는 그대로 유지...

    else:
        st.write("CSV 파일을 업로드해주세요.")

if __name__ == "__main__":
    run_product_analysis()