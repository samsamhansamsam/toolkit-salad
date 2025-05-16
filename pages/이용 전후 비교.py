import streamlit as st
import pandas as pd
import math
from datetime import timedelta
import altair as alt

st.set_page_config(page_title="이용 전후 비교", layout="wide")
st.title("📊 이용 전후 비교")

# 1) CSV 업로드
uploaded_file = st.file_uploader("📂 주문 데이터 CSV 업로드", type="csv")
if not uploaded_file:
    st.info("먼저 주문 데이터 CSV를 업로드해 주세요.")
    st.stop()

# 2) 데이터 로드 & 전처리
df_raw = pd.read_csv(uploaded_file)
df_raw["주문일"] = pd.to_datetime(df_raw["주문일"])
orders = (
    df_raw[["주문번호", "주문일", "총 상품수", "총 주문 금액"]]
    .drop_duplicates(subset="주문번호")
    .assign(주문일_date=lambda d: d["주문일"].dt.date)
)

# 3) 날짜 범위 절반으로 분할
min_date = orders["주문일_date"].min()
max_date = orders["주문일_date"].max()
total_days = (max_date - min_date).days + 1
half_days = total_days // 2

prev_start = min_date
prev_end   = prev_start + timedelta(days=half_days - 1)
curr_start = prev_end + timedelta(days=1)
curr_end   = max_date

# 필터링
prev_df = orders[(orders["주문일_date"] >= prev_start) & (orders["주문일_date"] <= prev_end)]
curr_df = orders[(orders["주문일_date"] >= curr_start) & (orders["주문일_date"] <= curr_end)]

if prev_df.empty or curr_df.empty:
    st.warning("데이터 분할 후, 이전 또는 이후 기간에 주문 데이터가 없습니다.")
    st.stop()

# 4) 동적 임계값 계산
# 4-1) 상품 수 기준 n
prev_avg_items = prev_df["총 상품수"].mean()
threshold_n = math.ceil(prev_avg_items) if prev_avg_items > 2 else 2

# 4-2) 금액 기준 (만원 단위 올림)
prev_avg_amount = prev_df["총 주문 금액"].mean()
threshold_amount = math.ceil(prev_avg_amount / 10000) * 10000

# 5) 비중 계산
prev_prop_n   = (prev_df["총 상품수"] >= threshold_n).mean()
curr_prop_n   = (curr_df["총 상품수"] >= threshold_n).mean()
prev_prop_amt = (prev_df["총 주문 금액"] >= threshold_amount).mean()
curr_prop_amt = (curr_df["총 주문 금액"] >= threshold_amount).mean()

# 6) 결과 출력 (기존 Metric)
st.subheader(f"이전 기간 ({prev_start} ~ {prev_end}) vs 이후 기간 ({curr_start} ~ {curr_end})")
st.markdown("---")
st.subheader(f"1. 상품 수 기준: {threshold_n}개 이상 주문 비중")
c1, c2 = st.columns(2)
c1.metric("이전 기간 비중", f"{prev_prop_n:.2%}")
c2.metric("이후 기간 비중", f"{curr_prop_n:.2%}", delta=f"{(curr_prop_n - prev_prop_n):.2%}")

st.subheader(f"2. 주문 금액 기준: {threshold_amount:,}원 이상 주문 비중")
d1, d2 = st.columns(2)
d1.metric("이전 기간 비중", f"{prev_prop_amt:.2%}")
d2.metric("이후 기간 비중", f"{curr_prop_amt:.2%}", delta=f"{(curr_prop_amt - prev_prop_amt):.2%}")

# 7) 세련된 Altair 막대그래프
# 1) 상대 증감 계산 (증가비율)
delta_items_rel  = (curr_prop_n  - prev_prop_n) / prev_prop_n
delta_amount_rel = (curr_prop_amt - prev_prop_amt) / prev_prop_amt

# 1) 데이터 준비
df_items = pd.DataFrame({
    '기간': ['이전 기간', '이후 기간'],
    '비중': [prev_prop_n, curr_prop_n]
})
df_amount = pd.DataFrame({
    '기간': ['이전 기간', '이후 기간'],
    '비중': [prev_prop_amt, curr_prop_amt]
})

# 2) 공통 스케일 & 축 설정 (0%~최대*1.1, tickCount=5)
max_val    = max(df_items['비중'].max(), df_amount['비중'].max())
y_scale    = alt.Scale(domain=[0, max_val * 1.1], nice=False)
y_axis     = alt.Axis(title='', format='.0%', tickCount=5, grid=True)

# 3) 차트 생성 함수
def make_chart(df, title, delta, thresh_label):
    base = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                '기간:O',
                axis=alt.Axis(
                    labelAngle=0,
                    domain=False,
                    ticks=False,
                    title=None        # ← 여기서 축 제목 제거
                )
            ),
            y=alt.Y('비중:Q', axis=y_axis, scale=y_scale),
            color=alt.Color('기간:N',
                            scale=alt.Scale(range=['#4c78a8','#f58518']),
                            legend=None)
        )
        .properties(width=300, height=360, title=title)
    )
    # 바 내부 백분율 레이블
    labels = base.mark_text(
        dy=-12, fontSize=14, color='white', fontWeight='bold'
    ).encode(
        text=alt.Text('비중:Q', format='.1%')
    )
    # 상대 증가비율 레이블 (이후 기간에만)
    delta_chart = (
        alt.Chart(pd.DataFrame({
            '기간': ['이후 기간'],
            'y': [df.loc[df['기간']=='이후 기간', '비중'].values[0]],
            'delta': [delta]
        }))
        .mark_text(
            dy=-40, fontSize=20, color='yellow', fontWeight='bold'
        )
        .encode(
            x='기간:O',
            y='y:Q',
            text=alt.Text('delta:Q', format='+.0%')
        )
    )
    return base + labels + delta_chart

# 4) 차트 그리기
st.markdown("## 📈 비중 변화 그래프")
col1, col2 = st.columns(2)

with col1:
    chart1 = make_chart(
        df_items,
        title=f"상품 수 기준 ({threshold_n}개 이상)",
        delta=delta_items_rel,
        thresh_label=f"{threshold_n}개 이상"
    )
    st.altair_chart(chart1.configure_view(strokeOpacity=0), use_container_width=True)

with col2:
    chart2 = make_chart(
        df_amount,
        title=f"금액 기준 ({threshold_amount:,}원 이상)",
        delta=delta_amount_rel,
        thresh_label=f"{threshold_amount:,}원 이상"
    )
    st.altair_chart(chart2.configure_view(strokeOpacity=0), use_container_width=True)