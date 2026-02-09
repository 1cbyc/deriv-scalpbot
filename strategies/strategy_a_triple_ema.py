"""
Strategy A: Triple EMA Trend Filter
----------------------------------
Buy Signal: Price > 300 EMA AND 6 EMA crosses above 22 EMA
Sell Signal: Price < 300 EMA AND 6 EMA crosses below 22 EMA

Returns: 1 (Buy), -1 (Sell), 0 (Neutral)
"""

import pandas as pd
import numpy as np
from typing import Tuple
import config


class StrategyA_TripleEMA:
    """Triple EMA Trend Filter Strategy"""
    
    def __init__(self):
        self.name = "Strategy A: Triple EMA"
        self.params = config.STRATEGY_A_PARAMS
        self.fast_ema = self.params['fast_ema']
        self.medium_ema = self.params['medium_ema']
        self.slow_ema = self.params['slow_ema']
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    def detect_crossover(self, fast: pd.Series, slow: pd.Series) -> Tuple[bool, bool]:
        """
        Detect EMA crossovers
        
        Returns:
            Tuple of (bullish_cross, bearish_cross)
        """
        if len(fast) < 2 or len(slow) < 2:
            return False, False
            
        # Current values
        fast_curr = fast.iloc[-1]
        slow_curr = slow.iloc[-1]
        
        # Previous values
        fast_prev = fast.iloc[-2]
        slow_prev = slow.iloc[-2]
        
        # Bullish crossover: fast crosses above slow
        bullish_cross = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
        
        # Bearish crossover: fast crosses below slow
        bearish_cross = (fast_prev >= slow_prev) and (fast_curr < slow_curr)
        
        return bullish_cross, bearish_cross
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[int, str]:
        """
        Generate trading signal based on Triple EMA strategy
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (signal, reason)
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Description of why signal was generated
        """
        if df is None or len(df) < self.slow_ema + 10:
            return 0, "Insufficient data"
        
        try:
            # Calculate EMAs
            ema_6 = self.calculate_ema(df['close'], self.fast_ema)
            ema_22 = self.calculate_ema(df['close'], self.medium_ema)
            ema_300 = self.calculate_ema(df['close'], self.slow_ema)
            
            # Current price
            current_price = df['close'].iloc[-1]
            
            # Detect 6/22 crossover
            bullish_cross, bearish_cross = self.detect_crossover(ema_6, ema_22)
            
            # Check trend filter (price vs 300 EMA)
            above_300 = current_price > ema_300.iloc[-1]
            below_300 = current_price < ema_300.iloc[-1]
            
            # Buy Signal: Price > 300 EMA AND 6 crosses above 22
            if above_300 and bullish_cross:
                reason = f"BUY: Price ({current_price:.5f}) > 300EMA ({ema_300.iloc[-1]:.5f}), 6EMA crossed above 22EMA"
                return 1, reason
            
            # Sell Signal: Price < 300 EMA AND 6 crosses below 22
            if below_300 and bearish_cross:
                reason = f"SELL: Price ({current_price:.5f}) < 300EMA ({ema_300.iloc[-1]:.5f}), 6EMA crossed below 22EMA"
                return -1, reason
            
            return 0, "No crossover or trend filter not met"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_indicator_values(self, df: pd.DataFrame) -> dict:
        """
        Get current indicator values for logging/debugging
        
        Returns:
            Dictionary with current EMA values
        """
        if df is None or len(df) < self.slow_ema + 10:
            return {}
            
        try:
            ema_6 = self.calculate_ema(df['close'], self.fast_ema)
            ema_22 = self.calculate_ema(df['close'], self.medium_ema)
            ema_300 = self.calculate_ema(df['close'], self.slow_ema)
            
            return {
                'ema_6': ema_6.iloc[-1],
                'ema_22': ema_22.iloc[-1],
                'ema_300': ema_300.iloc[-1],
                'current_price': df['close'].iloc[-1]
            }
        except:
            return {}
