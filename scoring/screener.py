"""배치 스크리너 - 인덱스별 Top N 종목 스코어링"""

import json
import os
from datetime import datetime, timedelta
from data.index_constituents import get_index_tickers

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CACHE_DIR = os.path.join(PROJECT_ROOT, ".cache", "screener")
GIT_RESULTS_DIR = os.path.join(PROJECT_ROOT, "screener_results")


def screen_index(index_name: str, top_n: int = 5, max_workers: int = 4,
                 progress_callback=None) -> list[dict]:
    """인덱스 전체 종목 분석 후 Top N 반환

    Args:
        index_name: "NASDAQ 100", "S&P 500", "Russell 2000"
        top_n: 상위 N개 반환
        max_workers: 병렬 분석 스레드 수
        progress_callback: fn(current, total, ticker) 진행률 콜백

    Returns:
        [{"rank": 1, "ticker": "AAPL", "name": "Apple", "price": 260,
          "score": 82, "grade": "A", "signal": "강력 매수", "weekly_pct": 3.5,
          "trend": "상승장", "rsi": 45.2}, ...]
    """
    tickers = get_index_tickers(index_name)
    if not tickers:
        return []

    results = []
    total = len(tickers)

    def analyze_one(ticker: str) -> dict | None:
        try:
            from main import run_analysis
            result = run_analysis(ticker)
            return {
                "ticker": result.ticker,
                "name": result.company_name,
                "price": result.current_price,
                "score": result.ai_score,
                "grade": result.grade.value,
                "signal": result.final_signal,
                "weekly_pct": result.weekly_performance_pct,
                "trend": result.trend.direction.value,
                "rsi": result.momentum.rsi,
                "target_price": result.price_target.target_price,
                "target_pct": result.price_target.target_pct,
                "stop_loss": result.price_target.stop_loss,
                "stop_loss_pct": result.price_target.stop_loss_pct,
                "risk_reward_ratio": result.price_target.risk_reward_ratio,
            }
        except Exception as e:
            print(f"  [스킵] {ticker}: {e}")
            return None

    completed = 0
    # 순차 처리 (yfinance 세션 충돌 방지)
    for ticker in tickers:
        completed += 1
        result = analyze_one(ticker)
        if result is not None:
            results.append(result)
        if progress_callback:
            progress_callback(completed, total, ticker)

    # 점수 기준 정렬
    results.sort(key=lambda x: x["score"], reverse=True)

    # Top N 추출 및 순위 부여
    top_results = results[:top_n]
    for i, r in enumerate(top_results):
        r["rank"] = i + 1

    # 결과 저장 (캐시 + git-tracked)
    _save_results(index_name, top_results, len(tickers))

    return top_results


def get_saved_results(index_name: str) -> dict | None:
    """저장된 스크리닝 결과 불러오기 (캐시 우선, 없으면 git 결과)"""
    # 1. 로컬 캐시 확인 (직접 실행한 최신 결과)
    cache_path = _get_filepath(index_name, CACHE_DIR)
    cache_data = _load_json(cache_path)

    # 2. git-tracked 결과 확인 (GitHub Actions에서 실행한 결과)
    git_path = _get_filepath(index_name, GIT_RESULTS_DIR)
    git_data = _load_json(git_path)

    # 둘 다 있으면 더 최신 것 반환
    if cache_data and git_data:
        try:
            cache_time = datetime.fromisoformat(cache_data["analysis_time"])
            git_time = datetime.fromisoformat(git_data["analysis_time"])
            return cache_data if cache_time > git_time else git_data
        except Exception:
            return cache_data
    return cache_data or git_data


def get_all_saved_results() -> dict:
    """모든 인덱스의 저장된 결과 반환"""
    all_results = {}
    for index_name in ["NASDAQ 100", "S&P 500", "Russell 2000"]:
        saved = get_saved_results(index_name)
        if saved:
            all_results[index_name] = saved
    return all_results


def is_result_fresh(index_name: str, max_age_hours: int = 24) -> bool:
    """결과가 최신인지 확인 (기본 24시간)"""
    saved = get_saved_results(index_name)
    if saved is None:
        return False
    try:
        saved_time = datetime.fromisoformat(saved["analysis_time"])
        return datetime.now() - saved_time < timedelta(hours=max_age_hours)
    except Exception:
        return False


def _load_json(filepath: str) -> dict | None:
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_results(index_name: str, top_results: list, total_analyzed: int):
    """결과를 JSON으로 저장 (캐시 + git-tracked 양쪽)"""
    data = {
        "index_name": index_name,
        "analysis_time": datetime.now().isoformat(),
        "total_analyzed": total_analyzed,
        "top_results": top_results,
    }
    # 캐시 저장 (.cache/screener/ - gitignore됨)
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = _get_filepath(index_name, CACHE_DIR)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # git-tracked 저장 (screener_results/ - 커밋 가능)
    os.makedirs(GIT_RESULTS_DIR, exist_ok=True)
    git_path = _get_filepath(index_name, GIT_RESULTS_DIR)
    with open(git_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_filepath(index_name: str, base_dir: str) -> str:
    safe_name = index_name.replace(" ", "_").replace("&", "and")
    return os.path.join(base_dir, f"{safe_name}.json")
