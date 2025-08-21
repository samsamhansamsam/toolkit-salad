import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(
    page_title='Order Price and Items Distribution Analysis v1.31',
    layout='wide'
)

# CSS for content width and alignment
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

st.title('Order Price and Items Distribution Analysis v1.31')

uploaded_file = st.file_uploader("Upload CSV file.", type="csv")


def generate_markdown_report(
    period_info, total_revenue, upsell_conversion, upsell_bundle,
    avg_order_value, avg_bundle_order_value, avg_items_all, avg_items_bundle,
    benchmark_data, widget_stats, promotion_data, subscription_data
):
    md = f"""
# 1. 알파업셀성과

## 📊 요약
- 기간 : {period_info}
- 주문금액(원)
  - 전체주문 : {total_revenue:,}
  - [업셀]전환주문 : {upsell_conversion:,}
  - **`{benchmark_data['conversion_rate']:.2f}%`**
  - [업셀]함께구매주문금액 : {upsell_bundle:,}
  - **`{benchmark_data['bundle_rate']:.2f}%`**
- 객단가(원)
  - 전체주문 : {int(avg_order_value):,}
  - [업셀]함께구매주문금액 : {int(avg_bundle_order_value):,}
  - **+{int(avg_bundle_order_value - avg_order_value):,}원(`{benchmark_data['bundle_order_rate']}` 🆙)**
- 주문 당 평균 상품 수(개)
  - 전체주문 : {avg_items_all:.1f}
  - [업셀]함께구매주문금액 : **{avg_items_bundle:.1f}**
  - **`+{avg_items_bundle - avg_items_all:.1f}개`** 🆙

## 벤치마크 지표
- 전체주문금액 중 [업셀]전환주문 비율 : 전체평균 7.14% **대비 비슷** `{benchmark_data['conversion_rate']:.2f}%`
- 전체주문금액 중 [업셀]함께구매주문금액 비율 : 전체평균 3.17% **대비 낮음** `{benchmark_data['bundle_rate']:.2f}%`
- [전체주문 vs 업셀주문] 객단가 : 전체평균 34%⤴️ **대비 높음** `{benchmark_data['bundle_order_rate']} 🆙`
- 주문 당 평균 상품수 : 전체평균 0.7개 대비 **높음** **`+{avg_items_bundle - 0.7:.1f}개`** ⤴️

> 💡
> 주문금액 공헌도 : 평균 대비 비슷하거나, 낮음
> 체험 후반으로 갈수록 완만한 우상향 추세
> 금액별 할인 프로모션 사용과 성과 상관관계 지켜보기
> 📌 성과한계 : 정기배송 상품의 상세페이지에는 위젯이 노출 되지 않음
> 세일즈 적극도(위젯 활용도) : 고객당 상품추천수 **`{widget_stats['avg_recommend_per_customer']}`** 으로 평균 약 9.1건 대비 높음
> 인사이트 메뉴에서 지표 확인하기
> [무라벨 530mL] 닥터유 제주용암수 530mL×20병 **`제주용암수`** 업셀링 순위 확인


# 2. 자사몰현황 ({widget_stats['recent_period_start']} ~ {widget_stats['recent_period_end']})
*최근30일 🗓️*

## 주문 당 구매품목수
- 고객의 {widget_stats['single_item_pct']:.1f}%는 1개만 구매하고 쇼핑이 종료됨
- 추가 구매할 이유 만들어 주기 🔥

## 객단가분포
1. 전체주문 객단가분포
🚚무료배송 `2만원` 이상

2. [업셀] 함께구매주문 객단가분포


# 3. 성과 제고를 위한 액션 🏃🏻
> 💡
> 위젯을 충분히 활용하고 있는가? 🏹🏹
> 구매력 있는 상위고객에게 추가구매할 이유를 만들어 주고 있는가? 🔥🔥

### 1️⃣ 추가사용 추천위젯
구매버튼클릭 (함께 구매 주문 금액 2위)

✅ 상세페이지최하단위젯 : (복수사용 예시)
[예시](https://verish.me/shop1/product/detail.html?product_no=83)

⚡️ 위젯별 성과
| 순위 | 전환 주문 금액 | 함께 구매 주문 금액 |
|---|---:|---:|
| 1 | {widget_stats['widget_1_conversion']:,} | {widget_stats['widget_1_bundle']:,} |
| 2 | {widget_stats['widget_2_conversion']:,} | {widget_stats['widget_2_bundle']:,} |

### 2️⃣ 프로모션 설정  **`사용중`** 👍
📈 프로모션설정과 업셀주문의 상관관계

| 기간 | 업셀 주문수 | 하루평균 함께구매주문 건수 |
|---|---:|---:|
| {promotion_data['non_promo_period']} | {promotion_data['non_promo_count']}건 | {promotion_data['non_promo_daily']:.2f}건 |
| {promotion_data['promo_period']} | {promotion_data['promo_count']}건 | **`{promotion_data['promo_daily']:.2f}`건** |

> 💡
> **프로모션으로 인한 업셀주문 증가율:** **{promotion_data['increased_rate']:.2f}배**

[직접설정 사례 🔗]({promotion_data['direct_link']})


### 3️⃣ 위젯 영역 구석구석 활용하기
- 추가 구매를 유도하는 인상적인 위젯 타이틀 문구 (상세페이지, 장바구니페이지, CTA바 등)
- 혜택 최대한 보여주어 업셀링 유도


### 4️⃣ 위젯 디자인 설정
- 썸네일비율 & 테두리 디테일 : 예) 세로로 길게, 모서리는 직각


# 4. 구독료안내
월 **~~{subscription_data['old_price']}원~~ {subscription_data['new_price']}원** (부가세별도) **`{subscription_data['plan_name']}`** 
(월주문수 한도: ~{subscription_data['order_limit']}건) 

`스페셜오퍼`: **한단계 낮은 플랜으로**  
조건 : 6개월 또는 12개월 선납형태로 금액 묶기  
6개월 = {subscription_data['six_months']}원  
12개월 = {subscription_data['twelve_months']}원

🌱 **구독료 - 월평균주문수 기준**  
최근 한달 주문 수 {subscription_data['recent_order_count']}건 (25.8.18 11:59 기준)  

플랜테이블

**📌 연간 구독 시 12개월간 납부한 구독료로 (주문수 연관없이) 추가요금 없이 구독 가능**
"""
    return md


if uploaded_file is not None:
    raw_data = pd.read_csv(uploaded_file)

    # Basic data pre-processing to filter relevant orders
    raw_data['총 주문 금액'] = pd.to_numeric(raw_data['총 주문 금액'], errors='coerce')
    raw_data = raw_data[raw_data['총 주문 금액'] > 0]

    # Deduplication keeping up-sell preferential
    data = raw_data.copy()
    data = data.sort_values(by=['일반/업셀 구분'], ascending=False)
    data = data.drop_duplicates(subset=['주문번호'], keep='last')

    raw_data['주문일'] = pd.to_datetime(raw_data['주문일'], errors='coerce')
    start_date_dt = raw_data['주문일'].min()
    end_date_dt = raw_data['주문일'].max()
    period_days = (end_date_dt - start_date_dt).days + 1
    period_info = f"{start_date_dt.strftime('%y.%m.%d')} ~ {end_date_dt.strftime('%y.%m.%d')} `{period_days}일간`"

    # KPI & basic metrics
    total_revenue = data['총 주문 금액'].sum()
    upsell_conversion = data[data['일반/업셀 구분'] == '업셀 상품']['총 주문 금액'].sum()
    upsell_bundle = raw_data[raw_data['일반/업셀 구분'] == '함께 구매 상품']['총 주문 금액'].sum() if '함께 구매 상품' in raw_data['일반/업셀 구분'].unique() else 0
    avg_order_value = data['총 주문 금액'].mean()
    avg_bundle_order_value = raw_data[raw_data['일반/업셀 구분'] == '함께 구매 상품']['총 주문 금액'].mean() if '함께 구매 상품' in raw_data['일반/업셀 구분'].unique() else 0
    order_items = raw_data.groupby('주문번호').size()
    avg_items_all = order_items.mean()
    bundle_orders = raw_data[raw_data['일반/업셀 구분'] == '함께 구매 상품']
    avg_items_bundle = bundle_orders.groupby('주문번호').size().mean() if not bundle_orders.empty else 0

    # Benchmarks (static or from external config)
    benchmark_data = {
        'conversion_rate': (upsell_conversion / total_revenue * 100) if total_revenue else 0,
        'bundle_rate': (upsell_bundle / total_revenue * 100) if total_revenue else 0,
        'bundle_order_rate': "82.25%",
    }

    # Widget statistics example (fill with actual data or dummy)
    widget_stats = {
        'avg_recommend_per_customer': 13.3,
        'recent_period_start': '25.7.19',
        'recent_period_end': '25.8.17',
        'single_item_pct': 85.1,
        'widget_1_conversion': 4656410,
        'widget_1_bundle': 1361960,
        'widget_2_conversion': 4442980,
        'widget_2_bundle': 1075600,
    }

    # Promotion performance example (fill with actual data or dummy)
    promotion_data = {
        'non_promo_period': '1월25일~2월2일, 2월10~11일',
        'promo_period': '2월 3일 ~ 2월 9일',
        'non_promo_count': 15,
        'promo_count': 55,
        'non_promo_daily': 1.67,
        'promo_daily': 7.86,
        'increased_rate': 4.71,
        'direct_link': 'https://sum37mall.cafe24.com/product/detail.html?product_no=322&cate_no=30&display_group=1',
    }

    # Subscription info example (fill with actual data or dummy)
    subscription_data = {
        'old_price': '800,000',
        'new_price': '540,000',
        'plan_name': '엔터프라이즈3',
        'order_limit': 20000,
        'six_months': '3,240,000',
        'twelve_months': '6,480,000',
        'recent_order_count': 10074,
    }

    # Generate and show markdown report
    markdown_report = generate_markdown_report(
        period_info, total_revenue, upsell_conversion, upsell_bundle,
        avg_order_value, avg_bundle_order_value, avg_items_all, avg_items_bundle,
        benchmark_data, widget_stats, promotion_data, subscription_data
    )

    st.markdown("## 📋 보고서 마크다운 미리보기")
    st.code(markdown_report, language='markdown')

    if st.button("📋 보고서 마크다운 복사"):
        try:
            import pyperclip
            pyperclip.copy(markdown_report)
            st.success("마크다운 내용이 클립보드에 복사되었습니다!")
        except Exception:
            st.info("복사 기능이 지원되지 않으니 직접 마크다운 영역을 복사하세요.")

    # Display pie chart for "주문 당 구매품목수"
    order_item_counts = order_items.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(order_item_counts.index.astype(str), order_item_counts.values, color='seagreen')
    ax.set_xlabel('주문 당 상품 개수')
    ax.set_ylabel('주문 건수')
    ax.set_title('주문 당 구매품목수 분포')
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom')
    st.pyplot(fig)

    # Save and provide image download button
    img_name = 'order_items_distribution.png'
    fig.savefig(img_name)
    with open(img_name, "rb") as f:
        st.download_button("📥 그래프 이미지 다운로드", data=f, file_name=img_name, mime="image/png")

    if os.path.exists(img_name):
        os.remove(img_name)

else:
    st.write("CSV 파일을 업로드해 주세요.")
