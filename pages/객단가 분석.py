import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 제목 설정
st.title('객단가 및 주문별 상품 개수 분석 v1.3')

# CSV 파일 업로더
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

if uploaded_file is not None:
    # 원본 데이터 읽기: 주문번호, 총 주문 금액, 주문자 아이디, 일반/업셀 구분 등의 컬럼이 포함되어 있다고 가정
    raw_data = pd.read_csv(uploaded_file)
    
    # 총 주문 금액 전처리: 문자열 등 오류 처리 및 0원 주문(취소/환불된 주문) 제거
    raw_data['총 주문 금액'] = pd.to_numeric(raw_data['총 주문 금액'], errors='coerce')
    raw_data = raw_data[raw_data['총 주문 금액'] > 0]
    
    # ##########################
    # 기존 분석을 위한 데이터 준비: 주문번호 별 중복 제거 (업셀 주문 우선 보존)
    data = raw_data.copy()
    data = data.sort_values(by=['일반/업셀 구분'], ascending=False)  # '업셀 상품'을 우선 보존하기 위해 정렬
    data = data.drop_duplicates(subset=['주문번호'], keep='last')
    
    # ##########################
    # 1. 회원과 비회원의 주문 비중 비교
    st.write("### 1. 회원과 비회원의 주문 비중 비교")
    
    # 회원여부 컬럼 생성: 주문자 아이디가 없으면 Guest, 있으면 Member
    data['회원여부'] = data['주문자 아이디'].apply(lambda x: 'Guest' if pd.isna(x) or str(x).strip() == '' else 'Member')
    
    # 주문 건수 계산 및 비율 산출
    member_counts = data['회원여부'].value_counts()
    total_orders_member = member_counts.sum()
    member_percentages = (member_counts / total_orders_member) * 100
    
    st.write("**주문 건수:**")
    st.write(member_counts)
    st.write("**주문 비율 (%):**")
    st.write(member_percentages)
    
    # 파이 차트 시각화
    fig1, ax1 = plt.subplots()
    ax1.pie(member_counts.values, labels=member_counts.index, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    ax1.set_title('회원/비회원 주문 비중')
    st.pyplot(fig1)
    
    # ##########################
    # 2. 전체 주문 기준 객단가(총 주문 금액) 분포 분석
    st.write("### 2. 전체 주문 기준 객단가 분포")
    
    # 10,000원 단위로 범주화: 총 주문 금액을 10,000원 단위로 그룹핑하고, 200,000원 초과 값은 200,000원으로 변환
    data['금액 범주'] = (data['총 주문 금액'] // 10000) * 10000
    data['금액 범주'] = data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)
    
    # 0원부터 200,000원까지 모든 범주 설정 (빈 범주 포함)
    full_range = pd.Series([i * 10000 for i in range(21)])  # 0, 10000, ..., 200000
    order_counts = data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()
    
    st.write("**총 주문 건수 (금액 범주별):**", order_counts)
    
    # 막대그래프: 주문 건수
    plt.figure(figsize=(10, 6))
    bars = plt.bar(order_counts.index, order_counts.values, color='skyblue', width=8000)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')
    
    # x축 라벨 설정: 10,000원 단위 -> 1.0, 2.0, ..., 20.0 (200,000원은 >20.0 처리)
    xticks_labels = [f">{i // 10000}.0" if i == 200000 else f"{i // 10000}.0" for i in full_range]
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('주문 금액 범위 (단위: 원)')
    plt.ylabel('주문 건수')
    plt.title('전체 주문 기준 객단가 분포')
    st.pyplot(plt)
    
    # 주문 비율 분포 시각화 (전체 주문 기준)
    st.write("### 3. 전체 주문 기준 객단가 분포 비율")
    total_orders = order_counts.sum()
    order_percentages = (order_counts / total_orders) * 100
    st.write("**주문 비율 (금액 범주별):**", order_percentages)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(order_counts.index, order_percentages.values, color='skyblue', width=8000)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha='center', va='bottom')
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('주문 금액 범위 (단위: 원)')
    plt.ylabel('주문 비율 (%)')
    plt.title('전체 주문 기준 객단가 분포 (비율)')
    st.pyplot(plt)
    
    # ##########################
    # 4. 업셀 주문 기준 분석: 업셀 주문의 객단가 분포 및 비율
    st.write("### 4. 업셀 주문 기준 객단가 분포 및 비율")
    upsell_data = data[data['일반/업셀 구분'] == '업셀 상품']
    
    if upsell_data.empty:
        st.write("경고: 업셀 주문 데이터가 없습니다.")
    else:
        upsell_data['금액 범주'] = (upsell_data['총 주문 금액'] // 10000) * 10000
        upsell_data['금액 범주'] = upsell_data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)
        upsell_order_counts = upsell_data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()
        st.write("**업셀 주문 건수 (금액 범주별):**", upsell_order_counts)
        
        # 업셀 주문 건수 바 차트
        plt.figure(figsize=(10, 6))
        bars = plt.bar(upsell_order_counts.index, upsell_order_counts.values, color='orange', width=8000)
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')
        plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
        plt.xlabel('주문 금액 범위 (단위: 원)')
        plt.ylabel('주문 건수')
        plt.title('업셀 주문 기준 객단가 분포')
        st.pyplot(plt)
        
        # 업셀 주문 비율 차트
        total_upsell_orders = upsell_order_counts.sum()
        upsell_order_percentages = (upsell_order_counts / total_upsell_orders) * 100
        st.write("**업셀 주문 비율 (금액 범주별):**", upsell_order_percentages)
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(upsell_order_counts.index, upsell_order_percentages.values, color='orange', width=8000)
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha='center', va='bottom')
        plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
        plt.xlabel('주문 금액 범위 (단위: 원)')
        plt.ylabel('주문 비율 (%)')
        plt.title('업셀 주문 기준 객단가 분포 (비율)')
        st.pyplot(plt)
    
    # ##########################
    # 5. 주문별 상품 개수 분포 분석
    st.write("### 5. 주문별 상품 개수 분포 분석")
    
    # 한 주문에 여러 행(상품)이 기록되어 있다고 가정하고, 주문번호별 상품 개수 집계
    order_items = raw_data.groupby('주문번호').size().reset_index(name='상품개수')
    st.write("**주문별 상품 개수 예시 (상위 5개):**")
    st.write(order_items.head())
    
    # 상품 개수 분포: 각 주문에 담긴 상품 개수별 주문 건수
    product_count_distribution = order_items['상품개수'].value_counts().sort_index()
    st.write("**상품 개수별 주문 건수:**")
    st.write(product_count_distribution)
    
    # 바 차트: 주문별 상품 개수 분포 (건수)
    fig_items, ax_items = plt.subplots(figsize=(10, 6))
    bars = ax_items.bar(product_count_distribution.index.astype(str), product_count_distribution.values, color='green')
    ax_items.set_xlabel('한 주문에 담긴 상품 개수')
    ax_items.set_ylabel('주문 건수')
    ax_items.set_title('전체 주문 중 상품 개수 분포')
    for bar in bars:
        yval = bar.get_height()
        ax_items.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')
    st.pyplot(fig_items)
    
    # 상품 개수 분포(비율)
    total_orders_items = product_count_distribution.sum()
    product_percentage = (product_count_distribution / total_orders_items) * 100
    st.write("**상품 개수별 주문 비율 (%):**")
    st.write(product_percentage)
    
    fig_items_pct, ax_items_pct = plt.subplots(figsize=(10, 6))
    bars = ax_items_pct.bar(product_percentage.index.astype(str), product_percentage.values, color='lightblue')
    ax_items_pct.set_xlabel('한 주문에 담긴 상품 개수')
    ax_items_pct.set_ylabel('주문 비율 (%)')
    ax_items_pct.set_title('전체 주문 중 상품 개수 비중 (비율)')
    for bar in bars:
        yval = bar.get_height()
        ax_items_pct.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha='center', va='bottom')
    st.pyplot(fig_items_pct)
    
else:
    st.write("주문목록 내 '내보내기' 버튼을 통해 내려받은 CSV 파일만 사용 가능합니다.")
