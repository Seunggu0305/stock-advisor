"""전체 데이터 모델 정의"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TrendDirection(str, Enum):
    STRONG_BULLISH = "강한 상승장"
    BULLISH = "상승장"
    NEUTRAL = "보합"
    BEARISH = "하락장"
    STRONG_BEARISH = "강한 하락장"


class TrendStrength(str, Enum):
    STRONG = "강함"
    MODERATE = "보통"
    WEAK = "약함"


class MacroStatus(str, Enum):
    STABLE = "안정세"
    CAUTION = "주의"
    DANGER = "위험"
    MIXED = "보합세"


class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


# ── Macro ──

class MacroIndicator(BaseModel):
    name: str
    value: float
    status: MacroStatus
    label: str


class MacroResult(BaseModel):
    interest_rate: MacroIndicator
    vix: MacroIndicator
    oil: MacroIndicator
    gold: MacroIndicator
    dxy: MacroIndicator = None
    market_breadth_score: float = 50.0
    score: float = 50.0


# ── Technical ──

class TrendResult(BaseModel):
    direction: TrendDirection = TrendDirection.NEUTRAL
    strength: TrendStrength = TrendStrength.MODERATE
    adx: float = 0.0
    sma_alignment: str = "혼합"
    score: float = 50.0


class MomentumResult(BaseModel):
    rsi: float = 50.0
    macd_signal: str = "중립"
    stochastic_signal: str = "중립"
    energy_label: str = "중립"
    cross_type: Optional[str] = None
    score: float = 50.0


class VolumeResult(BaseModel):
    obv_retention: float = 1.0
    obv_label: str = "보통"
    vwap: float = 0.0
    price_vs_vwap: str = "위"
    poc_price: float = 0.0
    value_area_high: float = 0.0
    value_area_low: float = 0.0
    score: float = 50.0


class IchimokuResult(BaseModel):
    cloud_position: str = "구름 내"
    tenkan_kijun_cross: Optional[str] = None
    chikou_signal: str = "중립"
    score: float = 50.0


class FibonacciResult(BaseModel):
    levels: dict = Field(default_factory=dict)
    current_level: str = "없음"
    retracement_pct: float = 0.0
    score: float = 50.0


# ── Pattern ──

class WaveResult(BaseModel):
    current_wave: str = "판별 불가"
    wave_position: str = "판별 불가"
    confidence: float = 0.0
    score: float = 50.0


class FVGResult(BaseModel):
    bullish_gaps: list = Field(default_factory=list)
    bearish_gaps: list = Field(default_factory=list)
    nearest_support_gap: Optional[float] = None
    nearest_resistance_gap: Optional[float] = None
    label: str = "없음"
    score: float = 50.0


class CandlestickResult(BaseModel):
    patterns: list[str] = Field(default_factory=list)
    dominant_signal: str = "중립"
    score: float = 50.0


class SimilarityResult(BaseModel):
    similarity_pct: float = 0.0
    reference_return_pct: float = 0.0
    matched_period: str = ""
    score: float = 50.0


class ComplexPatternResult(BaseModel):
    patterns: list[str] = Field(default_factory=list)
    score: float = 50.0


# ── Quant ──

class ShortSqueezeResult(BaseModel):
    short_interest_pct: float = 0.0
    days_to_cover: float = 0.0
    potential: str = "낮음"
    score: float = 50.0


class RSIDivergenceResult(BaseModel):
    divergence_type: Optional[str] = None
    strength: float = 0.0
    score: float = 50.0


class BBSqueezeResult(BaseModel):
    is_squeezing: bool = False
    squeeze_duration: int = 0
    expected_direction: Optional[str] = None
    score: float = 50.0


class MeanReversionResult(BaseModel):
    z_score: float = 0.0
    signal: str = "중립"
    score: float = 50.0


class MomentumFactorResult(BaseModel):
    momentum_score: float = 50.0
    rank_label: str = "보통"
    score: float = 50.0
    deceleration_detected: bool = False
    bottoming_detected: bool = False


class SectorRelativeResult(BaseModel):
    sector_name: str = "Unknown"
    relative_strength: float = 0.0
    sector_rank: int = 0
    total_sectors: int = 11
    score: float = 50.0


class EarningsSurpriseResult(BaseModel):
    last_surprise_pct: float = 0.0
    surprise_streak: int = 0
    next_earnings_date: Optional[str] = None
    score: float = 50.0


class InstitutionalFlowResult(BaseModel):
    institutional_pct: float = 0.0
    change_label: str = "변동 없음"
    score: float = 50.0


class OptionsFlowResult(BaseModel):
    put_call_ratio: float = 1.0
    iv_rank: float = 50.0
    signal: str = "중립"
    score: float = 50.0


class LunarPhaseResult(BaseModel):
    phase_name: str = "알 수 없음"
    phase_emoji: str = ""
    market_bias: str = "중립"
    score: float = 50.0


# ── Fundamental ──

class FundamentalResult(BaseModel):
    valuation_score: float = 50.0
    valuation_label: str = "데이터 없음"
    profitability_score: float = 50.0
    profitability_label: str = "데이터 없음"
    growth_score: float = 50.0
    growth_label: str = "데이터 없음"
    financial_health_score: float = 50.0
    financial_health_label: str = "데이터 없음"
    dividend_score: float = 50.0
    dividend_label: str = "무배당"
    analyst_score: float = 50.0
    analyst_label: str = "데이터 없음"
    insider_score: float = 50.0
    insider_label: str = "데이터 없음"
    score: float = 50.0


# ── Price Targets ──

class PriceTarget(BaseModel):
    target_price: float = 0.0
    target_pct: float = 0.0
    resistance_1: float = 0.0
    stop_loss: float = 0.0
    stop_loss_pct: float = 0.0
    support_1: float = 0.0
    risk_reward_ratio: float = 0.0
    rr_label: str = "산출 불가"


# ── Final Composite ──

class StockAnalysisResult(BaseModel):
    ticker: str
    company_name: str = ""
    current_price: float = 0.0
    analysis_time: datetime = Field(default_factory=datetime.now)

    # Macro
    macro: MacroResult

    # Score
    ai_score: float = 50.0
    previous_score: Optional[float] = None
    grade: Grade = Grade.C

    # Technical
    trend: TrendResult = Field(default_factory=TrendResult)
    weekly_performance_pct: float = 0.0
    momentum: MomentumResult = Field(default_factory=MomentumResult)
    volume: VolumeResult = Field(default_factory=VolumeResult)
    ichimoku: IchimokuResult = Field(default_factory=IchimokuResult)
    fibonacci: FibonacciResult = Field(default_factory=FibonacciResult)

    # Pattern
    wave: WaveResult = Field(default_factory=WaveResult)
    fvg: FVGResult = Field(default_factory=FVGResult)
    candlestick: CandlestickResult = Field(default_factory=CandlestickResult)
    similarity: SimilarityResult = Field(default_factory=SimilarityResult)
    complex_patterns: ComplexPatternResult = Field(default_factory=ComplexPatternResult)

    # Quant
    short_squeeze: ShortSqueezeResult = Field(default_factory=ShortSqueezeResult)
    rsi_divergence: RSIDivergenceResult = Field(default_factory=RSIDivergenceResult)
    bb_squeeze: BBSqueezeResult = Field(default_factory=BBSqueezeResult)
    mean_reversion: MeanReversionResult = Field(default_factory=MeanReversionResult)
    momentum_factor: MomentumFactorResult = Field(default_factory=MomentumFactorResult)
    sector_relative: SectorRelativeResult = Field(default_factory=SectorRelativeResult)
    earnings_surprise: EarningsSurpriseResult = Field(default_factory=EarningsSurpriseResult)
    institutional_flow: InstitutionalFlowResult = Field(default_factory=InstitutionalFlowResult)
    options_flow: OptionsFlowResult = Field(default_factory=OptionsFlowResult)
    lunar_phase: LunarPhaseResult = Field(default_factory=LunarPhaseResult)

    # Fundamental
    fundamental: FundamentalResult = Field(default_factory=FundamentalResult)

    # Special
    special_signals: list[str] = Field(default_factory=list)
    final_signal: str = "분석 중"

    # Targets
    price_target: PriceTarget = Field(default_factory=PriceTarget)

    # Alerts
    alerts: list[str] = Field(default_factory=list)
