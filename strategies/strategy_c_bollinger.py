"""
Strategy C: Bollinger Band Mean Reversion
------------------------------------------
Buy Signal: Price touches lower band AND closes above the Middle Line
Sell Signal: Price touches upper band AND closes below the Middle Line

Returns: 1 (Buy), -1 (Sell), 0 (Neutral)
"""

import pandas as pd
import numpy as np
from typing import Tuple
import config


class StrategyC_Bollinger:
    """Bollinger Band Mean Reversion Strategy"""
    
    def __init__(self):
        self.name = "Strategy C: Bollinger Mean Reversion"
        self.params = config.STRATEGY_C_PARAMS
        self.bb_period = self.params['bb_period']
        self.bb_std = self.params['bb_std']
        self.touch_threshold = self.params['touch_threshold']
        
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        # Middle band is the Simple Moving Average
        middle_band = df['close'].rolling(window=self.bb_period).mean()
        
        # Standard deviation
        std = df['close'].rolling(window=self.bb_period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (self.bb_std * std)
        lower_band = middle_band - (self.bb_std * std)
        
        return upper_band, middle_band, lower_band
    
    def check_band_touch(self, price: float, band: float, threshold: float) -> bool:
        """
        Check if price touches or penetrates a band
        
        Args:
            price: Current price
            band: Band level
            threshold: Threshold for "touching" (in price units)
            
        Returns:
            True if price touches band within threshold
        """
        return abs(price - band) <= threshold
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[int, str]:
        """
        Generate trading signal based on Bollinger Band mean reversion
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (signal, reason)
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Description of why signal was generated
        """
        if df is None or len(df) < self.bb_period + 5:
            return 0, "Insufficient data"
        
        try:
            # Calculate Bollinger Bands
            upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df)
            
            # Get current and previous bar data
            current_close = df['close'].iloc[-1]
            current_low = df['low'].iloc[-1]
            current_high = df['high'].iloc[-1]
            
            prev_close = df['close'].iloc[-2]
            prev_low = df['low'].iloc[-2]
            prev_high = df['high'].iloc[-2]
            
            current_upper = upper_band.iloc[-1]
            current_middle = middle_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            # Buy Signal: Price touches lower band AND closes above middle line
            # Check if low touched or went below lower band in current or previous bar
            touched_lower = (
                self.check_band_touch(current_low, current_lower, self.touch_threshold) or
                current_low < current_lower or
                self.check_band_touch(prev_low, lower_band.iloc[-2], self.touch_threshold) or
                prev_low < lower_band.iloc[-2]
            )
            
            closed_above_middle = current_close > current_middle
            
            if touched_lower and closed_above_middle:
                reason = f"BUY: Touched Lower BB ({current_lower:.5f}), Closed above Middle ({current_middle:.5f})"
                return 1, reason
            
            # Sell Signal: Price touches upper band AND closes below middle line
            # Check if high touched or went above upper band in current or previous bar
            touched_upper = (
                self.check_band_touch(current_high, current_upper, self.touch_threshold) or
                current_high > current_upper or
                self.check_band_touch(prev_high, upper_band.iloc[-2], self.touch_threshold) or
                prev_high > upper_band.iloc[-2]
            )
            
            closed_below_middle = current_close < current_middle
            
            if touched_upper and closed_below_middle:
                reason = f"SELL: Touched Upper BB ({current_upper:.5f}), Closed below Middle ({current_middle:.5f})"
                return -1, reason
            
            return 0, "No Bollinger Band mean reversion signal"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_indicator_values(self, df: pd.DataFrame) -> dict:
        """Get current indicator values for logging/debugging"""
        if df is None or len(df) < self.bb_period + 5:
            return {}
            
        try:
            upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df)
            
            current_close = df['close'].iloc[-1]
            bb_width = upper_band.iloc[-1] - lower_band.iloc[-1]
            bb_position = (current_close - lower_band.iloc[-1]) / bb_width if bb_width > 0 else 0.5
            
            return {
                'upper_band': upper_band.iloc[-1],
                'middle_band': middle_band.iloc[-1],
                'lower_band': lower_band.iloc[-1],
                'current_close': current_close,
                'bb_width': bb_width,
                'bb_position': bb_position  # 0 = lower band, 1 = upper band
            }
        except:
            return {}
