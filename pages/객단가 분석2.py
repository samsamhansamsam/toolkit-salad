# streamlit run app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta
from io import StringIO

# =========================================
# 0) 페이지/스타일 & 상수(벤치마크, 컬럼 매핑)
# =========================================
st.set_page_config(page_title="알파업셀 보고서 생성기", layout="wide")

# ---- 벤치마크(필요시 조정) ----
BM_UPSELL_CONV_RATIO = 7.14     # 전체주문금액 중 [업셀]전환주문 비율 (%)
BM_UPSELL_TOGETHER_RATIO = 3.17 # 전체주문금액 중 [업셀]함께구매주문금액 비율 (%)
BM_AOV_LIFT = 34.0              # 업셀 AOV가 전체 AOV 대비 평균 상승률 (%)
BM_ITEMS_LIFT = 0.7             # 주문당 평균 상품수 상승(개)

# ---- 컬럼명 매핑(너희 CSV에 맞춰 1회만 수정) ----
COL_ORDER_ID = "주문번호"
COL_ORDER_TOTAL = "총 주문 금액"     # 주문 총액(주문별 동일 값)
COL_BUYER_ID = "주문자 아이디"
COL_UPSELL_FLAG = "일반/업셀 구분"   # 값 예: "업셀 상품" / "일반 상품"
VAL_UPSELL = "업셀 상품"
COL_ORDER_DATE = "주문일"             # YYYY-MM-DD 혹은 날짜 포맷
# 라인금액 관련(없으면 자동계산 시도)
COL_LINE_PRICE = None                 # 라인단가(판매가)
COL_LINE_QTY = None                   # 수량
COL_LINE_AMOUNT = None                # 라인금액(=단가*수량)

# =========================================
# 1) 사이드바 / 업로드
# =========================================
with st.sidebar:
    st.header("입력")
    st.caption("필수: 라인아이템 단위 CSV (주문번호/총 주문 금액/주문일/일반·업셀 구분 포함)")
    up_file = st.file_uploader("주문 CSV 업로드", type=["csv"])

    st.divider()
    st.subheader("분석 기간 설정")
    custom_range = st.checkbox("분석 기간 직접 설정", value=False)
    start_date = None
    end_date = None

    # 선택 입력(있으면 섹션 확장)
    st.divider()
    st.subheader("선택 입력(있으면 표시)")
    widget_perf_file = st.file_uploader("위젯별 성과 CSV(선택)", type=["csv"])
    # 기대 컬럼: [순위, 전환주문금액, 함께구매주문금액, 위젯명] 등 자유형. 아래에서 유연 표시

    st.divider()
    st.subheader("구독료 안내 설정")
    plan_image = st.file_uploader("플랜 이미지(선택, PNG/JPG)", type=["png","jpg","jpeg"])
    enterprise_offer = st.checkbox("스페셜오퍼(한 단계 낮은 플랜로 제안) 표시", value=True)

# =========================================
# 2) 스타일
# =========================================
st.markdown("""
<style>
.block-container { max-width: 880px; margin-left: 40px; }
.h1 { font-size: 26px; font-weight: 800; margin: 6px 0 18px; }
.h2 { font-size: 20px; font-weight: 800; margin: 22px 0 10px; }
.h3 { font-size: 16px; font-weight: 700; margin: 16px 0 6px; }
.tbl th, .tbl td { padding: 6px 8px; font-size: 14px; }
.kpi { display:grid; grid-template-columns: repeat(3,1fr); gap:10px; }
.k { border:1px solid #e5e7eb; border-radius:10px; padding:12px; background:#fafafa; }
.k .lab { color:#6b7280; font-size:12px; margin-bottom:6px; }
.k .val { font-size:18px; font-weight:700; }
.callout { border-left:4px solid #2563eb; background:#f3f8ff; padding:12px 14px; border-radius:6px; }
.gray { color:#6b7280; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono"; }
hr { border: none; height: 1px; background: #e5e7eb; margin: 18px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="h1">1. 알파업셀성과</div>', unsafe_allow_html=True)

if up_file is None:
    st.info("주문 CSV를 업로드하세요.")
    st.stop()

# =========================================
# 3) 로딩/전처리
# =========================================
df = pd.read_csv(up_file)

# 타입 보정
df[COL_ORDER_TOTAL] = pd.to_numeric(df[COL_ORDER_TOTAL], errors="coerce")
df[COL_ORDER_DATE] = pd.to_datetime(df[COL_ORDER_DATE], errors="coerce")
df = df[(df[COL_ORDER_TOTAL] > 0) & df[COL_ORDER_DATE].notna()].copy()

# 라인금액 확보
if COL_LINE_AMOUNT and (COL_LINE_AMOUNT in df.columns):
    df["_라인금액"] = pd.to_numeric(df[COL_LINE_AMOUNT], errors="coerce")
elif (COL_LINE_PRICE in df.columns) and (COL_LINE_QTY in df.columns):
    df["_라인금액"] = pd.to_numeric(df[COL_LINE_PRICE], errors="coerce") * pd.to_numeric(df[COL_LINE_QTY], errors="coerce")
else:
    # 라인금액이 없으면 업셀 금액은 추정이 불가 → 업셀 라인 금액 표시는 스킵하되 전환주문 금액은 가능
    df["_라인금액"] = np.nan

# 분석 기간
min_dt, max_dt = df[COL_ORDER_DATE].min(), df[COL_ORDER_DATE].max()
if custom_range:
    c1, c2 = st.columns(2)
    with c1: start_date = st.date_input("시작일", value=min_dt.date())
    with c2: end_date = st.date_input("종료일", value=max_dt.date())
    mask = (df[COL_ORDER_DATE] >= pd.to_datetime(start_date)) & (df[COL_ORDER_DATE] <= pd.to_datetime(end_date))
    df = df[mask].copy()
else:
    start_date, end_date = min_dt.date(), max_dt.date()

period_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1

# 업셀 전환주문 판별
df["_is_upsell_line"] = (df[COL_UPSELL_FLAG].astype(str).str.strip() == VAL_UPSELL)
upsell_orders = df.groupby(COL_ORDER_ID)["_is_upsell_line"].any()  # 주문단위 True/False
upsell_order_ids = upsell_orders[upsell_orders].index

# 주문 단위 집계(중복 주문번호→1행)
orders = df.sort_values([COL_UPSELL_FLAG], ascending=False).drop_duplicates(subset=[COL_ORDER_ID], keep="last")
orders_total_sum = float(orders[COL_ORDER_TOTAL].sum())
orders_cnt = int(orders.shape[0])

# 업셀 전환주문 금액 & AOV
upsell_orders_only = orders[orders[COL_ORDER_ID].isin(upsell_order_ids)].copy()
upsell_conv_amount = float(upsell_orders_only[COL_ORDER_TOTAL].sum())
upsell_orders_cnt = int(upsell_orders_only.shape[0])
aov_all = float(orders[COL_ORDER_TOTAL].mean()) if orders_cnt else 0.0
aov_upsell_orders = float(upsell_orders_only[COL_ORDER_TOTAL].mean()) if upsell_orders_cnt else 0.0

# 함께구매주문금액(라인합계)
if df["_라인금액"].notna().any():
    upsell_together_amount = float(df.loc[df["_is_upsell_line"], "_라인금액"].sum())
else:
    upsell_together_amount = None  # 표시 불가

# 주문당 평균 상품 수(전체 vs 업셀전환주문)
items_per_order = df.groupby(COL_ORDER_ID).size()
items_all_avg = float(items_per_order.mean()) if len(items_per_order) else 0.0
items_upsell_avg = float(items_per_order.loc[items_per_order.index.isin(upsell_order_ids)].mean()) if len(upsell_order_ids) else 0.0

# 비율계산
ratio_upsell_conv = (upsell_conv_amount / orders_total_sum * 100.0) if orders_total_sum else 0.0
ratio_upsell_together = (upsell_together_amount / orders_total_sum * 100.0) if (orders_total_sum and upsell_together_amount is not None) else None

# =========================================
# 4) 1. 알파업셀성과 — 요약 테이블들
# =========================================
st.markdown(f"- 기간 : {start_date} ~ {end_date} `{period_days}일간`")

# 금액/비율 표
tbl1 = pd.DataFrame({
    "": ["전체주문", "[업셀]전환주문", "[업셀]함께구매주문금액"],
    "주문금액(원)": [
        round(orders_total_sum),
        round(upsell_conv_amount),
        (round(upsell_together_amount) if upsell_together_amount is not None else np.nan)
    ],
    "비율(%)": [
        "",
        f"{ratio_upsell_conv:,.2f}%",
        (f"{ratio_upsell_together:,.2f}%" if ratio_upsell_together is not None else "N/A")
    ]
})
st.table(tbl1)

# 객단가 표
aov_diff = aov_upsell_orders - aov_all
aov_lift_pct = (aov_diff / aov_all * 100.0) if aov_all else 0.0
tbl2 = pd.DataFrame({
    "": ["전체주문", "[업셀]함께구매주문금액"],
    "객단가(원)": [round(aov_all), round(aov_upsell_orders)],
    "비교": ["", f"+{round(aov_diff):,}원(`{aov_lift_pct:.2f}%` 🆙)"]
})
st.table(tbl2)

# 주문당 평균 상품수 표
items_diff = items_upsell_avg - items_all_avg
tbl3 = pd.DataFrame({
    "": ["전체주문", "[업셀]함께구매주문금액"],
    "주문 당 평균 상품 수(개)": [round(items_all_avg,1), round(items_upsell_avg,1)],
    "비교": ["", f"`+{items_diff:.1f}개` 🆙"]
})
st.table(tbl3)

# 벤치마크 비교
def tag_cmp(val, bm, high_good=None):
    # high_good: True면 높을수록 좋음, False면 낮을수록 좋음, None면 '비슷/낮음/높음'만
    if val is None or np.isnan(val):
        return "**데이터 부족**"
    diff = val - bm
    if abs(diff) < (bm * 0.15 if bm > 0 else 2):  # ±15%p 이내면 '비슷' 판단(임의)
        return f"전체평균 {bm:.2f}% **대비 비슷** `{val:.2f}%`"
    if diff >= 0:
        verdict = "**높음**" if (high_good is None or high_good) else "**높음(주의)**"
    else:
        verdict = "**낮음**" if (high_good is None or not high_good) else "**낮음(보완)**"
    return f"전체평균 {bm:.2f}% 대비 {verdict} `{val:.2f}%`"

st.markdown("---")
st.markdown("**벤치마크 지표**")
bm_lines = [
    f"- 전체주문금액 중 [업셀]전환주문 비율 : {tag_cmp(ratio_upsell_conv, BM_UPSELL_CONV_RATIO, high_good=True)}",
    f"- 전체주문금액 중 [업셀]함께구매주문금액 비율 : " + (
        tag_cmp(ratio_upsell_together, BM_UPSELL_TOGETHER_RATIO, high_good=True) if ratio_upsell_together is not None
        else "**라인금액 미제공 → 산출 불가**"
    ),
    f"- [전체주문 vs 업셀주문] 객단가 : 전체평균 {BM_AOV_LIFT:.0f}%⤴️ 대비 " +
        (f"**높음 `{aov_lift_pct:.2f}%` 🆙**" if aov_lift_pct >= BM_AOV_LIFT else f"**낮음 `{aov_lift_pct:.2f}%`**"),
    f"- 주문 당 평균 상품수 : 전체평균 {BM_ITEMS_LIFT:.1f}개 대비 " +
        (f"**높음 `+{items_diff:.1f}개` ⤴️**" if items_diff >= BM_ITEMS_LIFT else f"**낮음 `+{items_diff:.1f}개`**"),
]
st.markdown("\n".join(bm_lines))

st.markdown("---")
st.markdown("""
<div class="callout">
<b>💡 인사이트</b><br>
- 주문금액 공헌도: 평균 대비 비슷/낮음 여부를 위 표에서 확인. 체험 후반부로 갈수록 추세가 우상향이면 <b>금액별 할인</b> 등과의 상관관계를 추가 관찰.<br>
- 📌 성과 한계: 특정 상품(예: 정기배송 상세)엔 위젯 노출이 제한될 수 있음 → 적용 범위 점검 필요.<br>
- 세일즈 적극도(위젯 활용도): <span class="gray">별도 데이터 제공 시 '고객당 추천수'를 표기</span>.
</div>
""", unsafe_allow_html=True)

# =========================================
# 5) 2. 자사몰현황(최근 30일)
# =========================================
st.markdown('<div class="h1">2. 자사몰현황(최근 30일 🗓️)</div>', unsafe_allow_html=True)
cutoff = df[COL_ORDER_DATE].max() - timedelta(days=29)
recent = df[df[COL_ORDER_DATE] >= cutoff].copy()

# 주문당 구매품목수 — 파이차트 (최근30일)
st.markdown('<div class="h3">주문 당 구매품목수</div>', unsafe_allow_html=True)
recent_items = recent.groupby(COL_ORDER_ID).size()
dist = recent_items.value_counts().sort_index()
total_recent_orders = dist.sum()

labels, vals, others_sum = [], [], 0
for k, v in dist.items():
    pct = (v / total_recent_orders * 100.0) if total_recent_orders else 0.0
    if pct < 3:
        others_sum += v
    else:
        labels.append(str(k))
        vals.append(v)
if others_sum > 0:
    labels.append("Others")
    vals.append(others_sum)

fig, ax = plt.subplots(figsize=(6.6, 6.6))
explode = [0.03]*len(vals)
wedges, texts, autotexts = ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=0,
                                  explode=explode, pctdistance=0.8, labeldistance=1.05)
ax.axis('equal'); ax.set_title("최근 30일: 주문 당 구매품목수 비중")
st.pyplot(fig)

if 1 in dist.index and total_recent_orders:
    one_pct = dist.loc[1]/total_recent_orders*100.0
    st.markdown(f"""
<div class="callout"><b>💡</b> 1개만 구매하고 쇼핑이 끝나는 <b>`{one_pct:.1f}%`</b> 고객에게 <b>추가 구매 사유</b>를 만들어 주는 액션이 필요.</div>
""", unsafe_allow_html=True)

# 객단가 분포 — 전체/업셀
st.markdown('<div class="h3">객단가분포</div>', unsafe_allow_html=True)
# 전체
orders_recent = recent.sort_values([COL_UPSELL_FLAG], ascending=False).drop_duplicates(subset=[COL_ORDER_ID], keep="last")
orders_recent["_만원대"] = ((orders_recent[COL_ORDER_TOTAL]//10000)*10000).clip(upper=200000)
vc_all = orders_recent["_만원대"].value_counts().reindex([i*10000 for i in range(21)], fill_value=0).sort_index()
labels_all = [f">{200000//10000}.0" if i==200000 else f"{i//10000}.0" for i in vc_all.index]
fig2, ax2 = plt.subplots(figsize=(10,5.6))
bars = ax2.bar(labels_all, vc_all.values)
ax2.set_title("1) 전체주문 객단가분포"); ax2.set_xlabel("만원대 구간"); ax2.set_ylabel("주문 건수")
for b in bars: ax2.text(b.get_x()+b.get_width()/2, b.get_height(), int(b.get_height()),
                        ha="center", va="bottom", fontsize=9)
st.pyplot(fig2)
st.caption("🚚 무료배송 임계값 예: 2만원 이상")

# 업셀
orders_recent["_is_upsell_order"] = orders_recent[COL_ORDER_ID].isin(upsell_order_ids)
upsell_recent = orders_recent[orders_recent["_is_upsell_order"]]
if not upsell_recent.empty:
    upsell_recent["_만원대"] = ((upsell_recent[COL_ORDER_TOTAL]//10000)*10000).clip(upper=200000)
    vc_up = upsell_recent["_만원대"].value_counts().reindex([i*10000 for i in range(21)], fill_value=0).sort_index()
    labels_up = [f">{200000//10000}.0" if i==200000 else f"{i//10000}.0" for i in vc_up.index]
    fig3, ax3 = plt.subplots(figsize=(10,5.6))
    bars = ax3.bar(labels_up, vc_up.values)
    ax3.set_title("2) [업셀] 함께구매주문 객단가분포"); ax3.set_xlabel("만원대 구간"); ax3.set_ylabel("주문 건수")
    for b in bars: ax3.text(b.get_x()+b.get_width()/2, b.get_height(), int(b.get_height()),
                            ha="center", va="bottom", fontsize=9)
    st.pyplot(fig3)
else:
    st.caption("최근 30일 업셀 전환주문 없음")

# =========================================
# 6) 3. 성과 제고를 위한 액션
# =========================================
st.markdown('<div class="h1">3. 성과 제고를 위한 액션 🏃🏻</div>', unsafe_allow_html=True)
st.markdown("""
<div class="callout">
<b>💡 체크리스트</b><br>
1) 위젯을 충분히 활용하고 있는가?<br>
2) 구매력이 있는 상위고객에게 추가 구매 이유를 만들고 있는가?
</div>
""", unsafe_allow_html=True)

# (선택) 위젯별 성과 표
if widget_perf_file is not None:
    wdf = pd.read_csv(widget_perf_file)
    st.markdown('<div class="h3">⚡️위젯별 성과</div>', unsafe_allow_html=True)
    st.dataframe(wdf)
else:
    st.caption("위젯별 성과 CSV를 업로드하면 표로 표시됩니다.")

st.markdown('<div class="h3">1️⃣ 추가사용 추천위젯</div>', unsafe_allow_html=True)
st.write("- 구매버튼클릭, 상세페이지 최하단 위젯 등 **구매 의사결정 직전/후** 노출 영역 우선 테스트를 권장.")
st.write("- CTA 바 하단, 장바구니 페이지 등 **다중 접점**에 반복 노출로 함께구매 기회를 극대화.")

st.markdown('<div class="h3">2️⃣ 프로모션 설정 & 상관관계</div>', unsafe_allow_html=True)
st.write("- 금액별/수량별 할인, 묶음 혜택과 업셀 전환주문 **증가 상관**을 A/B로 확인할 것.")
st.caption("※ 프로모션 사례/스크린샷은 선택 자료로 첨부 가능(이미지 업로드/링크).")

st.markdown('<div class="h3">3️⃣ 위젯 타이틀/디자인 최적화</div>', unsafe_allow_html=True)
st.write("- 추가구매를 유도하는 **타이틀 문구**와 **썸네일 비율/테두리** 등 피드 시각매력 개선.")

# =========================================
# 7) 4. 구독료 안내
# =========================================
st.markdown('<div class="h1">4. 구독료 안내</div>', unsafe_allow_html=True)

# 최근 한 달 주문 수
month_cut = df[COL_ORDER_DATE].max() - timedelta(days=29)
recent_month_orders = df[df[COL_ORDER_DATE] >= month_cut][COL_ORDER_ID].nunique()
st.write(f"🌱 최근 한달 주문 수: **{recent_month_orders:,}건**")

st.write("- 월 **~~800,000원~~ 540,000원**(부가세별도) **`엔터프라이즈3`** (월주문수 한도: ~20,000건)")
if enterprise_offer:
    st.write("- `스페셜오퍼` : **한 단계 낮은 플랜으로**")
st.write("- 조건 : 6개월 또는 12개월 선납 (예: 6개월=3,240,000 / 12개월=6,480,000)")

if plan_image is not None:
    st.image(plan_image, caption="알파업셀 구독 플랜 (예시)")

st.markdown("""
> **📌 연간 구독 시** 12개월간 납부한 구독료로 (주문수 연관없이) **추가요금 없이 구독 가능**
""")

# =========================================
# 8) 마무리/주의
# =========================================
st.markdown("---")
st.caption("※ [업셀]함께구매주문금액은 라인금액(또는 단가×수량) 제공 시 산출됩니다. 없는 경우 전환주문/비율, AOV, 상품수는 정상 산출됩니다.")
