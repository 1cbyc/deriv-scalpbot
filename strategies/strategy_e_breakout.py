"""
Strategy E: Breakout Scalper
-----------------------------
Detect 15-minute opening range high/low.
Enter on high-volume breakout of these levels.

Buy Signal: Price breaks above 15-min opening range high with volume > 1.5x average
Sell Signal: Price breaks below 15-min opening range low with volume > 1.5x average

Returns: 1 (Buy), -1 (Sell), 0 (Neutral)
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from datetime import datetime, time
import config


class StrategyE_Breakout:
    """Opening Range Breakout Scalper Strategy"""
    
    def __init__(self):
        self.name = "Strategy E: Breakout Scalper"
        self.params = config.STRATEGY_E_PARAMS
        self.opening_range_minutes = self.params['opening_range_minutes']
        self.volume_multiplier = self.params['volume_multiplier']
        self.volume_lookback = self.params['volume_lookback']
        
        # Cache opening range for each day
        self.opening_range_cache = {}
        
    def get_opening_range(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[datetime]]:
        """
        Calculate the opening range (first N minutes high/low)
        
        Returns:
            Tuple of (range_high, range_low, range_date)
        """
        if df is None or len(df) < self.opening_range_minutes:
            return None, None, None
        
        try:
            # Get the current date (latest bar)
            latest_time = df['time'].iloc[-1]
            current_date = latest_time.date()
            
            # Check if we have cached opening range for today
            if current_date in self.opening_range_cache:
                return self.opening_range_cache[current_date]
            
            # Filter bars for the current trading day
            today_bars = df[df['time'].dt.date == current_date]
            
            if len(today_bars) < self.opening_range_minutes:
                # Not enough data for opening range yet
                return None, None, None
            
            # Get first N minutes of the day
            opening_bars = today_bars.head(self.opening_range_minutes)
            
            range_high = opening_bars['high'].max()
            range_low = opening_bars['low'].min()
            
            # Cache the result
            self.opening_range_cache[current_date] = (range_high, range_low, current_date)
            
            return range_high, range_low, current_date
            
        except Exception as e:
            print(f"[ERROR] Failed to calculate opening range: {e}")
            return None, None, None
    
    def calculate_average_volume(self, df: pd.DataFrame, lookback: int) -> float:
        """
        Calculate average volume over lookback period
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to average
            
        Returns:
            Average volume
        """
        if df is None or len(df) < lookback:
            lookback = len(df) if df is not None else 0
        
        if lookback == 0:
            return 0.0
        
        try:
            recent_volume = df['tick_volume'].tail(lookback)
            avg_volume = recent_volume.mean()
            return avg_volume
        except:
            return 0.0
    
    def detect_breakout(self, df: pd.DataFrame) -> Tuple[bool, bool, float]:
        """
        Detect breakout with volume confirmation
        
        Returns:
            Tuple of (bullish_breakout, bearish_breakout, current_volume_ratio)
        """
        if df is None or len(df) < 2:
            return False, False, 0.0
        
        try:
            # Get opening range
            range_high, range_low, range_date = self.get_opening_range(df)
            
            if range_high is None or range_low is None:
                return False, False, 0.0
            
            # Current price action
            current_close = df['close'].iloc[-1]
            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]
            current_volume = df['tick_volume'].iloc[-1]
            
            # Calculate average volume
            avg_volume = self.calculate_average_volume(df, self.volume_lookback)
            
            if avg_volume == 0:
                return False, False, 0.0
            
            # Volume ratio
            volume_ratio = current_volume / avg_volume
            
            # Check for volume spike
            high_volume = volume_ratio >= self.volume_multiplier
            
            # Bullish breakout: Price breaks above opening range high with high volume
            bullish_breakout = (current_high > range_high) and high_volume and (current_close > range_high)
            
            # Bearish breakout: Price breaks below opening range low with high volume
            bearish_breakout = (current_low < range_low) and high_volume and (current_close < range_low)
            
            return bullish_breakout, bearish_breakout, volume_ratio
            
        except Exception as e:
            print(f"[ERROR] Breakout detection failed: {e}")
            return False, False, 0.0
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[int, str]:
        """
        Generate trading signal based on Opening Range Breakout
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (signal, reason)
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Description of why signal was generated
        """
        if df is None or len(df) < max(self.opening_range_minutes, self.volume_lookback):
            return 0, "Insufficient data"
        
        try:
            # Get opening range
            range_high, range_low, range_date = self.get_opening_range(df)
            
            if range_high is None or range_low is None:
                return 0, "Opening range not yet established"
            
            # Detect breakout
            bullish_breakout, bearish_breakout, volume_ratio = self.detect_breakout(df)
            
            # Buy Signal: Bullish breakout with high volume
            if bullish_breakout:
                reason = f"BUY: Breakout above Opening Range High ({range_high:.5f}), Volume: {volume_ratio:.2f}x avg"
                return 1, reason
            
            # Sell Signal: Bearish breakout with high volume
            if bearish_breakout:
                reason = f"SELL: Breakout below Opening Range Low ({range_low:.5f}), Volume: {volume_ratio:.2f}x avg"
                return -1, reason
            
            return 0, "No breakout signal"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_indicator_values(self, df: pd.DataFrame) -> dict:
        """Get current indicator values for logging/debugging"""
        if df is None or len(df) < self.opening_range_minutes:
            return {}
            
        try:
            range_high, range_low, range_date = self.get_opening_range(df)
            avg_volume = self.calculate_average_volume(df, self.volume_lookback)
            current_volume = df['tick_volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                'opening_range_high': range_high if range_high else 0,
                'opening_range_low': range_low if range_low else 0,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'current_price': df['close'].iloc[-1]
            }
        except:
            return {}
