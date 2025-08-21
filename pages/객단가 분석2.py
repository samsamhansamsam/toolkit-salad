import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pyperclip  # To copy markdown text to clipboard (optional, supports some environments)


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
st.title('Order Price and Items Distribution Analysis v1.31')


# CSV file uploader
uploaded_file = st.file_uploader("Upload CSV file.", type="csv")


def generate_markdown_report(data, raw_data, start_date, end_date, period_days):

    total_revenue = data['총 주문 금액'].sum()
    avg_order_value = data['총 주문 금액'].mean()

    member_counts = data['회원여부'].value_counts()
    total_orders_member = member_counts.sum()
    member_percentages = (member_counts / total_orders_member) * 100

    data['금액 범주'] = (data['총 주문 금액'] // 10000) * 10000
    data['금액 범주'] = data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)
    full_range = pd.Series([i * 10000 for i in range(21)])  # 0, 10000, ..., 200000
    order_counts = data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()
    total_orders = order_counts.sum()
    order_percentages = (order_counts / total_orders) * 100

    upsell_data = data[data['일반/업셀 구분'] == '업셀 상품']
    if not upsell_data.empty:
        upsell_data['금액 범주'] = (upsell_data['총 주문 금액'] // 10000) * 10000
        upsell_data['금액 범주'] = upsell_data['금액 범주'].apply(lambda x: 200000 if x > 200000 else x)
        upsell_order_counts = upsell_data['금액 범주'].value_counts().reindex(full_range, fill_value=0).sort_index()
        total_upsell_orders = upsell_order_counts.sum()
        upsell_order_percentages = (upsell_order_counts / total_upsell_orders) * 100
    else:
        upsell_order_counts = pd.Series(dtype=int)
        upsell_order_percentages = pd.Series(dtype=float)

    order_items = raw_data.groupby('주문번호').size().reset_index(name='ItemCount')
    product_count_distribution = order_items['ItemCount'].value_counts().sort_index()

    md = f"""
# 주문 데이터 분석 보고서

## 📊 요약
- 분석 기간: **{start_date} ~ {end_date}** ({period_days}일)
- 전체 매출: **{total_revenue:,.0f} KRW**
- 평균 객단가: **{avg_order_value:,.0f} KRW**

## 1. 회원 vs 비회원 주문 비율
| 구분 | 주문 건수 | 주문 비중(%) |
|---|---|---|
| 회원 | {member_counts.get('Member',0)} | {member_percentages.get('Member',0):.2f}% |
| 비회원 | {member_counts.get('Guest',0)} | {member_percentages.get('Guest',0):.2f}% |

## 2. 전체 주문가 분포 (KRW 단위 10,000원 구간)
| 가격 범위 | 주문 건수 | 주문 비중(%) |
|---|---|---|
"""
    # Add order price distribution rows
    for price, count in order_counts.items():
        label = f">{price // 10000}.0" if price == 200000 else f"{price // 10000}.0"
        percent = order_percentages.get(price, 0)
        md += f"| {label}만 | {count} | {percent:.2f}% |\n"

    md += "\n"

    if not upsell_order_counts.empty:
        md += "## 3. 업셀 상품 주문가 분포 (KRW 단위 10,000원 구간)\n"
        md += "| 가격 범위 | 주문 건수 | 주문 비중(%) |\n|---|---|---|\n"
        for price, count in upsell_order_counts.items():
            label = f">{price // 10000}.0" if price == 200000 else f"{price // 10000}.0"
            percent = upsell_order_percentages.get(price, 0)
            md += f"| {label}만 | {count} | {percent:.2f}% |\n"
        md += "\n"

    md += "## 4. 한 주문 당 상품 개수 분포\n| 상품 개수 | 주문 건수 |\n|---|---|\n"
    for item_num, cnt in product_count_distribution.items():
        md += f"| {item_num} | {cnt} |\n"

    md += """
---
*본 보고서는 Streamlit 분석 도구를 통해 자동 생성되었습니다.*
    """
    return md


if uploaded_file is not None:
    # Read raw data
    raw_data = pd.read_csv(uploaded_file)

    # Preprocessing
    raw_data['총 주문 금액'] = pd.to_numeric(raw_data['총 주문 금액'], errors='coerce')
    raw_data = raw_data[raw_data['총 주문 금액'] > 0]

    data = raw_data.copy()
    data = data.sort_values(by=['일반/업셀 구분'], ascending=False)
    data = data.drop_duplicates(subset=['주문번호'], keep='last')

    raw_data['주문일'] = pd.to_datetime(raw_data['주문일'], errors='coerce')
    start_date_dt = raw_data['주문일'].min()
    end_date_dt = raw_data['주문일'].max()
    start_date = start_date_dt.strftime('%Y-%m-%d')
    end_date = end_date_dt.strftime('%Y-%m-%d')
    period_days = (end_date_dt - start_date_dt).days + 1

    data['회원여부'] = data['주문자 아이디'].apply(lambda x: 'Guest' if pd.isna(x) or str(x).strip() == '' else 'Member')

    # Existing analysis display - as in your original code (metrics, charts, tables)...

    st.metric(label="전체 매출", value=f"{data['총 주문 금액'].sum():,.0f} KRW")
    st.metric(label="평균 객단가", value=f"{data['총 주문 금액'].mean():,.0f} KRW")
    st.write(f"**분석 기간:** {start_date} ~ {end_date} ({period_days}일)")

    # [Add your existing charts, tables here as before]

    # Generate markdown report text
    markdown_report = generate_markdown_report(data, raw_data, start_date, end_date, period_days)

    # Display markdown preview
    st.markdown("---")
    st.markdown("## 📋 보고서 마크다운 미리보기")
    st.code(markdown_report, language='markdown')

    # Button to copy markdown text to clipboard (some environments support this)
    if st.button("📋 보고서 마크다운 복사"):
        try:
            pyperclip.copy(markdown_report)
            st.success("마크다운 내용이 클립보드에 복사되었습니다! (환경에 따라 동작하지 않을 수 있음)")
        except Exception as e:
            st.error(f"복사 기능이 지원되지 않습니다. 수동으로 복사해 주세요. ({e})")

else:
    st.write("Please use the CSV file downloaded by clicking the 'Export' button in the order list.")
