"""피보나치 되돌림/확장 분석"""

import pandas as pd
import numpy as np
from models.schemas import FibonacciResult
from utils.helpers import find_swing_highs, find_swing_lows


def analyze_fibonacci(df: pd.DataFrame) -> FibonacciResult:
    if df is None or len(df) < 60:
        return FibonacciResult()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # 주요 스윙 포인트 찾기
    swing_highs = find_swing_highs(high.values, window=10)
    swing_lows = find_swing_lows(low.values, window=10)

    if not swing_highs or not swing_lows:
        return FibonacciResult()

    # 가장 최근의 주요 고점과 저점
    recent_high = max(swing_highs[-3:], key=lambda x: x[1]) if len(swing_highs) >= 3 else swing_highs[-1]
    recent_low = min(swing_lows[-3:], key=lambda x: x[1]) if len(swing_lows) >= 3 else swing_lows[-1]

    high_price = recent_high[1]
    low_price = recent_low[1]
    diff = high_price - low_price

    if diff <= 0:
        return FibonacciResult()

    current = float(close.iloc[-1])

    # 되돌림 레벨
    fib_ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    levels = {}

    # 하락 추세 (고점 → 저점으로 진행): 되돌림은 저점에서 위로
    if recent_high[0] < recent_low[0]:
        # 상승 후 하락 → 저점에서 반등 가능
        for ratio in fib_ratios:
            level_price = low_price + diff * ratio
            levels[f"{ratio*100:.1f}%"] = round(level_price, 2)
    else:
        # 하락 후 상승 → 고점에서 하락 되돌림
        for ratio in fib_ratios:
            level_price = high_price - diff * ratio
            levels[f"{ratio*100:.1f}%"] = round(level_price, 2)

    # 현재 가격이 어느 피보나치 레벨에 있는지
    retracement = abs(current - low_price) / diff * 100 if diff > 0 else 0
    retracement = min(retracement, 100)

    # 가장 가까운 레벨 찾기
    closest_level = ""
    min_dist = float("inf")
    for label, price in levels.items():
        dist = abs(current - price)
        if dist < min_dist:
            min_dist = dist
            closest_level = f"{label} 근접"
    # 지지/저항 여부
    if current < float(list(levels.values())[3]):  # 50% 이하
        closest_level += " (지지)"
    else:
        closest_level += " (저항)"

    # 점수: 38.2~61.8% 사이에서 반등 시 높은 점수
    if 35 <= retracement <= 65:
        score = 70  # 건전한 되돌림 구간
    elif retracement < 23.6:
        score = 40  # 너무 약한 되돌림
    elif retracement > 78.6:
        score = 30  # 너무 깊은 되돌림
    else:
        score = 55

    return FibonacciResult(
        levels=levels,
        current_level=closest_level,
        retracement_pct=round(retracement, 1),
        score=round(score, 1),
    )
