"""주식 투자 진입 스코어링 프로그램 - 엔트리포인트"""

import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from data.fetcher import DataFetcher
from analysis.macro.macro_analyzer import analyze_macro
from analysis.technical.trend_analyzer import analyze_trend
from analysis.technical.momentum_analyzer import analyze_momentum
from analysis.technical.volume_analyzer import analyze_volume
from analysis.technical.ichimoku_analyzer import analyze_ichimoku
from analysis.technical.fibonacci_analyzer import analyze_fibonacci
from analysis.pattern.wave_analyzer import analyze_wave
from analysis.pattern.fvg_analyzer import analyze_fvg
from analysis.pattern.candlestick_pattern import analyze_candlestick
from analysis.pattern.similarity_analyzer import analyze_similarity
from analysis.pattern.complex_pattern import analyze_complex_patterns
from analysis.quant.short_squeeze import analyze_short_squeeze
from analysis.quant.rsi_divergence import analyze_rsi_divergence
from analysis.quant.bb_squeeze import analyze_bb_squeeze
from analysis.quant.mean_reversion import analyze_mean_reversion
from analysis.quant.momentum_factor import analyze_momentum_factor
from analysis.quant.sector_relative import analyze_sector_relative
from analysis.quant.earnings_surprise import analyze_earnings_surprise
from analysis.quant.institutional_flow import analyze_institutional_flow
from analysis.quant.options_flow import analyze_options_flow
from analysis.quant.lunar_phase import analyze_lunar_phase
from analysis.fundamental.fundamental_analyzer import analyze_fundamental
from scoring.score_engine import calculate_total_score
from scoring.grade_system import get_grade
from scoring.target_calculator import calculate_targets
from scoring.signal_compositor import compose_signal
from scoring.alert_generator import generate_alerts
from models.schemas import StockAnalysisResult


def run_analysis(ticker: str) -> StockAnalysisResult:
    """전체 분석 파이프라인 실행"""
    ticker = ticker.upper().strip()

    # 1. 데이터 수집
    fetcher = DataFetcher(ticker)
    data = fetcher.fetch_all()

    price_data = data.get("price_data")
    stock_info = data.get("stock_info") or {}
    current_price = 0.0
    if price_data is not None and not price_data.empty:
        current_price = float(price_data["Close"].iloc[-1])

    company_name = stock_info.get("shortName", stock_info.get("longName", ticker))

    # 주간 성과
    weekly_perf = 0.0
    if price_data is not None and len(price_data) >= 5:
        weekly_perf = round((current_price / float(price_data["Close"].iloc[-5]) - 1) * 100, 2)

    # 2. 분석 실행
    macro = analyze_macro(data.get("macro"), data.get("fred_rates"))
    trend = analyze_trend(price_data)
    mom = analyze_momentum(price_data)
    vol = analyze_volume(price_data)
    ichi = analyze_ichimoku(price_data)
    fib = analyze_fibonacci(price_data)
    wave = analyze_wave(price_data)
    fvg = analyze_fvg(price_data)
    candle = analyze_candlestick(price_data)
    sim = analyze_similarity(price_data)
    short_sq = analyze_short_squeeze(data.get("finviz"), price_data)
    rsi_div = analyze_rsi_divergence(price_data)
    bb_sq = analyze_bb_squeeze(price_data)
    mean_rev = analyze_mean_reversion(price_data)
    mom_factor = analyze_momentum_factor(price_data)
    sector_rel = analyze_sector_relative(stock_info, data.get("sector_etfs"))
    earnings = analyze_earnings_surprise(data.get("earnings"), data.get("finviz"))
    inst_flow = analyze_institutional_flow(data.get("institutional"), data.get("finviz"))
    opt_flow = analyze_options_flow(data.get("options"))
    lunar = analyze_lunar_phase()
    fundamental = analyze_fundamental(stock_info, data.get("finviz"))

    # 모든 결과를 dict로 모음
    all_results = {
        "macro": macro, "trend": trend, "momentum": mom, "volume": vol,
        "ichimoku": ichi, "fibonacci": fib, "wave": wave, "fvg": fvg,
        "candlestick": candle, "similarity": sim,
        "short_squeeze": short_sq, "rsi_divergence": rsi_div,
        "bb_squeeze": bb_sq, "mean_reversion": mean_rev,
        "momentum_factor": mom_factor, "sector_relative": sector_rel,
        "earnings_surprise": earnings, "institutional_flow": inst_flow,
        "options_flow": opt_flow, "lunar_phase": lunar,
        "fundamental": fundamental,
    }

    # 복합 패턴
    complex_p = analyze_complex_patterns(all_results)
    all_results["complex_patterns"] = complex_p

    # 특수 신호
    special = _detect_special_signals(price_data, data.get("finviz"), earnings)
    all_results["special_signals"] = special

    # 3. 스코어링
    ai_score = calculate_total_score(all_results)
    grade = get_grade(ai_score)
    final_signal = compose_signal(ai_score, grade, all_results)
    targets = calculate_targets(price_data, fib, fvg, vol)
    alerts = generate_alerts(all_results, current_price)

    # 4. 결과 조립
    return StockAnalysisResult(
        ticker=ticker,
        company_name=company_name,
        current_price=current_price,
        analysis_time=datetime.now(),
        macro=macro,
        ai_score=ai_score,
        grade=grade,
        trend=trend,
        weekly_performance_pct=weekly_perf,
        momentum=mom,
        volume=vol,
        ichimoku=ichi,
        fibonacci=fib,
        wave=wave,
        fvg=fvg,
        candlestick=candle,
        similarity=sim,
        complex_patterns=complex_p,
        short_squeeze=short_sq,
        rsi_divergence=rsi_div,
        bb_squeeze=bb_sq,
        mean_reversion=mean_rev,
        momentum_factor=mom_factor,
        sector_relative=sector_rel,
        earnings_surprise=earnings,
        institutional_flow=inst_flow,
        options_flow=opt_flow,
        lunar_phase=lunar,
        fundamental=fundamental,
        special_signals=special,
        final_signal=final_signal,
        price_target=targets,
        alerts=alerts,
    )


def _detect_special_signals(df, finviz_data, earnings) -> list[str]:
    """특수 신호 감지"""
    signals = []
    if df is None or len(df) < 20:
        return signals

    close = df["Close"]
    volume = df["Volume"]
    high = df["High"]
    low = df["Low"]
    current = float(close.iloc[-1])

    # 거래량 폭발
    avg_vol = float(volume.iloc[-20:].mean())
    today_vol = float(volume.iloc[-1])
    if avg_vol > 0 and today_vol > avg_vol * 3:
        signals.append("거래량 폭발 (평균의 {:.1f}배)".format(today_vol / avg_vol))

    # 갭 발생
    if len(close) >= 2:
        prev_close = float(close.iloc[-2])
        gap_pct = (current - prev_close) / prev_close * 100
        if gap_pct > 2:
            signals.append(f"갭 상승 ({gap_pct:.1f}%)")
        elif gap_pct < -2:
            signals.append(f"갭 하락 ({gap_pct:.1f}%)")

    # 52주 신고/신저
    year_high = float(high.max())
    year_low = float(low.min())
    if current >= year_high * 0.98:
        signals.append("52주 신고 근접")
    elif current <= year_low * 1.02:
        signals.append("52주 신저 근접")

    # 상대 거래량
    if finviz_data:
        rel_vol = finviz_data.get("rel_volume", 1)
        if rel_vol > 2:
            signals.append(f"상대 거래량 높음 ({rel_vol:.1f}x)")

    return signals


def run_screener(index_name: str = None, top_n: int = 5):
    """인덱스 스크리닝 실행 (CLI용)"""
    from scoring.screener import screen_index

    indices = [index_name] if index_name else ["NASDAQ 100", "S&P 500", "Russell 2000"]

    for idx_name in indices:
        print(f"\n{'='*60}")
        print(f"  {idx_name} Top {top_n} 스크리닝 시작...")
        print(f"{'='*60}")

        def on_progress(current, total, ticker):
            print(f"  [{current}/{total}] {ticker}...", end="\r")

        results = screen_index(idx_name, top_n=top_n, max_workers=4,
                               progress_callback=on_progress)
        print()

        if not results:
            print("  결과 없음")
            continue

        print(f"\n  {'순위':<4} {'등급':<4} {'티커':<8} {'종목명':<20} {'점수':<6} {'주간':<8} {'신호'}")
        print(f"  {'-'*70}")
        for r in results:
            print(f"  {r['rank']:<4} [{r['grade']}]  {r['ticker']:<8} {r['name'][:18]:<20} "
                  f"{r['score']:<6.0f} {r['weekly_pct']:>+6.1f}%  {r['signal'][:20]}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "screen":
            # python main.py screen [인덱스명] [top_n]
            index_name = sys.argv[2] if len(sys.argv) > 2 else None
            top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            run_screener(index_name, top_n)
        else:
            # python main.py <TICKER>
            ticker = arg
            result = run_analysis(ticker)
            print(f"\n{'='*50}")
            print(f"  {result.company_name} ({result.ticker})")
            print(f"  현재가: ${result.current_price:.2f}")
            print(f"  AI 점수: {result.ai_score:.0f} | 등급: [{result.grade.value}]")
            print(f"  최종 신호: {result.final_signal}")
            print(f"{'='*50}")
    else:
        print("사용법:")
        print("  python main.py <TICKER>            종목 분석")
        print('  python main.py screen              전체 인덱스 스크리닝')
        print('  python main.py screen "NASDAQ 100" NASDAQ 100만 스크리닝')
        print('  python main.py screen "S&P 500" 10 S&P 500 Top 10')
        print("  streamlit run ui/streamlit_app.py   웹 대시보드")
