"""yfinance 래퍼 - 주가, 옵션, 재무, 매크로 티커 데이터 수집"""

import yfinance as yf
import pandas as pd
from data.cache_manager import get_or_fetch
from config.settings import (
    CACHE_TTL_PRICE, CACHE_TTL_FINANCIAL, CACHE_TTL_OPTIONS, CACHE_TTL_MACRO,
    DEFAULT_PERIOD,
)


def get_stock_data(ticker: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    """OHLCV 일봉 데이터"""
    def fetch():
        t = yf.Ticker(ticker)
        df = t.history(period=period, auto_adjust=True)
        if df is not None and not df.empty:
            df = _clean_ohlcv(df)
        return df
    return get_or_fetch(f"stock_{ticker}_{period}", fetch, CACHE_TTL_PRICE)


def _clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """OHLCV 데이터 NaN 정리 - 모든 하류 분석 모듈 보호"""
    # Close에 NaN이 있는 행 제거 (가격 없으면 분석 불가)
    df = df.dropna(subset=["Close"])
    # High/Low/Open에 NaN이 있으면 Close로 채움
    for col in ["Open", "High", "Low"]:
        if col in df.columns:
            df[col] = df[col].fillna(df["Close"])
    # Volume NaN은 0으로
    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].fillna(0)
    return df


def get_stock_info(ticker: str) -> dict:
    """종목 기본 정보 (이름, 섹터, 시총 등)"""
    def fetch():
        t = yf.Ticker(ticker)
        return t.info
    return get_or_fetch(f"info_{ticker}", fetch, CACHE_TTL_FINANCIAL)


def get_options_chain(ticker: str) -> dict | None:
    """옵션 체인 (가장 가까운 만기)"""
    def fetch():
        t = yf.Ticker(ticker)
        try:
            dates = t.options
            if not dates:
                return None
            chain = t.option_chain(dates[0])
            return {"calls": chain.calls, "puts": chain.puts, "expiry": dates[0]}
        except Exception:
            return None
    return get_or_fetch(f"options_{ticker}", fetch, CACHE_TTL_OPTIONS)


def get_institutional_holders(ticker: str) -> pd.DataFrame | None:
    """기관 보유 현황"""
    def fetch():
        t = yf.Ticker(ticker)
        try:
            return t.institutional_holders
        except Exception:
            return None
    return get_or_fetch(f"inst_{ticker}", fetch, CACHE_TTL_FINANCIAL)


def get_earnings(ticker: str) -> dict | None:
    """어닝 정보"""
    def fetch():
        t = yf.Ticker(ticker)
        try:
            cal = t.calendar
            earnings_hist = t.earnings_history
            return {"calendar": cal, "history": earnings_hist}
        except Exception:
            return None
    return get_or_fetch(f"earnings_{ticker}", fetch, CACHE_TTL_FINANCIAL)


def get_macro_data() -> dict:
    """매크로 티커 데이터 (VIX, 유가, 금, S&P500)"""
    def fetch():
        tickers = {
            "vix": "^VIX",
            "oil": "CL=F",
            "gold": "GC=F",
            "sp500": "^GSPC",
            "treasury_10y": "^TNX",
            "dxy": "DX-Y.NYB",
        }
        result = {}
        for name, sym in tickers.items():
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="3mo")
                if not hist.empty:
                    result[name] = {
                        "current": float(hist["Close"].iloc[-1]),
                        "history": hist["Close"],
                    }
            except Exception:
                pass
        return result
    return get_or_fetch("macro_data", fetch, CACHE_TTL_MACRO)


def get_sector_etfs() -> dict:
    """섹터 ETF 데이터"""
    def fetch():
        sector_map = {
            "Technology": "XLK", "Healthcare": "XLV", "Financial": "XLF",
            "Consumer Disc.": "XLY", "Consumer Staples": "XLP",
            "Energy": "XLE", "Utilities": "XLU", "Industrial": "XLI",
            "Materials": "XLB", "Real Estate": "XLRE", "Communication": "XLC",
        }
        result = {}
        for name, etf in sector_map.items():
            try:
                t = yf.Ticker(etf)
                hist = t.history(period="3mo")
                if not hist.empty:
                    ret_1m = (hist["Close"].iloc[-1] / hist["Close"].iloc[-21] - 1) * 100
                    result[name] = {"etf": etf, "return_1m": float(ret_1m)}
            except Exception:
                pass
        return result
    return get_or_fetch("sector_etfs", fetch, CACHE_TTL_MACRO)
