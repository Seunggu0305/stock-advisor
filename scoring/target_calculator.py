"""목표가/손절가 계산"""

import pandas as pd
import utils.ta_utils as ta
from models.schemas import PriceTarget, FibonacciResult, FVGResult, VolumeResult
from utils.helpers import find_swing_highs, find_swing_lows


def calculate_targets(
    df: pd.DataFrame,
    fibonacci: FibonacciResult,
    fvg: FVGResult,
    volume: VolumeResult,
) -> PriceTarget:
    if df is None or len(df) < 30:
        return PriceTarget()

    current = float(df["Close"].iloc[-1])

    # ATR
    atr = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    atr_val = float(atr.iloc[-1]) if atr is not None and not atr.empty else current * 0.02

    # 스윙 포인트
    swing_highs = find_swing_highs(df["High"].values, window=10)
    swing_lows = find_swing_lows(df["Low"].values, window=10)

    # ── 목표가 계산 ──
    target_candidates = []

    # 1) 최근 스윙 고점
    recent_highs = [h[1] for h in swing_highs if h[1] > current]
    if recent_highs:
        target_candidates.append(min(recent_highs))  # 가장 가까운 저항

    # 2) 피보나치 확장
    if fibonacci.levels:
        for label, price in fibonacci.levels.items():
            if price > current * 1.02:  # 현재가 대비 2% 이상
                target_candidates.append(price)
                break  # 가장 가까운 것만

    # 3) FVG 저항
    if fvg.nearest_resistance_gap and fvg.nearest_resistance_gap > current:
        target_candidates.append(fvg.nearest_resistance_gap)

    # 4) Volume Profile VAH
    if volume.value_area_high > current:
        target_candidates.append(volume.value_area_high)

    # 5) ATR 기반 (2.5 ATR)
    target_candidates.append(current + atr_val * 2.5)

    if target_candidates:
        target_price = sum(target_candidates) / len(target_candidates)
    else:
        target_price = current * 1.10  # 기본 10%

    target_pct = (target_price / current - 1) * 100

    # 1차 저항 (가장 가까운 저항 레벨)
    resistance_1 = min(target_candidates) if target_candidates else target_price

    # ── 손절가 계산 ──
    stop_candidates = []

    # 1) ATR 기반 (2 ATR)
    stop_candidates.append(current - atr_val * 2)

    # 2) 최근 스윙 저점
    recent_lows = [l[1] for l in swing_lows if l[1] < current]
    if recent_lows:
        stop_candidates.append(max(recent_lows))  # 가장 가까운 지지

    # 3) FVG 지지 하단
    if fvg.nearest_support_gap:
        stop_candidates.append(fvg.nearest_support_gap * 0.98)

    # 4) Volume Profile VAL
    if volume.value_area_low > 0 and volume.value_area_low < current:
        stop_candidates.append(volume.value_area_low)

    # 보수적 선택 (가장 가까운 = 가장 높은 손절가)
    if stop_candidates:
        stop_loss = max(stop_candidates)
    else:
        stop_loss = current * 0.95  # 기본 -5%

    stop_loss_pct = (stop_loss / current - 1) * 100

    # 1차 지지
    support_1 = max([s for s in stop_candidates if s < current], default=stop_loss)

    return PriceTarget(
        target_price=round(target_price, 2),
        target_pct=round(target_pct, 1),
        resistance_1=round(resistance_1, 2),
        stop_loss=round(stop_loss, 2),
        stop_loss_pct=round(stop_loss_pct, 1),
        support_1=round(support_1, 2),
    )
