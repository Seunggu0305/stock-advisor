"""RSI 다이버전스 감지 (강세/약세/히든)"""

import numpy as np
import pandas as pd
import utils.ta_utils as ta
from models.schemas import RSIDivergenceResult
from utils.helpers import find_swing_highs, find_swing_lows


def analyze_rsi_divergence(df: pd.DataFrame) -> RSIDivergenceResult:
    if df is None or len(df) < 50:
        return RSIDivergenceResult()

    close = df["Close"]
    rsi = ta.rsi(close, length=14)

    if rsi is None or rsi.empty:
        return RSIDivergenceResult()

    close_arr = close.values
    rsi_arr = rsi.values

    # 로컬 극값 찾기 (최근 60일)
    lookback = min(60, len(close_arr))
    close_recent = close_arr[-lookback:]
    rsi_recent = rsi_arr[-lookback:]

    price_lows = find_swing_lows(close_recent, window=5)
    price_highs = find_swing_highs(close_recent, window=5)
    rsi_lows = find_swing_lows(rsi_recent, window=5)
    rsi_highs = find_swing_highs(rsi_recent, window=5)

    divergence_type = None
    strength = 0.0

    # 강세 다이버전스: 가격 저점 ↓, RSI 저점 ↑
    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
        p1, p2 = price_lows[-2][1], price_lows[-1][1]
        r1, r2 = rsi_lows[-2][1], rsi_lows[-1][1]
        if p2 < p1 and r2 > r1:
            divergence_type = "강세 다이버전스"
            strength = min((r2 - r1) / 10, 1.0) * 100

    # 약세 다이버전스: 가격 고점 ↑, RSI 고점 ↓
    if divergence_type is None and len(price_highs) >= 2 and len(rsi_highs) >= 2:
        p1, p2 = price_highs[-2][1], price_highs[-1][1]
        r1, r2 = rsi_highs[-2][1], rsi_highs[-1][1]
        if p2 > p1 and r2 < r1:
            divergence_type = "약세 다이버전스"
            strength = min((r1 - r2) / 10, 1.0) * 100

    # 히든 강세 다이버전스: 가격 저점 ↑, RSI 저점 ↓
    if divergence_type is None and len(price_lows) >= 2 and len(rsi_lows) >= 2:
        p1, p2 = price_lows[-2][1], price_lows[-1][1]
        r1, r2 = rsi_lows[-2][1], rsi_lows[-1][1]
        if p2 > p1 and r2 < r1:
            divergence_type = "히든 강세 다이버전스"
            strength = min((p2 - p1) / p1 * 100, 100)

    # 히든 약세 다이버전스: 가격 고점 ↓, RSI 고점 ↑
    if divergence_type is None and len(price_highs) >= 2 and len(rsi_highs) >= 2:
        p1, p2 = price_highs[-2][1], price_highs[-1][1]
        r1, r2 = rsi_highs[-2][1], rsi_highs[-1][1]
        if p2 < p1 and r2 > r1:
            divergence_type = "히든 약세 다이버전스"
            strength = min((p1 - p2) / p1 * 100, 100)

    # 점수
    if divergence_type is None:
        score = 50
    elif "강세" in divergence_type:
        score = 65 + strength * 0.2
    else:
        score = 35 - strength * 0.2

    return RSIDivergenceResult(
        divergence_type=divergence_type,
        strength=round(strength, 1),
        score=round(max(0, min(100, score)), 1),
    )
