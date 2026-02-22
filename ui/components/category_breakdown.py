"""카테고리별 점수 분해 컴포넌트"""

import streamlit as st
from models.schemas import StockAnalysisResult
from config.scoring_weights import SCORING_WEIGHTS
from models.schemas import MacroStatus


def render_category_breakdown(result: StockAnalysisResult):
    """스코어링 6개 카테고리별 하위 지표 점수를 표시 (접기/펼치기)"""

    categories = _build_categories(result)

    st.markdown(
        '<div style="text-align:center;margin-bottom:16px;">'
        '<h3 style="color:#FFD700;margin:0;">카테고리별 점수 분해</h3>'
        '<p style="color:#888;font-size:12px;margin:0;">각 카테고리와 하위 지표의 개별 점수 (0~100)</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 툴팁용 CSS (한 번만 주입)
    st.markdown(_TOOLTIP_STYLE, unsafe_allow_html=True)

    for cat in categories:
        _render_category_section(cat)


# ── 스타일 (details/summary 기반 툴팁) ──
_TOOLTIP_STYLE = """
<style>
details.ind-tip {
    display: inline;
    position: relative;
    margin-left: 4px;
}
details.ind-tip > summary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    background: #444;
    color: #aaa;
    font-size: 9px;
    font-weight: bold;
    cursor: pointer;
    list-style: none;
    vertical-align: middle;
}
details.ind-tip > summary::-webkit-details-marker { display: none; }
details.ind-tip > summary::marker { display: none; content: ""; }
details.ind-tip[open] > summary {
    background: #FFD700;
    color: #0d1117;
}
details.ind-tip > .tip-content {
    display: block;
    background: #2d2d44;
    color: #e0e0e0;
    font-size: 11px;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 4px 0 6px 0;
    line-height: 1.5;
    border: 1px solid #555;
}
</style>
"""


def _build_categories(result: StockAnalysisResult) -> list[dict]:
    """분석 결과에서 카테고리별 데이터를 구성"""

    return [
        {
            "name": "매크로 환경",
            "icon": "🌍",
            "weight": SCORING_WEIGHTS["macro"]["weight"],
            "score": result.macro.score,
            "indicators": [
                {"name": "금리", "score": _status_to_score(result.macro.interest_rate.status),
                 "label": f"{result.macro.interest_rate.value:.2f}% ({result.macro.interest_rate.status.value})",
                 "tooltip": "연준 기준금리와 국채 수익률. 금리 인하기에는 주식에 유리, 인상기에는 불리합니다."},
                {"name": "VIX", "score": _status_to_score(result.macro.vix.status),
                 "label": f"{result.macro.vix.value:.1f} ({result.macro.vix.status.value})",
                 "tooltip": "시장 공포 지수. 15 이하 안정, 20~30 주의, 30 이상 극단적 공포. 역발상 매수 기회가 될 수 있습니다."},
                {"name": "달러 (DXY)", "score": _status_to_score(result.macro.dxy.status) if result.macro.dxy else 50,
                 "label": f"{result.macro.dxy.value:.1f} ({result.macro.dxy.status.value})" if result.macro.dxy else "데이터 없음",
                 "tooltip": "달러 인덱스(DXY). 달러 강세는 미국 다국적기업 실적과 신흥국 자금흐름에 부정적입니다. 달러 약세는 주식에 유리합니다."},
                {"name": "원유", "score": _status_to_score(result.macro.oil.status),
                 "label": f"${result.macro.oil.value:.1f} ({result.macro.oil.status.value})",
                 "tooltip": "국제 유가 동향. 급등 시 인플레이션 우려로 시장에 부정적, 안정 시 긍정적입니다."},
                {"name": "금", "score": _status_to_score(result.macro.gold.status),
                 "label": f"${result.macro.gold.value:,.0f} ({result.macro.gold.status.value})",
                 "tooltip": "안전자산 선호도 지표. 금 가격 상승은 위험 회피 심리를 반영합니다."},
                {"name": "시장 브레드스", "score": result.macro.market_breadth_score,
                 "label": f"{result.macro.market_breadth_score:.0f}점",
                 "tooltip": "S&P500 지수의 SMA20/SMA50 대비 위치로 전반적 시장 건강도를 측정합니다."},
            ],
        },
        {
            "name": "추세 / 모멘텀",
            "icon": "📈",
            "weight": SCORING_WEIGHTS["trend_momentum"]["weight"],
            "score": _calc_category_score("trend_momentum", {
                "trend_direction": result.trend.score,
                "trend_strength": result.trend.score,
                "rsi_macd": result.momentum.score,
                "ichimoku": result.ichimoku.score,
            }),
            "indicators": [
                {"name": "추세 방향/강도", "score": result.trend.score,
                 "label": f"{result.trend.direction.value} ({result.trend.strength.value})",
                 "tooltip": "SMA 20/50/200 정배열 여부와 ADX로 추세 방향과 강도를 판단합니다. 정배열(20>50>200)이면 강한 상승 추세입니다."},
                {"name": "RSI / MACD", "score": result.momentum.score,
                 "label": f"RSI {result.momentum.rsi:.0f} | {result.momentum.macd_signal}",
                 "tooltip": "RSI(30 이하 과매도, 70 이상 과매수)와 MACD 시그널 크로스, 스토캐스틱을 종합한 모멘텀 지표입니다."},
                {"name": "일목균형표", "score": result.ichimoku.score,
                 "label": result.ichimoku.cloud_position,
                 "tooltip": "구름대 위치, 전환선/기준선 크로스, 후행스팬을 분석합니다. 구름 위 = 상승, 구름 내 = 보합, 구름 아래 = 하락입니다."},
            ],
        },
        {
            "name": "거래량 / 수급",
            "icon": "💧",
            "weight": SCORING_WEIGHTS["volume_flow"]["weight"],
            "score": _calc_category_score("volume_flow", {
                "obv_retention": result.volume.score,
                "volume_profile": result.volume.score,
                "institutional_flow": result.institutional_flow.score,
                "options_flow": result.options_flow.score,
            }),
            "indicators": [
                {"name": "OBV / 볼륨 프로파일", "score": result.volume.score,
                 "label": f"OBV {result.volume.obv_retention:.2f}x ({result.volume.obv_label})",
                 "tooltip": "OBV 잔존율은 매수세 유지 정도를 측정합니다. 1.0 이상이면 매수세 우위. 볼륨 프로파일의 POC/VAH/VAL도 함께 분석합니다."},
                {"name": "기관 수급", "score": result.institutional_flow.score,
                 "label": f"보유 {result.institutional_flow.institutional_pct:.0f}% ({result.institutional_flow.change_label})",
                 "tooltip": "기관 투자자 보유 비율과 최근 매수/매도 변동을 추적합니다. 기관 순매수 증가는 긍정적 신호입니다."},
                {"name": "옵션 플로우", "score": result.options_flow.score,
                 "label": f"PCR {result.options_flow.put_call_ratio:.2f} | {result.options_flow.signal}",
                 "tooltip": "풋/콜 비율(PCR)과 내재 변동성 순위. PCR > 1.5이면 과도한 공포(역발상 매수), PCR < 0.5이면 과도한 낙관(주의) 신호입니다."},
            ],
        },
        {
            "name": "패턴 / 구조",
            "icon": "🔮",
            "weight": SCORING_WEIGHTS["pattern_structure"]["weight"],
            "score": _calc_category_score("pattern_structure", {
                "wave_analysis": result.wave.score,
                "fvg_levels": result.fvg.score,
                "fibonacci": result.fibonacci.score,
                "pattern_similarity": result.similarity.score,
                "candlestick": result.candlestick.score,
            }),
            "indicators": [
                {"name": "엘리엇 파동", "score": result.wave.score,
                 "label": f"{result.wave.current_wave} ({result.wave.wave_position})",
                 "tooltip": "ZigZag 알고리즘으로 파동 구조를 감지합니다. 상승 파동(HH/HL)이면 매수 우위, 하락 파동(LH/LL)이면 매도 우위입니다."},
                {"name": "FVG (가격 갭)", "score": result.fvg.score,
                 "label": result.fvg.label,
                 "tooltip": "Fair Value Gap - 3봉 패턴에서 발생한 가격 불균형 영역입니다. 미채워진 갭은 지지/저항으로 작용하며 가격이 되돌아올 가능성이 높습니다."},
                {"name": "피보나치", "score": result.fibonacci.score,
                 "label": result.fibonacci.current_level if result.fibonacci.current_level != "없음"
                 else f"되돌림 {result.fibonacci.retracement_pct:.0f}%",
                 "tooltip": "스윙 고점/저점 기준 되돌림 비율. 38.2~61.8% 구간(골든존)은 건강한 조정 후 반등이 나오기 쉬운 영역입니다."},
                {"name": "패턴 유사도", "score": result.similarity.score,
                 "label": f"{result.similarity.similarity_pct:.0f}% 일치",
                 "tooltip": "현재 가격 패턴과 과거 유사 패턴을 코사인 유사도로 비교합니다. 유사 패턴 이후 수익률이 양수였다면 긍정적 신호입니다."},
                {"name": "캔들스틱", "score": result.candlestick.score,
                 "label": result.candlestick.dominant_signal,
                 "tooltip": "해머, 도지, 장악형, 모닝/이브닝스타 등 6가지 캔들 패턴을 감지합니다. 매수 패턴이 많으면 점수가 올라갑니다."},
            ],
        },
        {
            "name": "퀀트 팩터",
            "icon": "🧮",
            "weight": SCORING_WEIGHTS["quant_factors"]["weight"],
            "score": _calc_category_score("quant_factors", {
                "mean_reversion": result.mean_reversion.score,
                "momentum_factor": result.momentum_factor.score,
                "sector_relative": result.sector_relative.score,
                "earnings_surprise": result.earnings_surprise.score,
                "rsi_divergence": result.rsi_divergence.score,
                "bb_squeeze": result.bb_squeeze.score,
            }),
            "indicators": [
                {"name": "평균 회귀 (Z-Score)", "score": result.mean_reversion.score,
                 "label": f"Z={result.mean_reversion.z_score:.2f} ({result.mean_reversion.signal})",
                 "tooltip": "가격이 SMA50에서 얼마나 벗어났는지 표준편차로 측정합니다. Z < -2 강한 과매도(매수 기회), Z > 2 강한 과매수(주의) 신호입니다."},
                {"name": "모멘텀 팩터", "score": result.momentum_factor.score,
                 "label": result.momentum_factor.rank_label,
                 "tooltip": "퀀트 전략의 12-1 모멘텀: 12개월 수익률에서 최근 1개월을 제외합니다. 단기 반전 효과를 배제한 중장기 모멘텀을 측정합니다."},
                {"name": "섹터 상대강도", "score": result.sector_relative.score,
                 "label": f"{result.sector_relative.sector_name} ({result.sector_relative.sector_rank}/{result.sector_relative.total_sectors}위)",
                 "tooltip": "11개 GICS 섹터 ETF의 1개월 수익률 순위에서 해당 종목 섹터의 위치입니다. 상위 섹터 종목일수록 유리합니다."},
                {"name": "어닝 서프라이즈", "score": result.earnings_surprise.score,
                 "label": f"{result.earnings_surprise.last_surprise_pct:+.1f}% (연속 {result.earnings_surprise.surprise_streak}회)",
                 "tooltip": "실제 EPS vs 예상 EPS 차이(서프라이즈 %)와 연속 비트 횟수입니다. 지속적인 어닝 비트는 주가 상승의 강력한 동력입니다."},
                {"name": "RSI 다이버전스", "score": result.rsi_divergence.score,
                 "label": result.rsi_divergence.divergence_type or "없음",
                 "tooltip": "가격과 RSI의 방향이 엇갈리는 현상입니다. 정규 강세 다이버전스(가격 신저 + RSI 상승)는 반등 신호, 약세 다이버전스는 하락 전환 신호입니다."},
                {"name": "BB 스퀴즈", "score": result.bb_squeeze.score,
                 "label": f"{'진행 중' if result.bb_squeeze.is_squeezing else '해제'} ({result.bb_squeeze.squeeze_duration}일)",
                 "tooltip": "볼린저 밴드가 켈트너 채널 안으로 수축하면 스퀴즈 상태입니다. 변동성 압축 후 큰 방향성 움직임이 나올 가능성이 높습니다."},
            ],
        },
        {
            "name": "리스크 / 특수 신호",
            "icon": "⚡",
            "weight": SCORING_WEIGHTS["risk_special"]["weight"],
            "score": _calc_category_score("risk_special", {
                "short_squeeze": result.short_squeeze.score,
                "special_signals": 50 + len([s for s in result.special_signals
                    if any(kw in s for kw in ["매수", "돌파", "신고"])]) * 10
                    - len([s for s in result.special_signals
                    if any(kw in s for kw in ["매도", "신저", "경고"])]) * 10,
                "complex_patterns": result.complex_patterns.score,
            }),
            "indicators": [
                {"name": "숏스퀴즈", "score": result.short_squeeze.score,
                 "label": f"{result.short_squeeze.potential} (공매도 {result.short_squeeze.short_interest_pct:.1f}%)",
                 "tooltip": "공매도 비율과 커버 소요일(Days to Cover)로 스퀴즈 가능성을 측정합니다. 공매도 20% 이상 + 거래량 급증 시 급등 가능성이 있습니다."},
                {"name": "특수 신호", "score": None,
                 "label": ", ".join(result.special_signals) if result.special_signals else "없음",
                 "tooltip": "거래량 폭발(평균 3배 이상), 갭 상승/하락(2% 이상), 52주 신고/신저 근접, 상대 거래량 이상 등 특이 이벤트를 감지합니다."},
                {"name": "복합 패턴", "score": result.complex_patterns.score,
                 "label": ", ".join(result.complex_patterns.patterns) if result.complex_patterns.patterns else "없음",
                 "tooltip": "여러 지표를 조합한 복합 시나리오 감지: 강한 바닥, 추세 전환 임박, 변동성 폭발, 스마트머니 매집, 강세 돌파 등 7가지 패턴입니다."},
            ],
        },
        {
            "name": "펀더멘털",
            "icon": "📊",
            "weight": SCORING_WEIGHTS["fundamental"]["weight"],
            "score": result.fundamental.score,
            "indicators": [
                {"name": "밸류에이션", "score": result.fundamental.valuation_score,
                 "label": result.fundamental.valuation_label,
                 "tooltip": "Forward P/E, PEG Ratio, EV/EBITDA를 종합한 밸류에이션 평가. PEG < 1이면 성장 대비 저평가, Forward P/E가 낮을수록 유리합니다."},
                {"name": "수익성", "score": result.fundamental.profitability_score,
                 "label": result.fundamental.profitability_label,
                 "tooltip": "ROE(자기자본이익률), 영업이익률, 순이익률을 종합 평가합니다. ROE 15% 이상이면 자본 효율이 뛰어나며 가격 회복력이 높습니다."},
                {"name": "성장성", "score": result.fundamental.growth_score,
                 "label": result.fundamental.growth_label,
                 "tooltip": "매출 성장률, 이익 성장률, 분기 이익 성장률을 분석합니다. 성장 가속 중인 기업은 기술적 돌파 시 모멘텀 지속 가능성이 높습니다."},
                {"name": "재무 건전성", "score": result.fundamental.financial_health_score,
                 "label": result.fundamental.financial_health_label,
                 "tooltip": "부채비율(D/E), 유동비율, 잉여현금흐름(FCF)으로 재무 안정성을 평가합니다. 건전한 재무구조는 하락 시 가격 방어력을 제공합니다."},
                {"name": "배당 안정성", "score": result.fundamental.dividend_score,
                 "label": result.fundamental.dividend_label,
                 "tooltip": "배당수익률과 배당성향(Payout Ratio)을 평가합니다. 무배당 성장주는 중립(50점), 지속 가능한 배당은 가격 하방 지지력을 제공합니다."},
                {"name": "애널리스트 컨센서스", "score": result.fundamental.analyst_score,
                 "label": result.fundamental.analyst_label,
                 "tooltip": "월가 애널리스트 평균 목표가 대비 업사이드와 추천 등급(Buy/Hold/Sell)을 종합합니다. 목표가 업사이드가 클수록 유리합니다."},
                {"name": "인사이더 보유", "score": result.fundamental.insider_score,
                 "label": result.fundamental.insider_label,
                 "tooltip": "경영진/이사회 내부자 지분율. 5~30%가 이상적(이해관계 일치). 너무 높으면 유동성 우려, 너무 낮으면 경영진 신뢰도 의문입니다."},
            ],
        },
    ]


def _calc_category_score(cat_name: str, sub_scores: dict) -> float:
    """카테고리 점수를 서브 가중치로 계산"""
    sw = SCORING_WEIGHTS[cat_name]["sub_weights"]
    total = 0.0
    for key, weight in sw.items():
        total += sub_scores.get(key, 50) * weight
    return round(total, 1)


def _render_category_section(cat: dict):
    """하나의 카테고리 섹션을 st.expander로 렌더링 (접기/펼치기)"""
    score = cat["score"]
    weight_pct = int(cat["weight"] * 100)
    color = _score_color(score)
    bar_width = max(2, min(100, score))

    header = f'{cat["icon"]} {cat["name"]}  —  {score:.0f}점  (비중 {weight_pct}%)'

    with st.expander(header, expanded=False):
        # 카테고리 점수 바
        st.markdown(
            f'<div style="background:#0d1117;border-radius:4px;height:6px;overflow:hidden;margin-bottom:12px;">'
            f'<div style="background:{color};width:{bar_width}%;height:100%;border-radius:4px;"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 하위 지표 렌더링
        for ind in cat["indicators"]:
            _render_indicator_row(ind)


def _render_indicator_row(ind: dict):
    """개별 지표를 st.markdown으로 렌더링"""
    ind_score = ind["score"]
    label = ind["label"]
    tooltip = ind.get("tooltip", "")

    # 툴팁: <details> 기반 (클릭 토글, iframe 불필요)
    tip_html = ""
    if tooltip:
        tip_html = (
            f'<details class="ind-tip">'
            f'<summary>?</summary>'
            f'<div class="tip-content">{tooltip}</div>'
            f'</details>'
        )

    if ind_score is not None:
        ind_color = _score_color(ind_score)
        ind_bar_width = max(2, min(100, ind_score))
        html = (
            f'<div style="padding:4px 0;border-bottom:1px solid #1a1a2e;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="color:#aaa;font-size:12px;">{ind["name"]}{tip_html}</span>'
            f'<span style="color:{ind_color};font-size:13px;font-weight:bold;">{ind_score:.0f}</span>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:8px;margin-top:3px;">'
            f'<div style="flex:1;background:#0d1117;border-radius:3px;height:4px;overflow:hidden;">'
            f'<div style="background:{ind_color};width:{ind_bar_width}%;height:100%;border-radius:3px;"></div>'
            f'</div>'
            f'<span style="color:#888;font-size:11px;min-width:120px;text-align:right;">{label}</span>'
            f'</div>'
            f'</div>'
        )
    else:
        html = (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:4px 0;border-bottom:1px solid #1a1a2e;">'
            f'<span style="color:#aaa;font-size:12px;">{ind["name"]}{tip_html}</span>'
            f'<span style="color:#ccc;font-size:11px;max-width:250px;text-align:right;'
            f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{label}</span>'
            f'</div>'
        )

    st.markdown(html, unsafe_allow_html=True)


def _status_to_score(status: MacroStatus) -> float:
    """매크로 상태를 0~100 점수로 변환"""
    return {
        MacroStatus.STABLE: 80,
        MacroStatus.MIXED: 50,
        MacroStatus.CAUTION: 30,
        MacroStatus.DANGER: 10,
    }.get(status, 50)


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
