"""AI 점수 + 등급 카드 컴포넌트"""

import streamlit as st
from models.schemas import Grade
from scoring.grade_system import get_grade_color, get_grade_description


def render_score_card(ai_score: float, grade: Grade, previous_score: float | None = None):
    """AI 추천 점수 및 등급 표시"""
    grade_color = get_grade_color(grade)
    description = get_grade_description(grade)

    # 점수 변화 화살표
    if previous_score is not None:
        arrow = "→"
        score_display = f"{previous_score:.0f} {arrow} {ai_score:.0f}"
    else:
        score_display = f"{ai_score:.0f}"

    # 게이지 바 색상
    if ai_score >= 80:
        bar_color = "#26a69a"
    elif ai_score >= 65:
        bar_color = "#66bb6a"
    elif ai_score >= 45:
        bar_color = "#ffa726"
    elif ai_score >= 25:
        bar_color = "#ff7043"
    else:
        bar_color = "#ef5350"

    st.markdown(f"""
    <div style="text-align:center; padding:20px; background:#0d1117; border-radius:10px; border:1px solid #333;">
        <div style="color:#888; font-size:14px; margin-bottom:5px;">AI 추천 점수</div>
        <div style="font-size:48px; font-weight:bold; color:{bar_color};">{score_display}</div>
        <div style="margin:10px auto; width:80%; height:8px; background:#333; border-radius:4px;">
            <div style="width:{ai_score}%; height:100%; background:{bar_color}; border-radius:4px;"></div>
        </div>
        <div style="font-size:28px; font-weight:bold; color:{grade_color};">등급 [{grade.value}]</div>
        <div style="color:#888; font-size:12px; margin-top:5px;">{description}</div>
    </div>
    """, unsafe_allow_html=True)
