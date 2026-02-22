"""달 위상 분석"""

from datetime import datetime
from models.schemas import LunarPhaseResult


def analyze_lunar_phase() -> LunarPhaseResult:
    try:
        import ephem
        moon = ephem.Moon()
        moon.compute(datetime.now())
        phase = moon.phase  # 0~100 (0=초승달, 50=보름달)

        if phase < 5:
            name, emoji, bias = "초승달", "🌑", "강세"
        elif phase < 25:
            name, emoji, bias = "차오르는 달", "🌒", "강세"
        elif phase < 45:
            name, emoji, bias = "상현달", "🌓", "중립"
        elif phase < 55:
            name, emoji, bias = "보름달", "🌕", "약세"
        elif phase < 75:
            name, emoji, bias = "하현달", "🌗", "중립"
        else:
            name, emoji, bias = "그믐달", "🌘", "강세"

        # 점수 (보조 지표, 미약한 영향)
        bias_scores = {"강세": 55, "중립": 50, "약세": 45}
        score = bias_scores.get(bias, 50)

        return LunarPhaseResult(
            phase_name=name,
            phase_emoji=emoji,
            market_bias=bias,
            score=score,
        )
    except ImportError:
        return LunarPhaseResult(phase_name="ephem 미설치", phase_emoji="🌙", market_bias="중립", score=50)
    except Exception:
        return LunarPhaseResult()
