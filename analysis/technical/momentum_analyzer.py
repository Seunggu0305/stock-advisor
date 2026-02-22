"""모멘텀/에너지 분석 - RSI, MACD, Stochastic, 골든/데드크로스"""

import pandas as pd
import utils.ta_utils as ta
from models.schemas import MomentumResult


def analyze_momentum(df: pd.DataFrame) -> MomentumResult:
    if df is None or len(df) < 50:
        return MomentumResult()

    close = df["Close"]

    # RSI
    rsi = ta.rsi(close, length=14)
    rsi_val = 50.0
    if rsi is not None and not rsi.empty:
        _rv = float(rsi.iloc[-1])
        if not pd.isna(_rv):
            rsi_val = _rv

    # MACD
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        macd_line = float(macd_df.iloc[-1, 0])
        signal_line = float(macd_df.iloc[-1, 2])
        histogram = float(macd_df.iloc[-1, 1])
        prev_hist = float(macd_df.iloc[-2, 1]) if len(macd_df) >= 2 else 0
        # NaN 방어
        if pd.isna(macd_line) or pd.isna(signal_line) or pd.isna(histogram):
            macd_signal = "중립"
            histogram = 0
        elif macd_line > signal_line and histogram > prev_hist:
            macd_signal = "매수"
        elif macd_line < signal_line and histogram < prev_hist:
            macd_signal = "매도"
        else:
            macd_signal = "중립"
    else:
        macd_signal = "중립"
        histogram = 0

    # Stochastic
    stoch = ta.stochastic(df["High"], df["Low"], close, k=14, d=3, smooth_k=3)
    if stoch is not None and not stoch.empty:
        k_val = float(stoch.iloc[-1, 0])
        d_val = float(stoch.iloc[-1, 1])
        # NaN 방어
        if pd.isna(k_val) or pd.isna(d_val):
            k_val, d_val = 50.0, 50.0
        if k_val < 20 and k_val > d_val:
            stoch_signal = "매수"
        elif k_val > 80 and k_val < d_val:
            stoch_signal = "매도"
        else:
            stoch_signal = "중립"
    else:
        stoch_signal = "중립"

    # 에너지 라벨
    if rsi_val > 50 and macd_signal == "매수":
        energy = "매수세 증가"
    elif rsi_val < 50 and macd_signal == "매도":
        energy = "매도세 증가"
    elif rsi_val > 50:
        energy = "매수세 감소" if histogram < 0 else "매수세 유지"
    elif rsi_val < 50:
        energy = "매도세 감소" if histogram > 0 else "매도세 유지"
    else:
        energy = "중립"

    # 골든/데드 크로스
    cross_type = None
    if len(df) >= 200:
        sma50 = ta.sma(close, length=50)
        sma200 = ta.sma(close, length=200)
        if sma50 is not None and sma200 is not None and len(sma50) >= 2:
            curr_50 = float(sma50.iloc[-1])
            prev_50 = float(sma50.iloc[-2])
            curr_200 = float(sma200.iloc[-1])
            prev_200 = float(sma200.iloc[-2])
            if prev_50 <= prev_200 and curr_50 > curr_200:
                cross_type = "골든크로스"
            elif prev_50 >= prev_200 and curr_50 < curr_200:
                cross_type = "데드크로스"
            # 최근 N일 이내 발생 여부도 체크
            elif curr_50 > curr_200 and abs(curr_50 - curr_200) / curr_200 < 0.01:
                cross_type = "골든크로스 근접"
            elif curr_50 < curr_200 and abs(curr_50 - curr_200) / curr_200 < 0.01:
                cross_type = "데드크로스 근접"

    # 점수 산출
    # RSI: 과매도(30 이하)=높은 점수(역발상), 과매수(70 이상)=낮은 점수
    if rsi_val < 30:
        rsi_score = 80 + min(30 - rsi_val, 20)  # 최대 100
    elif rsi_val > 70:
        rsi_score = max(0, 20 - (rsi_val - 70))  # 최소 0
    else:
        rsi_score = 50 + (50 - rsi_val) * 0.5  # 25~75 범위

    macd_scores = {"매수": 75, "중립": 50, "매도": 25}
    stoch_scores = {"매수": 75, "중립": 50, "매도": 25}

    score = (rsi_score * 0.4 + macd_scores[macd_signal] * 0.35 +
             stoch_scores[stoch_signal] * 0.25)

    # 크로스 보너스
    if cross_type == "골든크로스":
        score = min(100, score + 15)
    elif cross_type == "데드크로스":
        score = max(0, score - 15)

    if cross_type and "근접" in cross_type:
        energy += f" ({cross_type})"
    elif cross_type:
        energy += f" ({cross_type})"

    return MomentumResult(
        rsi=round(rsi_val, 1),
        macd_signal=macd_signal,
        stochastic_signal=stoch_signal,
        energy_label=energy,
        cross_type=cross_type,
        score=round(max(0, min(100, score)), 1),
    )
