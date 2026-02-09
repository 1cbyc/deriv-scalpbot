"""
Strategy D: Stochastic Divergence
----------------------------------
Buy Signal: Bullish divergence (Price Lower-Low, Stochastic Higher-Low) + 6/22 EMA bullish crossover
Sell Signal: Bearish divergence (Price Higher-High, Stochastic Lower-High) + 6/22 EMA bearish crossover

Returns: 1 (Buy), -1 (Sell), 0 (Neutral)
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
import config


class StrategyD_Stochastic:
    """Stochastic Divergence Strategy"""
    
    def __init__(self):
        self.name = "Strategy D: Stochastic Divergence"
        self.params = config.STRATEGY_D_PARAMS
        self.stoch_k = self.params['stoch_k']
        self.stoch_d = self.params['stoch_d']
        self.stoch_slowing = self.params['stoch_slowing']
        self.divergence_lookback = self.params['divergence_lookback']
        self.ema_fast = self.params['ema_fast']
        self.ema_medium = self.params['ema_medium']
        
    def calculate_stochastic(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator (%K and %D)
        
        Returns:
            Tuple of (%K, %D)
        """
        # Get high, low, close
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate %K
        lowest_low = low.rolling(window=self.stoch_k).min()
        highest_high = high.rolling(window=self.stoch_k).max()
        
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        
        # Apply slowing (smooth %K)
        if self.stoch_slowing > 1:
            stoch_k = stoch_k.rolling(window=self.stoch_slowing).mean()
        
        # Calculate %D (SMA of %K)
        stoch_d = stoch_k.rolling(window=self.stoch_d).mean()
        
        return stoch_k, stoch_d
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    def find_pivots(self, series: pd.Series, lookback: int) -> Tuple[List[int], List[int]]:
        """
        Find pivot highs and lows in a series
        
        Returns:
            Tuple of (pivot_high_indices, pivot_low_indices)
        """
        pivot_highs = []
        pivot_lows = []
        
        for i in range(lookback, len(series) - lookback):
            # Check if this is a pivot high
            window = series.iloc[i - lookback:i + lookback + 1]
            if series.iloc[i] == window.max():
                pivot_highs.append(i)
            
            # Check if this is a pivot low
            if series.iloc[i] == window.min():
                pivot_lows.append(i)
        
        return pivot_highs, pivot_lows
    
    def detect_bullish_divergence(self, df: pd.DataFrame, stoch_k: pd.Series) -> bool:
        """
        Detect bullish divergence: Price makes lower low, Stochastic makes higher low
        
        Returns:
            True if bullish divergence detected
        """
        if len(df) < self.divergence_lookback:
            return False
        
        try:
            # Get recent price lows
            recent_price = df['low'].tail(self.divergence_lookback)
            recent_stoch = stoch_k.tail(self.divergence_lookback)
            
            # Find last two lows in price
            price_lows_idx = []
            for i in range(2, len(recent_price) - 2):
                if (recent_price.iloc[i] < recent_price.iloc[i-1] and 
                    recent_price.iloc[i] < recent_price.iloc[i-2] and
                    recent_price.iloc[i] < recent_price.iloc[i+1] and
                    recent_price.iloc[i] < recent_price.iloc[i+2]):
                    price_lows_idx.append(i)
            
            if len(price_lows_idx) < 2:
                return False
            
            # Get last two price lows
            idx1 = price_lows_idx[-2]
            idx2 = price_lows_idx[-1]
            
            price_low1 = recent_price.iloc[idx1]
            price_low2 = recent_price.iloc[idx2]
            
            stoch_low1 = recent_stoch.iloc[idx1]
            stoch_low2 = recent_stoch.iloc[idx2]
            
            # Bullish divergence: Price Lower-Low, Stochastic Higher-Low
            if price_low2 < price_low1 and stoch_low2 > stoch_low1:
                return True
            
            return False
            
        except:
            return False
    
    def detect_bearish_divergence(self, df: pd.DataFrame, stoch_k: pd.Series) -> bool:
        """
        Detect bearish divergence: Price makes higher high, Stochastic makes lower high
        
        Returns:
            True if bearish divergence detected
        """
        if len(df) < self.divergence_lookback:
            return False
        
        try:
            # Get recent price highs
            recent_price = df['high'].tail(self.divergence_lookback)
            recent_stoch = stoch_k.tail(self.divergence_lookback)
            
            # Find last two highs in price
            price_highs_idx = []
            for i in range(2, len(recent_price) - 2):
                if (recent_price.iloc[i] > recent_price.iloc[i-1] and 
                    recent_price.iloc[i] > recent_price.iloc[i-2] and
                    recent_price.iloc[i] > recent_price.iloc[i+1] and
                    recent_price.iloc[i] > recent_price.iloc[i+2]):
                    price_highs_idx.append(i)
            
            if len(price_highs_idx) < 2:
                return False
            
            # Get last two price highs
            idx1 = price_highs_idx[-2]
            idx2 = price_highs_idx[-1]
            
            price_high1 = recent_price.iloc[idx1]
            price_high2 = recent_price.iloc[idx2]
            
            stoch_high1 = recent_stoch.iloc[idx1]
            stoch_high2 = recent_stoch.iloc[idx2]
            
            # Bearish divergence: Price Higher-High, Stochastic Lower-High
            if price_high2 > price_high1 and stoch_high2 < stoch_high1:
                return True
            
            return False
            
        except:
            return False
    
    def detect_ema_crossover(self, ema_fast: pd.Series, ema_slow: pd.Series) -> Tuple[bool, bool]:
        """
        Detect EMA crossovers
        
        Returns:
            Tuple of (bullish_cross, bearish_cross)
        """
        if len(ema_fast) < 2 or len(ema_slow) < 2:
            return False, False
        
        # Current values
        fast_curr = ema_fast.iloc[-1]
        slow_curr = ema_slow.iloc[-1]
        
        # Previous values
        fast_prev = ema_fast.iloc[-2]
        slow_prev = ema_slow.iloc[-2]
        
        # Bullish crossover
        bullish_cross = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
        
        # Bearish crossover
        bearish_cross = (fast_prev >= slow_prev) and (fast_curr < slow_curr)
        
        return bullish_cross, bearish_cross
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[int, str]:
        """
        Generate trading signal based on Stochastic Divergence
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (signal, reason)
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Description of why signal was generated
        """
        if df is None or len(df) < self.divergence_lookback + 20:
            return 0, "Insufficient data"
        
        try:
            # Calculate Stochastic
            stoch_k, stoch_d = self.calculate_stochastic(df)
            
            # Calculate EMAs
            ema_6 = self.calculate_ema(df['close'], self.ema_fast)
            ema_22 = self.calculate_ema(df['close'], self.ema_medium)
            
            # Detect divergences
            bullish_div = self.detect_bullish_divergence(df, stoch_k)
            bearish_div = self.detect_bearish_divergence(df, stoch_k)
            
            # Detect EMA crossovers
            bullish_cross, bearish_cross = self.detect_ema_crossover(ema_6, ema_22)
            
            # Buy Signal: Bullish divergence + 6/22 EMA bullish crossover
            if bullish_div and bullish_cross:
                reason = f"BUY: Bullish Divergence detected + 6EMA crossed above 22EMA"
                return 1, reason
            
            # Sell Signal: Bearish divergence + 6/22 EMA bearish crossover
            if bearish_div and bearish_cross:
                reason = f"SELL: Bearish Divergence detected + 6EMA crossed below 22EMA"
                return -1, reason
            
            return 0, "No divergence + crossover signal"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_indicator_values(self, df: pd.DataFrame) -> dict:
        """Get current indicator values for logging/debugging"""
        if df is None or len(df) < self.divergence_lookback + 20:
            return {}
            
        try:
            stoch_k, stoch_d = self.calculate_stochastic(df)
            ema_6 = self.calculate_ema(df['close'], self.ema_fast)
            ema_22 = self.calculate_ema(df['close'], self.ema_medium)
            
            return {
                'stoch_k': stoch_k.iloc[-1],
                'stoch_d': stoch_d.iloc[-1],
                'ema_6': ema_6.iloc[-1],
                'ema_22': ema_22.iloc[-1]
            }
        except:
            return {}
