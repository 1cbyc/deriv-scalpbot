"""
Deriv Scalping Bot - Main Engine
High-Frequency Trading Bot for Deriv API
Multi-Strategy Scalping Engine using WebSocket streaming
"""

import time
import signal
import sys
from datetime import datetime
from typing import Dict, List

import config
from deriv_api import DerivAPI
from data_handler import DataHandler
from risk_manager import RiskManager
from execution import ExecutionEngine
from logger import BotLogger
from performance_tracker import PerformanceTracker
from strategies import (
    StrategyA_TripleEMA,
    StrategyB_ADXDI,
    StrategyC_Bollinger,
    StrategyD_Stochastic,
    StrategyE_Breakout
)

# Import Telegram alerts from existing trade-alerts system
telegram_alerter = None
if config.ENABLE_TELEGRAM_ALERTS:
    try:
        import sys
        sys.path.insert(0, 'trade-alerts/src')
        from notifiers.telegram_bot import TelegramNotifier
        from telegram_adapter import TelegramAlertAdapter
        
        telegram_notifier = TelegramNotifier(
            bot_token=config.TELEGRAM_BOT_TOKEN,
            chat_id=config.TELEGRAM_CHAT_ID
        )
        telegram_alerter = TelegramAlertAdapter(telegram_notifier)
        print("[TELEGRAM] ✓ Using existing trade-alerts Telegram system")
    except ImportError as e:
        print(f"[WARNING] Could not load trade-alerts Telegram: {e}")


class DerivScalpBot:
    """
    Main scalping bot engine for Deriv API
    Monitors multiple symbols via WebSocket and executes CALL/PUT contracts
    """
    
    def __init__(self):
        self.logger = BotLogger()
        
        # Initialize Deriv API client
        self.logger.info("Initializing Deriv API client...")
        self.deriv_client = DerivAPI(
            app_id=config.DERIV_APP_ID,
            api_token=config.DERIV_API_TOKEN
        )
        
        # Initialize components
        self.data_handler = DataHandler(self.deriv_client)
        self.risk_manager = RiskManager()
        self.performance_tracker = PerformanceTracker()
        
        # Store telegram alerter reference
        self.telegram = telegram_alerter
        
        # Initialize execution engine with Deriv client
        self.execution = ExecutionEngine(
            self.risk_manager, 
            self.data_handler, 
            self.deriv_client, 
            telegram_alerter,
            self.performance_tracker
        )
        
        # Initialize strategies
        self.strategies = [
            StrategyA_TripleEMA(),
            StrategyB_ADXDI(),
            StrategyC_Bollinger(),
            StrategyD_Stochastic(),
            StrategyE_Breakout()
        ]
        
        self.running = False
        self.connected = False
        
        # Daily loss limit tracking
        self.starting_balance = None
        self.daily_pnl = 0.0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.warning("\nShutdown signal received. Initiating graceful shutdown...")
        self.shutdown()
    
    def connect_deriv(self) -> bool:
        """
        Initialize connection to Deriv API
        
        Returns:
            True if connection successful
        """
        self.logger.info("Connecting to Deriv API...")
        
        # Validate credentials
        if not config.DERIV_APP_ID or not config.DERIV_API_TOKEN:
            error_msg = "Missing Deriv credentials. Set DERIV_APP_ID and DERIV_API_TOKEN in .env"
            self.logger.error(error_msg)
            if self.telegram:
                self.telegram.alert_connection_error(error_msg)
            return False
        
        # Validate that credentials are not placeholder values
        if config.DERIV_APP_ID == 'your_app_id_here' or config.DERIV_API_TOKEN == 'your_api_token_here':
            error_msg = "Please update DERIV_APP_ID and DERIV_API_TOKEN in .env with your actual credentials"
            self.logger.error(error_msg)
            if self.telegram:
                self.telegram.alert_connection_error(error_msg)
            return False
        
        # Connect via WebSocket
        if not self.deriv_client.connect():
            error_msg = "Failed to connect to Deriv WebSocket"
            self.logger.error(error_msg)
            if self.telegram:
                self.telegram.alert_connection_error(error_msg)
            return False
        
        # Get account info
        account = self.deriv_client.account_info
        if not account:
            error_msg = "Failed to retrieve account information"
            self.logger.error(error_msg)
            return False
        
        # Get balance
        balance = self.deriv_client.get_balance()
        
        self.logger.separator()
        self.logger.info("✓ Connected to Deriv API")
        self.logger.info(f"Account ID: {account.get('loginid', 'Unknown')}")
        self.logger.info(f"Currency: {account.get('currency', 'USD')}")
        self.logger.info(f"Balance: ${balance:.2f}")
        self.logger.separator()
        
        self.connected = True
        return True
    
    def initialize_symbols(self) -> bool:
        """
        Initialize all trading symbols with historical data and subscriptions
        
        Returns:
            True if all symbols initialized successfully
        """
        self.logger.info(f"Initializing {len(config.TRADING_SYMBOLS)} symbols...")
        
        success_count = 0
        for symbol in config.TRADING_SYMBOLS:
            if self.data_handler.initialize_symbol(symbol):
                self.logger.info(f"✓ {symbol:15s} - Historical data loaded and subscribed")
                success_count += 1
            else:
                self.logger.error(f"✗ {symbol:15s} - Failed to initialize")
        
        self.logger.separator()
        
        if success_count == 0:
            self.logger.error("No symbols initialized successfully")
            return False
        
        if success_count < len(config.TRADING_SYMBOLS):
            self.logger.warning(f"Only {success_count}/{len(config.TRADING_SYMBOLS)} symbols initialized")
        
        return True
    
    def process_symbol(self, symbol: str):
        """
        Process a single symbol: analyze data, run strategies, execute trades
        
        Args:
            symbol: Trading symbol to process
        """
        try:
            # Get tick data as DataFrame
            tick_df = self.data_handler.get_tick_data(symbol, count=500)
            
            if tick_df is None or len(tick_df) < 50:
                return
            
            # Convert ticks to OHLC for strategies that need candles
            ohlc_df = self.data_handler.convert_ticks_to_ohlc(symbol, count=500, candle_ticks=10)
            
            if ohlc_df is None or len(ohlc_df) < 20:
                return
            
            # Calculate indicators
            ohlc_df = self.data_handler.calculate_indicators(ohlc_df)
            
            # Get swing high/low for stop loss
            swing_high, swing_low = self.data_handler.get_swing_high_low(ohlc_df, lookback=20)
            
            # Get current price
            current_price = self.data_handler.get_current_price(symbol)
            if not current_price:
                return
            
            # Run each strategy
            for strategy in self.strategies:
                try:
                    signal, reason = strategy.generate_signal(ohlc_df)
                    
                    # Log signal (debug level for neutral signals)
                    if signal != 0:
                        self.logger.signal(symbol, strategy.name, signal, reason)
                    
                    # If we have a signal, check if we need to act
                    if signal != 0:
                        # Check if we have an opposite position - flip if needed
                        if self.execution.has_position(symbol):
                            current_signal = self.execution.active_positions[symbol]['signal']
                            
                            if current_signal != signal:
                                # Opposite signal - flip position
                                self.execution.check_and_flip_position(
                                    symbol=symbol,
                                    new_signal=signal,
                                    strategy_name=strategy.name,
                                    reason=reason,
                                    swing_high=swing_high,
                                    swing_low=swing_low
                                )
                        else:
                            # No position - open new trade
                            self.execution.execute_trade(
                                symbol=symbol,
                                signal=signal,
                                strategy_name=strategy.name,
                                reason=reason,
                                swing_high=swing_high,
                                swing_low=swing_low
                            )
                
                except Exception as e:
                    self.logger.error(f"Error processing {strategy.name} for {symbol}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {e}")
    
    def run(self):
        """
        Main bot loop
        Monitors real-time tick data and executes strategies
        """
        self.logger.header("DERIV SCALPING BOT STARTED")
        self.logger.info(f"Monitoring {len(config.TRADING_SYMBOLS)} symbols:")
        self.logger.info(f"{', '.join(config.TRADING_SYMBOLS)}")
        self.logger.info(f"Strategies: {len(self.strategies)}")
        self.logger.info(f"Contract Duration: {config.CONTRACT_DURATION} {config.CONTRACT_DURATION_UNIT}")
        self.logger.info(f"Base Stake: ${config.BASE_STAKE_USD:.2f}")
        self.logger.separator()
        
        # Get starting balance
        self.starting_balance = self.deriv_client.get_balance()
        self.logger.info(f"Starting balance: ${self.starting_balance:.2f}")
        self.logger.info(f"Daily loss limit: ${config.DAILY_LOSS_LIMIT_USD:.2f}")
        self.logger.separator()
        
        # Send Telegram notification
        if self.telegram:
            self.telegram.alert_bot_started()
        
        self.running = True
        iteration = 0
        last_status_time = time.time()
        last_analysis_time = {}  # Track last analysis time per symbol
        last_health_check = time.time()
        
        try:
            while self.running:
                iteration += 1
                current_time = time.time()
                
                # Check daily loss limit (every loop)
                try:
                    current_balance = self.deriv_client.get_balance()
                    self.daily_pnl = current_balance - self.starting_balance
                    
                    if self.daily_pnl <= -config.DAILY_LOSS_LIMIT_USD:
                        self.logger.error(f"Daily loss limit hit: ${self.daily_pnl:.2f}")
                        if self.telegram:
                            msg = f"⛔️ DAILY LOSS LIMIT HIT: ${self.daily_pnl:.2f}\nStarting: ${self.starting_balance:.2f}\nCurrent: ${current_balance:.2f}\nBot shutting down..."
                            self.telegram._send_async(msg)
                        self.shutdown()
                        break
                except Exception as e:
                    self.logger.error(f"Error checking balance: {e}")
                
                # Health check every 60 seconds
                if current_time - last_health_check >= 60:
                    # Check WebSocket connection
                    if not self.deriv_client.connected:
                        self.logger.error("WebSocket disconnected - reconnection in progress...")
                        if self.telegram:
                            self.telegram.alert_connection_error("WebSocket disconnected")
                        # Deriv API will auto-reconnect
                    
                    # Check data freshness
                    for symbol in config.TRADING_SYMBOLS:
                        price = self.data_handler.get_current_price(symbol)
                        if price is None:
                            self.logger.warning(f"No data for {symbol} - may need resubscription")
                    
                    last_health_check = current_time
                
                # Process each symbol on a regular interval
                for symbol in config.TRADING_SYMBOLS:
                    try:
                        # Analyze each symbol every 10 seconds (avoid over-trading)
                        last_time = last_analysis_time.get(symbol, 0)
                        
                        if current_time - last_time >= config.ANALYSIS_INTERVAL_SECONDS:
                            self.process_symbol(symbol)
                            last_analysis_time[symbol] = current_time
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                
                # Monitor existing positions (check for expirations)
                self.execution.monitor_positions()
                
                # Print status every 60 seconds
                if current_time - last_status_time >= 60:
                    self.print_status()
                    last_status_time = current_time
                
                # Sleep for tick interval (small delay between iterations)
                time.sleep(config.TICK_SLEEP_INTERVAL)
        
        except Exception as e:
            self.logger.error(f"Fatal error in main loop: {e}")
            self.shutdown()
    
    def print_status(self):
        """Print current bot status with performance metrics"""
        try:
            balance = self.deriv_client.get_balance()
            stats = self.risk_manager.get_statistics()
            
            self.logger.separator()
            self.logger.status(f"Balance: ${balance:.2f} | Daily P/L: ${self.daily_pnl:.2f}")
            self.logger.status(f"Active Contracts: {self.execution.get_position_count()}")
            self.logger.status(f"Total Trades: {stats['total_trades']} | Wins: {stats['total_wins']} | Losses: {stats['total_losses']}")
            self.logger.status(f"Win Rate: {stats['win_rate']:.1f}%")
            self.logger.status(f"Win Streak: {stats['consecutive_wins']} | Loss Streak: {stats['consecutive_losses']}")
            
            # Add performance summary if tracker has data
            if self.performance_tracker:
                # Get best strategies
                best_strategies = self.performance_tracker.get_best_strategies(top_n=2, metric='roi')
                if best_strategies:
                    self.logger.info("Top Strategies:")
                    for strat in best_strategies:
                        self.logger.info(f"  {strat['strategy']}: {strat['win_rate']:.1f}% WR, {strat['roi']:.1f}% ROI, {strat['trades']} trades")
                
                # Get best symbols
                best_symbols = self.performance_tracker.get_best_symbols(top_n=2, metric='roi')
                if best_symbols:
                    self.logger.info("Top Symbols:")
                    for sym in best_symbols:
                        self.logger.info(f"  {sym['symbol']}: {sym['win_rate']:.1f}% WR, {sym['roi']:.1f}% ROI, {sym['trades']} trades")
            
            self.logger.separator()
        except Exception as e:
            self.logger.error(f"Error printing status: {e}")
    
    def shutdown(self):
        """
        Graceful shutdown sequence
        """
        self.logger.header("INITIATING SHUTDOWN SEQUENCE")
        
        self.running = False
        
        # Close all positions if configured
        if config.CLOSE_ALL_ON_SHUTDOWN:
            self.logger.info("Closing all open contracts...")
            self.execution.close_all_positions()
        
        # Print final statistics
        self.logger.header("FINAL STATISTICS")
        stats = self.risk_manager.get_statistics()
        self.logger.statistics(stats)
        
        # Print performance report if available
        if self.performance_tracker:
            self.logger.separator()
            report = self.performance_tracker.generate_performance_report()
            print(report)
        
        # Get final balance
        try:
            final_balance = self.deriv_client.get_balance()
            self.logger.info(f"Final Balance: ${final_balance:.2f}")
            self.logger.info(f"Session P/L: ${final_balance - self.starting_balance:.2f}" if self.starting_balance else "")
        except:
            pass
        
        # Send Telegram notification with performance data
        if self.telegram:
            telegram_stats = {
                'total_trades': stats['total_trades'],
                'win_rate': stats['win_rate'],
                'net_pl': final_balance - self.starting_balance if self.starting_balance and final_balance else 0
            }
            self.telegram.alert_bot_stopped(telegram_stats)
            
            # Send performance summary if tracker has data
            if self.performance_tracker:
                best_strats = self.performance_tracker.get_best_strategies(top_n=2)
                worst_strats = self.performance_tracker.get_worst_strategies(bottom_n=1)
                best_syms = self.performance_tracker.get_best_symbols(top_n=2)
                
                if best_strats or best_syms:
                    perf_msg = "📊 <b>SESSION PERFORMANCE</b>\n\n"
                    
                    if best_strats:
                        perf_msg += "🏆 Top Strategies:\n"
                        for s in best_strats:
                            perf_msg += f"  • {s['strategy']}: {s['win_rate']:.1f}% WR, ${s['total_pnl']:.2f}\n"
                    
                    if best_syms:
                        perf_msg += "\n🎯 Top Symbols:\n"
                        for s in best_syms:
                            perf_msg += f"  • {s['symbol']}: {s['win_rate']:.1f}% WR, ${s['total_pnl']:.2f}\n"
                    
                    if worst_strats:
                        perf_msg += "\n⚠️ Needs Attention:\n"
                        for s in worst_strats:
                            perf_msg += f"  • {s['strategy']}: {s['win_rate']:.1f}% WR\n"
                    
                    self.telegram._send_async(perf_msg)
        
        # Disconnect from Deriv
        if self.connected:
            self.logger.info("Disconnecting from Deriv API...")
            # WebSocket will close automatically
        
        self.logger.header("BOT SHUTDOWN COMPLETE")
        
        sys.exit(0)


def main():
    """
    Main entry point
    """
    # Create bot instance
    bot = DerivScalpBot()
    
    # Connect to Deriv API
    if not bot.connect_deriv():
        bot.logger.error("Failed to connect to Deriv API. Exiting...")
        return
    
    # Initialize symbols
    if not bot.initialize_symbols():
        bot.logger.error("Symbol initialization failed. Exiting...")
        return
    
    # Run the bot
    bot.run()


if __name__ == "__main__":
    main()
