"""매크로 환경 종합 분석"""

import numpy as np
from models.schemas import MacroResult, MacroIndicator, MacroStatus
from utils.helpers import normalize_score


def analyze_macro(macro_data: dict | None, fred_rates: dict | None) -> MacroResult:
    """매크로 환경 종합 분석"""
    # 금리 분석
    interest_rate = _analyze_interest_rate(fred_rates, macro_data)
    # VIX 분석
    vix = _analyze_vix(macro_data)
    # 유가 분석
    oil = _analyze_oil(macro_data)
    # 금 분석
    gold = _analyze_gold(macro_data)
    # 달러 인덱스
    dxy = _analyze_dxy(macro_data)
    # 시장 폭
    breadth_score = _analyze_market_breadth(macro_data)

    # 종합 매크로 점수 (높을수록 매수 유리, 0~100)
    weights = [0.25, 0.25, 0.10, 0.10, 0.15, 0.15]
    indicators = [interest_rate, vix, oil, gold, dxy]
    indicator_scores = [_status_to_score(ind.status) for ind in indicators]
    indicator_scores.append(breadth_score)  # 이미 0~100
    total = sum(s * w for s, w in zip(indicator_scores, weights))

    return MacroResult(
        interest_rate=interest_rate,
        vix=vix,
        oil=oil,
        gold=gold,
        dxy=dxy,
        market_breadth_score=round(breadth_score, 1),
        score=round(total, 1),
    )


def _analyze_interest_rate(fred_rates: dict | None, macro_data: dict | None) -> MacroIndicator:
    if fred_rates and "fed_funds" in fred_rates:
        rate = fred_rates["fed_funds"]["current"]
        change_3m = fred_rates["fed_funds"].get("change_3m", 0)
        if abs(change_3m) < 0.25:
            status = MacroStatus.STABLE
        elif change_3m > 0:
            status = MacroStatus.CAUTION
        else:
            status = MacroStatus.STABLE  # 금리 하락 = 주식에 유리
        return MacroIndicator(name="interest_rate", value=rate, status=status, label="금리")
    # fallback: Yahoo Treasury
    if macro_data and "treasury_10y" in macro_data:
        rate = macro_data["treasury_10y"]["current"]
        return MacroIndicator(name="interest_rate", value=rate, status=MacroStatus.MIXED, label="금리")
    return MacroIndicator(name="interest_rate", value=0, status=MacroStatus.MIXED, label="금리")


def _analyze_vix(macro_data: dict | None) -> MacroIndicator:
    if not macro_data or "vix" not in macro_data:
        return MacroIndicator(name="vix", value=0, status=MacroStatus.MIXED, label="VIX")
    vix_val = macro_data["vix"]["current"]
    if vix_val < 15:
        status = MacroStatus.STABLE
    elif vix_val < 20:
        status = MacroStatus.CAUTION
    elif vix_val < 30:
        status = MacroStatus.CAUTION
    else:
        status = MacroStatus.DANGER
    return MacroIndicator(name="vix", value=round(vix_val, 1), status=status, label="VIX")


def _analyze_oil(macro_data: dict | None) -> MacroIndicator:
    if not macro_data or "oil" not in macro_data:
        return MacroIndicator(name="oil", value=0, status=MacroStatus.MIXED, label="유가")
    oil_data = macro_data["oil"]
    current = oil_data["current"]
    hist = oil_data["history"]
    if len(hist) >= 60:
        change_pct = (current / float(hist.iloc[-60]) - 1) * 100
    else:
        change_pct = 0
    if abs(change_pct) < 5:
        status = MacroStatus.STABLE
    elif abs(change_pct) < 15:
        status = MacroStatus.CAUTION
    else:
        status = MacroStatus.DANGER
    return MacroIndicator(name="oil", value=round(current, 2), status=status, label="유가")


def _analyze_gold(macro_data: dict | None) -> MacroIndicator:
    if not macro_data or "gold" not in macro_data:
        return MacroIndicator(name="gold", value=0, status=MacroStatus.MIXED, label="금")
    gold_data = macro_data["gold"]
    current = gold_data["current"]
    hist = gold_data["history"]
    if len(hist) >= 60:
        change_pct = (current / float(hist.iloc[-60]) - 1) * 100
    else:
        change_pct = 0
    if abs(change_pct) < 5:
        status = MacroStatus.MIXED
    elif change_pct > 10:
        status = MacroStatus.CAUTION  # 금 급등 = 위험회피
    else:
        status = MacroStatus.STABLE
    return MacroIndicator(name="gold", value=round(current, 2), status=status, label="금")


def _analyze_dxy(macro_data: dict | None) -> MacroIndicator:
    """달러 인덱스 분석 - 강달러는 주식(특히 다국적기업)에 부정적"""
    if not macro_data or "dxy" not in macro_data:
        return MacroIndicator(name="dxy", value=0, status=MacroStatus.MIXED, label="달러")
    dxy_data = macro_data["dxy"]
    current = dxy_data["current"]
    hist = dxy_data["history"]
    if len(hist) >= 60:
        change_pct = (current / float(hist.iloc[-60]) - 1) * 100
    else:
        change_pct = 0
    # 달러 강세(상승) = 주식에 부정적
    if abs(change_pct) < 2:
        status = MacroStatus.STABLE
    elif change_pct > 5:
        status = MacroStatus.DANGER  # 급격한 달러 강세
    elif change_pct > 2:
        status = MacroStatus.CAUTION  # 달러 강세
    elif change_pct < -2:
        status = MacroStatus.STABLE  # 달러 약세 = 주식에 유리
    else:
        status = MacroStatus.MIXED
    return MacroIndicator(name="dxy", value=round(current, 2), status=status, label="달러")


def _analyze_market_breadth(macro_data: dict | None) -> float:
    """시장 폭 점수 (0~100). S&P500 추세 기반 간이 분석"""
    if not macro_data or "sp500" not in macro_data:
        return 50.0
    hist = macro_data["sp500"]["history"]
    if len(hist) < 50:
        return 50.0
    current = float(hist.iloc[-1])
    sma20 = float(hist.iloc[-20:].mean())
    sma50 = float(hist.iloc[-50:].mean())
    score = 50.0
    if current > sma20:
        score += 15
    if current > sma50:
        score += 15
    if sma20 > sma50:
        score += 10
    # 최근 5일 모멘텀
    ret_5d = (current / float(hist.iloc[-5]) - 1) * 100
    if ret_5d > 1:
        score += 10
    elif ret_5d < -1:
        score -= 10
    return max(0, min(100, score))


def _status_to_score(status: MacroStatus) -> float:
    """매크로 상태를 0~100 점수로 변환"""
    return {
        MacroStatus.STABLE: 80,
        MacroStatus.MIXED: 50,
        MacroStatus.CAUTION: 30,
        MacroStatus.DANGER: 10,
    }.get(status, 50)
