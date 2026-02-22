"""모멘텀 팩터 스코어링 - 감속/가속 감지 포함"""

import pandas as pd
from models.schemas import MomentumFactorResult


def analyze_momentum_factor(df: pd.DataFrame) -> MomentumFactorResult:
    if df is None or len(df) < 252:
        return MomentumFactorResult()

    close = df["Close"]

    # 기간별 수익률
    ret_12m = float(close.iloc[-1] / close.iloc[-252] - 1) if len(close) >= 252 else 0
    ret_1m = float(close.iloc[-1] / close.iloc[-21] - 1) if len(close) >= 21 else 0
    ret_6m = float(close.iloc[-1] / close.iloc[-126] - 1) if len(close) >= 126 else 0
    ret_3m = float(close.iloc[-1] / close.iloc[-63] - 1) if len(close) >= 63 else 0
    momentum_12_1 = ret_12m - ret_1m

    # 모멘텀 가속/감속 감지
    # 연환산하여 공정 비교
    rate_6m_ann = ret_6m * 2
    rate_3m_ann = ret_3m * 4

    accel_3v6 = rate_3m_ann - rate_6m_ann

    deceleration_detected = False
    bottoming_detected = False

    # 상승세 감속: 6개월간 올랐지만 3개월 속도가 현저히 둔화
    if ret_6m > 0.05 and accel_3v6 < -0.10:
        deceleration_detected = True

    # 하락세 감속 (바닥 형성): 6개월간 떨어졌지만 3개월 하락 속도 둔화
    if ret_6m < -0.05 and accel_3v6 > 0.10:
        bottoming_detected = True

    # 전통 모멘텀 점수 (40%)
    weighted_mom = momentum_12_1 * 0.40 + ret_6m * 0.35 + ret_3m * 0.25
    trad_score = 50 + weighted_mom * 100
    trad_score = max(0, min(100, trad_score))

    # 감속/가속 점수 (60%)
    if bottoming_detected:
        decel_score = 70 + min(abs(accel_3v6) * 50, 20)
    elif deceleration_detected:
        decel_score = 30 - min(abs(accel_3v6) * 30, 15)
    else:
        decel_score = 50

    # 블렌딩: 전통 40% + 감속감지 60%
    score = trad_score * 0.40 + decel_score * 0.60
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
        deceleration_detected=deceleration_detected,
        bottoming_detected=bottoming_detected,
    )
