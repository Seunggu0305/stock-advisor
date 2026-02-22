"""기관 보유 변동 분석"""

import pandas as pd
from models.schemas import InstitutionalFlowResult


def analyze_institutional_flow(
    institutional_data: pd.DataFrame | None,
    finviz_data: dict | None
) -> InstitutionalFlowResult:
    inst_pct = 0.0
    change_label = "데이터 없음"

    if finviz_data:
        inst_pct = finviz_data.get("inst_own", 0)

    if institutional_data is not None and not institutional_data.empty:
        try:
            # finviz 데이터가 없을 때만 pctHeld 합산 사용 (상위 10개만이므로 부정확)
            if inst_pct == 0 and "pctHeld" in institutional_data.columns:
                total_pct = float(institutional_data["pctHeld"].sum()) * 100
                if total_pct > 0:
                    inst_pct = total_pct
            # 최근 변동 분석
            if "pctChange" in institutional_data.columns:
                avg_change = float(institutional_data["pctChange"].mean())
                if avg_change > 0.01:
                    change_label = "기관 매수 증가"
                elif avg_change < -0.01:
                    change_label = "기관 매도 증가"
                else:
                    change_label = "기관 보유 유지"
        except Exception:
            pass

    # 보유 수준 라벨 (변동 방향 라벨이 없을 때만 덮어쓰기)
    if change_label == "데이터 없음":
        if inst_pct > 80:
            change_label = "기관 집중 보유"
        elif inst_pct > 50:
            change_label = "기관 보유 높음"
        elif inst_pct > 20:
            change_label = "기관 보유 보통"
        elif inst_pct > 0:
            change_label = "기관 보유 낮음"

    # 점수: 기관 보유 수준 + 변동 방향 반영
    if 40 <= inst_pct <= 80:
        score = 65
    elif inst_pct > 80:
        score = 55
    elif inst_pct > 20:
        score = 55
    else:
        score = 40

    # 기관 매수/매도 변동 반영
    if institutional_data is not None and "pctChange" in institutional_data.columns:
        try:
            avg_change = float(institutional_data["pctChange"].mean())
            if avg_change > 0.02:
                score += 10  # 기관 적극 매수
            elif avg_change > 0:
                score += 5
            elif avg_change < -0.02:
                score -= 10  # 기관 적극 매도
            elif avg_change < 0:
                score -= 5
        except Exception:
            pass

    return InstitutionalFlowResult(
        institutional_pct=round(inst_pct, 1),
        change_label=change_label,
        score=round(score, 1),
    )
