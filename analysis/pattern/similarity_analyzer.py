"""과거 패턴 유사도 매칭"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from models.schemas import SimilarityResult
from config.settings import SIMILARITY_WINDOW


def analyze_similarity(df: pd.DataFrame, window: int = SIMILARITY_WINDOW) -> SimilarityResult:
    if df is None or len(df) < window * 3:
        return SimilarityResult()

    close = df["Close"].values

    # 최근 패턴 추출 및 정규화
    recent = close[-window:]
    recent_norm = _normalize(recent)

    # 과거 전체에서 슬라이딩 윈도우로 매칭
    best_sim = 0
    best_idx = 0
    best_return = 0

    # 최근 패턴이 완전 평탄(zero vector)이면 유사도 계산 불가
    if np.allclose(recent_norm, 0):
        return SimilarityResult(similarity_pct=0.0, score=50.0)

    search_end = len(close) - window - window  # 미래 수익률 계산 여유
    for i in range(0, search_end, 5):  # 5일 간격으로 검색 (속도)
        past = close[i:i + window]
        past_norm = _normalize(past)

        # 평탄 구간(zero vector) 스킵 - cosine_similarity에서 NaN 방지
        if np.allclose(past_norm, 0):
            continue

        sim = cosine_similarity(
            recent_norm.reshape(1, -1),
            past_norm.reshape(1, -1)
        )[0][0]

        if sim > best_sim:
            best_sim = sim
            best_idx = i
            # 유사 구간 이후 수익률
            future_end = min(i + window + 20, len(close))
            if future_end > i + window:
                future_return = (close[future_end - 1] / close[i + window - 1] - 1) * 100
            else:
                future_return = 0
            best_return = future_return

    similarity_pct = round(best_sim * 100, 1)
    ref_return = round(best_return, 1)

    # 기간 라벨
    if best_idx > 0 and isinstance(df.index, pd.DatetimeIndex):
        start_date = df.index[best_idx].strftime("%Y-%m")
        end_date = df.index[best_idx + window - 1].strftime("%Y-%m")
        matched_period = f"{start_date} ~ {end_date}"
    else:
        matched_period = f"{best_idx}일 ~ {best_idx + window}일 전"

    # 점수: 높은 유사도 + 양의 참조수익률 = 좋은 점수
    if similarity_pct > 80 and ref_return > 0:
        score = 70 + min(ref_return * 2, 20)
    elif similarity_pct > 60 and ref_return > 0:
        score = 55 + min(ref_return * 2, 15)
    elif ref_return < -5:
        score = 30
    else:
        score = 50

    return SimilarityResult(
        similarity_pct=similarity_pct,
        reference_return_pct=ref_return,
        matched_period=matched_period,
        score=round(max(0, min(100, score)), 1),
    )


def _normalize(arr: np.ndarray) -> np.ndarray:
    min_val = arr.min()
    max_val = arr.max()
    if max_val == min_val:
        return np.zeros_like(arr)
    return (arr - min_val) / (max_val - min_val)
