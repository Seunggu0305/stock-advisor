"""어닝 서프라이즈 팩터"""

import pandas as pd
from models.schemas import EarningsSurpriseResult


def analyze_earnings_surprise(earnings_data: dict | None, finviz_data: dict | None) -> EarningsSurpriseResult:
    result = EarningsSurpriseResult()

    if finviz_data:
        result.next_earnings_date = finviz_data.get("earnings_date", "N/A")

    if earnings_data is None:
        return result

    history = earnings_data.get("history")
    if history is None:
        return result

    # earnings_history가 DataFrame인 경우
    if isinstance(history, pd.DataFrame) and not history.empty:
        try:
            if "epsActual" in history.columns and "epsEstimate" in history.columns:
                recent = history.iloc[0]
                actual = float(recent.get("epsActual", 0) or 0)
                estimate = float(recent.get("epsEstimate", 0) or 0)
                if estimate != 0:
                    surprise_pct = ((actual - estimate) / abs(estimate)) * 100
                    result.last_surprise_pct = round(surprise_pct, 1)

                # 연속 서프라이즈 횟수
                streak = 0
                for _, row in history.iterrows():
                    a = float(row.get("epsActual", 0) or 0)
                    e = float(row.get("epsEstimate", 0) or 0)
                    if e != 0 and a > e:
                        streak += 1
                    else:
                        break
                result.surprise_streak = streak
        except Exception:
            pass

    # 점수
    if result.last_surprise_pct > 10:
        score = 75 + min(result.surprise_streak * 5, 15)
    elif result.last_surprise_pct > 0:
        score = 60 + min(result.surprise_streak * 3, 10)
    elif result.last_surprise_pct < -10:
        score = 25
    elif result.last_surprise_pct < 0:
        score = 40
    else:
        score = 50

    result.score = round(max(0, min(100, score)), 1)
    return result
