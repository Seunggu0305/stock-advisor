"""목표가/손절가/손익비 패널 컴포넌트"""

import streamlit as st
from models.schemas import PriceTarget
from utils.formatters import fmt_price, fmt_pct


def _rr_color(rr: float) -> str:
    if rr >= 3.0:
        return "#26a69a"
    elif rr >= 2.0:
        return "#66bb6a"
    elif rr >= 1.0:
        return "#ffa726"
    elif rr > 0:
        return "#ef5350"
    return "#666"


def render_target_panel(target: PriceTarget):
    """목표가/손익비/손절가 패널"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="padding:15px; background:#0d1117; border-radius:8px;
                    border:1px solid #26a69a; text-align:center;">
            <div style="color:#888; font-size:12px;">목표가 (TARGET)</div>
            <div style="color:#26a69a; font-size:24px; font-weight:bold;">
                {fmt_price(target.target_price)} ({fmt_pct(target.target_pct)})
            </div>
            <div style="color:#666; font-size:11px; margin-top:5px;">
                [1차저항: {fmt_price(target.resistance_1)}]
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        rr = getattr(target, 'risk_reward_ratio', 0)
        rr_lbl = getattr(target, 'rr_label', '산출 불가')
        color = _rr_color(rr)
        rr_display = f"1:{rr:.1f}" if rr > 0 else "-"
        st.markdown(f"""
        <div style="padding:15px; background:#0d1117; border-radius:8px;
                    border:1px solid {color}; text-align:center;">
            <div style="color:#888; font-size:12px;">손익비 (R:R)</div>
            <div style="color:{color}; font-size:24px; font-weight:bold;">
                {rr_display}
            </div>
            <div style="color:#666; font-size:11px; margin-top:5px;">
                [{rr_lbl}]
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="padding:15px; background:#0d1117; border-radius:8px;
                    border:1px solid #ef5350; text-align:center;">
            <div style="color:#888; font-size:12px;">손절가 (STOP)</div>
            <div style="color:#ef5350; font-size:24px; font-weight:bold;">
                {fmt_price(target.stop_loss)} ({fmt_pct(target.stop_loss_pct)})
            </div>
            <div style="color:#666; font-size:11px; margin-top:5px;">
                [1차지지: {fmt_price(target.support_1)}]
            </div>
        </div>
        """, unsafe_allow_html=True)
