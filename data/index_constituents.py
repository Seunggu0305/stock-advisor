"""인덱스 구성종목 수집 - NASDAQ 100, S&P 500, Russell 2000
모든 인덱스를 Finviz 스크리너에서 통일 수집, 실패 시 하드코딩 폴백 사용.
"""

import math
from data.cache_manager import get_or_fetch


def _fetch_finviz_index(index_filter: str, fallback: list[str],
                        label: str, min_count: int = 50) -> list[str]:
    """Finviz 스크리너에서 인덱스 구성종목 수집 (공통 로직)"""
    try:
        from finvizfinance.screener.overview import Overview
        foverview = Overview()
        foverview.set_filter(filters_dict={"Index": index_filter})
        df = foverview.screener_view()
        if len(df) >= min_count:
            tickers = sorted(df["Ticker"].tolist())
            print(f"[정보] {label}: {len(tickers)}개 종목 수집 완료")
            return tickers
        return fallback
    except Exception as e:
        print(f"[경고] {label} Finviz 수집 실패: {e}, 내장 목록 사용")
        return fallback


def get_nasdaq100_tickers() -> list[str]:
    """NASDAQ 100 구성종목"""
    def fetch():
        return _fetch_finviz_index("NASDAQ 100", _NASDAQ100_FALLBACK, "NASDAQ 100", 90)
    return get_or_fetch("nasdaq100_tickers", fetch, ttl=86400)


def get_sp500_tickers() -> list[str]:
    """S&P 500 구성종목"""
    def fetch():
        return _fetch_finviz_index("S&P 500", _SP500_FALLBACK, "S&P 500", 400)
    return get_or_fetch("sp500_tickers", fetch, ttl=86400)


def get_russell2000_tickers() -> list[str]:
    """Russell 2000 전체 구성종목 (~1,930개)"""
    def fetch():
        return _fetch_finviz_index("RUSSELL 2000", _RUSSELL2000_FALLBACK, "Russell 2000", 100)
    return get_or_fetch("russell2000_tickers", fetch, ttl=86400)


def get_russell2000_prefiltered(top_n: int = 200) -> list[str]:
    """Russell 2000 다중 팩터 사전 필터링

    기존 모멘텀 편향 문제 해결:
    - 모멘텀(35%) + 밸류(30%) + 거래량(20%) + 안정성(15%)
    - 섹터 분산 보장 (섹터당 최대 30%, 최소 3종목)
    """
    def fetch():
        try:
            return _multifactor_filter(top_n)
        except Exception as e:
            print(f"[경고] Russell 2000 다중팩터 실패: {e}, 모멘텀 방식으로 폴백")
            try:
                return _momentum_only_filter(top_n)
            except Exception as e2:
                print(f"[경고] Russell 2000 모멘텀도 실패: {e2}, 내장 목록 사용")
                return _RUSSELL2000_FALLBACK
    return get_or_fetch("russell2000_prefiltered", fetch, ttl=86400)


def _multifactor_filter(top_n: int) -> list[str]:
    """다중 팩터 필터링 (Performance + Overview 병합)"""
    from finvizfinance.screener.overview import Overview
    from finvizfinance.screener.performance import Performance

    # 성과 데이터 (모멘텀, 거래량, 변동성)
    fp = Performance()
    fp.set_filter(filters_dict={"Index": "RUSSELL 2000"})
    perf_df = fp.screener_view()
    if len(perf_df) < 100:
        raise ValueError(f"Performance 데이터 부족: {len(perf_df)}개")

    # 섹터/밸류에이션 데이터
    fo = Overview()
    fo.set_filter(filters_dict={"Index": "RUSSELL 2000"})
    over_df = fo.screener_view()

    # 병합
    df = perf_df.merge(
        over_df[["Ticker", "Sector", "P/E"]],
        on="Ticker", how="left",
    )

    total = len(df)

    # 기본 필터: 페니스탁 제외
    df = df.dropna(subset=["Price"])
    df = df[df["Price"] > 2.0]

    # ── 1. 모멘텀 점수 (35%) ──
    # 주간 30% + 월간 40% + 분기 30% → 백분위 순위
    mom_raw = (
        df["Perf Week"].fillna(0) * 0.3
        + df["Perf Month"].fillna(0) * 0.4
        + df["Perf Quart"].fillna(0) * 0.3
    )
    df["momentum_score"] = mom_raw.rank(pct=True) * 100

    # ── 2. 밸류 점수 (30%) ──
    # 낮은 P/E = 높은 점수, 적자/데이터없음 = 중립
    df["value_score"] = df["P/E"].apply(_pe_to_score)

    # ── 3. 거래량 활성도 (20%) ──
    # 상대 거래량 높을수록 관심 집중
    vol_raw = df["Rel Volume"].fillna(1).clip(upper=10)
    df["activity_score"] = vol_raw.rank(pct=True) * 100

    # ── 4. 안정성 점수 (15%) ──
    # 낮은 월간 변동성 = 높은 품질 (안정적 상승 선호)
    vol_m = df["Volatility M"].fillna(df["Volatility M"].median())
    df["stability_score"] = (1 - vol_m.rank(pct=True)) * 100  # 변동성 낮을수록 높은 점수

    # ── 복합 점수 ──
    df["pre_score"] = (
        df["momentum_score"] * 0.35
        + df["value_score"] * 0.30
        + df["activity_score"] * 0.20
        + df["stability_score"] * 0.15
    )

    # ── 섹터 분산 선정 ──
    tickers = _select_with_sector_balance(df, top_n)
    print(f"[정보] Russell 2000: {total}개 중 다중팩터 상위 {len(tickers)}개 선정")
    return tickers


def _momentum_only_filter(top_n: int) -> list[str]:
    """폴백: 기존 모멘텀 방식 (Overview 수집 실패 시)"""
    from finvizfinance.screener.performance import Performance

    fp = Performance()
    fp.set_filter(filters_dict={"Index": "RUSSELL 2000"})
    df = fp.screener_view()
    if len(df) < 100:
        raise ValueError(f"Performance 데이터 부족: {len(df)}개")

    total = len(df)
    df = df.dropna(subset=["Price"])
    df = df[df["Price"] > 2.0]

    df["pre_score"] = (
        df["Perf Week"].fillna(0) * 30
        + df["Perf Month"].fillna(0) * 30
        + df["Perf Quart"].fillna(0) * 20
        + df["Rel Volume"].fillna(1).clip(upper=5) * 4
    )
    df = df.sort_values("pre_score", ascending=False)
    tickers = df["Ticker"].head(top_n).tolist()
    print(f"[정보] Russell 2000: {total}개 중 모멘텀 상위 {len(tickers)}개 선정 (폴백)")
    return tickers


def _pe_to_score(pe) -> float:
    """P/E → 밸류 점수 (낮을수록 좋지만, 적자는 중립)"""
    try:
        pe = float(pe)
        if math.isnan(pe) or math.isinf(pe):
            return 40.0
    except (TypeError, ValueError):
        return 40.0  # 데이터 없음 = 중립
    if pe <= 0:
        return 35.0  # 적자 기업
    if pe < 10:
        return 90.0
    if pe < 15:
        return 75.0
    if pe < 20:
        return 60.0
    if pe < 30:
        return 45.0
    if pe < 50:
        return 30.0
    return 15.0



def _select_with_sector_balance(df, top_n: int) -> list[str]:
    """섹터 분산 보장하며 상위 종목 선정

    - 섹터당 최소: 인덱스 비중의 50% (최소 3종목)
    - 섹터당 최대: 30% 상한
    - 나머지는 pre_score 순으로 채움
    """
    df = df.sort_values("pre_score", ascending=False)

    max_per_sector = max(10, int(top_n * 0.30))

    # 섹터별 인덱스 비중에 비례한 최소 보장
    sector_shares = df["Sector"].value_counts(normalize=True)

    selected_set = set()
    selected_list = []
    sector_counts = {}

    # 1단계: 각 섹터에서 비례 최소 인원 확보
    sectors = [s for s in df["Sector"].dropna().unique() if s]
    for sector in sectors:
        share = sector_shares.get(sector, 0)
        min_for_sector = max(3, int(share * top_n * 0.5))
        sector_df = df[df["Sector"] == sector].head(min_for_sector)
        for ticker in sector_df["Ticker"]:
            if ticker not in selected_set:
                selected_set.add(ticker)
                selected_list.append(ticker)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # 2단계: 나머지 슬롯을 pre_score 순으로 채움 (섹터 상한 적용)
    for _, row in df.iterrows():
        if len(selected_list) >= top_n:
            break
        ticker = row["Ticker"]
        sector = row.get("Sector") or "Unknown"
        if ticker in selected_set:
            continue
        if sector_counts.get(sector, 0) >= max_per_sector:
            continue
        selected_set.add(ticker)
        selected_list.append(ticker)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return selected_list


def get_index_tickers(index_name: str) -> list[str]:
    index_map = {
        "NASDAQ 100": get_nasdaq100_tickers,
        "S&P 500": get_sp500_tickers,
        "Russell 2000": get_russell2000_prefiltered,
    }
    fn = index_map.get(index_name)
    return fn() if fn else []


# ── Fallback 하드코딩 목록 ──

_NASDAQ100_FALLBACK = sorted([
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN",
    "AMZN", "ANSS", "APP", "ARM", "ASML", "AVGO", "AZN", "BIIB", "BKNG", "BKR",
    "CCEP", "CDNS", "CDW", "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO",
    "CSGP", "CSX", "CTAS", "CTSH", "DASH", "DDOG", "DLTR", "DXCM", "EA", "EXC",
    "FANG", "FAST", "FTNT", "GEHC", "GFS", "GILD", "GOOG", "GOOGL", "HON", "IDXX",
    "ILMN", "INTC", "INTU", "ISRG", "KDP", "KHC", "KLAC", "LIN", "LRCX", "LULU",
    "MAR", "MCHP", "MDB", "MDLZ", "MELI", "META", "MNST", "MRVL", "MSFT", "MU",
    "NFLX", "NVDA", "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR", "PDD",
    "PEP", "PYPL", "QCOM", "REGN", "ROP", "ROST", "SBUX", "SMCI", "SNPS", "TEAM",
    "TMUS", "TSLA", "TTD", "TTWO", "TXN", "VRSK", "VRTX", "WBD", "WDAY", "XEL",
    "ZS",
])

_SP500_FALLBACK = sorted([
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "ADI", "ADM", "ADP", "ADSK", "AEE",
    "AEP", "AES", "AFL", "AIG", "AIZ", "AJG", "AKAM", "ALB", "ALGN", "ALL",
    "ALLE", "AMAT", "AMCR", "AMD", "AME", "AMGN", "AMP", "AMT", "AMZN", "ANET",
    "ANSS", "AON", "AOS", "APA", "APD", "APH", "APTV", "ARE", "ATO", "ATVI",
    "AVB", "AVGO", "AVY", "AWK", "AXP", "AZO", "BA", "BAC", "BAX", "BBWI",
    "BBY", "BDX", "BEN", "BF-B", "BIIB", "BIO", "BK", "BKNG", "BKR", "BLK",
    "BMY", "BR", "BRK-B", "BRO", "BSX", "BWA", "BXP", "C", "CAG", "CAH",
    "CARR", "CAT", "CB", "CBOE", "CBRE", "CCI", "CCL", "CDAY", "CDNS", "CDW",
    "CE", "CEG", "CF", "CFG", "CHD", "CHRW", "CHTR", "CI", "CINF", "CL",
    "CLX", "CMA", "CMCSA", "CME", "CMG", "CMI", "CMS", "CNC", "CNP", "COF",
    "COO", "COP", "COST", "CPB", "CPRT", "CPT", "CRL", "CRM", "CSCO", "CSGP",
    "CSX", "CTAS", "CTLT", "CTRA", "CTSH", "CTVA", "CVS", "CVX", "CZR", "D",
    "DAL", "DD", "DE", "DFS", "DG", "DGX", "DHI", "DHR", "DIS", "DISH",
    "DLR", "DLTR", "DOV", "DOW", "DPZ", "DRI", "DTE", "DUK", "DVA", "DVN",
    "DXC", "DXCM", "EA", "EBAY", "ECL", "ED", "EFX", "EIX", "EL", "EMN",
    "EMR", "ENPH", "EOG", "EPAM", "EQIX", "EQR", "EQT", "ES", "ESS", "ETN",
    "ETR", "ETSY", "EVRG", "EW", "EXC", "EXPD", "EXPE", "EXR", "F", "FANG",
    "FAST", "FBHS", "FCX", "FDS", "FDX", "FE", "FFIV", "FIS", "FISV", "FITB",
    "FLT", "FMC", "FOX", "FOXA", "FRC", "FRT", "FTNT", "FTV", "GD", "GE",
    "GILD", "GIS", "GL", "GLW", "GM", "GNRC", "GOOG", "GOOGL", "GPC", "GPN",
    "GRMN", "GS", "GWW", "HAL", "HAS", "HBAN", "HCA", "HD", "HOLX", "HON",
    "HPE", "HPQ", "HRL", "HSIC", "HST", "HSY", "HUM", "HWM", "IBM", "ICE",
    "IDXX", "IEX", "IFF", "ILMN", "INCY", "INTC", "INTU", "INVH", "IP", "IPG",
    "IQV", "IR", "IRM", "ISRG", "IT", "ITW", "IVZ", "J", "JBHT", "JCI",
    "JKHY", "JNJ", "JNPR", "JPM", "K", "KDP", "KEY", "KEYS", "KHC", "KIM",
    "KLAC", "KMB", "KMI", "KMX", "KO", "KR", "L", "LDOS", "LEN", "LH",
    "LHX", "LIN", "LKQ", "LLY", "LMT", "LNC", "LNT", "LOW", "LRCX", "LULU",
    "LUV", "LVS", "LW", "LYB", "LYV", "MA", "MAA", "MAR", "MAS", "MCD",
    "MCHP", "MCK", "MCO", "MDLZ", "MDT", "MET", "META", "MGM", "MHK", "MKC",
    "MKTX", "MLM", "MMC", "MMM", "MNST", "MO", "MOH", "MOS", "MPC", "MPWR",
    "MRK", "MRNA", "MRO", "MS", "MSCI", "MSFT", "MSI", "MTB", "MTCH", "MTD",
    "MU", "NCLH", "NDAQ", "NDSN", "NEE", "NEM", "NFLX", "NI", "NKE", "NOC",
    "NOW", "NRG", "NSC", "NTAP", "NTRS", "NUE", "NVDA", "NVR", "NWL", "NWS",
    "NWSA", "NXPI", "O", "ODFL", "OGN", "OKE", "OMC", "ON", "ORCL", "ORLY",
    "OTIS", "OXY", "PARA", "PAYC", "PAYX", "PCAR", "PCG", "PEAK", "PEG", "PEP",
    "PFE", "PFG", "PG", "PGR", "PH", "PHM", "PKG", "PKI", "PLD", "PM",
    "PNC", "PNR", "PNW", "POOL", "PPG", "PPL", "PRU", "PSA", "PSX", "PTC",
    "PVH", "PWR", "PXD", "PYPL", "QCOM", "QRVO", "RCL", "RE", "REG", "REGN",
    "RF", "RHI", "RJF", "RL", "RMD", "ROK", "ROL", "ROP", "ROST", "RSG",
    "RTX", "SBAC", "SBNY", "SBUX", "SCHW", "SEE", "SHW", "SIVB", "SJM", "SLB",
    "SNA", "SNPS", "SO", "SPG", "SPGI", "SRE", "STE", "STT", "STX", "STZ",
    "SWK", "SWKS", "SYF", "SYK", "SYY", "T", "TAP", "TDG", "TDY", "TECH",
    "TEL", "TER", "TFC", "TFX", "TGT", "TMO", "TMUS", "TPR", "TRGP", "TRMB",
    "TROW", "TRV", "TSCO", "TSLA", "TSN", "TT", "TTWO", "TXN", "TXT", "TYL",
    "UAL", "UDR", "UHS", "ULTA", "UNH", "UNP", "UPS", "URI", "USB", "V",
    "VFC", "VICI", "VLO", "VMC", "VRSK", "VRSN", "VRTX", "VTR", "VTRS", "VZ",
    "WAB", "WAT", "WBA", "WBD", "WDC", "WEC", "WELL", "WFC", "WHR", "WM",
    "WMB", "WMT", "WRB", "WRK", "WST", "WTW", "WY", "WYNN", "XEL", "XOM",
    "XRAY", "XYL", "YUM", "ZBH", "ZBRA", "ZION", "ZTS",
])

_RUSSELL2000_FALLBACK = sorted([
    # 섹터별 대표 소형주 (Finviz 수집 실패 시 사용)
    # Technology
    "SMCI", "CRDO", "CORT", "KTOS", "SANM", "RMBS", "NOVT", "AEIS", "VICR", "CALX",
    # Healthcare
    "MEDP", "HALO", "NUVB", "GKOS", "TGTX", "PCVX", "TVTX", "ENSG", "LNTH", "AXNX",
    # Financial
    "CADE", "IBOC", "SFBS", "HOMB", "PNFP", "BANR", "GBCI", "WSFS", "FNB", "UMBF",
    # Consumer
    "BOOT", "SHAK", "FIZZ", "PLNT", "CAKE", "DINE", "JACK", "WING", "EAT", "TXRH",
    # Industrial
    "AAON", "AVAV", "MATX", "GMS", "ROAD", "MYRG", "UFPI", "TILE", "ROCK", "AWI",
    # Energy
    "MTDR", "SM", "PTEN", "RRC", "CNX", "CIVI", "TALO", "GPOR", "OAS", "PDCE",
    # Real Estate
    "IIPR", "NXRT", "OLP", "GTY", "UMH", "GOOD", "EPRT", "STAG", "TRNO", "REXR",
])
