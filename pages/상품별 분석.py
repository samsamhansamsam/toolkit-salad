import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from collections import Counter
import itertools
import os
import matplotlib.font_manager as fm  # 폰트 관련 용도 as fm

@st.cache_data
def fontRegistered():
    font_dirs = [os.getcwd() + '/customFonts']
    font_files = fm.findSystemFonts(fontpaths=font_dirs)

    for font_file in font_files:
        fm.fontManager.addfont(font_file)
    fm._load_fontmanager(try_read_cache=False)


def run_product_analysis():
    st.title('상품 연관성 분석')

    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

    fontRegistered()
    fontNames = [f.name for f in fm.fontManager.ttflist]
    fontname = st.selectbox("폰트 선택", unique(fontNames))

    if uploaded_file is not None:
        # 데이터 읽기 및 전처리
        data = pd.read_csv(uploaded_file)
        data['총 주문 금액'] = pd.to_numeric(data['총 주문 금액'], errors='coerce')
        data = data[data['총 주문 금액'] > 0]
        data = data.sort_values(by=['일반/업셀 구분'], ascending=False)
        
        # '상품 옵션' 열이 없거나 NaN인 경우 빈 문자열로 채우기
        if '상품 옵션' not in data.columns:
            data['상품 옵션'] = ''
        else:
            data['상품 옵션'] = data['상품 옵션'].fillna('')
        
        data = data.drop_duplicates(subset=['주문번호', '상품 코드', '상품 옵션'], keep='last')

        # 상품 코드와 옵션을 결합하여 고유 상품 식별자 생성
        data['상품_식별자'] = data['상품 코드'] + '_' + data['상품 옵션']

        # 주문별 상품 그룹화
        order_groups = data.groupby('주문번호')['상품_식별자'].apply(list).reset_index()

        # 상품 조합 생성 및 빈도 계산
        def get_product_combinations(products):
            return list(itertools.combinations(set(products), 2))

        all_combinations = []
        for _, row in order_groups.iterrows():
            all_combinations.extend(get_product_combinations(row['상품_식별자']))

        combination_counts = Counter(all_combinations)

        # 각 상품과 연관된 구매 횟수 계산
        product_related_counts = Counter()
        for (prod1, prod2), count in combination_counts.items():
            product_related_counts[prod1] += count
            product_related_counts[prod2] += count

        # 상품 목록 생성 (연관 구매 횟수 순으로 정렬)
        product_list = [product for product, _ in product_related_counts.most_common()]

        # 상품명과 옵션을 조합하여 드롭다운에 표시할 텍스트 생성
        product_display_names = {
            identifier: f"{row['상품명']} ({row['상품 옵션']})" if row['상품 옵션'] else row['상품명']
            for identifier, row in data.set_index('상품_식별자')[['상품명', '상품 옵션']].iterrows()
        }

        # 드롭다운 메뉴에 표시할 리스트 생성
        dropdown_options = [product_display_names[product] for product in product_list]

        # 상품 선택 위젯
        selected_product_display_name = st.selectbox("상품을 선택하세요:", dropdown_options)

        # 선택된 상품의 식별자를 찾기
        selected_product_identifier = next(
            identifier for identifier, display_name in product_display_names.items()
            if display_name == selected_product_display_name
        )

        # 함께 구매된 상품 찾기 함수
        def find_related_products(product_identifier):
            related = []
            for (prod1, prod2), count in combination_counts.items():
                if prod1 == product_identifier:
                    related.append((prod2, count))
                elif prod2 == product_identifier:
                    related.append((prod1, count))
            return sorted(related, key=lambda x: x[1], reverse=True)

        # 선택된 상품과 함께 구매된 상품 표시
        if selected_product_identifier:
            related_products = find_related_products(selected_product_identifier)
            st.write(f"{selected_product_display_name}와(과) 함께 구매된 상품:")
            
            if related_products:
                # 데이터프레임 생성
                df_related = pd.DataFrame(related_products, columns=['상품_식별자', '함께 구매된 횟수'])
                
                # 상품 코드와 옵션 분리
                df_related[['상품 코드', '상품 옵션']] = df_related['상품_식별자'].str.split('_', n=1, expand=True)
                
                # 상품명 추가
                df_related = df_related.merge(data[['상품 코드', '상품명']].drop_duplicates(), on='상품 코드', how='left')
                
                # 상위 10개 상품만 표시
                df_display = df_related[['상품명', '상품 옵션', '함께 구매된 횟수']].head(10)
                st.dataframe(df_display)

                # 막대 그래프로 시각화
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(df_display['상품명'] + ' (' + df_display['상품 옵션'] + ')', df_display['함께 구매된 횟수'])
                ax.set_xticklabels(df_display['상품명'] + ' (' + df_display['상품 옵션'] + ')', rotation=45, ha='right')
                ax.set_xlabel('상품명 (옵션)')
                ax.set_ylabel('함께 구매된 횟수')
                ax.set_title(f'{selected_product_display_name}와(과) 함께 구매된 상위 10개 상품')
                st.pyplot(fig)
            else:
                st.write("이 상품과 함께 구매된 다른 상품이 없습니다.")

    else:
        st.write("CSV 파일을 업로드해주세요.")

if __name__ == "__main__":
    run_product_analysis()