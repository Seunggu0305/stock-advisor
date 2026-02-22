"""옵션 플로우 분석 - 풋/콜 비율, IV Rank"""

import pandas as pd
import numpy as np
from models.schemas import OptionsFlowResult


def analyze_options_flow(options_data: dict | None) -> OptionsFlowResult:
    if options_data is None:
        return OptionsFlowResult()

    calls = options_data.get("calls")
    puts = options_data.get("puts")

    if calls is None or puts is None:
        return OptionsFlowResult()

    if not isinstance(calls, pd.DataFrame) or not isinstance(puts, pd.DataFrame):
        return OptionsFlowResult()

    # 풋/콜 비율 (거래량 기반)
    total_call_vol = float(calls["volume"].sum()) if "volume" in calls.columns else 0
    total_put_vol = float(puts["volume"].sum()) if "volume" in puts.columns else 0

    if total_call_vol > 0:
        pcr = total_put_vol / total_call_vol
    else:
        pcr = 1.0

    # IV Rank (현재 IV의 상대적 위치)
    iv_rank = 50.0
    try:
        all_iv = pd.concat([
            calls["impliedVolatility"] if "impliedVolatility" in calls.columns else pd.Series(),
            puts["impliedVolatility"] if "impliedVolatility" in puts.columns else pd.Series(),
        ]).dropna()
        if not all_iv.empty and len(all_iv) >= 5:
            current_iv = float(all_iv.median())
            iv_min = float(all_iv.min())
            iv_max = float(all_iv.max())
            if iv_max > iv_min:
                iv_rank = (current_iv - iv_min) / (iv_max - iv_min) * 100
            else:
                iv_rank = 50.0
    except Exception:
        pass

    # 시그널 판단
    if pcr > 1.2:
        signal = "약세 심리 (역발상 매수?)"
    elif pcr > 0.8:
        signal = "중립"
    elif pcr > 0.5:
        signal = "강세"
    else:
        signal = "강한 강세"

    # 점수
    # 높은 PCR = 시장 공포 = 역발상 매수 기회 (높은 점수)
    if pcr > 1.5:
        score = 75  # 극단적 공포 = 매수 기회
    elif pcr > 1.0:
        score = 60
    elif pcr > 0.7:
        score = 50
    elif pcr > 0.5:
        score = 45
    else:
        score = 35  # 과도한 낙관 = 주의

    return OptionsFlowResult(
        put_call_ratio=round(pcr, 2),
        iv_rank=round(iv_rank, 1),
        signal=signal,
        score=round(score, 1),
    )
