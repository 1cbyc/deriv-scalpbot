"""
Data Handler for Deriv API
Manages price data streaming, historical data, and indicator calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime
import logging
from deriv_api import DerivAPI

logger = logging.getLogger(__name__)


class DataHandler:
    """
    Handles real-time and historical market data from Deriv API
    """
    
    def __init__(self, deriv_client: DerivAPI, max_history: int = 1000):
        """
        Initialize data handler
        
        Args:
            deriv_client: Connected Deriv API client
            max_history: Maximum number of ticks to keep in memory per symbol
        """
        self.client = deriv_client
        self.max_history = max_history
        
        # Store tick data for each symbol
        self.tick_data = {}  # symbol -> deque of {time, price}
        self.current_prices = {}  # symbol -> latest price
        
        # Subscribed symbols
        self.subscribed_symbols = set()
        
    def initialize_symbol(self, symbol: str) -> bool:
        """
        Initialize a symbol by loading historical data and subscribing to ticks
        
        Args:
            symbol: Trading symbol (e.g., 'R_100', 'frxEURUSD')
            
        Returns:
            bool: True if initialized successfully
        """
        try:
            # Get historical ticks
            ticks = self.client.get_ticks_history(symbol, count=self.max_history)
            
            if not ticks:
                logger.error(f"Failed to get historical data for {symbol}")
                return False
            
            # Store in deque for efficient append/pop
            self.tick_data[symbol] = deque(ticks, maxlen=self.max_history)
            self.current_prices[symbol] = ticks[-1]['price']
            
            # Subscribe to real-time ticks
            self.client.subscribe_ticks(symbol, lambda tick: self._on_tick(symbol, tick))
            self.subscribed_symbols.add(symbol)
            
            logger.info(f"Initialized {symbol} with {len(ticks)} historical ticks")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing {symbol}: {e}")
            return False
    
    def _on_tick(self, symbol: str, tick: Dict):
        """
        Handle incoming tick from real-time stream
        
        Args:
            symbol: Symbol that tick belongs to
            tick: Tick data dict {time, price, symbol}
        """
        if symbol not in self.tick_data:
            self.tick_data[symbol] = deque(maxlen=self.max_history)
        
        self.tick_data[symbol].append({
            'time': tick['time'],
            'price': tick['price']
        })
        
        self.current_prices[symbol] = tick['price']
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price or None if not available
        """
        return self.current_prices.get(symbol)
    
    def get_tick_data(self, symbol: str, count: int = 500) -> Optional[pd.DataFrame]:
        """
        Get recent tick data as DataFrame
        
        Args:
            symbol: Trading symbol
            count: Number of recent ticks to return
            
        Returns:
            DataFrame with columns [time, price] or None if not available
        """
        if symbol not in self.tick_data or len(self.tick_data[symbol]) == 0:
            return None
        
        ticks = list(self.tick_data[symbol])[-count:]
        df = pd.DataFrame(ticks, columns=['time', 'price'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def convert_ticks_to_ohlc(self, symbol: str, count: int = 500, 
                              candle_ticks: int = 10) -> Optional[pd.DataFrame]:
        """
        Convert tick data to OHLC candles
        
        Args:
            symbol: Trading symbol
            count: Number of recent ticks to convert
            candle_ticks: Number of ticks per candle
            
        Returns:
            DataFrame with columns [time, open, high, low, close] or None
        """
        tick_df = self.get_tick_data(symbol, count)
        
        if tick_df is None or len(tick_df) < candle_ticks:
            return None
        
        # Group ticks into candles
        candles = []
        for i in range(0, len(tick_df), candle_ticks):
            chunk = tick_df.iloc[i:i+candle_ticks]
            if len(chunk) > 0:
                candle = {
                    'time': chunk['time'].iloc[-1],
                    'open': chunk['price'].iloc[0],
                    'high': chunk['price'].max(),
                    'low': chunk['price'].min(),
                    'close': chunk['price'].iloc[-1]
                }
                candles.append(candle)
        
        if not candles:
            return None
            
        return pd.DataFrame(candles)
    
    def calculate_ema(self, symbol: str, period: int, count: int = 500) -> Optional[np.ndarray]:
        """
        Calculate Exponential Moving Average
        
        Args:
            symbol: Trading symbol
            period: EMA period
            count: Number of ticks to use
            
        Returns:
            EMA array or None if insufficient data
        """
        tick_df = self.get_tick_data(symbol, count)
        
        if tick_df is None or len(tick_df) < period:
            return None
        
        prices = tick_df['price'].values
        ema = self._calculate_ema_array(prices, period)
        return ema
    
    def _calculate_ema_array(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA for price array"""
        ema = np.zeros_like(prices)
        multiplier = 2 / (period + 1)
        
        # First EMA = SMA
        ema[period-1] = np.mean(prices[:period])
        
        # Calculate EMA
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def calculate_sma(self, symbol: str, period: int, count: int = 500) -> Optional[np.ndarray]:
        """
        Calculate Simple Moving Average
        
        Args:
            symbol: Trading symbol
            period: SMA period
            count: Number of ticks to use
            
        Returns:
            SMA array or None if insufficient data
        """
        tick_df = self.get_tick_data(symbol, count)
        
        if tick_df is None or len(tick_df) < period:
            return None
        
        prices = tick_df['price'].values
        sma = np.convolve(prices, np.ones(period)/period, mode='valid')
        
        # Pad with NaN to match input size
        sma = np.concatenate([np.full(period-1, np.nan), sma])
        return sma
    
    def calculate_bollinger_bands(self, symbol: str, period: int = 20, std_dev: float = 2.0,
                                  count: int = 500) -> Optional[Dict[str, np.ndarray]]:
        """
        Calculate Bollinger Bands
        
        Args:
            symbol: Trading symbol
            period: Period for moving average
            std_dev: Number of standard deviations
            count: Number of ticks to use
            
        Returns:
            Dict with 'middle', 'upper', 'lower' bands or None
        """
        tick_df = self.get_tick_data(symbol, count)
        
        if tick_df is None or len(tick_df) < period:
            return None
        
        prices = tick_df['price'].values
        
        # Calculate middle band (SMA)
        middle = np.convolve(prices, np.ones(period)/period, mode='valid')
        middle = np.concatenate([np.full(period-1, np.nan), middle])
        
        # Calculate standard deviation
        std = pd.Series(prices).rolling(window=period).std().values
        
        # Calculate upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'middle': middle,
            'upper': upper,
            'lower': lower
        }
    
    def calculate_rsi(self, symbol: str, period: int = 14, count: int = 500) -> Optional[np.ndarray]:
        """
        Calculate Relative Strength Index
        
        Args:
            symbol: Trading symbol
            period: RSI period
            count: Number of ticks to use
            
        Returns:
            RSI array or None if insufficient data
        """
        tick_df = self.get_tick_data(symbol, count)
        
        if tick_df is None or len(tick_df) < period + 1:
            return None
        
        prices = tick_df['price'].values
        
        # Calculate price changes
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')
        
        # Calculate RS and RSI
        rs = avg_gains / (avg_losses + 1e-10)  # Add small value to avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        # Pad to match input size
        rsi = np.concatenate([np.full(period, np.nan), rsi])
        
        return rsi
    
    def calculate_stochastic(self, symbol: str, k_period: int = 14, d_period: int = 3,
                            count: int = 500) -> Optional[Dict[str, np.ndarray]]:
        """
        Calculate Stochastic Oscillator
        
        Args:
            symbol: Trading symbol
            k_period: %K period
            d_period: %D period (SMA of %K)
            count: Number of ticks to use
            
        Returns:
            Dict with 'k' and 'd' values or None
        """
        # Convert ticks to OHLC candles for stochastic
        ohlc_df = self.convert_ticks_to_ohlc(symbol, count, candle_ticks=10)
        
        if ohlc_df is None or len(ohlc_df) < k_period:
            return None
        
        high = ohlc_df['high'].values
        low = ohlc_df['low'].values
        close = ohlc_df['close'].values
        
        # Calculate %K
        k = np.zeros_like(close)
        for i in range(k_period-1, len(close)):
            highest_high = np.max(high[i-k_period+1:i+1])
            lowest_low = np.min(low[i-k_period+1:i+1])
            
            if highest_high != lowest_low:
                k[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low)
            else:
                k[i] = 50  # Neutral if no range
        
        # Calculate %D (SMA of %K)
        d = np.convolve(k[k_period-1:], np.ones(d_period)/d_period, mode='valid')
        d = np.concatenate([np.full(k_period + d_period - 2, np.nan), d])
        
        # Pad %K to match
        k[:k_period-1] = np.nan
        
        return {
            'k': k,
            'd': d
        }
    
    def calculate_adx(self, symbol: str, period: int = 14, count: int = 500) -> Optional[Dict[str, np.ndarray]]:
        """
        Calculate Average Directional Index and +DI/-DI
        
        Args:
            symbol: Trading symbol
            period: ADX period
            count: Number of ticks to use
            
        Returns:
            Dict with 'adx', 'plus_di', 'minus_di' or None
        """
        # Convert ticks to OHLC candles for ADX
        ohlc_df = self.convert_ticks_to_ohlc(symbol, count, candle_ticks=10)
        
        if ohlc_df is None or len(ohlc_df) < period * 2:
            return None
        
        high = ohlc_df['high'].values
        low = ohlc_df['low'].values
        close = ohlc_df['close'].values
        
        # Calculate True Range
        tr = np.maximum(high[1:] - low[1:],
                       np.maximum(abs(high[1:] - close[:-1]),
                                 abs(low[:-1] - close[:-1])))
        
        # Calculate Directional Movement
        plus_dm = np.maximum(high[1:] - high[:-1], 0)
        minus_dm = np.maximum(low[:-1] - low[1:], 0)
        
        # Smooth TR and DM
        atr = np.convolve(tr, np.ones(period)/period, mode='valid')
        plus_di = 100 * np.convolve(plus_dm, np.ones(period)/period, mode='valid') / (atr + 1e-10)
        minus_di = 100 * np.convolve(minus_dm, np.ones(period)/period, mode='valid') / (atr + 1e-10)
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = np.convolve(dx, np.ones(period)/period, mode='valid')
        
        # Pad arrays
        pad_size = len(close) - len(adx)
        adx = np.concatenate([np.full(pad_size, np.nan), adx])
        plus_di = np.concatenate([np.full(len(close) - len(plus_di), np.nan), plus_di])
        minus_di = np.concatenate([np.full(len(close) - len(minus_di), np.nan), minus_di])
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators on OHLC data
        This is a helper method for strategies
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with added indicator columns
        """
        if df is None or df.empty:
            return df
            
        try:
            # Make a copy to avoid modifying original
            data = df.copy()
            
            # Add basic calculated fields
            data['hl2'] = (data['high'] + data['low']) / 2
            data['hlc3'] = (data['high'] + data['low'] + data['close']) / 3
            data['ohlc4'] = (data['open'] + data['high'] + data['low'] + data['close']) / 4
            
            # Price change
            data['change'] = data['close'] - data['open']
            data['is_green'] = data['change'] > 0
            data['is_red'] = data['change'] < 0
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            return df
    
    def get_swing_high_low(self, df: pd.DataFrame, lookback: int = 20) -> tuple:
        """
        Calculate recent swing high and low for stop loss placement
        
        Args:
            df: DataFrame with OHLC data
            lookback: Number of candles to look back
            
        Returns:
            Tuple of (swing_high, swing_low)
        """
        try:
            if df is None or len(df) < lookback:
                lookback = len(df) if df is not None and len(df) > 0 else 0
                
            if lookback == 0:
                return 0.0, 0.0
                
            recent_data = df.tail(lookback)
            swing_high = recent_data['high'].max()
            swing_low = recent_data['low'].min()
            
            return swing_high, swing_low
            
        except Exception as e:
            logger.error(f"Failed to calculate swing high/low: {e}")
            return 0.0, 0.0
    
    def cleanup(self):
        """Unsubscribe from all symbols"""
        for symbol in self.subscribed_symbols:
            try:
                self.client.unsubscribe_ticks(symbol)
            except Exception as e:
                logger.error(f"Error unsubscribing from {symbol}: {e}")
        
        self.subscribed_symbols.clear()
        logger.info("Data handler cleaned up")
