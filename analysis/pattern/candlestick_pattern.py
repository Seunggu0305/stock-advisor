"""캔들스틱 패턴 인식"""

import pandas as pd
from models.schemas import CandlestickResult


def analyze_candlestick(df: pd.DataFrame) -> CandlestickResult:
    if df is None or len(df) < 10:
        return CandlestickResult()

    patterns = []
    o = df["Open"].values
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values

    # 최근 3개 봉 분석
    i = len(df) - 1
    body = abs(c[i] - o[i])
    upper_wick = h[i] - max(c[i], o[i])
    lower_wick = min(c[i], o[i]) - l[i]
    total_range = h[i] - l[i]

    if total_range == 0:
        return CandlestickResult()

    is_bullish = c[i] > o[i]

    # 망치형 (Hammer) - 하락추세 바닥에서 긴 아래꼬리
    if lower_wick > body * 2 and upper_wick < body * 0.5 and body > 0:
        if _is_downtrend(c, i):
            patterns.append("망치형 (매수)")

    # 역망치형 (Inverted Hammer)
    if upper_wick > body * 2 and lower_wick < body * 0.5 and body > 0:
        if _is_downtrend(c, i):
            patterns.append("역망치형 (매수)")

    # 교수형 (Hanging Man)
    if lower_wick > body * 2 and upper_wick < body * 0.5 and body > 0:
        if _is_uptrend(c, i):
            patterns.append("교수형 (매도)")

    # 도지 (Doji)
    if body < total_range * 0.1:
        patterns.append("도지 (전환)")

    # 장악형 (Engulfing)
    if i >= 1:
        prev_body = abs(c[i-1] - o[i-1])
        if is_bullish and c[i-1] < o[i-1]:  # 이전 음봉
            if o[i] <= c[i-1] and c[i] >= o[i-1] and body > prev_body:
                patterns.append("상승장악형 (매수)")
        elif not is_bullish and c[i-1] > o[i-1]:  # 이전 양봉
            if o[i] >= c[i-1] and c[i] <= o[i-1] and body > prev_body:
                patterns.append("하락장악형 (매도)")

    # 샛별/석별 (Morning/Evening Star)
    if i >= 2:
        body_2 = abs(c[i-2] - o[i-2])
        body_1 = abs(c[i-1] - o[i-1])
        if (c[i-2] < o[i-2] and  # 첫 번째 음봉
            body_1 < body_2 * 0.3 and  # 작은 몸통
            is_bullish and body > body_2 * 0.5):  # 큰 양봉
            patterns.append("샛별형 (매수)")
        elif (c[i-2] > o[i-2] and
              body_1 < body_2 * 0.3 and
              not is_bullish and body > body_2 * 0.5):
            patterns.append("석별형 (매도)")

    # 지배적 신호 판단
    buy_signals = sum(1 for p in patterns if "매수" in p)
    sell_signals = sum(1 for p in patterns if "매도" in p)

    if buy_signals > sell_signals:
        dominant = "매수"
    elif sell_signals > buy_signals:
        dominant = "매도"
    elif patterns:
        dominant = "전환 가능"
    else:
        dominant = "중립"

    # 점수
    if dominant == "매수":
        score = 65 + buy_signals * 5
    elif dominant == "매도":
        score = 35 - sell_signals * 5
    else:
        score = 50

    return CandlestickResult(
        patterns=patterns,
        dominant_signal=dominant,
        score=round(max(0, min(100, score)), 1),
    )


def _is_downtrend(close, idx, period=5) -> bool:
    if idx < period:
        return False
    return close[idx] < close[idx - period]


def _is_uptrend(close, idx, period=5) -> bool:
    if idx < period:
        return False
    return close[idx] > close[idx - period]
