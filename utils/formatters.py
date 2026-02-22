"""숫자/퍼센트 포맷터"""


def fmt_price(value: float) -> str:
    if value >= 1000:
        return f"${value:,.2f}"
    elif value >= 1:
        return f"${value:.2f}"
    else:
        return f"${value:.4f}"


def fmt_pct(value: float, sign: bool = True) -> str:
    if sign and value > 0:
        return f"+{value:.2f}%"
    return f"{value:.2f}%"


def fmt_score(value: float) -> str:
    return f"{value:.0f}"


def fmt_large_number(value: float) -> str:
    if value >= 1e12:
        return f"${value / 1e12:.1f}T"
    elif value >= 1e9:
        return f"${value / 1e9:.1f}B"
    elif value >= 1e6:
        return f"${value / 1e6:.1f}M"
    return f"${value:,.0f}"
