import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# ----------------------------
# Page / Style
# ----------------------------
st.set_page_config(page_title="Order Report v2 (Narrative)", layout="wide")

REPORT_WIDTH = 820

st.markdown(
    f"""
    <style>
    .block-container {{
        max-width: {REPORT_WIDTH}px !important;
        margin-left: 50px !important;
        margin-right: auto !important;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        line-height: 1.5;
    }}
    .report-title {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .report-subtle {{
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 18px;
    }}
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin: 8px 0 18px 0;
    }}
    .kpi-card {{
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 14px 16px;
        background: #fafafa;
    }}
    .kpi-label {{
        font-size: 12px;
        color: #6b7280;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 18px;
        font-weight: 700;
    }}
    .callout {{
        border-left: 4px solid #2563eb;
        background: #f3f8ff;
        padding: 12px 14px;
        margin: 12px 0;
        border-radius: 6px;
        font-size: 14px;
    }}
    .h2 {{
        font-size: 20px;
        font-weight: 700;
        margin-top: 22px;
        margin-bottom: 10px;
    }}
    .h3 {{
        font-size: 16px;
        font-weight: 700;
        margin-top: 14px;
        margin-bottom: 6px;
    }}
    .mono {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 13px;
        color: #374151;
    }}
    ul.tight > li {{ margin-bottom: 4px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="report-title">주문 리포트 (자동 요약 & 인사이트)</div>', unsafe_allow_html=True)
st.markdown('<div class="report-subtle">Order Report v2 — 본문 800px, 내러티브/시각화/다운로드 포함</div>', unsafe_allow_html=True)

# ----------------------------
# Sidebar (TOC)
# ----------------------------
with st.sidebar:
    st.header("보고서 목차")
    st.markdown(
        """
- 개요/요약
- 핵심 지표
- 상세 분석
  - 회원 vs 비회원
  - 객단가 분포(전체/업셀)
  - 주문별 상품수 분포
- 자동 생성 인사이트
- 부록(정의/가정)
        """
    )
    st.divider()
    st.caption("CSV 컬럼 최소 요구: 주문번호, 총 주문 금액, 주문자 아이디, 일반/업셀 구분, 주문일")

# ----------------------------
# Upload
# ----------------------------
uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")

# ----------------------------
# Helpers
# ----------------------------
REQUIRED_COLS = ["주문번호", "총 주문 금액", "주문자 아이디", "일반/업셀 구분", "주문일"]

def check_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    return missing

def format_money(x):
    try:
        return f"{x:,.0f} KRW"
    except Exception:
        return "-"

@st.cache_data(show_spinner=False)
def load_and_prepare(file):
    df = pd.read_csv(file)
    miss = check_columns(df)
    if miss:
        raise ValueError(f"누락 컬럼: {', '.join(miss)}")

    # typing
    df["총 주문 금액"] = pd.to_numeric(df["총 주문 금액"], errors="coerce")
    df["주문일"] = pd.to_datetime(df["주문일"], errors="coerce")

    # 유효 주문만 (금액>0 & 날짜 존재)
    df = df[(df["총 주문 금액"] > 0) & (df["주문일"].notna())].copy()

    # 중복 주문번호 제거: 업셀 우선 보존
    data = df.sort_values(by=["일반/업셀 구분"], ascending=False).drop_duplicates(subset=["주문번호"], keep="last").copy()

    # 분석 기간
    start_dt = df["주문일"].min()
    end_dt = df["주문일"].max()
    period_days = int((end_dt - start_dt).days) + 1

    # 회원여부
    data["회원여부"] = data["주문자 아이디"].apply(lambda x: "Guest" if pd.isna(x) or str(x).strip() == "" else "Member")

    return df, data, start_dt, end_dt, period_days

def price_bucket(series: pd.Series, top_cap=200_000, step=10_000):
    b = (series // step) * step
    b = b.apply(lambda x: top_cap if x > top_cap else x)
    full = pd.Series([i * step for i in range(top_cap // step + 1)])
    vc = b.value_counts().reindex(full, fill_value=0).sort_index()
    labels = [f">{top_cap//step}.0" if v == top_cap else f"{v//step}.0" for v in vc.index]
    return vc, labels, full

def fig_bar(x_idx, y_vals, title, xlabel, ylabel, width=8000):
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bars = ax.bar(x_idx, y_vals, width=width)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x_idx)
    ax.set_xticklabels(x_idx, rotation=45)
    for bar in bars:
        y = bar.get_height()
        ax.text(bar.get_x()+bar.get_width()/2, y, f"{y:.0f}" if isinstance(y, (int,float)) else y, ha="center", va="bottom", fontsize=9)
    ax.margins(x=0.01)
    return fig

def fig_pie(labels, values, title):
    fig, ax = plt.subplots(figsize=(6.8, 6.8))
    explode = [0.03] * len(values)
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct="%1.1f%%",
                                      startangle=0, explode=explode, pctdistance=0.8, labeldistance=1.05)
    ax.set_title(title)
    ax.axis("equal")
    for t in texts:
        t.set_fontsize(11)
    for at in autotexts:
        at.set_fontsize(10)
    return fig

def to_html_report(title, period, kpis, summary_lines, insights_lines):
    # 간단한 자체 HTML 템플릿 (차트 이미지는 Streamlit 내 렌더; 다운로드는 텍스트 보고서 기준)
    kpi_html = "".join([f"""
      <div style="border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;background:#fafafa;">
        <div style="font-size:12px;color:#6b7280">{label}</div>
        <div style="font-size:18px;font-weight:700">{value}</div>
      </div>
    """ for label, value in kpis])

    return f"""
    <html>
    <head><meta charset="utf-8"><title>{title}</title></head>
    <body style="font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,'Apple Color Emoji','Segoe UI Emoji';">
      <h1 style="margin-bottom:6px;">{title}</h1>
      <div style="color:#6b7280;">{period}</div>

      <h2>요약</h2>
      <ul>
        {''.join(f'<li>{line}</li>' for line in summary_lines)}
      </ul>

      <h2>핵심 지표</h2>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
        {kpi_html}
      </div>

      <h2>자동 생성 인사이트</h2>
      <ul>
        {''.join(f'<li>{line}</li>' for line in insights_lines)}
      </ul>

      <hr/>
      <div style="font-size:12px;color:#6b7280;">
        ※ 본 보고서는 업로드된 CSV의 유효 주문(금액>0)을 기준으로 자동 생성되었습니다.
      </div>
    </body>
    </html>
    """

# ----------------------------
# Main
# ----------------------------
if uploaded_file is None:
    st.info("샘플이 아니라 **실제 주문 내역 CSV**를 업로드하세요. (필수 컬럼: 주문번호, 총 주문 금액, 주문자 아이디, 일반/업셀 구분, 주문일)")
else:
    try:
        raw_data, data, start_dt, end_dt, period_days = load_and_prepare(uploaded_file)

        # ----------------------------
        # KPIs
        # ----------------------------
        total_revenue = float(data["총 주문 금액"].sum())
        avg_order_value = float(data["총 주문 금액"].mean()) if len(data) else 0.0
        total_orders = int(len(data))

        st.markdown('<div class="h2">개요 / 요약</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="report-subtle">분석 기간: <span class="mono">{start_dt.strftime("%Y-%m-%d")} ~ {end_dt.strftime("%Y-%m-%d")}</span> '
            f'(<span class="mono">{period_days}일</span>)</div>',
            unsafe_allow_html=True,
        )

        # 자동 요약 문장
        share_member = (data["회원여부"].value_counts(normalize=True).get("Member", 0) * 100.0)
        upsell_orders = data[data["일반/업셀 구분"] == "업셀 상품"]
        upsell_share = (len(upsell_orders) / total_orders * 100.0) if total_orders else 0.0

        # 가격대 최빈 구간
        price_counts, price_labels, price_index = price_bucket(data["총 주문 금액"])
        top_bucket_idx = int(price_counts.values.argmax()) if len(price_counts) else 0
        top_bucket_label = price_labels[top_bucket_idx] if price_labels else "-"

        summary_lines = [
            f"총 매출 {format_money(total_revenue)}, 총 주문 {total_orders:,}건, 평균 객단가 {format_money(avg_order_value)}.",
            f"회원 주문 비중은 약 {share_member:.1f}%. 업셀 주문 비중은 약 {upsell_share:.1f}%.",
            f"가장 빈도가 높은 결제 금액대는 '{top_bucket_label} 만원대' 구간.",
        ]
        st.markdown('<div class="callout">' + "<br/>".join(summary_lines) + "</div>", unsafe_allow_html=True)

        # KPI 그리드
        st.markdown('<div class="h2">핵심 지표</div>', unsafe_allow_html=True)
        kpi_items = [
            ("전체 매출", format_money(total_revenue)),
            ("평균 객단가 (AOV)", format_money(avg_order_value)),
            ("총 주문 수", f"{total_orders:,} 건"),
        ]
        st.markdown('<div class="kpi-grid">' + "".join(
            [f'<div class="kpi-card"><div class="kpi-label">{k}</div><div class="kpi-value">{v}</div></div>' for k, v in kpi_items]
        ) + '</div>', unsafe_allow_html=True)

        # ----------------------------
        # 상세 분석
        # ----------------------------
        st.markdown('<div class="h2">상세 분석</div>', unsafe_allow_html=True)

        # 1) 회원 vs 비회원
        st.markdown('<div class="h3">1) 회원 vs Guest 주문 비중</div>', unsafe_allow_html=True)
        member_counts = data["회원여부"].value_counts()
        st.dataframe(member_counts.rename_axis("구분").to_frame("건수"))

        fig1 = fig_pie(member_counts.index.tolist(), member_counts.values.tolist(), "Order Share (Member vs Guest)")
        st.pyplot(fig1)

        # 2) 객단가 분포 (전체)
        st.markdown('<div class="h3">2) 객단가 분포 — 전체 주문</div>', unsafe_allow_html=True)
        order_counts = price_counts
        st.dataframe(order_counts.rename_axis("만원대 구간").to_frame("주문 건수"))

        fig2 = fig_bar(price_labels, order_counts.values, "Distribution of Order Prices (All Orders)", "만원대 구간", "건수", width=0.8)
        st.pyplot(fig2)

        order_pct = (order_counts / order_counts.sum() * 100.0) if order_counts.sum() else order_counts*0
        fig3 = fig_bar(price_labels, order_pct.values, "Order Price Distribution by % (All Orders)", "만원대 구간", "비중(%)", width=0.8)
        st.pyplot(fig3)

        # 3) 객단가 분포 (업셀)
        st.markdown('<div class="h3">3) 객단가 분포 — 업셀 주문</div>', unsafe_allow_html=True)
        upsell_data = data[data["일반/업셀 구분"] == "업셀 상품"]
        if upsell_data.empty:
            st.caption("업셀 주문이 없습니다.")
        else:
            up_counts, up_labels, _ = price_bucket(upsell_data["총 주문 금액"])
            st.dataframe(up_counts.rename_axis("만원대 구간").to_frame("업셀 주문 건수"))

            fig4 = fig_bar(up_labels, up_counts.values, "Distribution of Order Prices (Upsell Orders)", "만원대 구간", "건수", width=0.8)
            st.pyplot(fig4)

            up_pct = (up_counts / up_counts.sum() * 100.0) if up_counts.sum() else up_counts*0
            fig5 = fig_bar(up_labels, up_pct.values, "Order Price Distribution by % (Upsell)", "만원대 구간", "비중(%)", width=0.8)
            st.pyplot(fig5)

        # 4) 주문별 상품수 분포
        st.markdown('<div class="h3">4) 주문별 상품수 분포</div>', unsafe_allow_html=True)
        order_items = raw_data.groupby("주문번호").size().reset_index(name="ItemCount")
        dist = order_items["ItemCount"].value_counts().sort_index()
        st.dataframe(dist.rename_axis("상품수").to_frame("주문 건수"))

        # 파이(3% 미만 Others)
        total_item_orders = dist.sum()
        labels, vals, others_sum = [], [], 0
        for k, v in dist.items():
            pct = (v / total_item_orders) * 100 if total_item_orders else 0
            if pct < 3:
                others_sum += v
            else:
                labels.append(str(k))
                vals.append(v)
        if others_sum > 0:
            labels.append("Others")
            vals.append(others_sum)
        fig6 = fig_pie(labels, vals, "Distribution of Items per Order (Pie)")
        st.pyplot(fig6)

        # 바차트(원본)
        fig7, ax_items_bar = plt.subplots(figsize=(10, 5.6))
        bars = ax_items_bar.bar(dist.index.astype(str), dist.values)
        ax_items_bar.set_xlabel("주문별 상품 수")
        ax_items_bar.set_ylabel("주문 건수")
        ax_items_bar.set_title("Distribution of Items per Order (Bar)")
        for b in bars:
            y = b.get_height()
            ax_items_bar.text(b.get_x()+b.get_width()/2, y, int(y), ha="center", va="bottom", fontsize=9)
        st.pyplot(fig7)

        # ----------------------------
        # 자동 생성 인사이트 (간단 규칙 기반)
        # ----------------------------
        st.markdown('<div class="h2">자동 생성 인사이트</div>', unsafe_allow_html=True)
        insights = []

        # 회원 비중
        if share_member >= 70:
            insights.append(f"회원 비중이 {share_member:.1f}%로 높음 → 회원 등급/리텐션 프로모션 최적화 여지.")
        elif share_member <= 40:
            insights.append(f"회원 비중이 {share_member:.1f}%로 낮음 → 간편가입/첫구매 유도 인센티브 검토 필요.")

        # 업셀 비중
        if upsell_share >= 15:
            insights.append(f"업셀 주문 비중 {upsell_share:.1f}% → 업셀 구성/위치 유지 혹은 확대 테스트 권장.")
        elif 0 < upsell_share < 8:
            insights.append(f"업셀 주문 비중 {upsell_share:.1f}% → 페이지 진입 위치/카피/가격대 재검토 필요.")

        # 최빈 가격대
        if top_bucket_label not in ("-",):
            try:
                bucket_val = float(top_bucket_label.replace(">", ""))  # e.g., '12.0' or '>20.0'
            except Exception:
                bucket_val = None
            if bucket_val is not None and bucket_val <= 5:
                insights.append("저가 구간 집중 → 번들/목표 AOV 상향 프로모션 고려.")
            elif bucket_val is not None and bucket_val >= 15:
                insights.append("고가 구간 비중 ↑ → 고가 제품 리뷰/보증/혜택 강조로 전환 방어.")
        
        # 주문별 상품수
        if not dist.empty:
            mode_items = dist.idxmax()
            if mode_items == 1:
                insights.append("단품 구매가 다수 → 관련 액세서리/보완재 추천 카드 강화.")
            elif mode_items >= 3:
                insights.append("다품목 구매 성향 → 묶음/세트 할인 메시지 테스트.")

        if not insights:
            insights.append("특이점 없음. 데이터 확대 혹은 기간 분할(주/월별) 비교로 추가 패턴 탐색 권장.")

        st.markdown("- " + "\n- ".join(insights))

        # ----------------------------
        # 부록
        # ----------------------------
        st.markdown('<div class="h2">부록: 정의/가정</div>', unsafe_allow_html=True)
        st.markdown(
            """
- **유효 주문**: `총 주문 금액 > 0` & `주문일` 존재
- **중복 제거**: 동일 `주문번호` 존재 시 `일반/업셀 구분` 기준으로 업셀 우선 보존
- **가격대 구간**: 1만원 단위, 20만원 초과는 `>20.0`으로 집계
- **회원여부**: `주문자 아이디` 비어있으면 Guest, 아니면 Member
            """
        )

        # ----------------------------
        # 보고서 다운로드(HTML/Markdown)
        # ----------------------------
        st.markdown('<div class="h2">보고서 다운로드</div>', unsafe_allow_html=True)

        period_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')} ({period_days}일)"
        html_doc = to_html_report(
            "주문 리포트 (자동 요약본)",
            f"분석 기간: {period_str}",
            kpi_items,
            summary_lines,
            insights
        )
        st.download_button("요약 보고서 HTML 다운로드", data=html_doc.encode("utf-8"), file_name="order_report_summary.html", mime="text/html")

        md_lines = [
            "# 주문 리포트 (자동 요약본)",
            f"- 분석 기간: **{period_str}**",
            "",
            "## 요약",
            *[f"- {s}" for s in summary_lines],
            "",
            "## 핵심 지표",
            *[f"- {k}: {v}" for k, v in kpi_items],
            "",
            "## 자동 생성 인사이트",
            *[f"- {s}" for s in insights],
            "",
            "> 본 보고서는 업로드된 CSV의 유효 주문(금액>0)을 기준으로 자동 생성되었습니다.",
        ]
        md_text = "\n".join(md_lines)
        st.download_button("요약 보고서 Markdown 다운로드", data=md_text.encode("utf-8"), file_name="order_report_summary.md", mime="text/markdown")

    except ValueError as ve:
        st.error(str(ve))
    except Exception as e:
        st.exception(e)
