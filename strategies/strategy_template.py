"""
Custom Strategy Template
-----------------------
Use this template to create your own scalping strategies

Copy this file and rename it to strategy_f_custom.py (or any name you prefer)
Then implement your own logic in the generate_signal method.

Returns: 1 (Buy), -1 (Sell), 0 (Neutral)
"""

import pandas as pd
import numpy as np
from typing import Tuple
import config


class StrategyF_Custom:
    """Custom Strategy Template - Implement Your Own Logic"""
    
    def __init__(self):
        self.name = "Strategy F: Custom"  # Change this to your strategy name
        
        # Add your strategy parameters here
        # For example:
        # self.period = 20
        # self.threshold = 0.5
        
    def calculate_indicator(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate your custom indicator
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Series with calculated indicator values
        """
        # Example: Simple Moving Average
        # return df['close'].rolling(window=self.period).mean()
        
        # Example: Custom calculation
        # return (df['high'] + df['low']) / 2
        
        pass
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[int, str]:
        """
        Generate trading signal based on your custom logic
        
        Args:
            df: DataFrame with OHLCV data
            Columns available: open, high, low, close, tick_volume, time
            
        Returns:
            Tuple of (signal, reason)
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Description of why signal was generated
        """
        # Check if we have enough data
        min_bars_needed = 50  # Adjust based on your indicator needs
        if df is None or len(df) < min_bars_needed:
            return 0, "Insufficient data"
        
        try:
            # ============================================================
            # IMPLEMENT YOUR STRATEGY LOGIC HERE
            # ============================================================
            
            # Example Strategy: Buy when price crosses above SMA, sell when below
            # 
            # sma = df['close'].rolling(window=20).mean()
            # current_price = df['close'].iloc[-1]
            # prev_price = df['close'].iloc[-2]
            # current_sma = sma.iloc[-1]
            # prev_sma = sma.iloc[-2]
            # 
            # # Bullish crossover
            # if prev_price <= prev_sma and current_price > current_sma:
            #     reason = f"BUY: Price crossed above SMA ({current_sma:.5f})"
            #     return 1, reason
            # 
            # # Bearish crossover
            # if prev_price >= prev_sma and current_price < current_sma:
            #     reason = f"SELL: Price crossed below SMA ({current_sma:.5f})"
            #     return -1, reason
            
            # ============================================================
            # END OF CUSTOM LOGIC
            # ============================================================
            
            # If no signal condition is met, return neutral
            return 0, "No signal"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_indicator_values(self, df: pd.DataFrame) -> dict:
        """
        Get current indicator values for logging/debugging
        
        Returns:
            Dictionary with current indicator values
        """
        if df is None or len(df) < 50:
            return {}
        
        try:
            # Return your indicator values here for debugging
            # For example:
            # sma = df['close'].rolling(window=20).mean()
            # return {
            #     'sma': sma.iloc[-1],
            #     'current_price': df['close'].iloc[-1],
            #     'distance_from_sma': df['close'].iloc[-1] - sma.iloc[-1]
            # }
            
            return {}
        except:
            return {}


# ============================================================
# EXAMPLE STRATEGIES TO INSPIRE YOU
# ============================================================

"""
Example 1: RSI Overbought/Oversold
----------------------------------
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

rsi = calculate_rsi(df, 14)
current_rsi = rsi.iloc[-1]

if current_rsi < 30:  # Oversold
    return 1, f"BUY: RSI oversold at {current_rsi:.2f}"
elif current_rsi > 70:  # Overbought
    return -1, f"SELL: RSI overbought at {current_rsi:.2f}"
"""

"""
Example 2: MACD Crossover
-------------------------
def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

macd, signal = calculate_macd(df)

# Bullish crossover
if macd.iloc[-2] <= signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]:
    return 1, "BUY: MACD bullish crossover"

# Bearish crossover
if macd.iloc[-2] >= signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]:
    return -1, "SELL: MACD bearish crossover"
"""

"""
Example 3: Price Action - Pin Bar
---------------------------------
current_bar = df.iloc[-1]
body = abs(current_bar['close'] - current_bar['open'])
total_range = current_bar['high'] - current_bar['low']
upper_wick = current_bar['high'] - max(current_bar['open'], current_bar['close'])
lower_wick = min(current_bar['open'], current_bar['close']) - current_bar['low']

# Bullish pin bar (long lower wick, small body)
if lower_wick > 2 * body and lower_wick > 0.6 * total_range:
    return 1, "BUY: Bullish pin bar detected"

# Bearish pin bar (long upper wick, small body)
if upper_wick > 2 * body and upper_wick > 0.6 * total_range:
    return -1, "SELL: Bearish pin bar detected"
"""

"""
Example 4: Volume Spike with Price Direction
--------------------------------------------
avg_volume = df['tick_volume'].rolling(window=20).mean()
current_volume = df['tick_volume'].iloc[-1]
volume_ratio = current_volume / avg_volume.iloc[-1]

current_bar = df.iloc[-1]
is_bullish = current_bar['close'] > current_bar['open']
is_bearish = current_bar['close'] < current_bar['open']

if volume_ratio > 2.0:  # Volume spike
    if is_bullish:
        return 1, f"BUY: Volume spike ({volume_ratio:.1f}x) with bullish bar"
    elif is_bearish:
        return -1, f"SELL: Volume spike ({volume_ratio:.1f}x) with bearish bar"
"""

"""
TO ADD YOUR CUSTOM STRATEGY TO THE BOT:
---------------------------------------
1. Copy this template file
2. Rename it (e.g., strategy_f_my_strategy.py)
3. Implement your logic in generate_signal()
4. Add it to strategies/__init__.py:
   
   from .strategy_f_my_strategy import StrategyF_MyStrategy
   
   __all__ = [
       'StrategyA_TripleEMA',
       ...
       'StrategyF_MyStrategy'  # Add your strategy here
   ]

5. Add it to main.py in the __init__ method:
   
   self.strategies = [
       StrategyA_TripleEMA(),
       ...
       StrategyF_MyStrategy()  # Add your strategy here
   ]

6. Test it thoroughly on a demo account first!
"""
