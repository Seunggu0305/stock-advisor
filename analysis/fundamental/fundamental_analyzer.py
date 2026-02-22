"""재무제표 기본 분석 - 밸류에이션, 수익성, 성장성, 건전성, 배당, 컨센서스, 인사이더"""

import math
from models.schemas import FundamentalResult


def analyze_fundamental(stock_info: dict | None, finviz_data: dict | None = None) -> FundamentalResult:
    """yfinance .info + finviz 데이터 기반 펀더멘털 분석"""
    if not stock_info:
        return FundamentalResult()

    val_score, val_label = _score_valuation(stock_info)
    prof_score, prof_label = _score_profitability(stock_info)
    grow_score, grow_label = _score_growth(stock_info)
    health_score, health_label = _score_financial_health(stock_info)
    div_score, div_label = _score_dividend(stock_info)
    analyst_score, analyst_label = _score_analyst_consensus(stock_info)
    insider_score, insider_label = _score_insider(stock_info, finviz_data)

    composite = (
        val_score * 0.20
        + prof_score * 0.20
        + grow_score * 0.20
        + health_score * 0.10
        + div_score * 0.05
        + analyst_score * 0.15
        + insider_score * 0.10
    )

    return FundamentalResult(
        valuation_score=val_score,
        valuation_label=val_label,
        profitability_score=prof_score,
        profitability_label=prof_label,
        growth_score=grow_score,
        growth_label=grow_label,
        financial_health_score=health_score,
        financial_health_label=health_label,
        dividend_score=div_score,
        dividend_label=div_label,
        analyst_score=analyst_score,
        analyst_label=analyst_label,
        insider_score=insider_score,
        insider_label=insider_label,
        score=round(max(0, min(100, composite)), 1),
    )


def _safe_get(info: dict, key: str) -> float | None:
    """info에서 값을 안전하게 가져오기 (None, NaN 체크)"""
    val = info.get(key)
    if val is None:
        return None
    try:
        val = float(val)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    except (TypeError, ValueError):
        return None


# ── 밸류에이션 ──

def _score_valuation(info: dict) -> tuple[float, str]:
    scores = []

    fpe = _safe_get(info, "forwardPE")
    if fpe is not None and fpe > 0:
        if fpe < 10:
            scores.append(85)
        elif fpe < 15:
            scores.append(75)
        elif fpe < 20:
            scores.append(60)
        elif fpe < 30:
            scores.append(45)
        elif fpe < 50:
            scores.append(30)
        else:
            scores.append(15)

    peg = _safe_get(info, "pegRatio")
    if peg is not None and peg > 0:
        if peg < 0.5:
            scores.append(90)
        elif peg < 1.0:
            scores.append(75)
        elif peg < 1.5:
            scores.append(55)
        elif peg < 2.0:
            scores.append(40)
        else:
            scores.append(20)

    ev_ebitda = _safe_get(info, "enterpriseToEbitda")
    if ev_ebitda is not None and ev_ebitda > 0:
        if ev_ebitda < 8:
            scores.append(80)
        elif ev_ebitda < 12:
            scores.append(65)
        elif ev_ebitda < 18:
            scores.append(50)
        elif ev_ebitda < 25:
            scores.append(35)
        else:
            scores.append(20)

    if not scores:
        return 50.0, "데이터 없음"

    score = sum(scores) / len(scores)

    if score >= 70:
        tag = "저평가"
    elif score >= 50:
        tag = "적정"
    elif score >= 35:
        tag = "고평가"
    else:
        tag = "과대평가"

    parts = []
    if fpe is not None and fpe > 0:
        parts.append(f"FwdPE {fpe:.1f}")
    if peg is not None and peg > 0:
        parts.append(f"PEG {peg:.1f}")
    label = " | ".join(parts) + f" ({tag})" if parts else tag

    return round(score, 1), label


# ── 수익성 ──

def _score_profitability(info: dict) -> tuple[float, str]:
    scores = []

    roe = _safe_get(info, "returnOnEquity")
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 25:
            scores.append(90)
        elif roe_pct > 15:
            scores.append(75)
        elif roe_pct > 10:
            scores.append(60)
        elif roe_pct > 5:
            scores.append(45)
        elif roe_pct > 0:
            scores.append(30)
        else:
            scores.append(15)

    op_margin = _safe_get(info, "operatingMargins")
    if op_margin is not None:
        op_pct = op_margin * 100
        if op_pct > 25:
            scores.append(85)
        elif op_pct > 15:
            scores.append(70)
        elif op_pct > 8:
            scores.append(55)
        elif op_pct > 0:
            scores.append(40)
        else:
            scores.append(20)

    net_margin = _safe_get(info, "profitMargins")
    if net_margin is not None:
        net_pct = net_margin * 100
        if net_pct > 20:
            scores.append(85)
        elif net_pct > 10:
            scores.append(70)
        elif net_pct > 5:
            scores.append(55)
        elif net_pct > 0:
            scores.append(40)
        else:
            scores.append(20)

    if not scores:
        return 50.0, "데이터 없음"

    score = sum(scores) / len(scores)
    parts = []
    if roe is not None:
        parts.append(f"ROE {roe * 100:.1f}%")
    if op_margin is not None:
        parts.append(f"영업이익률 {op_margin * 100:.1f}%")
    label = " | ".join(parts) if parts else "데이터 없음"

    return round(score, 1), label


# ── 성장성 ──

def _score_growth(info: dict) -> tuple[float, str]:
    scores = []

    rev_growth = _safe_get(info, "revenueGrowth")
    if rev_growth is not None:
        rg_pct = rev_growth * 100
        if rg_pct > 30:
            scores.append(90)
        elif rg_pct > 15:
            scores.append(75)
        elif rg_pct > 5:
            scores.append(60)
        elif rg_pct > 0:
            scores.append(45)
        elif rg_pct > -10:
            scores.append(30)
        else:
            scores.append(15)

    earn_growth = _safe_get(info, "earningsGrowth")
    if earn_growth is not None:
        eg_pct = earn_growth * 100
        if eg_pct > 50:
            scores.append(90)
        elif eg_pct > 20:
            scores.append(75)
        elif eg_pct > 5:
            scores.append(60)
        elif eg_pct > 0:
            scores.append(45)
        elif eg_pct > -20:
            scores.append(30)
        else:
            scores.append(15)

    qtr_growth = _safe_get(info, "earningsQuarterlyGrowth")
    if qtr_growth is not None:
        qg_pct = qtr_growth * 100
        if qg_pct > 30:
            scores.append(85)
        elif qg_pct > 10:
            scores.append(70)
        elif qg_pct > 0:
            scores.append(55)
        elif qg_pct > -15:
            scores.append(35)
        else:
            scores.append(20)

    if not scores:
        return 50.0, "데이터 없음"

    score = sum(scores) / len(scores)
    parts = []
    if rev_growth is not None:
        parts.append(f"매출 {rev_growth * 100:+.1f}%")
    if earn_growth is not None:
        parts.append(f"이익 {earn_growth * 100:+.1f}%")
    label = " | ".join(parts) if parts else "데이터 없음"

    return round(score, 1), label


# ── 재무 건전성 ──

def _score_financial_health(info: dict) -> tuple[float, str]:
    scores = []

    dte = _safe_get(info, "debtToEquity")
    if dte is not None:
        if dte < 30:
            scores.append(90)
        elif dte < 50:
            scores.append(75)
        elif dte < 100:
            scores.append(60)
        elif dte < 150:
            scores.append(40)
        elif dte < 250:
            scores.append(25)
        else:
            scores.append(10)

    cr = _safe_get(info, "currentRatio")
    if cr is not None:
        if cr > 3.0:
            scores.append(85)
        elif cr > 2.0:
            scores.append(75)
        elif cr > 1.5:
            scores.append(65)
        elif cr > 1.0:
            scores.append(45)
        else:
            scores.append(20)

    fcf = _safe_get(info, "freeCashflow")
    total_debt = _safe_get(info, "totalDebt")
    if fcf is not None:
        if fcf > 0:
            if total_debt and total_debt > 0:
                coverage = fcf / total_debt
                if coverage > 0.3:
                    scores.append(85)
                elif coverage > 0.15:
                    scores.append(70)
                else:
                    scores.append(55)
            else:
                scores.append(75)
        else:
            scores.append(25)

    if not scores:
        return 50.0, "데이터 없음"

    score = sum(scores) / len(scores)
    parts = []
    if dte is not None:
        parts.append(f"D/E {dte:.0f}%")
    if cr is not None:
        parts.append(f"유동비율 {cr:.1f}")
    if fcf is not None:
        parts.append("FCF+" if fcf > 0 else "FCF-")
    label = " | ".join(parts) if parts else "데이터 없음"

    return round(score, 1), label


# ── 배당 안정성 ──

def _score_dividend(info: dict) -> tuple[float, str]:
    div_yield = _safe_get(info, "dividendYield")
    payout = _safe_get(info, "payoutRatio")

    if div_yield is None or div_yield == 0:
        return 50.0, "무배당"

    dy_pct = div_yield * 100

    if dy_pct > 6:
        yield_score = 40
    elif dy_pct > 3:
        yield_score = 75
    elif dy_pct > 1.5:
        yield_score = 65
    elif dy_pct > 0.5:
        yield_score = 55
    else:
        yield_score = 50

    payout_score = 50
    if payout is not None:
        if payout < 0:
            payout_score = 20
        elif payout < 0.3:
            payout_score = 80
        elif payout < 0.5:
            payout_score = 70
        elif payout < 0.7:
            payout_score = 55
        elif payout < 1.0:
            payout_score = 40
        else:
            payout_score = 20

    score = yield_score * 0.5 + payout_score * 0.5
    label = f"배당 {dy_pct:.2f}%"
    if payout is not None:
        label += f" | 배당성향 {payout * 100:.0f}%"

    return round(score, 1), label


# ── 애널리스트 컨센서스 ──

def _score_analyst_consensus(info: dict) -> tuple[float, str]:
    """애널리스트 목표가 및 추천 등급 기반 점수"""
    target = _safe_get(info, "targetMeanPrice")
    current = _safe_get(info, "currentPrice") or _safe_get(info, "previousClose")
    rec = info.get("recommendationKey")
    n_analysts = _safe_get(info, "numberOfAnalystOpinions")

    scores = []

    # 목표가 대비 업사이드
    if target and current and current > 0:
        upside = (target / current - 1) * 100
        if upside > 30:
            scores.append(90)
        elif upside > 15:
            scores.append(75)
        elif upside > 5:
            scores.append(60)
        elif upside > -5:
            scores.append(45)
        elif upside > -15:
            scores.append(30)
        else:
            scores.append(15)
    else:
        upside = None

    # 추천 등급
    rec_scores = {
        "strong_buy": 90, "buy": 75, "overweight": 70,
        "hold": 50, "neutral": 50,
        "underweight": 30, "sell": 20, "strong_sell": 10,
    }
    if rec and rec.lower() in rec_scores:
        scores.append(rec_scores[rec.lower()])

    if not scores:
        return 50.0, "데이터 없음"

    score = sum(scores) / len(scores)
    parts = []
    if upside is not None:
        parts.append(f"목표 {upside:+.1f}%")
    if rec:
        parts.append(rec.upper())
    if n_analysts and n_analysts > 0:
        parts.append(f"{int(n_analysts)}명")
    label = " | ".join(parts) if parts else "데이터 없음"

    return round(score, 1), label


# ── 인사이더 보유 ──

def _score_insider(stock_info: dict, finviz_data: dict | None) -> tuple[float, str]:
    """내부자 보유율"""
    insider_pct = None

    # finviz에서 가져오기
    if finviz_data:
        insider_pct = finviz_data.get("insider_own", 0)

    # yfinance fallback
    if insider_pct is None or insider_pct == 0:
        held = _safe_get(stock_info, "heldPercentInsiders")
        if held is not None:
            insider_pct = held * 100

    if insider_pct is None or insider_pct == 0:
        return 50.0, "데이터 없음"

    # 적절한 내부자 보유 = 이해관계 일치 (1~30% 이상적)
    if 5 <= insider_pct <= 30:
        score = 75
    elif 1 <= insider_pct < 5:
        score = 65
    elif 30 < insider_pct <= 50:
        score = 60
    elif insider_pct > 50:
        score = 45  # 너무 높으면 유동성 우려
    else:
        score = 50

    label = f"보유 {insider_pct:.1f}%"
    return round(score, 1), label
