"""매일 아침 자동 스크리닝 스크립트

사용법:
  1) 직접 실행:  python -m scheduler.daily_screener
  2) Windows Task Scheduler:  run_daily_screen.bat 등록
  3) 백그라운드 상주:  python -m scheduler.daily_screener --daemon
"""

import sys
import os
import time
import logging
from datetime import datetime

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scoring.screener import screen_index, is_result_fresh

LOG_DIR = os.path.join(PROJECT_ROOT, ".cache", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "daily_screener.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

INDICES = ["NASDAQ 100", "S&P 500", "Russell 2000"]
TOP_N = 5


def run_all_screenings(force: bool = False):
    """3개 인덱스 순차 스크리닝

    Args:
        force: True면 이미 오늘 결과가 있어도 재실행
    """
    logger.info("=" * 60)
    logger.info("일일 스크리닝 시작 - %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("=" * 60)

    total_start = time.time()

    for index_name in INDICES:
        # 오늘 이미 실행했으면 스킵 (24시간 이내)
        if not force and is_result_fresh(index_name, max_age_hours=20):
            logger.info("[스킵] %s - 최근 결과 있음", index_name)
            continue

        logger.info("[시작] %s 스크리닝...", index_name)
        start = time.time()

        def on_progress(current, total, ticker):
            if current % 20 == 0 or current == total:
                logger.info("  %s: %d/%d (%s)", index_name, current, total, ticker)

        try:
            results = screen_index(
                index_name,
                top_n=TOP_N,
                max_workers=4,
                progress_callback=on_progress,
            )
            elapsed = time.time() - start
            logger.info(
                "[완료] %s - %d개 선정 (%.1f분 소요)",
                index_name, len(results), elapsed / 60
            )
            for r in results:
                logger.info(
                    "  #%d [%s] %s (%s) - 점수: %.0f",
                    r["rank"], r["grade"], r["ticker"], r.get("name", "")[:15], r["score"]
                )
        except Exception as e:
            logger.error("[실패] %s: %s", index_name, e)

    total_elapsed = time.time() - total_start
    logger.info("전체 완료 - 총 %.1f분 소요", total_elapsed / 60)


def run_daemon(run_hour: int = 7, run_minute: int = 0):
    """백그라운드 데몬 모드 - 매일 지정 시각에 실행

    Args:
        run_hour: 실행 시각 (시, 24시간제, 기본 07:00)
        run_minute: 실행 시각 (분)
    """
    logger.info("데몬 모드 시작 - 매일 %02d:%02d 에 실행", run_hour, run_minute)

    ran_today = False

    while True:
        now = datetime.now()

        # 지정 시각이 되면 실행
        if now.hour == run_hour and now.minute == run_minute and not ran_today:
            ran_today = True
            run_all_screenings()

        # 날짜가 바뀌면 리셋
        if now.hour == 0 and now.minute == 0:
            ran_today = False

        time.sleep(30)  # 30초마다 체크


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        # 데몬 모드: 매일 아침 7시에 자동 실행
        hour = 7
        minute = 0
        for arg in sys.argv:
            if arg.startswith("--hour="):
                hour = int(arg.split("=")[1])
            if arg.startswith("--minute="):
                minute = int(arg.split("=")[1])
        run_daemon(run_hour=hour, run_minute=minute)
    elif "--force" in sys.argv:
        # 강제 실행 (이미 오늘 결과가 있어도)
        run_all_screenings(force=True)
    else:
        # 1회 실행
        run_all_screenings()
