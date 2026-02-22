"""A~F 등급 시스템"""

from models.schemas import Grade
from config.scoring_weights import GRADE_BOUNDARIES


def get_grade(score: float) -> Grade:
    for grade_str, (low, high) in GRADE_BOUNDARIES.items():
        if low <= score <= high:
            return Grade(grade_str)
    return Grade.C


def get_grade_description(grade: Grade) -> str:
    descriptions = {
        Grade.A: "강력 매수 구간 - 다수의 기술/퀀트 지표가 매수를 지지합니다",
        Grade.B: "매수 고려 - 대체로 긍정적이나 일부 주의 요인 존재",
        Grade.C: "중립/관망 - 매수와 매도 신호가 혼재",
        Grade.D: "주의 필요 - 부정적 신호 우세, 진입 자제 권고",
        Grade.F: "위험 구간 - 강한 하락 신호, 진입 비추천",
    }
    return descriptions.get(grade, "")


def get_grade_color(grade: Grade) -> str:
    colors = {
        Grade.A: "#00FF00",   # Green
        Grade.B: "#7FFF00",   # Chartreuse
        Grade.C: "#FFFF00",   # Yellow
        Grade.D: "#FF8C00",   # Orange
        Grade.F: "#FF0000",   # Red
    }
    return colors.get(grade, "#FFFFFF")
