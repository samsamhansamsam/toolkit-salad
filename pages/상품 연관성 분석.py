import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import itertools

def run_product_analysis():
    st.title('상품 연관성 분석 v1.0')

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
        
        data = data.drop_duplicates(subset=['주문번호', '상품 코드', '상품 옵션'], keep='last')

        # 상품 코드를 사용하여 고유 상품 식별자 생성
        data['상품_식별자'] = data['상품 코드']

        # 상품코드, 상품명, 옵션을 조합하여 드롭다운에 표시할 텍스트 생성
        product_display_names = {
            row['상품_식별자']: f"{row['상품 코드']} - {row['상품명']} ({row['상품 옵션']})" if row['상품 옵션'] else f"{row['상품 코드']} - {row['상품명']}"
            for _, row in data.drop_duplicates(subset=['상품_식별자']).iterrows()
        }

        # 상품명을 기준으로 정렬
        sorted_product_display_names = dict(sorted(product_display_names.items(), key=lambda x: x[1].split(' - ')[1]))

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

        order_groups = data.groupby('주문번호')['상품_식별자'].apply(list).reset_index()

        def get_product_combinations(products):
            return list(itertools.combinations(set(products), 2))

        all_combinations = []
        for _, row in order_groups.iterrows():
            all_combinations.extend(get_product_combinations(row['상품_식별자']))

        combination_counts = Counter(all_combinations)

        def find_related_products(product_identifier):
            related = []
            for (prod1, prod2), count in combination_counts.items():
                if prod1 == product_identifier:
                    related.append((prod2, count))
                elif prod2 == product_identifier:
                    related.append((prod1, count))
            return sorted(related, key=lambda x: x[1], reverse=True)

        if selected_product_identifier:
            related_products = find_related_products(selected_product_identifier)
            st.write(f"{selected_product_display_name}와(과) 함께 구매된 상품:")
            
            if related_products:
                df_related = pd.DataFrame(related_products, columns=['상품_식별자', '함께 구매된 횟수'])
                df_related = df_related.merge(data[['상품_식별자', '상품 코드', '상품명', '상품 옵션']].drop_duplicates(), on='상품_식별자', how='left')
                df_display = df_related[['상품 코드', '상품명', '상품 옵션', '함께 구매된 횟수']].head(10)
                st.dataframe(df_display)
                
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