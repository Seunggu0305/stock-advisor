"""매크로 상단 바 컴포넌트"""

import streamlit as st
from models.schemas import MacroResult, MacroStatus


def render_macro_bar(macro: MacroResult):
    """매크로 환경 요약 바"""
    def status_color(status: MacroStatus) -> str:
        return {
            MacroStatus.STABLE: "#00FF00",
            MacroStatus.MIXED: "#FFFF00",
            MacroStatus.CAUTION: "#FFA500",
            MacroStatus.DANGER: "#FF0000",
        }.get(status, "#FFFFFF")

    items = [macro.interest_rate, macro.vix, macro.oil, macro.gold]
    cols = st.columns(len(items))

    for col, item in zip(cols, items):
        color = status_color(item.status)
        with col:
            if item.name == "vix":
                display = f"{item.label}: {item.status.value} ({item.value})"
            else:
                display = f"{item.label}: {item.status.value}"
            st.markdown(
                f'<div style="text-align:center; padding:8px; '
                f'background-color:#1a1a2e; border-radius:5px;">'
                f'<span style="color:{color}; font-weight:bold;">{display}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
