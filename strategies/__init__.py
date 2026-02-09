"""
Strategy Module Package
Contains all scalping strategies for MT5ScalpBot
"""

from .strategy_a_triple_ema import StrategyA_TripleEMA
from .strategy_b_adx_di import StrategyB_ADXDI
from .strategy_c_bollinger import StrategyC_Bollinger
from .strategy_d_stochastic import StrategyD_Stochastic
from .strategy_e_breakout import StrategyE_Breakout

__all__ = [
    'StrategyA_TripleEMA',
    'StrategyB_ADXDI',
    'StrategyC_Bollinger',
    'StrategyD_Stochastic',
    'StrategyE_Breakout'
]
