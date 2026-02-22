"""추세 분석 - SMA/EMA 배열, ADX, DI"""

import pandas as pd
import utils.ta_utils as ta
from models.schemas import TrendResult, TrendDirection, TrendStrength


def analyze_trend(df: pd.DataFrame) -> TrendResult:
    if df is None or len(df) < 200:
        return TrendResult()

    close = df["Close"]

    # SMA 계산
    sma20 = ta.sma(close, length=20)
    sma50 = ta.sma(close, length=50)
    sma200 = ta.sma(close, length=200)

    if sma20 is None or sma50 is None or sma200 is None:
        return TrendResult()

    current = float(close.iloc[-1])
    s20 = float(sma20.iloc[-1])
    s50 = float(sma50.iloc[-1])
    s200 = float(sma200.iloc[-1])

    # NaN 안전 체크 (yfinance 데이터에 결측이 있을 수 있음)
    if pd.isna(current) or pd.isna(s20) or pd.isna(s50) or pd.isna(s200):
        return TrendResult()

    # SMA 배열
    if s20 > s50 > s200:
        alignment = "정배열"
    elif s20 < s50 < s200:
        alignment = "역배열"
    else:
        alignment = "혼합"

    # ADX
    adx_df = ta.adx(df["High"], df["Low"], close, length=14)
    if adx_df is not None and not adx_df.empty:
        adx_val = float(adx_df.iloc[-1, 0])  # ADX_14
        plus_di = float(adx_df.iloc[-1, 1])   # DMP_14
        minus_di = float(adx_df.iloc[-1, 2])  # DMN_14
        # ADX NaN 방어
        if pd.isna(adx_val):
            adx_val = 20.0
        if pd.isna(plus_di):
            plus_di = 25.0
        if pd.isna(minus_di):
            minus_di = 25.0
    else:
        adx_val, plus_di, minus_di = 20.0, 25.0, 25.0

    # 방향 판단
    above_sma = sum([current > s20, current > s50, current > s200])
    bullish_di = plus_di > minus_di

    # SMA 기울기 (20일 이평 방향)
    sma20_slope = (float(sma20.iloc[-1]) - float(sma20.iloc[-5])) / float(sma20.iloc[-5]) * 100 if len(sma20) >= 5 else 0

    # SMA 배열이 강한 구조적 신호이므로 우선 반영
    if above_sma >= 3 and alignment == "정배열":
        if bullish_di and adx_val > 25:
            direction = TrendDirection.STRONG_BULLISH
        else:
            direction = TrendDirection.BULLISH
    elif above_sma == 0 and alignment == "역배열":
        if not bullish_di and adx_val > 25:
            direction = TrendDirection.STRONG_BEARISH
        else:
            direction = TrendDirection.BEARISH
    elif above_sma >= 2 and sma20_slope > 0:
        direction = TrendDirection.BULLISH
    elif above_sma <= 1 and sma20_slope < 0:
        direction = TrendDirection.BEARISH
    else:
        direction = TrendDirection.NEUTRAL

    # 강도
    if adx_val > 40:
        strength = TrendStrength.STRONG
    elif adx_val > 20:
        strength = TrendStrength.MODERATE
    else:
        strength = TrendStrength.WEAK

    # 점수 산출
    direction_scores = {
        TrendDirection.STRONG_BULLISH: 90,
        TrendDirection.BULLISH: 70,
        TrendDirection.NEUTRAL: 50,
        TrendDirection.BEARISH: 30,
        TrendDirection.STRONG_BEARISH: 10,
    }
    base_score = direction_scores[direction]
    # ADX 보너스 (강한 추세일수록 신뢰도 가산)
    if direction in (TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH):
        bonus = min(adx_val / 50 * 10, 10)
    elif direction in (TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH):
        bonus = -min(adx_val / 50 * 10, 10)
    else:
        bonus = 0
    score = max(0, min(100, base_score + bonus))

    return TrendResult(
        direction=direction,
        strength=strength,
        adx=round(adx_val, 1),
        sma_alignment=alignment,
        score=round(score, 1),
    )
