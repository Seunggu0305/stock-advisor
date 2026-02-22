"""FRED API 래퍼 - 금리, 수익률곡선 데이터"""

import pandas as pd
from config.settings import FRED_API_KEY, CACHE_TTL_MACRO
from data.cache_manager import get_or_fetch


def _get_fred():
    if not FRED_API_KEY:
        return None
    from fredapi import Fred
    return Fred(api_key=FRED_API_KEY)


def get_interest_rates() -> dict | None:
    """금리 데이터 (기준금리, 10Y, 2Y, 장단기 스프레드)"""
    def fetch():
        fred = _get_fred()
        if fred is None:
            return None
        try:
            series_ids = {
                "fed_funds": "DFF",
                "treasury_10y": "DGS10",
                "treasury_2y": "DGS2",
                "spread_10y2y": "T10Y2Y",
            }
            result = {}
            for name, sid in series_ids.items():
                data = fred.get_series(sid, observation_start="2024-01-01")
                data = data.dropna()
                if not data.empty:
                    result[name] = {
                        "current": float(data.iloc[-1]),
                        "prev_month": float(data.iloc[-22]) if len(data) >= 22 else float(data.iloc[0]),
                        "change_3m": float(data.iloc[-1] - data.iloc[-66]) if len(data) >= 66 else 0.0,
                    }
            return result
        except Exception:
            return None
    return get_or_fetch("fred_rates", fetch, CACHE_TTL_MACRO)


def get_yield_curve_status() -> str:
    """수익률 곡선 상태"""
    rates = get_interest_rates()
    if rates is None or "spread_10y2y" not in rates:
        return "알 수 없음"
    spread = rates["spread_10y2y"]["current"]
    if spread > 0.5:
        return "정상"
    elif spread > 0:
        return "평탄"
    else:
        return "역전"
