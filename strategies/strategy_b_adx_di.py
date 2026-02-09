"""
Strategy B: 1-Min ADX/DI Scalper
---------------------------------
Buy Signal: +DI crosses -DI from below AND current candle is Green AND 88-period Trend-MA is Green
Sell Signal: -DI crosses +DI from below AND current candle is Red AND 88-period Trend-MA is Red

Returns: 1 (Buy), -1 (Sell), 0 (Neutral)
"""

import pandas as pd
import numpy as np
from typing import Tuple
import config


class StrategyB_ADXDI:
    """ADX/DI Directional Indicator Scalper Strategy"""
    
    def __init__(self):
        self.name = "Strategy B: ADX/DI Scalper"
        self.params = config.STRATEGY_B_PARAMS
        self.adx_period = self.params['adx_period']
        self.di_period = self.params['di_period']
        self.trend_ma_period = self.params['trend_ma_period']
        
    def calculate_tr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high = df['high']
        low = df['low']
        close_prev = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr
    
    def calculate_di(self, df: pd.DataFrame, period: int) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate +DI and -DI (Directional Indicators)
        
        Returns:
            Tuple of (+DI, -DI)
        """
        high = df['high']
        low = df['low']
        
        # Calculate directional movements
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        # Clean up DM values
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # If +DM > -DM, set -DM to 0, and vice versa
        plus_dm[(plus_dm < minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm)] = 0
        
        # Calculate True Range
        tr = self.calculate_tr(df)
        
        # Smooth DM and TR using Wilder's smoothing (EMA with alpha = 1/period)
        alpha = 1.0 / period
        plus_dm_smooth = plus_dm.ewm(alpha=alpha, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=alpha, adjust=False).mean()
        tr_smooth = tr.ewm(alpha=alpha, adjust=False).mean()
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        return plus_di, minus_di
    
    def calculate_adx(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate ADX (Average Directional Index)"""
        plus_di, minus_di = self.calculate_di(df, period)
        
        # Calculate DX (Directional Movement Index)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # ADX is the smoothed DX
        alpha = 1.0 / period
        adx = dx.ewm(alpha=alpha, adjust=False).mean()
        
        return adx
    
    def detect_di_crossover(self, plus_di: pd.Series, minus_di: pd.Series) -> Tuple[bool, bool]:
        """
        Detect +DI and -DI crossovers
        
        Returns:
            Tuple of (bullish_cross, bearish_cross)
        """
        if len(plus_di) < 2 or len(minus_di) < 2:
            return False, False
        
        # Current values
        plus_curr = plus_di.iloc[-1]
        minus_curr = minus_di.iloc[-1]
        
        # Previous values
        plus_prev = plus_di.iloc[-2]
        minus_prev = minus_di.iloc[-2]
        
        # Bullish: +DI crosses above -DI (from below)
        bullish_cross = (plus_prev <= minus_prev) and (plus_curr > minus_curr)
        
        # Bearish: -DI crosses above +DI (from below)
        bearish_cross = (minus_prev <= plus_prev) and (minus_curr > plus_curr)
        
        return bullish_cross, bearish_cross
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[int, str]:
        """
        Generate trading signal based on ADX/DI strategy
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (signal, reason)
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Description of why signal was generated
        """
        if df is None or len(df) < self.trend_ma_period + 20:
            return 0, "Insufficient data"
        
        try:
            # Calculate +DI and -DI
            plus_di, minus_di = self.calculate_di(df, self.di_period)
            
            # Calculate 88-period Trend MA (Simple Moving Average of Close)
            trend_ma = df['close'].rolling(window=self.trend_ma_period).mean()
            
            # Current candle color
            current_candle_green = df['close'].iloc[-1] > df['open'].iloc[-1]
            current_candle_red = df['close'].iloc[-1] < df['open'].iloc[-1]
            
            # Check if 88-MA is green (trending up) or red (trending down)
            ma_green = trend_ma.iloc[-1] > trend_ma.iloc[-2]
            ma_red = trend_ma.iloc[-1] < trend_ma.iloc[-2]
            
            # Detect DI crossover
            bullish_cross, bearish_cross = self.detect_di_crossover(plus_di, minus_di)
            
            # Buy Signal: +DI crosses -DI from below AND current candle is green AND 88-MA is green
            if bullish_cross and current_candle_green and ma_green:
                reason = f"BUY: +DI crossed above -DI, Green candle, 88MA trending up"
                return 1, reason
            
            # Sell Signal: -DI crosses +DI from below AND current candle is red AND 88-MA is red
            if bearish_cross and current_candle_red and ma_red:
                reason = f"SELL: -DI crossed above +DI, Red candle, 88MA trending down"
                return -1, reason
            
            return 0, "No valid ADX/DI signal"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"
    
    def get_indicator_values(self, df: pd.DataFrame) -> dict:
        """Get current indicator values for logging/debugging"""
        if df is None or len(df) < self.trend_ma_period + 20:
            return {}
            
        try:
            plus_di, minus_di = self.calculate_di(df, self.di_period)
            adx = self.calculate_adx(df, self.adx_period)
            trend_ma = df['close'].rolling(window=self.trend_ma_period).mean()
            
            return {
                'plus_di': plus_di.iloc[-1],
                'minus_di': minus_di.iloc[-1],
                'adx': adx.iloc[-1],
                'trend_ma_88': trend_ma.iloc[-1],
                'candle_color': 'green' if df['close'].iloc[-1] > df['open'].iloc[-1] else 'red'
            }
        except:
            return {}
