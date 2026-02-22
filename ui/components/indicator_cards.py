"""기술지표 카드 그리드 컴포넌트"""

import streamlit as st
from models.schemas import StockAnalysisResult
from utils.formatters import fmt_pct


def render_indicator_cards(result: StockAnalysisResult):
    """모든 기술지표를 카드 그리드로 표시"""

    indicators = [
        {
            "title": "추세",
            "value": f"{result.trend.direction.value} ({result.trend.strength.value})",
            "color": _score_color(result.trend.score),
        },
        {
            "title": "주간 성과 (1W)",
            "value": fmt_pct(result.weekly_performance_pct),
            "color": "#00FF00" if result.weekly_performance_pct > 0 else "#FF4444",
        },
        {
            "title": "파동",
            "value": f"{result.wave.current_wave} ({result.wave.wave_position})",
            "color": _score_color(result.wave.score),
        },
        {
            "title": "달/갭",
            "value": f"{result.lunar_phase.phase_emoji} {result.lunar_phase.phase_name} | {result.fvg.label}",
            "color": _score_color(result.fvg.score),
        },
        {
            "title": "에너지",
            "value": result.momentum.energy_label,
            "color": _score_color(result.momentum.score),
        },
        {
            "title": "패턴 유사",
            "value": f"{result.similarity.similarity_pct}% (참조수익률 {result.similarity.reference_return_pct}%)",
            "color": _score_color(result.similarity.score),
        },
        {
            "title": "OBV 잔존율",
            "value": f"{result.volume.obv_retention:.2f}x ({result.volume.obv_label})",
            "color": _score_color(result.volume.score),
        },
        {
            "title": "숏스퀴즈 잠재력",
            "value": f"{result.short_squeeze.potential} (공매도 {result.short_squeeze.short_interest_pct}%, Days {result.short_squeeze.days_to_cover})",
            "color": _score_color(result.short_squeeze.score),
        },
        {
            "title": "RSI 다이버전스",
            "value": result.rsi_divergence.divergence_type or "없음",
            "color": _score_color(result.rsi_divergence.score),
        },
        {
            "title": "BB 스퀴즈",
            "value": f"{'진행 중' if result.bb_squeeze.is_squeezing else '해제'} ({result.bb_squeeze.squeeze_duration}일)" + (f" → {result.bb_squeeze.expected_direction}" if result.bb_squeeze.expected_direction else ""),
            "color": _score_color(result.bb_squeeze.score),
        },
        {
            "title": "일목균형표",
            "value": f"{result.ichimoku.cloud_position}" + (f" | {result.ichimoku.tenkan_kijun_cross}" if result.ichimoku.tenkan_kijun_cross else ""),
            "color": _score_color(result.ichimoku.score),
        },
        {
            "title": "VWAP",
            "value": f"VWAP {result.volume.price_vs_vwap} (${result.volume.vwap:.2f})",
            "color": _score_color(result.volume.score),
        },
        {
            "title": "섹터 강도",
            "value": f"{result.sector_relative.sector_name} ({result.sector_relative.sector_rank}/{result.sector_relative.total_sectors}위)",
            "color": _score_color(result.sector_relative.score),
        },
        {
            "title": "옵션 PCR",
            "value": f"{result.options_flow.put_call_ratio:.2f} {result.options_flow.signal}",
            "color": _score_color(result.options_flow.score),
        },
        {
            "title": "피보나치",
            "value": result.fibonacci.current_level if result.fibonacci.current_level != "없음" else f"되돌림 {result.fibonacci.retracement_pct:.0f}%",
            "color": _score_color(result.fibonacci.score),
        },
        {
            "title": "평균 회귀",
            "value": f"Z={result.mean_reversion.z_score:.2f} ({result.mean_reversion.signal})",
            "color": _score_color(result.mean_reversion.score),
        },
        {
            "title": "모멘텀 팩터",
            "value": f"{result.momentum_factor.momentum_score:.0f}점 ({result.momentum_factor.rank_label})",
            "color": _score_color(result.momentum_factor.score),
        },
        {
            "title": "캔들스틱",
            "value": ", ".join(result.candlestick.patterns) if result.candlestick.patterns else "특이 패턴 없음",
            "color": _score_color(result.candlestick.score),
        },
        {
            "title": "특수 신호",
            "value": ", ".join(result.special_signals) if result.special_signals else "없음",
            "color": "#FFFF00" if result.special_signals else "#888",
        },
        {
            "title": "복합 패턴",
            "value": ", ".join(result.complex_patterns.patterns) if result.complex_patterns.patterns else "없음",
            "color": _score_color(result.complex_patterns.score),
        },
    ]

    # 최종 신호 (큰 카드)
    st.markdown(f"""
    <div style="text-align:center; padding:15px; background:#1a1a2e; border-radius:8px;
                border:2px solid {_score_color(result.ai_score)}; margin-bottom:15px;">
        <span style="color:#FFD700; font-size:16px; font-weight:bold;">
            최종 신호: {result.final_signal}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 3열 그리드로 표시
    cols_per_row = 3
    for i in range(0, len(indicators), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(indicators):
                ind = indicators[idx]
                with col:
                    st.markdown(f"""
                    <div style="padding:10px; background:#0d1117; border-radius:8px;
                                border-left:3px solid {ind['color']}; margin-bottom:8px;">
                        <div style="color:#888; font-size:11px;">{ind['title']}</div>
                        <div style="color:{ind['color']}; font-size:13px; font-weight:bold; margin-top:3px;">
                            {ind['value']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


def _score_color(score: float) -> str:
    if score >= 70:
        return "#00FF00"
    elif score >= 55:
        return "#7FFF00"
    elif score >= 45:
        return "#FFFF00"
    elif score >= 30:
        return "#FFA500"
    else:
        return "#FF4444"
