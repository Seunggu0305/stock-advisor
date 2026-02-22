"""알림 메시지 생성"""


def generate_alerts(all_results: dict, current_price: float) -> list[str]:
    """분석 결과 기반 알림 메시지 생성"""
    alerts = []

    # FVG 지지/저항 근접
    fvg = all_results.get("fvg")
    if fvg:
        if fvg.nearest_support_gap:
            dist = abs(current_price - fvg.nearest_support_gap) / current_price * 100
            if dist < 2:
                alerts.append(f"[!] FVG(Gap) 지지 구간 도달! ({fvg.nearest_support_gap})")
        if fvg.nearest_resistance_gap:
            dist = abs(fvg.nearest_resistance_gap - current_price) / current_price * 100
            if dist < 2:
                alerts.append(f"[!] FVG(Gap) 저항 구간 근접! ({fvg.nearest_resistance_gap})")

    # RSI 과매도/과매수
    momentum = all_results.get("momentum")
    if momentum:
        if momentum.rsi < 25:
            alerts.append(f"[!] RSI 극단적 과매도 ({momentum.rsi})")
        elif momentum.rsi > 80:
            alerts.append(f"[!] RSI 극단적 과매수 ({momentum.rsi})")
        if momentum.cross_type and "근접" not in str(momentum.cross_type):
            if "골든" in str(momentum.cross_type):
                alerts.append("[!] 골든크로스 발생!")
            elif "데드" in str(momentum.cross_type):
                alerts.append("[!] 데드크로스 발생!")

    # BB 스퀴즈
    bb_sq = all_results.get("bb_squeeze")
    if bb_sq and bb_sq.is_squeezing and bb_sq.squeeze_duration >= 10:
        alerts.append(f"[!] 볼린저 스퀴즈 {bb_sq.squeeze_duration}일 지속 - 폭발 임박")

    # 어닝 임박
    earnings = all_results.get("earnings_surprise")
    if earnings and earnings.next_earnings_date and earnings.next_earnings_date != "N/A":
        alerts.append(f"[i] 다음 어닝 발표: {earnings.next_earnings_date}")

    # 숏스퀴즈
    ss = all_results.get("short_squeeze")
    if ss and ss.potential in ("높음", "스퀴즈 진행 중"):
        alerts.append(f"[!] 숏스퀴즈 잠재력 {ss.potential} (공매도 {ss.short_interest_pct}%)")

    # RSI 다이버전스
    rsi_div = all_results.get("rsi_divergence")
    if rsi_div and rsi_div.divergence_type:
        alerts.append(f"[i] {rsi_div.divergence_type} 감지")

    # 평균 회귀
    mean_rev = all_results.get("mean_reversion")
    if mean_rev:
        if mean_rev.z_score < -2:
            alerts.append(f"[!] 평균 대비 극단적 저평가 (Z={mean_rev.z_score})")
        elif mean_rev.z_score > 2:
            alerts.append(f"[!] 평균 대비 극단적 고평가 (Z={mean_rev.z_score})")

    # 펀더멘털
    fundamental = all_results.get("fundamental")
    if fundamental:
        if fundamental.financial_health_score < 25:
            alerts.append("[!] 재무 건전성 위험 (높은 부채/낮은 유동성)")
        if fundamental.valuation_score > 80:
            alerts.append("[i] 펀더멘털 저평가 구간 (밸류에이션 매력적)")
        if fundamental.growth_score > 80:
            alerts.append("[i] 강한 실적 성장 모멘텀")

    return alerts
