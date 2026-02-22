"""Streamlit 대시보드 메인"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from main import run_analysis
from ui.components.macro_bar import render_macro_bar
from ui.components.score_card import render_score_card
from ui.components.price_chart import render_price_chart
from ui.components.target_panel import render_target_panel
from ui.components.alert_panel import render_alert_panel
from ui.components.category_breakdown import render_category_breakdown
from ui.components.screener_panel import render_screener_tab
from utils.formatters import fmt_price, fmt_pct

# ── 페이지 설정 ──
st.set_page_config(
    page_title="Stock Advisor - AI 투자 진입 분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 다크 테마 CSS ──
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #e6e6e6;
    }
    .stTextInput > div > div > input {
        background-color: #1a1a2e;
        color: #e6e6e6;
        border: 1px solid #333;
        font-size: 18px;
        text-align: center;
    }
    .stButton > button {
        background-color: #1a1a2e;
        color: #e0be36;
        border: 1px solid #e0be36;
        font-size: 16px;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #e0be36;
        color: #0d1117;
    }
    div[data-testid="stMetricValue"] {
        color: #e0be36;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a2e;
        color: #e0be36;
        border-radius: 8px;
        padding: 10px 24px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0be36 !important;
        color: #0d1117 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ──
st.markdown("""
<div style="text-align:center; padding:10px;">
    <h1 style="color:#e0be36; margin:0;">📊 Stock Advisor</h1>
    <p style="color:#888; margin:0;">AI 기반 투자 진입 점수 분석</p>
</div>
""", unsafe_allow_html=True)

# ── 탭 구조 ──
tab_analysis, tab_screener = st.tabs(["🔍 종목 분석", "🏆 주간 Top 5 스크리너"])

# ═══════════════════════════════════════
# 탭 1: 개별 종목 분석
# ═══════════════════════════════════════
with tab_analysis:
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input(
            "티커 입력",
            placeholder="예: AAPL, TSLA, MSFT, APP",
            label_visibility="collapsed",
        )
    with col2:
        analyze_btn = st.button("🔍 분석 시작", use_container_width=True)

    if (analyze_btn or ticker) and ticker:
        with st.spinner(f"{ticker.upper()} 분석 중... (데이터 수집 및 33개 지표 계산)"):
            try:
                result = run_analysis(ticker)
            except Exception as e:
                st.error(f"분석 오류: {e}")
                st.stop()

        # ── 매크로 바 ──
        st.markdown("<br>", unsafe_allow_html=True)
        render_macro_bar(result.macro)

        st.markdown("---")

        # ── 상단: 종목 정보 + 차트 | 점수 카드 ──
        left_col, right_col = st.columns([3, 2])

        with left_col:
            st.markdown(f"""
            <div style="padding:10px;">
                <h2 style="color:#42a5f5; margin:0;">{result.company_name}</h2>
                <h3 style="color:#e0be36; margin:0;">{result.ticker} &nbsp;
                    <span style="color:#{'26a69a' if result.weekly_performance_pct >= 0 else 'ef5350'};">
                        {fmt_price(result.current_price)} {fmt_pct(result.weekly_performance_pct)}
                    </span>
                </h3>
            </div>
            """, unsafe_allow_html=True)

            # 가격 차트
            from data.yahoo_client import get_stock_data
            price_data = get_stock_data(ticker)
            fig = render_price_chart(price_data, result.ticker)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        with right_col:
            render_score_card(result.ai_score, result.grade, result.previous_score)

        st.markdown("---")

        # ── 카테고리별 점수 분해 ──
        render_category_breakdown(result)

        st.markdown("---")

        # ── 목표가/손절가 ──
        render_target_panel(result.price_target)

        st.markdown("---")

        # ── 알림 ──
        if result.alerts:
            st.markdown("<br>", unsafe_allow_html=True)
            render_alert_panel(result.alerts)

        # ── 분석 시간 ──
        st.markdown(f"""
        <div style="text-align:center; color:#555; font-size:11px; margin-top:20px;">
            분석 시간: {result.analysis_time.strftime('%Y-%m-%d %H:%M:%S')} |
            면책: 이 분석은 투자 자문이 아닙니다. 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
        </div>
        """, unsafe_allow_html=True)

    elif not ticker:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#666;">
            <h3>티커를 입력하고 분석을 시작하세요</h3>
            <p>미국 주식 티커를 입력하면 30개 이상의 기술적/퀀트/펀더멘털 지표를 분석하여<br>
            AI 투자 진입 점수(0~100)와 등급(A~F)을 산출합니다.</p>
            <p style="color:#444; font-size:12px;">
                분석 항목: 매크로 환경 | 추세/모멘텀 | 거래량/수급 | 패턴/구조 | 퀀트 팩터 | 리스크/특수 신호 | 펀더멘털
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# 탭 2: 주간 Top 5 스크리너
# ═══════════════════════════════════════
with tab_screener:
    render_screener_tab()
