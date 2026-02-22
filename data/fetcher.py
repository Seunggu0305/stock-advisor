"""데이터 수집 오케스트레이터"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from data import yahoo_client, fred_client, finviz_client


class DataFetcher:
    """모든 데이터 소스를 수집하여 반환

    yfinance는 내부적으로 공유 세션을 사용하여 병렬 호출 시 충돌이 발생할 수 있음.
    핵심 데이터(price_data, stock_info)는 순차 수집,
    독립 소스(fred, finviz)만 병렬 수집.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.data = {}

    def fetch_all(self) -> dict:
        # Phase 1: 핵심 yfinance 데이터를 순차적으로 수집 (세션 충돌 방지)
        yf_tasks = [
            ("price_data", lambda: yahoo_client.get_stock_data(self.ticker)),
            ("stock_info", lambda: yahoo_client.get_stock_info(self.ticker)),
            ("options", lambda: yahoo_client.get_options_chain(self.ticker)),
            ("institutional", lambda: yahoo_client.get_institutional_holders(self.ticker)),
            ("earnings", lambda: yahoo_client.get_earnings(self.ticker)),
            ("macro", lambda: yahoo_client.get_macro_data()),
            ("sector_etfs", lambda: yahoo_client.get_sector_etfs()),
        ]

        for name, fn in yf_tasks:
            try:
                self.data[name] = fn()
            except Exception as e:
                print(f"[경고] {name} 데이터 수집 실패: {e}")
                self.data[name] = None

        # Phase 2: 독립 데이터 소스는 병렬 수집
        parallel_tasks = {
            "fred_rates": lambda: fred_client.get_interest_rates(),
            "finviz": lambda: finviz_client.get_stock_stats(self.ticker),
        }

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(fn): name for name, fn in parallel_tasks.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    self.data[name] = future.result()
                except Exception as e:
                    print(f"[경고] {name} 데이터 수집 실패: {e}")
                    self.data[name] = None

        return self.data
