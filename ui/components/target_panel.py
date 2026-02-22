"""목표가/손절가 패널 컴포넌트"""

import streamlit as st
from models.schemas import PriceTarget
from utils.formatters import fmt_price, fmt_pct


def render_target_panel(target: PriceTarget):
    """목표가/손절가 패널"""
    col1, col2 = st.columns(2)

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
