import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import itertools

def run_product_analysis():
    st.title('상품 연관성 분석')

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

        # 1. 전체 상품 조합 분석
        st.header("1. 전체 상품 조합 분석")

        order_groups = data.groupby('주문번호')['상품_식별자'].apply(list).reset_index()

        def get_product_combinations(products):
            return list(itertools.combinations(set(products), 2))

        all_combinations = []
        for _, row in order_groups.iterrows():
            all_combinations.extend(get_product_combinations(row['상품_식별자']))

        combination_counts = Counter(all_combinations)

        product_related_counts = Counter()
        for (prod1, prod2), count in combination_counts.items():
            product_related_counts[prod1] += count
            product_related_counts[prod2] += count

        product_list = [product for product, _ in product_related_counts.most_common()]

        # 상품명과 옵션을 조합하여 드롭다운에 표시할 텍스트 생성
        product_display_names = {
            row['상품_식별자']: f"{row['상품명']} ({row['상품 옵션']})" if row['상품 옵션'] else row['상품명']
            for _, row in data.drop_duplicates(subset=['상품_식별자']).iterrows()
        }

        dropdown_options = [product_display_names[product] for product in product_list]

        selected_product_display_name = st.selectbox("상품을 선택하세요 (전체 상품):", dropdown_options)

        selected_product_identifier = next(
            (identifier for identifier, display_name in product_display_names.items()
             if display_name == selected_product_display_name),
            selected_product_display_name
        )

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
                df_related = df_related.merge(data[['상품_식별자', '상품명', '상품 옵션']].drop_duplicates(), on='상품_식별자', how='left')
                df_display = df_related[['상품명', '상품 옵션', '함께 구매된 횟수']].head(10)
                st.dataframe(df_display)

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(df_display['상품명'] + ' (' + df_display['상품 옵션'] + ')', df_display['함께 구매된 횟수'])
                ax.set_xticklabels(df_display['상품명'] + ' (' + df_display['상품 옵션'] + ')', rotation=45, ha='right')
                ax.set_xlabel('상품명 (옵션)')
                ax.set_ylabel('함께 구매된 횟수')
                ax.set_title(f'{selected_product_display_name}와(과) 함께 구매된 상위 10개 상품')
                st.pyplot(fig)
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

        product_related_counts_upsell = Counter()
        for (general_prod, upsell_prod), count in combination_counts_upsell.items():
            product_related_counts_upsell[general_prod] += count

        product_list_upsell = [product for product, _ in product_related_counts_upsell.most_common()]

        product_display_names_upsell = {
            row['상품_식별자']: f"{row['상품명']} ({row['상품 옵션']})" if row['상품 옵션'] else row['상품명']
            for _, row in data[data['일반/업셀 구분'] == '일반 상품'].drop_duplicates(subset=['상품_식별자']).iterrows()
        }

        dropdown_options_upsell = [product_display_names_upsell[product] for product in product_list_upsell]

        selected_product_display_name_upsell = st.selectbox("상품을 선택하세요 (업셀 상품 분석):", dropdown_options_upsell)

        selected_product_identifier_upsell = next(
            (identifier for identifier, display_name in product_display_names_upsell.items()
             if display_name == selected_product_display_name_upsell),
            selected_product_display_name_upsell
        )

        def find_related_upsell_products(product_identifier):
            related = [(upsell_prod, count) for (general_prod, upsell_prod), count in combination_counts_upsell.items()
                       if general_prod == product_identifier]
            return sorted(related, key=lambda x: x[1], reverse=True)

        if selected_product_identifier_upsell:
            related_upsell_products = find_related_upsell_products(selected_product_identifier_upsell)
            st.write(f"{selected_product_display_name_upsell}와(과) 함께 구매된 업셀 상품:")
            
            if related_upsell_products:
                df_related_upsell = pd.DataFrame(related_upsell_products, columns=['상품_식별자', '함께 구매된 횟수'])
                df_related_upsell = df_related_upsell.merge(data[['상품_식별자', '상품명', '상품 옵션']].drop_duplicates(), on='상품_식별자', how='left')
                df_display_upsell = df_related_upsell[['상품명', '상품 옵션', '함께 구매된 횟수']].head(10)
                st.dataframe(df_display_upsell)

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(df_display_upsell['상품명'] + ' (' + df_display_upsell['상품 옵션'] + ')', df_display_upsell['함께 구매된 횟수'])
                ax.set_xticklabels(df_display_upsell['상품명'] + ' (' + df_display_upsell['상품 옵션'] + ')', rotation=45, ha='right')
                ax.set_xlabel('상품명 (옵션)')
                ax.set_ylabel('함께 구매된 횟수')
                ax.set_title(f'{selected_product_display_name_upsell}와(과) 함께 구매된 상위 10개 업셀 상품')
                st.pyplot(fig)
            else:
                st.write("이 상품과 함께 구매된 업셀 상품이 없습니다.")

    else:
        st.write("CSV 파일을 업로드해주세요.")

if __name__ == "__main__":
    run_product_analysis()