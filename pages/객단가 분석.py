import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


st.set_page_config(
    page_title='Order Price and Items Distribution Analysis v1.31',
    layout='wide'
)
# CSS로 콘텐츠 영역 너비 800px, 좌측 정렬
st.markdown(
    """
    <style>
    .block-container {
        max-width: 800px !important;
        margin-left: 50px !important;
        margin-right: auto !important;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title in English
st.title('Order Price and Items Distribution Analysis v1.3')

# CSV file uploader
uploaded_file = st.file_uploader("Upload CSV file.", type="csv")

if uploaded_file is not None:
    # Read raw data (assumes columns like '주문번호', '총 주문 금액', '주문자 아이디', '일반/업셀 구분', etc.)
    raw_data = pd.read_csv(uploaded_file)
    
    # Preprocessing: Convert '총 주문 금액' to numeric and remove orders with 0 (e.g., cancelled/refunded orders)
    raw_data['총 주문 금액'] = pd.to_numeric(raw_data['총 주문 금액'], errors='coerce')
    raw_data = raw_data[raw_data['총 주문 금액'] > 0]
    
    # Prepare data for existing analyses: Deduplicate by '주문번호' while preserving upsell orders preferentially
    data = raw_data.copy()
    data = data.sort_values(by=['일반/업셀 구분'], ascending=False)
    data = data.drop_duplicates(subset=['주문번호'], keep='last')

    # ----------------------------------------------------------------
    # 0. 평균 객단가 계산 및 표시 추가
    avg_order_value = data['총 주문 금액'].mean()  # 평균 객단가 계산
    st.subheader("0. 평균 객단가 (Average Order Value)")
    st.metric(label="평균 객단가", value=f"{avg_order_value:,.0f} KRW")
    
    # ----------------------------------------------------------------
    # 1. Member vs Guest Order Share
    st.write("### 1. Member vs Guest Order Share")
    
    # Create membership indicator column
    data['회원여부'] = data['주문자 아이디'].apply(lambda x: 'Guest' if pd.isna(x) or str(x).strip() == '' else 'Member')
    member_counts = data['회원여부'].value_counts()
    total_orders_member = member_counts.sum()
    member_percentages = (member_counts / total_orders_member) * 100
    
    st.write("**Order Counts:**")
    st.write(member_counts)
    st.write("**Order Percentages (%):**")
    st.write(member_percentages)
    
    fig1, ax1 = plt.subplots()
    ax1.pie(member_counts.values, labels=member_counts.index, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    ax1.set_title('Member vs Guest Order Share')
    st.pyplot(fig1)
    
    # ----------------------------------------------------------------
    # 2. Distribution of Order Prices (All Orders)
    st.write("### 2. Distribution of Order Prices (All Orders)")
    
    # Group orders by price range (in 10,000 KRW intervals)
    data['금액 범주'] = (data['총 주문 금액'] // 10000) * 10000
    data['금액 범주'] = data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)
    full_range = pd.Series([i * 10000 for i in range(21)])  # 0, 10000, ..., 200000
    order_counts = data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()
    
    st.write("**Order Counts (by price range):**", order_counts)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(order_counts.index, order_counts.values, color='skyblue', width=8000)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom')
    xticks_labels = [f">{i // 10000}.0" if i == 200000 else f"{i // 10000}.0" for i in full_range]
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('Order Amount Range (KRW)')
    plt.ylabel('Number of Orders')
    plt.title('Distribution of Order Prices (All Orders)')
    st.pyplot(plt)
    
    # ----------------------------------------------------------------
    # 3. Order Price Distribution by Percentage (All Orders)
    st.write("### 3. Order Price Distribution by Percentage (All Orders)")
    
    total_orders = order_counts.sum()
    order_percentages = (order_counts / total_orders) * 100
    st.write("**Order Percentages (by price range):**", order_percentages)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(order_counts.index, order_percentages.values, color='skyblue', width=8000)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{yval:.1f}%", ha='center', va='bottom')
    plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
    plt.xlabel('Order Amount Range (KRW)')
    plt.ylabel('Percentage (%)')
    plt.title('Order Price Distribution by Percentage (All Orders)')
    st.pyplot(plt)
    
    # ----------------------------------------------------------------
    # 4. Distribution of Order Prices (Upsell Orders)
    st.write("### 4. Distribution of Order Prices (Upsell Orders)")
    
    upsell_data = data[data['일반/업셀 구분'] == '업셀 상품']
    
    if upsell_data.empty:
        st.write("Warning: No Upsell Order Data available.")
    else:
        upsell_data['금액 범주'] = (upsell_data['총 주문 금액'] // 10000) * 10000
        upsell_data['금액 범주'] = upsell_data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)
        upsell_order_counts = upsell_data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()
        st.write("**Upsell Order Counts (by price range):**", upsell_order_counts)
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(upsell_order_counts.index, upsell_order_counts.values, color='orange', width=8000)
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom')
        plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
        plt.xlabel('Order Amount Range (KRW)')
        plt.ylabel('Number of Orders')
        plt.title('Distribution of Order Prices (Upsell Orders)')
        st.pyplot(plt)
        
        total_upsell_orders = upsell_order_counts.sum()
        upsell_order_percentages = (upsell_order_counts / total_upsell_orders) * 100
        st.write("**Upsell Order Percentages (by price range):**", upsell_order_percentages)
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(upsell_order_counts.index, upsell_order_percentages.values, color='orange', width=8000)
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{yval:.1f}%", ha='center', va='bottom')
        plt.xticks(ticks=full_range, labels=xticks_labels, rotation=45)
        plt.xlabel('Order Amount Range (KRW)')
        plt.ylabel('Percentage (%)')
        plt.title('Order Price Distribution by Percentage (Upsell Orders)')
        st.pyplot(plt)
    
    # ----------------------------------------------------------------
    # 5. Distribution of Items per Order (All Orders)
    st.write("### 5. Distribution of Items per Order (All Orders)")
    
    # Group raw_data by '주문번호' to count the number of items per order
    order_items = raw_data.groupby('주문번호').size().reset_index(name='ItemCount')
    st.write("**Example of Items per Order (Top 5):**")
    st.write(order_items.head())
    
    product_count_distribution = order_items['ItemCount'].value_counts().sort_index()
    st.write("**Order Counts by Number of Items:**")
    st.write(product_count_distribution)
    
    # ----- Pie Chart: Combine slices with less than 3% into "Others" -----
    total_items_orders = product_count_distribution.sum()
    labels = []
    values = []
    others_sum = 0
    for item_count, count in product_count_distribution.items():
        percentage = (count / total_items_orders) * 100
        if percentage < 3:
            others_sum += count
        else:
            labels.append(str(item_count))
            values.append(count)
    if others_sum > 0:
        labels.append("Others")
        values.append(others_sum)
    
    # Create pie chart using a cleaner color palette (Pastel1 colormap)
    fig_items, ax_items = plt.subplots(figsize=(8, 8))
    colors = plt.get_cmap('Pastel1').colors  # Use Pastel1 for a clean look
    ax_items.pie(values,
                 labels=labels,
                 autopct='%1.1f%%',
                 startangle=90,
                 colors=colors)
    ax_items.axis('equal')
    ax_items.set_title('Distribution of Items per Order (Pie Chart)')
    st.pyplot(fig_items)
    
    # ----- Bar Chart: Original distribution (not grouped as Others) -----
    fig_items_bar, ax_items_bar = plt.subplots(figsize=(10, 6))
    bars = ax_items_bar.bar(product_count_distribution.index.astype(str),
                            product_count_distribution.values,
                            color='seagreen')
    ax_items_bar.set_xlabel('Number of Items per Order')
    ax_items_bar.set_ylabel('Number of Orders')
    ax_items_bar.set_title('Distribution of Items per Order (Bar Chart)')
    for bar in bars:
        yval = bar.get_height()
        ax_items_bar.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom')
    st.pyplot(fig_items_bar)
    
else:
    st.write("Please use the CSV file downloaded by clicking the 'Export' button in the order list.")
