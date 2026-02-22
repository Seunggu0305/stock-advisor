"""가격/볼륨 차트 (plotly)"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def render_price_chart(df: pd.DataFrame, ticker: str):
    """캔들스틱 + 볼륨 차트"""
    if df is None or df.empty:
        return

    # 최근 90일
    df_recent = df.tail(90)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    # 캔들스틱
    fig.add_trace(
        go.Candlestick(
            x=df_recent.index,
            open=df_recent["Open"],
            high=df_recent["High"],
            low=df_recent["Low"],
            close=df_recent["Close"],
            name=ticker,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1, col=1,
    )

    # 이동평균선
    for period, color in [(20, "#e0be36"), (50, "#42a5f5"), (200, "#ab47bc")]:
        if len(df) >= period:
            sma = df["Close"].rolling(period).mean()
            fig.add_trace(
                go.Scatter(
                    x=df_recent.index,
                    y=sma.loc[df_recent.index],
                    name=f"SMA{period}",
                    line=dict(color=color, width=1),
                ),
                row=1, col=1,
            )

    # 볼륨
    colors = ["#26a69a" if c >= o else "#ef5350"
              for c, o in zip(df_recent["Close"], df_recent["Open"])]
    fig.add_trace(
        go.Bar(
            x=df_recent.index,
            y=df_recent["Volume"],
            name="거래량",
            marker_color=colors,
            opacity=0.6,
        ),
        row=2, col=1,
    )

    # 휴장일 계산 (주말 + 데이터에 없는 평일)
    all_days = pd.date_range(start=df_recent.index.min(), end=df_recent.index.max(), freq="B")
    holidays = all_days.difference(df_recent.index)

    fig.update_layout(
        template="plotly_dark",
        height=450,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
    )
    fig.update_xaxes(
        gridcolor="#1a1a2e",
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # 주말
            dict(values=[d.strftime("%Y-%m-%d") for d in holidays]),  # 공휴일
        ],
    )
    fig.update_yaxes(gridcolor="#1a1a2e")

    return fig
