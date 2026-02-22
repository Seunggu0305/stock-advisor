"""복합 패턴 인식 - 다중 지표 결합"""

from models.schemas import ComplexPatternResult


def analyze_complex_patterns(all_results: dict) -> ComplexPatternResult:
    """여러 분석 결과를 결합하여 복합 패턴 식별"""
    patterns = []

    trend = all_results.get("trend")
    momentum = all_results.get("momentum")
    volume = all_results.get("volume")
    rsi_div = all_results.get("rsi_divergence")
    bb_sq = all_results.get("bb_squeeze")
    fvg = all_results.get("fvg")

    if not all([trend, momentum, volume]):
        return ComplexPatternResult()

    # 1. 강력 바닥 과매도
    if (momentum.rsi < 30 and
        volume.obv_label != "약함" and
        trend.score < 40):
        if rsi_div and rsi_div.divergence_type and "강세" in rsi_div.divergence_type:
            patterns.append("강력 바닥 (과매도 + RSI 강세 다이버전스)")
        else:
            patterns.append("강력 바닥 (과매도)")

    # 2. 추세 전환 임박
    if (momentum.cross_type and "데드크로스" in momentum.cross_type and
        momentum.rsi > 40 and
        rsi_div and rsi_div.divergence_type and "강세" in rsi_div.divergence_type):
        patterns.append("추세 전환 임박 (데드크로스 + 강세 다이버전스)")

    # 3. 폭발 직전 수축
    if (bb_sq and bb_sq.is_squeezing and bb_sq.squeeze_duration >= 5 and
        trend.adx < 20):
        patterns.append("변동성 폭발 임박 (BB 스퀴즈)")

    # 4. 스마트머니 매집
    if (volume.obv_retention > 0.8 and
        trend.score > 40 and trend.score < 60 and
        volume.price_vs_vwap == "아래"):
        patterns.append("스마트머니 매집 (OBV 강세 + 가격 횡보)")

    # 5. 하락 가속
    if (momentum.cross_type and "데드크로스" in momentum.cross_type and
        trend.adx > 25 and
        volume.obv_label == "약함"):
        patterns.append("하락 가속 (데드크로스 + 거래량 이탈)")

    # 6. 강세 돌파
    if (trend.score > 70 and
        momentum.rsi > 60 and momentum.rsi < 80 and
        volume.obv_label == "강함"):
        patterns.append("강세 돌파 (추세 + 모멘텀 + 거래량 정렬)")

    # 7. FVG 지지 확인
    if fvg and fvg.nearest_support_gap and fvg.score > 65:
        patterns.append("FVG 지지 구간 도달")

    # 점수: 강세 패턴이 많으면 높은 점수
    bullish_count = sum(1 for p in patterns if any(kw in p for kw in ["바닥", "매집", "돌파", "전환", "FVG 지지"]))
    bearish_count = sum(1 for p in patterns if any(kw in p for kw in ["하락", "가속"]))
    explosive_count = sum(1 for p in patterns if "폭발" in p)

    score = 50
    score += bullish_count * 10
    score -= bearish_count * 10
    score += explosive_count * 5

    return ComplexPatternResult(
        patterns=patterns,
        score=round(max(0, min(100, score)), 1),
    )
