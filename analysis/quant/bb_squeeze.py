"""볼린저 밴드 스퀴즈 감지 (BB vs Keltner Channel)"""

import pandas as pd
import utils.ta_utils as ta
from models.schemas import BBSqueezeResult


def analyze_bb_squeeze(df: pd.DataFrame) -> BBSqueezeResult:
    if df is None or len(df) < 50:
        return BBSqueezeResult()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # Bollinger Bands
    bb = ta.bbands(close, length=20, std=2)
    if bb is None or bb.empty:
        return BBSqueezeResult()

    bb_upper = bb.iloc[:, 0]  # BBU
    bb_mid = bb.iloc[:, 1]    # BBM
    bb_lower = bb.iloc[:, 2]  # BBL

    # Keltner Channel
    atr = ta.atr(high, low, close, length=20)
    ema20 = ta.ema(close, length=20)
    if atr is None or ema20 is None:
        return BBSqueezeResult()

    kc_upper = ema20 + atr * 1.5
    kc_lower = ema20 - atr * 1.5

    # NaN 체크
    if (pd.isna(bb_upper.iloc[-1]) or pd.isna(bb_lower.iloc[-1]) or
            pd.isna(kc_upper.iloc[-1]) or pd.isna(kc_lower.iloc[-1])):
        return BBSqueezeResult()

    # 스퀴즈 판단: BB가 KC 안에 있으면 스퀴즈 ON
    is_squeezing = (float(bb_upper.iloc[-1]) < float(kc_upper.iloc[-1]) and
                    float(bb_lower.iloc[-1]) > float(kc_lower.iloc[-1]))

    # 스퀴즈 지속 기간 계산
    squeeze_duration = 0
    for i in range(len(bb_upper) - 1, -1, -1):
        if pd.isna(bb_upper.iloc[i]) or pd.isna(kc_upper.iloc[i]):
            break
        if (float(bb_upper.iloc[i]) < float(kc_upper.iloc[i]) and
            float(bb_lower.iloc[i]) > float(kc_lower.iloc[i])):
            squeeze_duration += 1
        else:
            break

    # 예상 방향: 모멘텀 오실레이터 방향
    mom = ta.momentum(close, length=12)
    expected_dir = None
    if mom is not None and not mom.empty and not pd.isna(mom.iloc[-1]):
        mom_val = float(mom.iloc[-1])
        if mom_val > 0:
            expected_dir = "상승"
        elif mom_val < 0:
            expected_dir = "하락"

    # 점수: 스퀴즈 진행 중이면 폭발적 움직임 예상
    if is_squeezing:
        if expected_dir == "상승":
            score = 70 + min(squeeze_duration * 2, 20)
        elif expected_dir == "하락":
            score = 30 - min(squeeze_duration * 2, 20)
        else:
            score = 55
    else:
        # 최근 스퀴즈 해제 여부
        if squeeze_duration == 0 and len(bb_upper) >= 2:
            prev_sq = (float(bb_upper.iloc[-2]) < float(kc_upper.iloc[-2]) and
                       float(bb_lower.iloc[-2]) > float(kc_lower.iloc[-2]))
            if prev_sq:
                score = 65 if expected_dir == "상승" else 35
            else:
                score = 50
        else:
            score = 50

    return BBSqueezeResult(
        is_squeezing=is_squeezing,
        squeeze_duration=squeeze_duration,
        expected_direction=expected_dir,
        score=round(max(0, min(100, score)), 1),
    )
