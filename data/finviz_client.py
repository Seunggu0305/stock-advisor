"""Finviz 데이터 수집 - 공매도 비율, 섹터 정보"""

from data.cache_manager import get_or_fetch
from config.settings import CACHE_TTL_FINANCIAL


def get_stock_stats(ticker: str) -> dict:
    """Finviz에서 종목 통계 수집"""
    def fetch():
        try:
            from finvizfinance.quote import finvizfinance
            stock = finvizfinance(ticker)
            data = stock.ticker_fundament()
            return {
                "short_float": _parse_pct(data.get("Short Float", "0%")),
                "short_ratio": _parse_float(data.get("Short Ratio", "0")),
                "sector": data.get("Sector", "Unknown"),
                "industry": data.get("Industry", "Unknown"),
                "market_cap": data.get("Market Cap", "N/A"),
                "perf_week": _parse_pct(data.get("Perf Week", "0%")),
                "perf_month": _parse_pct(data.get("Perf Month", "0%")),
                "perf_quarter": _parse_pct(data.get("Perf Quarter", "0%")),
                "rel_volume": _parse_float(data.get("Rel Volume", "1")),
                "avg_volume": data.get("Avg Volume", "N/A"),
                "inst_own": _parse_pct(data.get("Inst Own", "0%")),
                "insider_own": _parse_pct(data.get("Insider Own", "0%")),
                "earnings_date": data.get("Earnings", "N/A"),
            }
        except Exception:
            return _default_stats()
    return get_or_fetch(f"finviz_{ticker}", fetch, CACHE_TTL_FINANCIAL)


def _parse_pct(val: str) -> float:
    try:
        return float(val.replace("%", "").replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def _parse_float(val: str) -> float:
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def _default_stats() -> dict:
    return {
        "short_float": 0.0, "short_ratio": 0.0, "sector": "Unknown",
        "industry": "Unknown", "market_cap": "N/A", "perf_week": 0.0,
        "perf_month": 0.0, "perf_quarter": 0.0, "rel_volume": 1.0,
        "avg_volume": "N/A", "inst_own": 0.0, "insider_own": 0.0,
        "earnings_date": "N/A",
    }
