"""엘리어트 파동 분석 - ZigZag 기반"""

import numpy as np
import pandas as pd
from models.schemas import WaveResult
from config.settings import ZIGZAG_THRESHOLD


def analyze_wave(df: pd.DataFrame) -> WaveResult:
    if df is None or len(df) < 60:
        return WaveResult()

    close = df["Close"].values
    high = df["High"].values
    low = df["Low"].values

    # ZigZag로 피봇 포인트 감지
    pivots = _zigzag(high, low, threshold=ZIGZAG_THRESHOLD)

    if len(pivots) < 4:
        return WaveResult()

    # 최근 피봇들로 파동 판단
    recent_pivots = pivots[-6:]  # 최근 6개 피봇
    current_price = float(close[-1])

    # 방향 판단
    last_pivot = recent_pivots[-1]
    prev_pivot = recent_pivots[-2] if len(recent_pivots) >= 2 else last_pivot

    # 파동 패턴 분석
    wave_label, position, confidence = _classify_wave(recent_pivots, current_price)

    # 점수
    score = _wave_score(position, current_price, recent_pivots)

    return WaveResult(
        current_wave=wave_label,
        wave_position=position,
        confidence=round(confidence, 1),
        score=round(score, 1),
    )


def _zigzag(high: np.ndarray, low: np.ndarray, threshold: float = 0.05) -> list:
    """ZigZag 피봇 포인트 감지"""
    pivots = []  # (index, price, type) type: 'H' or 'L'
    last_pivot_type = None
    last_pivot_price = high[0]
    last_pivot_idx = 0

    for i in range(1, len(high)):
        if last_pivot_type is None or last_pivot_type == 'L':
            # 고점 탐색
            if high[i] > last_pivot_price:
                last_pivot_price = high[i]
                last_pivot_idx = i
            elif (last_pivot_price - low[i]) / last_pivot_price >= threshold:
                pivots.append((last_pivot_idx, float(last_pivot_price), 'H'))
                last_pivot_type = 'H'
                last_pivot_price = low[i]
                last_pivot_idx = i
        else:
            # 저점 탐색
            if low[i] < last_pivot_price:
                last_pivot_price = low[i]
                last_pivot_idx = i
            elif (high[i] - last_pivot_price) / last_pivot_price >= threshold:
                pivots.append((last_pivot_idx, float(last_pivot_price), 'L'))
                last_pivot_type = 'L'
                last_pivot_price = high[i]
                last_pivot_idx = i

    # 마지막 피봇 추가
    if last_pivot_type:
        next_type = 'L' if last_pivot_type == 'H' else 'H'
        pivots.append((last_pivot_idx, float(last_pivot_price), next_type))

    return pivots


def _classify_wave(pivots: list, current_price: float) -> tuple:
    """피봇 패턴으로 파동 분류"""
    if len(pivots) < 3:
        return "판별 불가", "판별 불가", 0.0

    types = [p[2] for p in pivots]
    prices = [p[1] for p in pivots]
    last_type = types[-1]

    # 상승 파동 확인
    highs = [p[1] for p in pivots if p[2] == 'H']
    lows = [p[1] for p in pivots if p[2] == 'L']

    if len(highs) >= 2 and len(lows) >= 2:
        higher_highs = highs[-1] > highs[-2] if len(highs) >= 2 else False
        higher_lows = lows[-1] > lows[-2] if len(lows) >= 2 else False
        lower_highs = highs[-1] < highs[-2] if len(highs) >= 2 else False
        lower_lows = lows[-1] < lows[-2] if len(lows) >= 2 else False

        if higher_highs and higher_lows:
            # 상승 추세
            if current_price > highs[-1]:
                return "상승 파동", "고점 갱신 중", 70.0
            elif current_price > lows[-1]:
                return "상승 파동", "조정 파동 진행", 60.0
            else:
                return "상승 파동", "되돌림 깊어짐", 40.0
        elif lower_highs and lower_lows:
            # 하락 추세
            if current_price < lows[-1]:
                return "하락 파동", "저점 갱신", 70.0
            elif current_price < highs[-1]:
                return "하락 파동", "반등 시도 중", 50.0
            else:
                return "하락 파동", "반등 파동", 40.0
        elif higher_highs and lower_lows:
            return "확장 파동", "변동성 확대", 30.0
        else:
            return "수렴 파동", "삼각 수렴", 35.0

    return "판별 불가", "데이터 부족", 0.0


def _wave_score(position: str, current_price: float, pivots: list) -> float:
    """파동 위치 기반 점수"""
    scores = {
        "저점 갱신": 75,          # 역발상 매수 기회
        "반등 시도 중": 60,
        "반등 파동": 55,
        "되돌림 깊어짐": 65,      # 지지 확인 시 매수
        "조정 파동 진행": 55,
        "고점 갱신 중": 50,       # 이미 올라감
        "변동성 확대": 40,
        "삼각 수렴": 55,          # 돌파 대기
        "판별 불가": 50,
        "데이터 부족": 50,
    }
    return scores.get(position, 50)
