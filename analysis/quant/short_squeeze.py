"""숏스퀴즈 잠재력 분석"""

import pandas as pd
from models.schemas import ShortSqueezeResult


def analyze_short_squeeze(finviz_data: dict | None, df: pd.DataFrame | None) -> ShortSqueezeResult:
    if finviz_data is None:
        return ShortSqueezeResult()

    short_float = finviz_data.get("short_float", 0)
    short_ratio = finviz_data.get("short_ratio", 0)

    # 잠재력 판단
    if short_float > 20:
        potential = "높음"
    elif short_float > 10 and short_ratio > 5:
        potential = "보통"
    elif short_float > 10:
        potential = "낮음~보통"
    else:
        potential = "낮음"

    # 거래량 급증 체크 (스퀴즈 트리거)
    squeeze_active = False
    if df is not None and len(df) >= 20:
        avg_vol = float(df["Volume"].iloc[-20:].mean())
        recent_vol = float(df["Volume"].iloc[-1])
        price_change = float(df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1)
        if recent_vol > avg_vol * 2 and price_change > 0.02:
            squeeze_active = True
            potential = "스퀴즈 진행 중"

    # 점수
    if potential == "스퀴즈 진행 중":
        score = 85
    elif potential == "높음":
        score = 70
    elif potential == "보통":
        score = 60
    elif potential == "낮음~보통":
        score = 50
    else:
        score = 40

    return ShortSqueezeResult(
        short_interest_pct=round(short_float, 1),
        days_to_cover=round(short_ratio, 1),
        potential=potential,
        score=round(score, 1),
    )
