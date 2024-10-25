import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 제목 설정
st.title('알파업셀 객단가 시각화 도구 v1.3')

# 파일 업로더 생성
uploaded_file = st.file_uploader("CSV 파일을 달라.", type="csv")

if uploaded_file is not None:
    # 데이터 읽기
    data = pd.read_csv(uploaded_file)

    # '총 주문 금액' 데이터 타입 변환 및 0원 데이터 제거 (취소 및 환불된 주문)
    data['총 주문 금액'] = pd.to_numeric(data['총 주문 금액'], errors='coerce')
    data = data[data['총 주문 금액'] > 0]  # 0원인 데이터를 제거

    # 중복 제거: 중복된 '주문번호'가 있을 때 '업셀'을 우선적으로 보존
    data = data.sort_values(by=['일반/업셀 구분'], ascending=False)  # '일반'을 먼저 정렬하여 '업셀'을 남김
    data = data.drop_duplicates(subset=['주문번호'], keep='last')  # '업셀' 우선 보존


    ### 회원과 비회원의 주문 비중 비교 ###
    st.write("### 회원과 비회원의 주문 비중 비교")

    # '회원여부' 컬럼 생성
    data['회원여부'] = data['주문자 아이디'].apply(lambda x: 'Guest' if pd.isna(x) or str(x).strip() == '' else 'Member')

    # 주문 건수 계산
    member_counts = data['회원여부'].value_counts()

    # 비율 계산
    total_orders_member = member_counts.sum()
    member_percentages = (member_counts / total_orders_member) * 100

    # 주문 건수 및 비율 출력
    st.write("회원과 비회원의 주문 건수:")
    st.write(member_counts)

    st.write("회원과 비회원의 주문 비율 (%):")
    st.write(member_percentages)

    # 파이 차트 시각화
    fig1, ax1 = plt.subplots()
    ax1.pie(member_counts.values, labels=member_counts.index, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    ax1.set_title('Order Share')

    st.pyplot(fig1)


    ### 1. 전체 주문 기준 시각화 ###
    st.write("### 전체 주문 기준 객단가 분포")

    # 10,000원 단위로 범주화 (전체 주문 기준)
    data['금액 범주'] = (data['총 주문 금액'] // 10000) * 10000

    # 20만원 이상의 값은 200,000으로 변환
    data['금액 범주'] = data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)

    # 모든 범주를 설정 (빈 범주도 포함) - 0원부터 200,000원까지 범위
    full_range = pd.Series([i * 10000 for i in range(21)])  # 0, 10000, ..., 200000
    order_counts = data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()

    # 데이터 유효성 검사 (전체 주문 기준)
    st.write("Order Counts (전체 주문):", order_counts)

    # 시각화 (전체 주문 기준)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(order_counts.index, order_counts.values, color='skyblue', width=8000)

    # 각 막대 위에 수치 표시
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')

    # 가로축 라벨 설정
    xticks_labels = [f">{i // 10000}.0" if i < 200000 else ">20.0" for i in full_range]
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('Order Amount Range')
    plt.ylabel('Order Count')
    plt.title('Order Distribution by Amount (All Order)')

    # Streamlit에 전체 주문 기준 그래프 표시
    st.pyplot(plt)


    ### 2. 전체 주문 기준 객단가 분포 비율 ###
    st.write("### 전체 주문 기준 객단가 분포 비율")

    # 비율 계산 (전체 주문 기준)
    total_orders = order_counts.sum()  # 전체 주문 수
    order_percentages = (order_counts / total_orders) * 100  # 각 범주에 대한 비율(%)

    # 데이터 유효성 검사 (전체 주문 기준)
    st.write("Order Percentages (전체 주문):", order_percentages)

    # 시각화 (전체 주문 기준, 비율 표시)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(order_counts.index, order_percentages.values, color='skyblue', width=8000)

    # 각 막대 위에 비율 표시
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha='center', va='bottom')

    # 가로축 라벨 설정 (전체 주문 기준)
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('Order Amount Range')
    plt.ylabel('Percentage (%)')
    plt.title('Order Distribution by Percentage (All Order)')

    # Streamlit에 전체 주문 기준 비율 그래프 표시
    st.pyplot(plt)


    ### 3. 업셀 주문 기준 시각화 ###
    st.write("### 업셀 주문 기준 객단가 분포")

    # 업셀 주문 필터링
    upsell_data = data[data['일반/업셀 구분'] == '업셀 상품']

    # 데이터 유효성 검사: 업셀 주문 데이터가 없는 경우 경고 표시
    if upsell_data.empty:
        st.write("경고: 업셀 주문 데이터가 없습니다.")
    else:
        # 10,000원 단위로 범주화 (업셀 주문 기준)
        upsell_data['금액 범주'] = (upsell_data['총 주문 금액'] // 10000) * 10000

        # 20만원 이상의 값은 200,000으로 변환
        upsell_data['금액 범주'] = upsell_data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)

        # 모든 범주를 설정 (빈 범주도 포함)
        upsell_order_counts = upsell_data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()

        # 데이터 유효성 검사 (업셀 주문 기준)
        st.write("Order Counts (업셀 주문):", upsell_order_counts)

        # 시각화 (업셀 주문 기준)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(upsell_order_counts.index, upsell_order_counts.values, color='orange', width=8000)

        # 각 막대 위에 수치 표시
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')

        # 가로축 라벨 설정
        plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
        plt.xlabel('Order Amount Range')
        plt.ylabel('Order Count')
        plt.title('Order Distribution by Amount (Upsell Order)')

        # Streamlit에 업셀 주문 기준 그래프 표시
        st.pyplot(plt)


    ### 4. 업셀 주문 기준 객단가 분포 비율 ###
    st.write("### 업셀 주문 기준 객단가 분포 비율")

    # 비율 계산 (업셀 주문 기준)
    total_upsell_orders = upsell_order_counts.sum()  # 전체 업셀 주문 수
    upsell_order_percentages = (upsell_order_counts / total_upsell_orders) * 100  # 비율 계산

    # 데이터 유효성 검사 (업셀 주문 기준)
    st.write("Upsell Order Percentages (업셀 주문):", upsell_order_percentages)

    # 시각화 (업셀 주문 기준, 비율 표시)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(upsell_order_counts.index, upsell_order_percentages.values, color='orange', width=8000)

    # 각 막대 위에 비율 표시
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha='center', va='bottom')

    # 가로축 라벨 설정 (업셀 주문 기준)
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('Order Amount Range')
    plt.ylabel('Percentage (%)')
    plt.title('Order Distribution by Percentage (Upsell Order)')

    # Streamlit에 업셀 주문 기준 비율 그래프 표시
    st.pyplot(plt)

else:
    st.write("주문목록 내 '내보내기'버튼을 통해 내려받은 CSV 파일만 사용 가능합니다.")
