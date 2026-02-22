import os
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    FRED_API_KEY = st.secrets.get("FRED_API_KEY", os.getenv("FRED_API_KEY", ""))
except Exception:
    FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Cache TTL (seconds)
CACHE_TTL_MACRO = 3600       # 1 hour
CACHE_TTL_PRICE = 900        # 15 min
CACHE_TTL_FINANCIAL = 86400  # 24 hours
CACHE_TTL_OPTIONS = 1800     # 30 min

# Analysis defaults
DEFAULT_PERIOD = "1y"
DEFAULT_LOOKBACK_DAYS = 252  # 1 trading year
SIMILARITY_WINDOW = 60      # days for pattern matching
ZIGZAG_THRESHOLD = 0.05     # 5% for wave detection

# Macro thresholds
VIX_LEVELS = {"stable": 15, "caution": 20, "danger": 30}
