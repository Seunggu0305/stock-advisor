"""종합 점수 산출 엔진 - 가중 합산"""

from config.scoring_weights import SCORING_WEIGHTS


def calculate_total_score(all_results: dict) -> float:
    """모든 분석 결과의 서브스코어를 가중 합산하여 최종 0~100 점수 산출"""

    category_scores = {}

    # 1. 매크로 환경 (10%)
    macro = all_results.get("macro")
    if macro:
        category_scores["macro"] = macro.score
    else:
        category_scores["macro"] = 50.0

    # 2. 추세/모멘텀 (25%)
    trend = all_results.get("trend")
    momentum = all_results.get("momentum")
    ichimoku = all_results.get("ichimoku")

    sw = SCORING_WEIGHTS["trend_momentum"]["sub_weights"]
    trend_score = trend.score if trend else 50
    mom_score = momentum.score if momentum else 50
    ichi_score = ichimoku.score if ichimoku else 50

    category_scores["trend_momentum"] = (
        trend_score * (sw["trend_direction"] + sw["trend_strength"]) +
        mom_score * sw["rsi_macd"] +
        ichi_score * sw["ichimoku"]
    )

    # 3. 거래량/수급 (20%)
    volume = all_results.get("volume")
    inst_flow = all_results.get("institutional_flow")
    options = all_results.get("options_flow")

    sw = SCORING_WEIGHTS["volume_flow"]["sub_weights"]
    vol_score = volume.score if volume else 50
    inst_score = inst_flow.score if inst_flow else 50
    opt_score = options.score if options else 50

    category_scores["volume_flow"] = (
        vol_score * (sw["obv_retention"] + sw["volume_profile"]) +
        inst_score * sw["institutional_flow"] +
        opt_score * sw["options_flow"]
    )

    # 4. 패턴/구조 (20%)
    wave = all_results.get("wave")
    fvg = all_results.get("fvg")
    fib = all_results.get("fibonacci")
    sim = all_results.get("similarity")
    candle = all_results.get("candlestick")

    sw = SCORING_WEIGHTS["pattern_structure"]["sub_weights"]
    category_scores["pattern_structure"] = (
        (wave.score if wave else 50) * sw["wave_analysis"] +
        (fvg.score if fvg else 50) * sw["fvg_levels"] +
        (fib.score if fib else 50) * sw["fibonacci"] +
        (sim.score if sim else 50) * sw["pattern_similarity"] +
        (candle.score if candle else 50) * sw["candlestick"]
    )

    # 5. 퀀트 팩터 (15%)
    mr = all_results.get("mean_reversion")
    mf = all_results.get("momentum_factor")
    sr = all_results.get("sector_relative")
    es = all_results.get("earnings_surprise")
    rd = all_results.get("rsi_divergence")
    bs = all_results.get("bb_squeeze")

    sw = SCORING_WEIGHTS["quant_factors"]["sub_weights"]
    category_scores["quant_factors"] = (
        (mr.score if mr else 50) * sw["mean_reversion"] +
        (mf.score if mf else 50) * sw["momentum_factor"] +
        (sr.score if sr else 50) * sw["sector_relative"] +
        (es.score if es else 50) * sw["earnings_surprise"] +
        (rd.score if rd else 50) * sw["rsi_divergence"] +
        (bs.score if bs else 50) * sw["bb_squeeze"]
    )

    # 6. 리스크/특수 (10%)
    ss = all_results.get("short_squeeze")
    cp = all_results.get("complex_patterns")

    sw = SCORING_WEIGHTS["risk_special"]["sub_weights"]
    special_score = 50.0
    special_signals = all_results.get("special_signals", [])
    if special_signals:
        bullish = sum(1 for s in special_signals if any(kw in s for kw in ["매수", "돌파", "신고"]))
        bearish = sum(1 for s in special_signals if any(kw in s for kw in ["매도", "신저", "경고"]))
        special_score = 50 + bullish * 10 - bearish * 10
        special_score = max(0, min(100, special_score))

    category_scores["risk_special"] = (
        (ss.score if ss else 50) * sw["short_squeeze"] +
        special_score * sw["special_signals"] +
        (cp.score if cp else 50) * sw["complex_patterns"]
    )

    # 7. 펀더멘털 (10%)
    fundamental = all_results.get("fundamental")
    if fundamental:
        category_scores["fundamental"] = fundamental.score
    else:
        category_scores["fundamental"] = 50.0

    # 최종 점수 가중 합산
    total = 0.0
    for cat_name, cat_score in category_scores.items():
        weight = SCORING_WEIGHTS[cat_name]["weight"]
        total += cat_score * weight

    # 동적 가중치 조정
    total = _apply_dynamic_adjustment(total, all_results)

    return round(max(0, min(100, total)), 1)


def _apply_dynamic_adjustment(base_score: float, all_results: dict) -> float:
    """시장 상황에 따른 동적 조정 - 선행지표 수렴/과매수 감점"""
    score = base_score

    macro = all_results.get("macro")
    mr = all_results.get("mean_reversion")
    rd = all_results.get("rsi_divergence")
    bs = all_results.get("bb_squeeze")
    momentum = all_results.get("momentum")
    trend = all_results.get("trend")
    volume = all_results.get("volume")
    options = all_results.get("options_flow")
    ss = all_results.get("short_squeeze")
    mf = all_results.get("momentum_factor")

    # 1) 극단적 공포 + 과매도 보너스
    if macro and hasattr(macro, 'vix') and macro.vix.value > 30:
        if mr and mr.z_score < -1.5:
            score += 5
        if mr and mr.z_score < -2.0 and rd and rd.divergence_type and "강세" in rd.divergence_type:
            score += 3

    # 2) 선행 신호 수렴 보너스
    leading_bullish = 0
    if mr and mr.z_score < -1.0:
        leading_bullish += 1
    if rd and rd.divergence_type and "강세" in rd.divergence_type:
        leading_bullish += 1
    if bs and bs.is_squeezing and bs.expected_direction == "상승":
        leading_bullish += 1
    if options and options.put_call_ratio > 1.2:
        leading_bullish += 1
    if momentum and momentum.rsi < 35:
        leading_bullish += 1

    if leading_bullish >= 4:
        score += 7
    elif leading_bullish >= 3:
        score += 4

    # 3) 모멘텀 소진 감점
    if momentum and momentum.rsi > 70:
        if mf and mf.deceleration_detected:
            score -= 5
        if trend and trend.adx > 40:
            score -= 2

    # 4) 과매수 수렴 감점
    overbought = 0
    if momentum and momentum.rsi > 70:
        overbought += 1
    if mr and mr.z_score > 1.5:
        overbought += 1
    if trend and trend.score > 85:
        overbought += 1
    if options and options.put_call_ratio < 0.5:
        overbought += 1

    if overbought >= 3:
        score -= 5

    # 5) 장기 BB스퀴즈 + OBV 건전 → 돌파 임박
    if bs and bs.is_squeezing and bs.squeeze_duration >= 8:
        if volume and volume.obv_label != "약함":
            score += 3

    # 6) 숏스퀴즈 셋업 보너스
    if ss and ss.short_interest_pct > 15:
        if leading_bullish >= 2:
            score += 3

    return score
