"""알림 패널 컴포넌트"""

import streamlit as st


def render_alert_panel(alerts: list[str]):
    """알림 메시지 패널"""
    if not alerts:
        return

    alert_html = ""
    for alert in alerts:
        if alert.startswith("[!]"):
            color = "#e0be36"
            icon = "⚠"
        else:
            color = "#42a5f5"
            icon = "ℹ"

        text = alert.replace("[!] ", "").replace("[i] ", "")
        alert_html += f"""
        <div style="padding:8px 12px; background:#1a1a2e; border-radius:5px;
                    margin-bottom:5px; border-left:3px solid {color};">
            <span style="color:{color};">{icon} {text}</span>
        </div>
        """

    st.markdown(alert_html, unsafe_allow_html=True)
