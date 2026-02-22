"""거래량 분석 - OBV 잔존율, VWAP, Volume Profile"""

import pandas as pd
import numpy as np
import utils.ta_utils as ta
from models.schemas import VolumeResult


def analyze_volume(df: pd.DataFrame) -> VolumeResult:
    if df is None or len(df) < 30:
        return VolumeResult()

    close = df["Close"]
    volume = df["Volume"]
    high = df["High"]
    low = df["Low"]

    # OBV
    obv = ta.obv(close, volume)
    if obv is not None and not obv.empty:
        obv_max = float(obv.max())
        obv_min = float(obv.min())
        obv_current = float(obv.iloc[-1])
        if obv_max != obv_min:
            retention = (obv_current - obv_min) / (obv_max - obv_min)
        else:
            retention = 0.5
        retention = round(retention, 2)

        if retention >= 0.8:
            obv_label = "강함"
        elif retention >= 0.5:
            obv_label = "보통"
        else:
            obv_label = "약함"
    else:
        retention = 0.5
        obv_label = "보통"

    # VWAP (당일 또는 최근 20일 기준)
    typical_price = (high + low + close) / 3
    cumulative_tp_vol = (typical_price * volume).rolling(window=20).sum()
    cumulative_vol = volume.rolling(window=20).sum()
    vwap_series = cumulative_tp_vol / cumulative_vol
    vwap_val = float(vwap_series.iloc[-1]) if not vwap_series.empty else float(close.iloc[-1])
    if pd.isna(vwap_val):
        vwap_val = float(close.iloc[-1])
    current_price = float(close.iloc[-1])
    price_vs_vwap = "위" if current_price > vwap_val else "아래"

    # Volume Profile (간이 구현)
    price_range = np.linspace(float(low.min()), float(high.max()), 50)
    vol_profile = np.zeros(len(price_range) - 1)
    for i in range(len(df)):
        for j in range(len(price_range) - 1):
            if float(low.iloc[i]) <= price_range[j + 1] and float(high.iloc[i]) >= price_range[j]:
                vol_profile[j] += float(volume.iloc[i])

    poc_idx = np.argmax(vol_profile)
    poc_price = round((price_range[poc_idx] + price_range[poc_idx + 1]) / 2, 2)

    # Value Area (70% of volume)
    total_vol = vol_profile.sum()
    sorted_indices = np.argsort(vol_profile)[::-1]
    cumulative = 0
    va_indices = []
    for idx in sorted_indices:
        cumulative += vol_profile[idx]
        va_indices.append(idx)
        if cumulative >= total_vol * 0.7:
            break
    va_indices.sort()
    val = round(price_range[va_indices[0]], 2) if va_indices else poc_price
    vah = round(price_range[min(va_indices[-1] + 1, len(price_range) - 1)], 2) if va_indices else poc_price

    # 점수
    obv_score = retention * 100
    vwap_score = 60 if current_price > vwap_val else 40
    score = obv_score * 0.5 + vwap_score * 0.5

    return VolumeResult(
        obv_retention=retention,
        obv_label=obv_label,
        vwap=round(vwap_val, 2),
        price_vs_vwap=price_vs_vwap,
        poc_price=poc_price,
        value_area_high=vah,
        value_area_low=val,
        score=round(max(0, min(100, score)), 1),
    )
