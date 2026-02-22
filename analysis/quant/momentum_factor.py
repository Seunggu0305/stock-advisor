"""모멘텀 팩터 스코어링"""

import pandas as pd
from models.schemas import MomentumFactorResult


def analyze_momentum_factor(df: pd.DataFrame) -> MomentumFactorResult:
    if df is None or len(df) < 252:
        return MomentumFactorResult()

    close = df["Close"]

    # 12-1 모멘텀 (최근 1개월 제외, 12개월 수익률)
    ret_12m = float(close.iloc[-1] / close.iloc[-252] - 1) if len(close) >= 252 else 0
    ret_1m = float(close.iloc[-1] / close.iloc[-21] - 1) if len(close) >= 21 else 0
    momentum_12_1 = ret_12m - ret_1m

    # 6개월 모멘텀
    ret_6m = float(close.iloc[-1] / close.iloc[-126] - 1) if len(close) >= 126 else 0

    # 3개월 모멘텀
    ret_3m = float(close.iloc[-1] / close.iloc[-63] - 1) if len(close) >= 63 else 0

    # 종합 모멘텀 점수 (가중 합산, 수익률은 소수 비율)
    # 예: +20% 수익률 = 0.2 → weighted_mom ≈ 0.2
    weighted_mom = momentum_12_1 * 0.40 + ret_6m * 0.35 + ret_3m * 0.25

    # 0~100으로 변환: ±50% 수익률이 0~100 범위에 매핑되도록
    score = 50 + weighted_mom * 100  # +50%→100, -50%→0
    score = max(0, min(100, score))

    if score >= 70:
        rank_label = "강함"
    elif score >= 40:
        rank_label = "보통"
    else:
        rank_label = "약함"

    return MomentumFactorResult(
        momentum_score=round(score, 1),
        rank_label=rank_label,
        score=round(score, 1),
    )
