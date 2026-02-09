"""
Telegram Alert Adapter
Bridges the MT5 Scalping Bot with the existing trade-alerts Telegram system
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional


class TelegramAlertAdapter:
    """
    Adapter to use the existing trade-alerts TelegramNotifier with the scalping bot
    """
    
    def __init__(self, telegram_notifier):
        self.notifier = telegram_notifier
        self.enabled = telegram_notifier is not None
    
    def _send_async(self, message: str):
        """Helper to run async send_message in sync context"""
        if not self.enabled:
            return
        
        try:
            asyncio.run(self.notifier.send_message(message))
        except Exception as e:
            print(f"[TELEGRAM] Failed to send message: {e}")
    
    def alert_bot_started(self):
        """Alert when bot starts"""
        message = f"""
🤖 <b>MT5 SCALPING BOT STARTED</b>

Bot has been initialized and is now monitoring the markets.

⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_async(message)
    
    def alert_bot_stopped(self, stats: Dict = None):
        """Alert when bot stops"""
        message = f"""
⏹ <b>MT5 SCALPING BOT STOPPED</b>

Bot has been shut down gracefully.

⏰ Stopped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if stats:
            message += f"\n\n📊 Final Statistics:\n"
            message += f"Total Trades: {stats.get('total_trades', 0)}\n"
            message += f"Win Rate: {stats.get('win_rate', 0):.1f}%\n"
            message += f"Net P/L: ${stats.get('net_pl', 0):.2f}"
        
        self._send_async(message)
    
    def alert_trade_opened(self, symbol: str, action: str, price: float,
                          lot_size: float, sl: float, tp: float,
                          strategy: str, ticket: int):
        """Alert when a new trade is opened"""
        message = f"""
🔵 <b>TRADE OPENED</b>

📊 Symbol: <code>{symbol}</code>
🎯 Action: <b>{action}</b>
💰 Price: <code>{price:.5f}</code>
📦 Lot Size: <code>{lot_size:.2f}</code>

🛑 Stop Loss: <code>{sl:.5f}</code>
🎯 Take Profit: <code>{tp:.5f}</code>

📈 Strategy: {strategy}
🎫 Ticket: <code>{ticket}</code>

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_async(message)
    
    def alert_trade_closed(self, symbol: str, action: str, entry_price: float,
                          exit_price: float, lot_size: float, profit: float,
                          duration: str, ticket: int):
        """Alert when a trade is closed"""
        emoji = "🟢" if profit > 0 else "🔴"
        result = "PROFIT" if profit > 0 else "LOSS"
        
        message = f"""
{emoji} <b>TRADE CLOSED - {result}</b>

📊 Symbol: <code>{symbol}</code>
🎯 Action: <b>{action}</b>

💵 Entry: <code>{entry_price:.5f}</code>
💵 Exit: <code>{exit_price:.5f}</code>
📦 Lot Size: <code>{lot_size:.2f}</code>

💰 P/L: <b>${profit:.2f}</b>
⏱ Duration: {duration}
🎫 Ticket: <code>{ticket}</code>

⏰ Closed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_async(message)
    
    def alert_position_flipped(self, symbol: str, old_action: str,
                              new_action: str, reason: str):
        """Alert when a position is flipped"""
        message = f"""
🔄 <b>POSITION FLIPPED</b>

📊 Symbol: <code>{symbol}</code>
⚠️ Old Position: <b>{old_action}</b>
🔄 New Position: <b>{new_action}</b>

📝 Reason: {reason}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_async(message)
    
    def alert_margin_level(self, margin_level: float, equity: float, margin: float):
        """Alert on margin level"""
        if margin_level <= 100:
            alert_emoji = '🚨'
            alert_text = 'CRITICAL MARGIN LEVEL!'
            action_text = '<i>Consider closing positions immediately!</i>'
        elif margin_level <= 150:
            alert_emoji = '⚠️'
            alert_text = 'Low Margin Level Warning'
            action_text = '<i>Monitor positions carefully</i>'
        else:
            return
        
        message = f"""
{alert_emoji} <b>{alert_text}</b>

📊 Margin Level: <b>{margin_level:.2f}%</b>
💰 Equity: ${equity:.2f}
💳 Margin Used: ${margin:.2f}

⚠️ {action_text}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_async(message)
    
    def alert_connection_error(self, error_message: str):
        """Alert on MT5 connection error"""
        message = f"""
🔌 <b>CONNECTION ERROR</b>

❌ Failed to connect to MT5 terminal

Error: {error_message}

⚠️ Bot may not be functioning properly

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_async(message)
