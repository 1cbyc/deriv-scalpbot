"""
Logger Module
Custom logging for MT5 Scalping Bot
Outputs signals and trade results with timestamps
"""

import logging
from datetime import datetime
import config


class BotLogger:
    """
    Custom logger for the scalping bot
    Outputs to console and optionally to file
    """
    
    def __init__(self):
        self.logger = logging.getLogger('MT5ScalpBot')
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if config.CONSOLE_OUTPUT:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if config.LOG_TO_FILE:
            file_handler = logging.FileHandler(config.LOG_FILE_PATH)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def signal(self, symbol: str, strategy: str, signal: int, reason: str):
        """
        Log a trading signal
        
        Args:
            symbol: Trading symbol
            strategy: Strategy name
            signal: 1 (Buy), -1 (Sell), 0 (Neutral)
            reason: Signal reason
        """
        signal_type = "BUY" if signal == 1 else "SELL" if signal == -1 else "NEUTRAL"
        
        message = f"SIGNAL | {symbol:7s} | {strategy:30s} | {signal_type:7s} | {reason}"
        
        if signal != 0:
            self.logger.info(message)
        else:
            self.logger.debug(message)
    
    def trade(self, symbol: str, action: str, price: float, lot_size: float, 
             profit: float = None, ticket: int = None):
        """
        Log a trade execution
        
        Args:
            symbol: Trading symbol
            action: OPEN_BUY, OPEN_SELL, CLOSE, etc.
            price: Execution price
            lot_size: Position size
            profit: Profit/loss if closing
            ticket: Order ticket number
        """
        if profit is not None:
            message = f"TRADE  | {symbol:7s} | {action:10s} | Price: {price:.5f} | Lot: {lot_size:.2f} | P/L: ${profit:.2f}"
        else:
            message = f"TRADE  | {symbol:7s} | {action:10s} | Price: {price:.5f} | Lot: {lot_size:.2f}"
        
        if ticket:
            message += f" | Ticket: {ticket}"
        
        self.logger.info(message)
    
    def status(self, message: str):
        """Log status update"""
        self.logger.info(f"STATUS | {message}")
    
    def statistics(self, stats: dict):
        """
        Log performance statistics
        
        Args:
            stats: Dictionary with statistics
        """
        self.logger.info("=" * 80)
        self.logger.info("PERFORMANCE STATISTICS")
        self.logger.info("-" * 80)
        
        for key, value in stats.items():
            self.logger.info(f"  {key:30s}: {value}")
        
        self.logger.info("=" * 80)
    
    def separator(self):
        """Log a separator line"""
        self.logger.info("-" * 80)
    
    def header(self, text: str):
        """Log a header"""
        self.logger.info("=" * 80)
        self.logger.info(f"  {text}")
        self.logger.info("=" * 80)
