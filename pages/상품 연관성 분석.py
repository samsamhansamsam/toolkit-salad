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

        # 1. 전체 상품 조합 분석
        st.header("1. 전체 상품 조합 분석")

        order_groups = data.groupby('주문번호')['상품명'].apply(list).reset_index()

        def get_product_combinations(products):
            return list(itertools.combinations(set(products), 2))

        all_combinations = []
        for _, row in order_groups.iterrows():
            all_combinations.extend(get_product_combinations(row['상품명']))

        combination_counts = Counter(all_combinations)

        def find_related_products(product_name):
            related = []
            for (prod1, prod2), count in combination_counts.items():
                if prod1 == product_name:
                    related.append((prod2, count))
                elif prod2 == product_name:
                    related.append((prod1, count))
            return sorted(related, key=lambda x: x[1], reverse=True)

        if selected_product_identifier:
            selected_product_name = selected_product_identifier.split(' - ')[0]  # 상품명 추출
            related_products = find_related_products(selected_product_name)
            st.write(f"{selected_product_display_name}와(과) 함께 구매된 상품:")
            
            if related_products:
                df_related = pd.DataFrame(related_products, columns=['상품명', '함께 구매된 횟수'])
                st.dataframe(df_related.head(10))
            else:
                st.write("이 상품과 함께 구매된 다른 상품이 없습니다.")

        # 2. 업셀 상품 분석
        st.header("2. 업셀 상품 분석")

        order_groups_upsell = data.groupby('주문번호').apply(lambda x: {
            'general': x[x['일반/업셀 구분'] == '일반 상품']['상품_식별자'].tolist(),
            'upsell': x[x['일반/업셀 구분'] == '업셀 상품']['상품_식별자'].tolist()
        }).reset_index(name='products')

        def get_product_combinations_upsell(products):
            general = products.get('general', [])
            upsell = products.get('upsell', [])
            return list(itertools.product(general, upsell))

        all_combinations_upsell = []
        for _, row in order_groups_upsell.iterrows():
            all_combinations_upsell.extend(get_product_combinations_upsell(row['products']))

        combination_counts_upsell = Counter(all_combinations_upsell)

        def find_related_upsell_products(product_identifier):
            related = [(upsell_prod, count) for (general_prod, upsell_prod), count in combination_counts_upsell.items()
                       if general_prod == product_identifier]
            return sorted(related, key=lambda x: x[1], reverse=True)

        if selected_product_identifier:
            related_upsell_products = find_related_upsell_products(selected_product_identifier)
            st.write(f"{selected_product_display_name}와(과) 함께 구매된 업셀 상품:")
            
            if related_upsell_products:
                df_related_upsell = pd.DataFrame(related_upsell_products, columns=['상품_식별자', '함께 구매된 횟수'])
                df_related_upsell = df_related_upsell.merge(data[['상품_식별자', '상품 코드', '상품명', '상품 옵션']].drop_duplicates(), on='상품_식별자', how='left')
                df_display_upsell = df_related_upsell[['상품 코드', '상품명', '상품 옵션', '함께 구매된 횟수']].head(10)
                st.dataframe(df_display_upsell)

            else:
                st.write("이 상품과 함께 구매된 업셀 상품이 없습니다.")

    else:
        st.write("CSV 파일을 업로드해주세요.")

if __name__ == "__main__":
    run_product_analysis()