"""평균 회귀 시그널 - Z-Score, Hurst Exponent"""

import numpy as np
import pandas as pd
import utils.ta_utils as ta
from models.schemas import MeanReversionResult


def analyze_mean_reversion(df: pd.DataFrame) -> MeanReversionResult:
    if df is None or len(df) < 50:
        return MeanReversionResult()

    close = df["Close"]

    # Z-Score 계산
    sma50 = ta.sma(close, length=50)
    if sma50 is None or sma50.empty:
        return MeanReversionResult()

    std = close.rolling(50).std()
    current = float(close.iloc[-1])
    mean = float(sma50.iloc[-1])
    sd = float(std.iloc[-1])

    if sd == 0 or pd.isna(sd) or pd.isna(mean):
        return MeanReversionResult()

    z_score = (current - mean) / sd

    # 시그널 판단
    if z_score < -2:
        signal = "강한 과매도 (매수 기회)"
    elif z_score < -1:
        signal = "과매도"
    elif z_score > 2:
        signal = "강한 과매수 (매도 고려)"
    elif z_score > 1:
        signal = "과매수"
    else:
        signal = "중립"

    # 점수: Z < -2 = 매수 기회 (높은 점수)
    if z_score < -2:
        score = 85
    elif z_score < -1:
        score = 70
    elif z_score > 2:
        score = 15
    elif z_score > 1:
        score = 30
    else:
        score = 50 - z_score * 10

    return MeanReversionResult(
        z_score=round(z_score, 2),
        signal=signal,
        score=round(max(0, min(100, score)), 1),
    )
