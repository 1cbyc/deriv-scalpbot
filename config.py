"""
Deriv Scalping Bot Configuration
High-Frequency Trading Settings for Deriv API
WebSocket-based tick streaming and contract trading
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DERIV API CONNECTION SETTINGS
# ============================================================================
# Get credentials from api.deriv.com/dashboard
DERIV_APP_ID = os.getenv('DERIV_APP_ID')
DERIV_API_TOKEN = os.getenv('DERIV_API_TOKEN')
DERIV_ACCOUNT_ID = os.getenv('DERIV_ACCOUNT_ID')  # Account ID (e.g., VRTC2770532)

# ============================================================================
# TRADING PAIRS CONFIGURATION
# ============================================================================
# Load monitored symbols from environment or use defaults
MONITORED_SYMBOLS_ENV = os.getenv('MONITORED_SYMBOLS', '')

# Default Forex Major Pairs (Deriv format)
DEFAULT_FOREX_PAIRS = [
    "frxEURUSD",
    "frxGBPUSD",
    "frxUSDJPY",
    "frxAUDUSD",
    "frxUSDCAD",
    "frxUSDCHF",
    "frxNZDUSD"
]

# Synthetic Indices (Deriv format)
DEFAULT_SYNTHETIC_INDICES = [
    "R_10",   # Volatility 10 Index
    "R_25",   # Volatility 25 Index
    "R_50",   # Volatility 50 Index
    "R_75",   # Volatility 75 Index
    "R_100",  # Volatility 100 Index
    "BOOM500",
    "BOOM1000",
    "CRASH500",
    "CRASH1000"
]

# Use environment variable if set, otherwise use default forex pairs
if MONITORED_SYMBOLS_ENV:
    TRADING_SYMBOLS = [s.strip() for s in MONITORED_SYMBOLS_ENV.split(',')]
else:
    # Default to major forex pairs as requested
    TRADING_SYMBOLS = [
        "frxEURUSD",  # Most liquid
        "frxGBPUSD",  # High volatility
        "frxUSDJPY"   # Asian session
    ]

# ============================================================================
# DERIV CONTRACT SETTINGS
# ============================================================================
CONTRACT_DURATION = int(os.getenv('CONTRACT_DURATION', '5'))  # Default 5 ticks
CONTRACT_DURATION_UNIT = os.getenv('CONTRACT_DURATION_UNIT', 't')  # t=ticks, s=seconds, m=minutes

# ============================================================================
# ENGINE SETTINGS
# ============================================================================
TICK_SLEEP_INTERVAL = 0.1  # Sleep 0.1 seconds between iterations
ANALYSIS_INTERVAL_SECONDS = int(os.getenv('ANALYSIS_INTERVAL_SECONDS', '15'))  # Slower = safer
LOOKBACK_TICKS = 1000  # Number of historical ticks to keep in memory

# ============================================================================
# ACCOUNT & RISK SETTINGS (DERIV) - Optimized for Small Accounts
# ============================================================================
BASE_STAKE_USD = float(os.getenv('BASE_STAKE_USD', '0.50'))  # Base stake per contract in USD
MAX_STAKE_USD = float(os.getenv('MAX_STAKE_USD', '2.00'))  # Maximum stake cap

# Position Sizing - "Max Profit Builder" (Conservative)
BUILDER_WINS_THRESHOLD = int(os.getenv('BUILDER_WINS_THRESHOLD', '5'))  # Increase after 5 wins
BUILDER_INCREMENT = float(os.getenv('BUILDER_INCREMENT', '0.05'))  # Increase by 5%

# Risk-to-Reward (for reference calculation, actual R:R depends on contract)
RISK_REWARD_RATIO = 1.5  # Target Take Profit = 1.5 × Stop Loss
SWING_BUFFER_PIPS = 2  # Add/subtract 2 pips from swing high/low for SL

# Maximum positions (Reduced for small account)
MAX_POSITIONS_PER_SYMBOL = 1  # Only one contract per symbol at a time
MAX_TOTAL_POSITIONS = int(os.getenv('MAX_TOTAL_POSITIONS', '3'))  # Max 3 contracts (safer)

# ============================================================================
# STRATEGY PARAMETERS
# ============================================================================

# Strategy A: Triple EMA Trend Filter
STRATEGY_A_PARAMS = {
    "fast_ema": 6,
    "medium_ema": 22,
    "slow_ema": 300
}

# Strategy B: 1-Min ADX/DI Scalper
STRATEGY_B_PARAMS = {
    "adx_period": 14,
    "di_period": 14,
    "trend_ma_period": 88
}

# Strategy C: Bollinger Band Mean Reversion
STRATEGY_C_PARAMS = {
    "bb_period": 20,
    "bb_std": 2.0,
    "touch_threshold": 0.0001  # Pip threshold for "touching" band
}

# Strategy D: Stochastic Divergence
STRATEGY_D_PARAMS = {
    "stoch_k": 14,
    "stoch_d": 3,
    "stoch_slowing": 3,
    "divergence_lookback": 20,  # Look back N bars for divergence
    "ema_fast": 6,
    "ema_medium": 22
}

# Strategy E: Breakout Scalper
STRATEGY_E_PARAMS = {
    "opening_range_minutes": 15,  # First 15 minutes define the range
    "volume_multiplier": 1.5,  # Breakout volume > 1.5x average
    "volume_lookback": 20  # Average volume over 20 bars
}

# ============================================================================
# EXECUTION SETTINGS (DERIV)
# ============================================================================
# Contract settings are defined above in DERIV CONTRACT SETTINGS

# Price-lock mechanism (verify price before execution)
MAX_SLIPPAGE_PIPS = float(os.getenv('MAX_SLIPPAGE_PIPS', '0.5'))  # Max acceptable slippage

# Latency optimization (track tick gaps for better entry timing)
LATENCY_CHECK_ENABLED = True
MIN_TICK_GAP_THRESHOLD = 0.00005  # Minimum gap to consider better entry

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_FILE_PATH = "deriv_scalpbot.log"
CONSOLE_OUTPUT = True

# ============================================================================
# SHUTDOWN SETTINGS
# ============================================================================
GRACEFUL_SHUTDOWN_TIMEOUT = 10  # Seconds to wait for positions to close on shutdown
CLOSE_ALL_ON_SHUTDOWN = True  # Close all positions when shutting down

# ============================================================================
# TELEGRAM ALERTS CONFIGURATION
# ============================================================================
ENABLE_TELEGRAM_ALERTS = os.getenv('ENABLE_TRADE_ALERTS', 'true').lower() == 'true'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# ============================================================================
# RISK MANAGEMENT ALERTS (Enhanced for Small Accounts)
# ============================================================================
ENABLE_RISK_ALERTS = os.getenv('ENABLE_RISK_ALERTS', 'true').lower() == 'true'
DAILY_LOSS_LIMIT_PCT = float(os.getenv('DAILY_LOSS_LIMIT_PCT', '30.0'))  # Stop at -30%
DAILY_LOSS_LIMIT_USD = float(os.getenv('DAILY_LOSS_LIMIT_USD', '2.75'))  # Hard USD limit
DRAWDOWN_LIMIT_PCT = float(os.getenv('DRAWDOWN_LIMIT_PCT', '15.0'))
MARGIN_LEVEL_WARNING = float(os.getenv('MARGIN_LEVEL_WARNING', '150.0'))
MARGIN_LEVEL_CRITICAL = float(os.getenv('MARGIN_LEVEL_CRITICAL', '100.0'))

# ============================================================================
# MONITORING SETTINGS
# ============================================================================
PRICE_CHECK_INTERVAL = int(os.getenv('PRICE_CHECK_INTERVAL', '5'))
ENABLE_PROFIT_SUGGESTIONS = os.getenv('ENABLE_PROFIT_SUGGESTIONS', 'true').lower() == 'true'
MIN_PROFIT_FOR_SUGGESTION = float(os.getenv('MIN_PROFIT_FOR_SUGGESTION', '10.0'))
ENABLE_DAILY_SUMMARY = os.getenv('ENABLE_DAILY_SUMMARY', 'true').lower() == 'true'

