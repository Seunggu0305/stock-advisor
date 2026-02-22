"""일목균형표 분석"""

import pandas as pd
from models.schemas import IchimokuResult


def analyze_ichimoku(df: pd.DataFrame) -> IchimokuResult:
    # 구름(span_b)은 rolling(52)+shift(26)이므로 최소 78일 필요
    if df is None or len(df) < 78:
        return IchimokuResult()

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # 전환선 (Tenkan-sen) - 9일
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    # 기준선 (Kijun-sen) - 26일
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    # 선행스팬A (Senkou Span A) - (전환선+기준선)/2, 26일 선행
    span_a = ((tenkan + kijun) / 2).shift(26)
    # 선행스팬B (Senkou Span B) - 52일, 26일 선행
    span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    # 치코스팬 (Chikou Span) - 종가를 26일 후행
    chikou = close.shift(-26)

    current = float(close.iloc[-1])
    curr_tenkan = float(tenkan.iloc[-1])
    curr_kijun = float(kijun.iloc[-1])
    # NaN 안전 체크
    if pd.isna(curr_tenkan):
        curr_tenkan = current
    if pd.isna(curr_kijun):
        curr_kijun = current

    # 구름 위치 (현재 가격 기준)
    curr_span_a = float(span_a.iloc[-1]) if span_a is not None and len(span_a) > 0 and pd.notna(span_a.iloc[-1]) else current
    curr_span_b = float(span_b.iloc[-1]) if span_b is not None and len(span_b) > 0 and pd.notna(span_b.iloc[-1]) else current
    cloud_top = max(curr_span_a, curr_span_b)
    cloud_bottom = min(curr_span_a, curr_span_b)

    if current > cloud_top:
        cloud_position = "구름 위"
    elif current < cloud_bottom:
        cloud_position = "구름 아래"
    else:
        cloud_position = "구름 내"

    # 전환선/기준선 크로스
    if len(tenkan) >= 2 and len(kijun) >= 2:
        prev_tenkan = float(tenkan.iloc[-2])
        prev_kijun = float(kijun.iloc[-2])
        if prev_tenkan <= prev_kijun and curr_tenkan > curr_kijun:
            tk_cross = "호전 (매수)"
        elif prev_tenkan >= prev_kijun and curr_tenkan < curr_kijun:
            tk_cross = "역전 (매도)"
        elif curr_tenkan > curr_kijun:
            tk_cross = "매수 유지"
        else:
            tk_cross = "매도 유지"
    else:
        tk_cross = None

    # 치코스팬
    if len(chikou) > 26 and pd.notna(chikou.iloc[-27]):
        chikou_val = float(close.iloc[-1])
        past_price = float(close.iloc[-27])
        if chikou_val > past_price:
            chikou_signal = "강세"
        else:
            chikou_signal = "약세"
    else:
        chikou_signal = "중립"

    # 점수 (5가지 신호 각 20점)
    score = 0
    # 1) 가격 vs 구름
    if cloud_position == "구름 위":
        score += 20
    elif cloud_position == "구름 내":
        score += 10
    # 2) 전환선/기준선
    if tk_cross and "매수" in tk_cross:
        score += 20
    elif tk_cross and "호전" in tk_cross:
        score += 20
    elif tk_cross and "매도" not in str(tk_cross):
        score += 10
    # 3) 치코스팬
    if chikou_signal == "강세":
        score += 20
    elif chikou_signal == "중립":
        score += 10
    # 4) 구름 색상 (미래 구름)
    if curr_span_a > curr_span_b:
        score += 20  # 양운
    elif curr_span_a == curr_span_b:
        score += 10
    # 5) 가격 vs 기준선
    if current > curr_kijun:
        score += 20
    elif current > curr_tenkan:
        score += 10

    return IchimokuResult(
        cloud_position=cloud_position,
        tenkan_kijun_cross=tk_cross,
        chikou_signal=chikou_signal,
        score=round(score, 1),
    )
