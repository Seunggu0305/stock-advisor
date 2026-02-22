"""일일 Top 5 스크리너 패널 컴포넌트"""

import streamlit as st
from datetime import datetime
from scoring.screener import screen_index, get_saved_results, get_all_saved_results, is_result_fresh
from utils.formatters import fmt_price, fmt_pct
from scoring.grade_system import get_grade_color
from models.schemas import Grade


def _freshness_badge(saved: dict | None) -> str:
    """결과 신선도 배지 HTML 반환"""
    if not saved:
        return '<span style="color:#FF4444; font-size:11px;">결과 없음</span>'
    try:
        saved_time = datetime.fromisoformat(saved["analysis_time"])
        hours_ago = (datetime.now() - saved_time).total_seconds() / 3600
        time_str = saved["analysis_time"][:16].replace("T", " ")
        if hours_ago < 24:
            return f'<span style="color:#00FF00; font-size:11px;">오늘 {time_str}</span>'
        elif hours_ago < 48:
            return f'<span style="color:#FFFF00; font-size:11px;">어제 {time_str}</span>'
        else:
            days = int(hours_ago // 24)
            return f'<span style="color:#FF8800; font-size:11px;">{days}일 전 {time_str}</span>'
    except Exception:
        return '<span style="color:#888; font-size:11px;">시간 불명</span>'


def render_screener_tab():
    """일일 Top 5 스크리너 탭"""

    st.markdown("""
    <div style="text-align:center; padding:10px;">
        <h2 style="color:#FFD700; margin:0;">🏆 일일 Top 5 스크리너</h2>
        <p style="color:#888;">매일 자동 갱신 | NASDAQ 100 · S&P 500 · Russell 2000</p>
        <p style="color:#666; font-size:11px;">자동 갱신: GitHub Actions (클라우드) 또는 작업 스케줄러 (로컬)</p>
    </div>
    """, unsafe_allow_html=True)

    # 저장된 결과 표시
    all_saved = get_all_saved_results()

    # 스크리닝 실행 버튼
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    indices = ["NASDAQ 100", "S&P 500", "Russell 2000"]
    cols = [col1, col2, col3]

    for col, index_name in zip(cols, indices):
        with col:
            saved = all_saved.get(index_name)
            st.markdown(_freshness_badge(saved), unsafe_allow_html=True)
            if st.button(f"🔄 {index_name} 스크리닝", key=f"btn_{index_name}", use_container_width=True):
                _run_screening(index_name)

    st.markdown("")

    # 전체 동시 실행 버튼
    if st.button("🚀 전체 인덱스 스크리닝 (시간 소요)", use_container_width=True, type="primary"):
        for index_name in indices:
            _run_screening(index_name)

    st.markdown("---")

    # 결과 표시
    all_saved = get_all_saved_results()  # 새로 실행했을 수 있으므로 다시 로드

    if not all_saved:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#666;">
            <h3>아직 스크리닝 결과가 없습니다</h3>
            <p>위의 버튼을 클릭하거나, 자동 스크리닝을 설정하세요.</p>
            <p style="font-size:12px;">NASDAQ 100: ~5분 | S&P 500: ~25분 | Russell 2000: ~15분 (상위 200 후보)</p>
            <p style="font-size:11px; color:#555;">
                자동 설정: GitHub repo에 push하면 GitHub Actions가 매일 실행<br>
                또는 <code>run_daily_screen.bat</code>을 Windows 작업 스케줄러에 등록
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # 각 인덱스별 Top 5 카드
    for index_name in indices:
        saved = all_saved.get(index_name)
        if not saved:
            continue

        results = saved.get("top_results", [])
        total = saved.get("total_analyzed", 0)
        freshness = _freshness_badge(saved)

        st.markdown(f"""
        <div style="padding:10px 15px; background:#1a1a2e; border-radius:8px; margin-bottom:5px;">
            <span style="color:#FFD700; font-size:18px; font-weight:bold;">
                📊 {index_name} Top 5
            </span>
            <span style="float:right;">
                <span style="color:#666; font-size:12px;">{total}종목 분석 | </span>
                {freshness}
            </span>
        </div>
        """, unsafe_allow_html=True)

        if not results:
            st.info("결과 없음")
            continue

        _render_top5_table(results)
        st.markdown("<br>", unsafe_allow_html=True)


def _run_screening(index_name: str):
    """스크리닝 실행 (프로그레스 바 포함)"""
    progress_bar = st.progress(0, text=f"{index_name} 종목 목록 수집 중...")
    status_text = st.empty()

    def on_progress(current, total, ticker):
        pct = current / total
        progress_bar.progress(pct, text=f"{index_name}: {current}/{total} ({ticker})")

    try:
        results = screen_index(
            index_name,
            top_n=5,
            max_workers=4,
            progress_callback=on_progress,
        )
        progress_bar.progress(1.0, text=f"{index_name} 스크리닝 완료!")
        status_text.success(f"{index_name}: {len(results)}개 Top 종목 선정 완료")
    except Exception as e:
        progress_bar.empty()
        status_text.error(f"{index_name} 스크리닝 실패: {e}")


def _render_top5_table(results: list[dict]):
    """Top 5 결과를 테이블로 렌더링"""
    # 헤더
    header_cols = st.columns([0.5, 1, 2.5, 1.2, 1, 1.2, 1.5, 1.5])
    headers = ["#", "등급", "종목", "점수", "RSI", "주간", "목표가", "최종 신호"]
    for col, header in zip(header_cols, headers):
        with col:
            st.markdown(f"<span style='color:#888; font-size:11px; font-weight:bold;'>{header}</span>",
                       unsafe_allow_html=True)

    # 데이터 행
    for r in results:
        grade = Grade(r["grade"])
        grade_color = get_grade_color(grade)
        score_color = _score_to_color(r["score"])
        weekly_color = "#00FF00" if r.get("weekly_pct", 0) >= 0 else "#FF4444"

        row_cols = st.columns([0.5, 1, 2.5, 1.2, 1, 1.2, 1.5, 1.5])

        with row_cols[0]:
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(r["rank"], f" {r['rank']}")
            st.markdown(f"<span style='font-size:16px;'>{medal}</span>", unsafe_allow_html=True)

        with row_cols[1]:
            st.markdown(
                f"<span style='color:{grade_color}; font-size:20px; font-weight:bold;'>[{r['grade']}]</span>",
                unsafe_allow_html=True)

        with row_cols[2]:
            st.markdown(
                f"<div><span style='color:#00BFFF; font-weight:bold;'>{r['ticker']}</span> "
                f"<span style='color:#888; font-size:11px;'>{r.get('name', '')[:20]}</span><br>"
                f"<span style='color:#FFD700;'>{fmt_price(r['price'])}</span></div>",
                unsafe_allow_html=True)

        with row_cols[3]:
            st.markdown(
                f"<span style='color:{score_color}; font-size:22px; font-weight:bold;'>{r['score']:.0f}</span>",
                unsafe_allow_html=True)

        with row_cols[4]:
            rsi_val = r.get("rsi", 50)
            rsi_color = "#FF4444" if rsi_val > 70 else ("#00FF00" if rsi_val < 30 else "#FFFF00")
            st.markdown(f"<span style='color:{rsi_color};'>{rsi_val:.0f}</span>", unsafe_allow_html=True)

        with row_cols[5]:
            weekly = r.get("weekly_pct", 0)
            st.markdown(f"<span style='color:{weekly_color};'>{fmt_pct(weekly)}</span>",
                       unsafe_allow_html=True)

        with row_cols[6]:
            target_pct = r.get("target_pct", 0)
            st.markdown(f"<span style='color:#00FF00; font-size:12px;'>▲{target_pct:.1f}%</span>",
                       unsafe_allow_html=True)

        with row_cols[7]:
            signal = r.get("signal", "")[:15]
            st.markdown(f"<span style='color:#FFD700; font-size:11px;'>{signal}</span>",
                       unsafe_allow_html=True)

        # 구분선
        st.markdown("<hr style='margin:2px 0; border-color:#1a1a2e;'>", unsafe_allow_html=True)


def _score_to_color(score: float) -> str:
    if score >= 80:
        return "#00FF00"
    elif score >= 65:
        return "#7FFF00"
    elif score >= 45:
        return "#FFFF00"
    elif score >= 25:
        return "#FFA500"
    return "#FF4444"
