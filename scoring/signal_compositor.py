"""최종 시그널 라벨 합성"""

from models.schemas import Grade


def compose_signal(score: float, grade: Grade, all_results: dict) -> str:
    """종합 시그널 라벨 생성"""
    momentum = all_results.get("momentum")
    trend = all_results.get("trend")
    volume = all_results.get("volume")
    bb_sq = all_results.get("bb_squeeze")
    rsi_div = all_results.get("rsi_divergence")
    mean_rev = all_results.get("mean_reversion")
    complex_p = all_results.get("complex_patterns")

    # 복합 패턴이 있으면 우선 사용
    if complex_p and complex_p.patterns:
        return complex_p.patterns[0]

    # 규칙 기반 시그널
    rsi = momentum.rsi if momentum else 50

    # 강력 바닥
    if rsi < 30 and score > 60:
        if rsi_div and rsi_div.divergence_type and "강세" in rsi_div.divergence_type:
            return "강력 바닥 (과매도 + 강세 다이버전스)"
        return "강력 바닥 (과매도)"

    # 펀더멘털 + 기술적 동시 매수
    fundamental = all_results.get("fundamental")
    if score >= 70 and fundamental and fundamental.score > 70:
        if trend and trend.score > 60:
            return "펀더멘털 + 기술적 동시 매수 신호"

    # 강세 돌파
    if score >= 75 and trend and trend.score > 70:
        return "강세 돌파 매수"

    # 변동성 폭발
    if bb_sq and bb_sq.is_squeezing and bb_sq.squeeze_duration >= 5:
        if bb_sq.expected_direction == "상승":
            return "변동성 폭발 임박 (상승)"
        elif bb_sq.expected_direction == "하락":
            return "변동성 폭발 임박 (하락)"
        return "변동성 폭발 임박"

    # 평균 회귀
    if mean_rev and mean_rev.z_score < -2:
        return "극단적 과매도 (평균 회귀 기대)"
    if mean_rev and mean_rev.z_score > 2:
        return "극단적 과매수 (하락 회귀 주의)"

    # 과매수 경고
    if rsi > 70 and score < 40:
        return "과매수 경고"

    # 하락 추세 강화
    if score < 25:
        return "강한 하락 신호"

    # 등급 기반 기본 시그널
    grade_signals = {
        Grade.A: "강력 매수 신호",
        Grade.B: "매수 고려",
        Grade.C: "중립 관망",
        Grade.D: "매도 고려",
        Grade.F: "강력 매도 신호",
    }
    return grade_signals.get(grade, "분석 완료")
