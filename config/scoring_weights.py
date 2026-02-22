"""스코어링 가중치 설정 - 선행지표 중심 리밸런싱"""

SCORING_WEIGHTS = {
    "macro": {
        "weight": 0.08,
        "sub_weights": {
            "interest_rate": 0.25,
            "vix": 0.25,
            "dxy": 0.15,
            "oil_gold": 0.10,
            "market_breadth": 0.25,
        }
    },
    "trend_momentum": {
        "weight": 0.15,
        "sub_weights": {
            "trend_direction": 0.20,
            "trend_strength": 0.10,
            "rsi_macd": 0.45,
            "ichimoku": 0.25,
        }
    },
    "volume_flow": {
        "weight": 0.13,
        "sub_weights": {
            "obv_retention": 0.20,
            "volume_profile": 0.15,
            "institutional_flow": 0.30,
            "options_flow": 0.35,
        }
    },
    "pattern_structure": {
        "weight": 0.17,
        "sub_weights": {
            "wave_analysis": 0.30,
            "fvg_levels": 0.25,
            "fibonacci": 0.20,
            "pattern_similarity": 0.10,
            "candlestick": 0.15,
        }
    },
    "quant_factors": {
        "weight": 0.22,
        "sub_weights": {
            "mean_reversion": 0.25,
            "momentum_factor": 0.10,
            "sector_relative": 0.10,
            "earnings_surprise": 0.20,
            "rsi_divergence": 0.20,
            "bb_squeeze": 0.15,
        }
    },
    "risk_special": {
        "weight": 0.12,
        "sub_weights": {
            "short_squeeze": 0.40,
            "special_signals": 0.20,
            "complex_patterns": 0.40,
        }
    },
    "fundamental": {
        "weight": 0.13,
        "sub_weights": {
            "valuation": 0.25,
            "profitability": 0.15,
            "growth": 0.25,
            "financial_health": 0.10,
            "dividend": 0.05,
            "analyst_consensus": 0.10,
            "insider": 0.10,
        }
    },
}

GRADE_BOUNDARIES = {
    "A": (80, 100),
    "B": (65, 79),
    "C": (45, 64),
    "D": (25, 44),
    "F": (0, 24),
}
