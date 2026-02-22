"""기술 지표 직접 구현 - pandas/numpy 기반"""

import pandas as pd
import numpy as np


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(window=length).mean()


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/length, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "MACD": macd_line,
        "Histogram": histogram,
        "Signal": signal_line,
    })


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k: int = 14, d: int = 3, smooth_k: int = 3) -> pd.DataFrame:
    lowest_low = low.rolling(window=k).min()
    highest_high = high.rolling(window=k).max()
    raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    k_val = raw_k.rolling(window=smooth_k).mean()
    d_val = k_val.rolling(window=d).mean()
    return pd.DataFrame({"K": k_val, "D": d_val})


def adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.DataFrame:
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr = _true_range(high, low, close)
    atr_val = tr.ewm(alpha=1/length, min_periods=length).mean()

    plus_di = 100 * plus_dm.ewm(alpha=1/length, min_periods=length).mean() / atr_val.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/length, min_periods=length).mean() / atr_val.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_val = dx.ewm(alpha=1/length, min_periods=length).mean()

    return pd.DataFrame({
        "ADX": adx_val,
        "DMP": plus_di,
        "DMN": minus_di,
    })


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    tr = _true_range(high, low, close)
    return tr.ewm(alpha=1/length, min_periods=length).mean()


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def bbands(series: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    mid = sma(series, length)
    sd = series.rolling(window=length).std()
    upper = mid + std * sd
    lower = mid - std * sd
    return pd.DataFrame({"BBU": upper, "BBM": mid, "BBL": lower})


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def momentum(series: pd.Series, length: int = 12) -> pd.Series:
    return series.diff(length)


def keltner_channel(high: pd.Series, low: pd.Series, close: pd.Series,
                    length: int = 20, multiplier: float = 1.5) -> pd.DataFrame:
    mid = ema(close, length)
    atr_val = atr(high, low, close, length)
    upper = mid + multiplier * atr_val
    lower = mid - multiplier * atr_val
    return pd.DataFrame({"KCU": upper, "KCM": mid, "KCL": lower})
