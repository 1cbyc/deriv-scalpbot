"""
Execution Engine Module - Deriv API Version
Handles contract execution, position management for Deriv.com
Implements binary options CALL/PUT contracts with tick-based duration
"""

from datetime import datetime
from typing import Optional, Dict
import config
import logging

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Execution Engine for Deriv API
    - Places CALL/PUT contracts based on signals
    - Manages open contracts via portfolio
    - Handles contract expiry and early sell
    - Sends telegram alerts for all trading activity
    - Tracks performance metrics
    """
    
    def __init__(self, risk_manager, data_handler, deriv_client, telegram_alerter=None, performance_tracker=None):
        """
        Initialize execution engine
        
        Args:
            risk_manager: Risk manager instance
            data_handler: Data handler instance
            deriv_client: Connected Deriv API client
            telegram_alerter: Optional telegram alerter
            performance_tracker: Optional performance tracker
        """
        self.risk_manager = risk_manager
        self.data_handler = data_handler
        self.client = deriv_client
        self.telegram_alerter = telegram_alerter
        self.performance_tracker = performance_tracker
        self.active_positions = {}  # Track positions by symbol
        
    def place_order(self, symbol: str, signal: int, entry_price: float, 
                   stop_loss: float, take_profit: float, stake_amount: float,
                   strategy_name: str, reason: str) -> Optional[str]:
        """
        Place a Deriv contract (CALL or PUT)
        
        Args:
            symbol: Trading symbol (e.g., 'frxEURUSD', 'R_100')
            signal: 1 for CALL (buy), -1 for PUT (sell)
            entry_price: Current price (for reference)
            stop_loss: Stop loss price (converted to barrier)
            take_profit: Take profit price (converted to barrier)
            stake_amount: Stake amount in USD
            strategy_name: Name of strategy triggering the order
            reason: Reason for the trade
            
        Returns:
            Contract ID or None on failure
        """
        contract_type = "CALL" if signal == 1 else "PUT"
        current_price = self.data_handler.get_current_price(symbol)
        if not current_price:
            logger.error(f"Failed to get current price for {symbol}")
            return None
        
        print(f"\n[EXEC] {contract_type} CONTRACT: {symbol}")
        print(f"       Strategy: {strategy_name}")
        print(f"       Reason: {reason}")
        print(f"       Entry Price: {current_price:.5f} | Stake: ${stake_amount:.2f}")
        print(f"       Duration: {config.CONTRACT_DURATION} {config.CONTRACT_DURATION_UNIT}")
        
        contract = self.client.buy_contract(
            symbol=symbol,
            contract_type=contract_type,
            amount=stake_amount,
            duration=config.CONTRACT_DURATION,
            duration_unit=config.CONTRACT_DURATION_UNIT
        )
        
        if not contract:
            logger.error(f"Failed to buy contract for {symbol}")
            return None
        
        contract_id = contract['contract_id']
        buy_price = contract['buy_price']
        
        print(f"[EXEC] ✓ Contract purchased! ID: {contract_id}")
        print(f"       Buy Price: ${buy_price:.2f}")
        
        self.active_positions[symbol] = {
            'contract_id': contract_id,
            'signal': signal,
            'contract_type': contract_type,
            'entry_price': current_price,
            'buy_price': buy_price,
            'stake_amount': stake_amount,
            'strategy': strategy_name,
            'time': datetime.now(),
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        
        if self.telegram_alerter:
            self.telegram_alerter.alert_trade_opened(
                symbol=symbol,
                action=contract_type,
                price=current_price,
                lot_size=stake_amount,  # Use stake as "lot size"
                sl=stop_loss,
                tp=take_profit,
                strategy=strategy_name,
                ticket=contract_id
            )
        
        return contract_id
    
    def execute_trade_with_price_lock(self, symbol: str, signal: int, 
                                     trigger_price: float, strategy_name: str,
                                     reason: str, swing_high: float, swing_low: float) -> Optional[str]:
        """
        Execute trade with price verification (price-lock mechanism)
        Only executes if current price hasn't moved more than MAX_SLIPPAGE_PIPS
        
        Args:
            symbol: Trading symbol
            signal: 1 for CALL, -1 for PUT
            trigger_price: Price when signal was generated
            strategy_name: Strategy name
            reason: Trade reason
            swing_high: Swing high for SL
            swing_low: Swing low for SL
            
        Returns:
            Contract ID or None if price moved too much
        """
        current_price = self.data_handler.get_current_price(symbol)
        if not current_price:
            logger.error(f"Cannot get current price for {symbol}")
            return None
        
        # Calculate slippage in pips
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        slippage_pips = abs(current_price - trigger_price) / pip_size
        
        if slippage_pips > config.MAX_SLIPPAGE_PIPS:
            logger.warning(f"Price moved {slippage_pips:.1f} pips from trigger - rejecting trade")
            print(f"[EXEC] TRADE REJECTED: {symbol}")
            print(f"       Trigger: {trigger_price:.5f} | Current: {current_price:.5f}")
            print(f"       Slippage: {slippage_pips:.1f} pips (max: {config.MAX_SLIPPAGE_PIPS})")
            return None
        
        # Get stake amount
        stake_amount = self.calculate_stake_amount(symbol)
        
        # Calculate contract type
        contract_type = "CALL" if signal == 1 else "PUT"
        
        # Get fresh proposal with current price
        proposal_params = {
            "proposal": 1,
            "amount": stake_amount,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": self.client.account_info.get('currency', 'USD'),
            "duration": config.CONTRACT_DURATION,
            "duration_unit": config.CONTRACT_DURATION_UNIT,
            "symbol": symbol
        }
        
        try:
            proposal = self.client._send_and_wait(proposal_params)
            
            if not proposal or 'proposal' not in proposal:
                logger.error(f"Proposal failed: {proposal}")
                return None
            
            # Verify proposal price hasn't moved too much from trigger
            proposal_price = float(proposal['proposal']['spot'])
            proposal_slippage_pips = abs(proposal_price - trigger_price) / pip_size
            
            if proposal_slippage_pips > config.MAX_SLIPPAGE_PIPS:
                logger.warning(f"Proposal price slippage {proposal_slippage_pips:.1f} pips - rejecting")
                print(f"[EXEC] PROPOSAL REJECTED: {symbol}")
                print(f"       Trigger: {trigger_price:.5f} | Proposal: {proposal_price:.5f}")
                print(f"       Slippage: {proposal_slippage_pips:.1f} pips")
                return None
            
            # Price is acceptable - execute trade
            logger.info(f"Price-lock verified: {slippage_pips:.1f} pips slippage (acceptable)")
            return self.execute_trade(symbol, signal, strategy_name, reason, swing_high, swing_low)
            
        except Exception as e:
            logger.error(f"Error in price-lock verification: {e}")
            return None
    
    def close_position(self, symbol: str, reason: str = "Manual close") -> bool:
        """
        Close an open contract for a symbol (sell before expiry)
        
        Args:
            symbol: Trading symbol
            reason: Reason for closing
            
        Returns:
            True if closed successfully
        """
        if symbol not in self.active_positions:
            logger.warning(f"No open position for {symbol}")
            return False
        
        position = self.active_positions[symbol]
        contract_id = position['contract_id']
        
        print(f"\n[EXEC] CLOSING CONTRACT: {symbol} | ID: {contract_id}")
        print(f"       Reason: {reason}")
        
        # Sell the contract
        sell_result = self.client.sell_contract(contract_id)
        
        if not sell_result:
            logger.error(f"Failed to sell contract {contract_id}")
            return False
        
        # Calculate profit/loss
        sell_price = sell_result.get('sold_for', 0)
        profit = sell_price - position['buy_price']
        
        # Calculate duration
        time_diff = datetime.now() - position['time']
        minutes = int(time_diff.total_seconds() / 60)
        seconds = int(time_diff.total_seconds() % 60)
        duration = f"{minutes}m {seconds}s"
        
        print(f"[EXEC] ✓ Contract sold | Sell Price: ${sell_price:.2f} | P/L: ${profit:.2f}")
        
        # Record trade result
        self.risk_manager.record_trade_result(
            symbol=symbol,
            signal=position['signal'],
            entry_price=position['buy_price'],
            exit_price=sell_price,
            lot_size=position['stake_amount'],
            profit=profit
        )
        
        # Record performance if tracker available
        if self.performance_tracker:
            duration_seconds = time_diff.total_seconds()
            self.performance_tracker.record_trade(
                strategy=position['strategy'],
                symbol=symbol,
                profit=profit,
                stake=position['stake_amount'],
                duration=duration_seconds,
                entry_time=position['time'],
                contract_type=position['contract_type'],
                reason=reason
            )
        
        # Send Telegram alert
        if self.telegram_alerter:
            self.telegram_alerter.alert_trade_closed(
                symbol=symbol,
                action=position['contract_type'],
                entry_price=position['entry_price'],
                exit_price=self.data_handler.get_current_price(symbol) or position['entry_price'],
                lot_size=position['stake_amount'],
                profit=profit,
                duration=duration,
                ticket=contract_id
            )
        
        # Remove from active positions
        del self.active_positions[symbol]
        
        return True
    
    def check_and_flip_position(self, symbol: str, new_signal: int, 
                               strategy_name: str, reason: str,
                               swing_high: float, swing_low: float) -> Optional[str]:
        """
        Check if there's an opposite position and flip it
        
        Args:
            symbol: Trading symbol
            new_signal: New signal (1 or -1)
            strategy_name: Strategy generating the signal
            reason: Reason for the signal
            swing_high: Swing high for SL calculation
            swing_low: Swing low for SL calculation
            
        Returns:
            Contract ID of new position or None
        """
        if symbol not in self.active_positions:
            return None
        
        current_position = self.active_positions[symbol]
        current_signal = current_position['signal']
        
        # Check if signal is opposite
        if current_signal == new_signal:
            return None  # Same direction, no flip needed
        
        print(f"\n[EXEC] FLIP SIGNAL DETECTED for {symbol}")
        print(f"       Current: {current_position['contract_type']}")
        print(f"       New: {'CALL' if new_signal == 1 else 'PUT'}")
        
        # Send Telegram alert
        if self.telegram_alerter:
            self.telegram_alerter.alert_position_flipped(
                symbol=symbol,
                old_action=current_position['contract_type'],
                new_action='CALL' if new_signal == 1 else 'PUT',
                reason=reason
            )
        
        # Close current position
        if self.close_position(symbol, reason="Opposite signal - Flip"):
            # Open new position in opposite direction
            return self.execute_trade(symbol, new_signal, strategy_name, reason, swing_high, swing_low)
        
        return None
    
    def execute_trade(self, symbol: str, signal: int, strategy_name: str, 
                     reason: str, swing_high: float, swing_low: float) -> Optional[str]:
        """
        Execute a complete trade with all risk management
        
        Args:
            symbol: Trading symbol
            signal: 1 for CALL, -1 for PUT
            strategy_name: Strategy name
            reason: Trade reason
            swing_high: Swing high for SL
            swing_low: Swing low for SL
            
        Returns:
            Contract ID or None
        """
        # Check position limits
        if not self.risk_manager.check_position_limits(symbol):
            return None
        
        # Get current price
        current_price = self.data_handler.get_current_price(symbol)
        if not current_price:
            logger.error(f"Cannot get current price for {symbol}")
            return None
        
        # Calculate stake amount (convert lot size to USD stake)
        # For Deriv, we'll use a fixed stake or percentage of balance
        stake_amount = self.calculate_stake_amount(symbol)
        
        # Calculate stop loss and take profit (for reference/future barrier support)
        stop_loss = self.risk_manager.calculate_stop_loss(
            symbol, signal, swing_high, swing_low, current_price
        )
        
        take_profit = self.risk_manager.calculate_take_profit(signal, current_price, stop_loss)
        
        print(f"\n[EXEC] TRADE SETUP: {symbol}")
        print(f"       Stake: ${stake_amount:.2f}")
        print(f"       Expected SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
        
        # Place the order
        contract_id = self.place_order(
            symbol=symbol,
            signal=signal,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            stake_amount=stake_amount,
            strategy_name=strategy_name,
            reason=reason
        )
        
        return contract_id
    
    def calculate_stake_amount(self, symbol: str) -> float:
        """
        Calculate stake amount for Deriv contract
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Stake amount in USD
        """
        # Get base stake from config
        base_stake = config.BASE_STAKE_USD
        
        # Apply Max Profit Builder logic
        if self.risk_manager.consecutive_wins >= config.BUILDER_WINS_THRESHOLD:
            base_stake *= (1 + config.BUILDER_INCREMENT)
            
            # Cap at maximum stake
            if base_stake > config.MAX_STAKE_USD:
                base_stake = config.MAX_STAKE_USD
            
            logger.info(f"Stake increased to ${base_stake:.2f} after {self.risk_manager.consecutive_wins} wins")
            self.risk_manager.consecutive_wins = 0
        
        return base_stake
    
    def monitor_positions(self):
        """
        Monitor open positions via portfolio
        Update tracking and check for expired contracts
        """
        try:
            portfolio = self.client.get_portfolio()
            
            if portfolio is None:
                return
            
            # Get list of active contract IDs
            active_contract_ids = {c['contract_id'] for c in portfolio if c.get('contract_id')}
            
            # Check if any of our tracked positions have expired
            symbols_to_remove = []
            for symbol, position in self.active_positions.items():
                contract_id = position['contract_id']
                
                # If contract is no longer in portfolio, it has expired/closed
                if contract_id not in active_contract_ids:
                    # Contract has expired or been closed
                    logger.info(f"Contract {contract_id} for {symbol} has expired")
                    
                    # Try to get final payout from contract details
                    # For now, just remove from tracking
                    symbols_to_remove.append(symbol)
            
            # Remove expired contracts
            for symbol in symbols_to_remove:
                del self.active_positions[symbol]
                
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def close_all_positions(self):
        """
        Close all open positions (for shutdown)
        """
        if not self.active_positions:
            return
        
        print("\n[EXEC] Closing all positions...")
        
        symbols = list(self.active_positions.keys())
        for symbol in symbols:
            self.close_position(symbol, reason="Bot shutdown")
    
    def get_position_count(self) -> int:
        """Get number of active positions"""
        return len(self.active_positions)
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an active position for symbol"""
        return symbol in self.active_positions
