"""
Risk Manager Module - Deriv Version
Handles stake sizing, stop loss, take profit, and risk management
Implements the "Max Profit Builder" logic for dynamic stake sizing
"""

from typing import Tuple, Optional
import config
import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk Management for the Scalping Bot
    - Dynamic lot sizing with "Max Profit Builder"
    - Stop Loss calculation based on swing high/low
    - Take Profit calculation using Risk-Reward ratio
    - Position tracking and validation
    """
    
    def __init__(self):
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.total_wins = 0
        self.total_losses = 0
        self.current_stake = config.BASE_STAKE_USD
        self.trade_history = []
        
    def calculate_lot_size(self, symbol: str) -> float:
        """
        Calculate dynamic stake size based on "Max Profit Builder" logic
        Increase stake by 10% after every 3 consecutive wins
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Stake amount in USD
        """
        # Check if we've hit the threshold for increasing stake
        if self.consecutive_wins >= config.BUILDER_WINS_THRESHOLD:
            # Increase stake by 10%
            self.current_stake *= (1 + config.BUILDER_INCREMENT)
            
            # Cap at maximum stake
            if self.current_stake > config.MAX_STAKE_USD:
                self.current_stake = config.MAX_STAKE_USD
            
            # Reset consecutive wins counter after increase
            logger.info(f"Stake increased to ${self.current_stake:.2f} after {self.consecutive_wins} wins")
            self.consecutive_wins = 0
        
        return self.current_stake
    
    def calculate_stop_loss(self, symbol: str, signal: int, swing_high: float, 
                           swing_low: float, entry_price: float) -> float:
        """
        Calculate stop loss based on swing high/low +/- buffer pips
        (For Deriv, this is mainly for reference as contracts have fixed duration)
        
        Args:
            symbol: Trading symbol
            signal: 1 for buy, -1 for sell
            swing_high: Recent swing high
            swing_low: Recent swing low
            entry_price: Entry price for the trade
            
        Returns:
            Stop loss price
        """
        # Estimate pip size (for most forex pairs)
        point = 0.00001  # Default for 5-digit quotes
        if "JPY" in symbol:
            point = 0.001  # JPY pairs are 3-digit
        
        buffer = config.SWING_BUFFER_PIPS * point * 10  # Convert pips to price
        
        if signal == 1:  # Buy - SL below swing low
            sl_price = swing_low - buffer
        else:  # Sell - SL above swing high
            sl_price = swing_high + buffer
        
        # Ensure SL is not too close or too far from entry
        min_sl_distance = 5 * point * 10  # Minimum 5 pips
        max_sl_distance = 50 * point * 10  # Maximum 50 pips
        
        if signal == 1:
            sl_distance = entry_price - sl_price
            if sl_distance < min_sl_distance:
                sl_price = entry_price - min_sl_distance
            elif sl_distance > max_sl_distance:
                sl_price = entry_price - max_sl_distance
        else:
            sl_distance = sl_price - entry_price
            if sl_distance < min_sl_distance:
                sl_price = entry_price + min_sl_distance
            elif sl_distance > max_sl_distance:
                sl_price = entry_price + max_sl_distance
        
        return sl_price
    
    def calculate_take_profit(self, signal: int, entry_price: float, stop_loss: float) -> float:
        """
        Calculate take profit using Risk-Reward ratio (1:1.5)
        
        Args:
            signal: 1 for buy, -1 for sell
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            
        Returns:
            Take profit price
        """
        # Calculate risk (distance from entry to SL)
        if signal == 1:  # Buy
            risk = entry_price - stop_loss
            tp_price = entry_price + (risk * config.RISK_REWARD_RATIO)
        else:  # Sell
            risk = stop_loss - entry_price
            tp_price = entry_price - (risk * config.RISK_REWARD_RATIO)
        
        return tp_price
    
    def record_trade_result(self, symbol: str, signal: int, entry_price: float, 
                           exit_price: float, lot_size: float, profit: float):
        """
        Record trade result and update win/loss streaks
        
        Args:
            symbol: Trading symbol
            signal: 1 for buy, -1 for sell
            entry_price: Entry price
            exit_price: Exit price
            lot_size: Lot size used
            profit: Profit/loss amount
        """
        is_win = profit > 0
        
        trade_record = {
            'symbol': symbol,
            'signal': 'BUY' if signal == 1 else 'SELL',
            'entry': entry_price,
            'exit': exit_price,
            'lot_size': lot_size,
            'profit': profit,
            'result': 'WIN' if is_win else 'LOSS'
        }
        
        self.trade_history.append(trade_record)
        
        # Update win/loss counters
        if is_win:
            self.total_wins += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            print(f"[RISK] Trade WIN: {symbol} +${profit:.2f} | Streak: {self.consecutive_wins} wins")
        else:
            self.total_losses += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            
            # Reset stake to base after a loss
            self.current_stake = config.BASE_STAKE_USD
            print(f"[RISK] Trade LOSS: {symbol} -${abs(profit):.2f} | Stake reset to ${self.current_stake:.2f}")
    
    def check_position_limits(self, symbol: str) -> bool:
        """
        Check if we can open a new position based on limits
        (For Deriv, this is simplified as we track positions internally)
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if we can open a position, False otherwise
        """
        # This method will be called by execution engine which tracks positions
        # For now, just return True - execution engine handles actual tracking
        return True
    
    def get_pips_value(self, symbol: str) -> float:
        """
        Get pip value for a symbol (estimated)
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Value of 1 pip
        """
        # Estimate based on common symbol formats
        if "JPY" in symbol:
            return 0.01  # JPY pairs
        else:
            return 0.0001  # Most forex pairs
    
    def calculate_risk_amount(self, symbol: str, stake_amount: float, 
                             entry_price: float, stop_loss: float) -> float:
        """
        Calculate the dollar amount at risk for a trade
        (For Deriv contracts, risk is the stake amount)
        
        Args:
            symbol: Trading symbol
            stake_amount: Stake amount in USD
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Risk amount in account currency
        """
        # For Deriv contracts, the maximum loss is the stake amount
        return stake_amount
    
    def get_statistics(self) -> dict:
        """
        Get current risk management statistics
        
        Returns:
            Dictionary with statistics
        """
        total_trades = self.total_wins + self.total_losses
        win_rate = (self.total_wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'total_wins': self.total_wins,
            'total_losses': self.total_losses,
            'win_rate': win_rate,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'current_lot_size': self.current_stake  # Compatible with old interface
        }
