"""FVG (공정가치갭) 감지"""

import pandas as pd
import utils.ta_utils as ta
from models.schemas import FVGResult


def analyze_fvg(df: pd.DataFrame) -> FVGResult:
    if df is None or len(df) < 20:
        return FVGResult()

    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values
    current_price = float(close[-1])

    # ATR for filtering
    atr = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    min_gap_size = float(atr.iloc[-1]) * 0.5 if atr is not None and not atr.empty else 0

    bullish_gaps = []
    bearish_gaps = []

    for i in range(2, len(df)):
        # 강세 FVG: candle[i-2]의 high < candle[i]의 low
        gap_low = float(high[i - 2])
        gap_high = float(low[i])
        if gap_high > gap_low and (gap_high - gap_low) >= min_gap_size:
            # 미청산 여부 확인 (이후 가격이 갭을 채웠는지)
            filled = False
            for j in range(i + 1, len(df)):
                if float(low[j]) <= gap_low:
                    filled = True
                    break
            if not filled:
                bullish_gaps.append((round(gap_low, 2), round(gap_high, 2)))

        # 약세 FVG: candle[i-2]의 low > candle[i]의 high
        gap_high_b = float(low[i - 2])
        gap_low_b = float(high[i])
        if gap_high_b > gap_low_b and (gap_high_b - gap_low_b) >= min_gap_size:
            filled = False
            for j in range(i + 1, len(df)):
                if float(high[j]) >= gap_high_b:
                    filled = True
                    break
            if not filled:
                bearish_gaps.append((round(gap_low_b, 2), round(gap_high_b, 2)))

    # 현재가에 가장 가까운 FVG 지지/저항
    nearest_support = None
    nearest_resistance = None

    for gap_low, gap_high in bullish_gaps:
        if gap_high <= current_price:
            if nearest_support is None or gap_high > nearest_support:
                nearest_support = gap_high

    for gap_low, gap_high in bearish_gaps:
        if gap_low >= current_price:
            if nearest_resistance is None or gap_low < nearest_resistance:
                nearest_resistance = gap_low

    # 라벨 생성
    label_parts = []
    if nearest_support:
        label_parts.append(f"상승 갭(FVG) @ {nearest_support}")
    if nearest_resistance:
        label_parts.append(f"하락 갭(FVG) @ {nearest_resistance}")
    if not label_parts:
        label_parts.append("없음")
    label = " | ".join(label_parts)

    # 점수: FVG 지지가 가까우면 매수 기회
    score = 50.0
    if nearest_support:
        dist_pct = (current_price - nearest_support) / current_price * 100
        if dist_pct < 2:
            score = 75  # FVG 지지 근접
        elif dist_pct < 5:
            score = 65
    if nearest_resistance:
        dist_pct = (nearest_resistance - current_price) / current_price * 100
        if dist_pct < 2:
            score = max(score - 15, 30)  # FVG 저항 근접

    return FVGResult(
        bullish_gaps=bullish_gaps[-5:],  # 최근 5개만
        bearish_gaps=bearish_gaps[-5:],
        nearest_support_gap=nearest_support,
        nearest_resistance_gap=nearest_resistance,
        label=label,
        score=round(score, 1),
    )
