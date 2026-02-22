"""공통 유틸리티 함수"""

import numpy as np


def normalize_score(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    """값을 0~100 범위로 정규화"""
    if max_val == min_val:
        return 50.0
    score = (value - min_val) / (max_val - min_val) * 100
    score = max(0.0, min(100.0, score))
    if invert:
        score = 100.0 - score
    return round(score, 1)


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    if b == 0:
        return default
    return a / b


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def find_swing_highs(data, window: int = 5) -> list:
    """로컬 고점 찾기"""
    highs = []
    arr = np.array(data)
    for i in range(window, len(arr) - window):
        if arr[i] == max(arr[i - window:i + window + 1]):
            highs.append((i, float(arr[i])))
    return highs


def find_swing_lows(data, window: int = 5) -> list:
    """로컬 저점 찾기"""
    lows = []
    arr = np.array(data)
    for i in range(window, len(arr) - window):
        if arr[i] == min(arr[i - window:i + window + 1]):
            lows.append((i, float(arr[i])))
    return lows
