import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import itertools

def run_product_analysis():
    st.title('상품 연관성 분석')

    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)

        # 주문별 상품 그룹화
        order_groups = data.groupby('주문번호')['상품명'].apply(list).reset_index()

        # 상품 조합 생성 및 빈도 계산
        def get_product_combinations(products):
            return list(itertools.combinations(set(products), 2))

        all_combinations = []
        for _, row in order_groups.iterrows():
            all_combinations.extend(get_product_combinations(row['상품명']))

        combination_counts = Counter(all_combinations)

        # 상품 목록 생성 (판매량 순으로 정렬)
        product_sales = data['상품명'].value_counts()
        product_list = product_sales.index.tolist()

        # 상품 선택 위젯
        selected_product = st.selectbox("상품을 선택하세요:", product_list)

        # 함께 구매된 상품 찾기 함수
        def find_related_products(product_name):
            related = [(prod, count) for (prod1, prod2), count in combination_counts.items()
                       if prod1 == product_name or prod2 == product_name]
            related = [(prod1 if prod2 == product_name else prod2, count) for prod1, prod2, count in related]
            return sorted(related, key=lambda x: x[1], reverse=True)

        # 선택된 상품과 함께 구매된 상품 표시
        if selected_product:
            related_products = find_related_products(selected_product)
            st.write(f"{selected_product}와(과) 함께 구매된 상품:")
            
            # 데이터프레임 생성
            df_related = pd.DataFrame(related_products, columns=['상품명', '함께 구매된 횟수'])
            
            # 상위 10개 상품만 표시
            st.dataframe(df_related.head(10))

            # 막대 그래프로 시각화
            plt.figure(figsize=(10, 6))
            plt.bar(df_related['상품명'].head(10), df_related['함께 구매된 횟수'].head(10))
            plt.xticks(rotation=45, ha='right')
            plt.xlabel('상품명')
            plt.ylabel('함께 구매된 횟수')
            plt.title(f'{selected_product}와(과) 함께 구매된 상위 10개 상품')
            st.pyplot(plt)

    else:
        st.write("CSV 파일을 업로드해주세요.")

if __name__ == "__main__":
    run_product_analysis()