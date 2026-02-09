# MT5 SCALPING BOT - COMPLETE INTEGRATION GUIDE

## Project Overview

A professional multi-strategy scalping bot for MetaTrader 5, fully integrated with Apple Silicon M1 architecture and comprehensive Telegram alert system.

### Key Features
- **5 Advanced Scalping Strategies** running in parallel
- **High-Frequency Execution** with 0.1-second tick monitoring
- **Telegram Alerts** using existing trade-alerts infrastructure
- **M1 Mac Native** setup with automated installation
- **Major Forex Pairs** - EURUSD, USDJPY, GBPUSD, USDCHF, USDCAD, AUDUSD, NZDUSD
- **Smart Risk Management** with dynamic lot sizing

---

## Project Structure

```
mt5scalpbot/

 main.py # Main bot engine
 execution.py # Order execution & position management
 data_handler.py # OHLCV data & tick monitoring
 risk_manager.py # Dynamic risk & lot sizing
 config.py # Configuration hub
 logger.py # Console logging

 strategies/ # Trading strategies
 strategyA_triple_ema.py
 strategyB_adx_di.py
 strategyC_bollinger.py
 strategyD_stochastic.py
 strategyE_breakout.py

 telegram_adapter.py # Telegram alert adapter
 trade-alerts/ # Existing alert system
 src/notifiers/
 telegram_bot.py # 1337-line TelegramNotifier

 .env # Credentials (NEVER COMMIT)
 .env.example # Template

 setup_m1_mac.sh # Automated M1 setup
 service_control.sh # Start/stop helper
 run.sh # Quick start script
 commands.sh # Quick reference

 personal-docs/
 M1_MAC_SETUP_GUIDE.md
 SETUP_COMPLETE.md
 INTEGRATION_COMPLETE.md
 README.old.md
```

---

## Quick Start (M1 Mac)

### 1. **Run Automated Setup**
```bash
chmod +x setup_m1_mac.sh
./setup_m1_mac.sh
```

This installs:
- Homebrew
- Colima (x86_64 emulation)
- Docker
- MetaTrader 5 container
- Python 3.11 virtual environment
- All dependencies

### 2. **Configure MT5 via VNC**
```bash
# Open MT5 terminal in browser
open http://localhost:6081/vnc.html

# VNC Password: 123456
```

**In MT5 Terminal:**
- File → Login to Trade Account
- Login: 140117977
- Password: (from .env)
- Server: DerivVU-Server-03

**Enable Automated Trading:**
- Tools → Options → Expert Advisors
- Allow automated trading
- Allow WebRequest for listed URL

**Add Synthetic Indices to Market Watch:**
- Right-click Market Watch → Show All
- Find and enable: Volatility 10, 25, 50, 75, 100, etc.

### 3. **Test Telegram Connection**
```bash
source venv/bin/activate
cd trade-alerts
python -c "
import sys
sys.path.insert(0, 'src')
from notifiers.telegram_bot import TelegramNotifier
import os
from dotenv import load_dotenv
load_dotenv('../.env')

notifier = TelegramNotifier(
 bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
 chat_id=os.getenv('TELEGRAM_CHAT_ID')
)
import asyncio
asyncio.run(notifier.send_message(' MT5 Bot Test - Connection Successful!'))
"
```

### 4. **Start Trading Bot**
```bash
# Using helper script
./service_control.sh start

# Or manually
source venv/bin/activate
python main.py
```

---

## Configuration

### Environment Variables (`.env`)
```bash
# MT5 Credentials
MT5_LOGIN=140117977
MT5_PASSWORD=your_password_here
MT5_SERVER=DerivVU-Server-03

# Telegram Alerts
TELEGRAM_BOT_TOKEN=7977519104:AAF-Qf...
TELEGRAM_CHAT_ID=7366332019
ENABLE_TELEGRAM_ALERTS=True

# Trading Parameters
TRADING_SYMBOLS=EURUSD,USDJPY,GBPUSD,USDCHF,USDCAD,AUDUSD,NZDUSD
BASE_LOT_SIZE=0.01
MAX_LOT_SIZE=0.50
RISK_REWARD_RATIO=2.5
```

### Key Files Modified for Integration

#### **1. main.py**
```python
# Telegram Integration
sys.path.insert(0, 'trade-alerts/src')
from notifiers.telegram_bot import TelegramNotifier
from telegram_adapter import TelegramAlertAdapter

telegram_notifier = TelegramNotifier(...)
telegram_alerter = TelegramAlertAdapter(telegram_notifier)
```

#### **2. execution.py**
```python
class ExecutionEngine:
 def __init__(self, risk_manager, data_handler, telegram_alerter=None):
 self.telegram_alerter = telegram_alerter
 
 def place_order(self, ...):
 # Trade execution
 if self.telegram_alerter:
 self.telegram_alerter.alert_trade_opened(...)
```

#### **3. telegram_adapter.py**
Bridges the bot with the existing 1337-line `TelegramNotifier`:
- `alert_bot_started()` - Bot startup notification
- `alert_bot_stopped(stats)` - Shutdown with stats
- `alert_trade_opened(...)` - New position alerts
- `alert_trade_closed(...)` - Closed position with P/L
- `alert_position_flipped(...)` - Strategy reversal
- `alert_margin_level(...)` - Risk warnings
- `alert_connection_error(...)` - MT5 connection issues

---

## Trading Strategies

### Strategy A: Triple EMA Scalper
- **Indicators**: EMA(6), EMA(22), EMA(300)
- **Signal**: Buy when 6 > 22 > 300, Sell when 6 < 22 < 300
- **Best For**: Strong trending markets

### Strategy B: ADX/DI Scalper
- **Indicators**: ADX(14), +DI, -DI
- **Signal**: Buy when +DI > -DI & ADX > 25, Sell when -DI > +DI & ADX > 25
- **Best For**: Identifying strong trends

### Strategy C: Bollinger Mean Reversion
- **Indicators**: Bollinger Bands (20, 2), RSI(14)
- **Signal**: Buy when price < lower band & RSI < 30, Sell when price > upper band & RSI > 70
- **Best For**: Range-bound markets

### Strategy D: Stochastic Divergence
- **Indicators**: Stochastic(14, 3, 3)
- **Signal**: Buy when %K < 20 & crosses above %D, Sell when %K > 80 & crosses below %D
- **Best For**: Overbought/oversold reversals

### Strategy E: Breakout Scalper
- **Indicators**: Swing High/Low (20 bars), Volume
- **Signal**: Buy on breakout above swing high with volume confirmation
- **Best For**: Volatile breakout opportunities

---

## Telegram Alert Examples

### Bot Started
```
 MT5 SCALPING BOT STARTED

Bot has been initialized and is now monitoring the markets.

 Started: 2024-01-15 14:30:22
```

### Trade Opened
```
 TRADE OPENED

 Symbol: EURUSD
 Action: BUY
 Price: 1.08450
 Lot Size: 0.01

 Stop Loss: 1248.20
 Take Profit: 1254.70

 Strategy: Triple EMA Scalper
 Ticket: 123456789

 Time: 2024-01-15 14:31:05
```

### Trade Closed (Profit)
```
 TRADE CLOSED - PROFIT

 Symbol: EURUSD
 Action: BUY

 Entry: 1.08450
 Exit: 1.08675
 Lot Size: 0.01

 P/L: $4.25
 Duration: 00:02:34
 Ticket: 123456789

 Closed: 2024-01-15 14:33:39
```

### Position Flipped
```
 POSITION FLIPPED

 Symbol: USDJPY
 Old Position: BUY
 New Position: SELL

 Reason: ADX/DI Scalper - Strong bearish divergence

 Time: 2024-01-15 14:35:12
```

### Margin Warning
```
 Low Margin Level Warning

 Margin Level: 135.50%
 Equity: $1,255.23
 Margin Used: $926.45

 Monitor positions carefully

 Time: 2024-01-15 14:40:08
```

---

## Service Management

### Using Helper Script
```bash
# Start bot
./service_control.sh start

# Stop bot
./service_control.sh stop

# Restart bot
./service_control.sh restart

# Check status
./service_control.sh status

# View logs
./service_control.sh logs
```

### Manual Management
```bash
# Start Colima
colima start mt5scalpbot

# Check Docker containers
docker ps

# Start MT5 container (if not running)
docker start silicon-metatrader5

# Activate Python environment
source venv/bin/activate

# Run bot
python main.py

# View live logs
tail -f bot.log
```

---

## Troubleshooting

### Issue: "MT5 initialization failed"
```bash
# Check if Colima is running
colima status mt5scalpbot

# Start Colima if stopped
colima start mt5scalpbot

# Check MT5 container
docker ps -a | grep metatrader

# Start MT5 container
docker start silicon-metatrader5

# Wait 30 seconds for MT5 to fully load
sleep 30

# Retry bot
python main.py
```

### Issue: "Failed to login to MT5"
1. Open VNC: http://localhost:6081/vnc.html
2. Verify MT5 terminal is logged in
3. Check credentials in `.env` file
4. Ensure server is "DerivVU-Server-03"

### Issue: Telegram alerts not working
```bash
# Test bot token
curl -X GET "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Test chat ID
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
 -d "chat_id=<YOUR_CHAT_ID>&text=Test"

# Check environment variables
cat .env | grep TELEGRAM

# Verify python-telegram-bot is installed
pip show python-telegram-bot
```

### Issue: Symbol not found
```bash
# In MT5 VNC session:
# 1. Right-click Market Watch
# 2. Click "Show All"
# 3. Scroll to find synthetic indices
# 4. Right-click symbol → Show

# Or modify config.py to use different symbols
```

---

## Performance Monitoring

### View Real-Time Logs
```bash
tail -f bot.log
```

### Check Account Status
```python
import MetaTrader5 as mt5
mt5.initialize()
mt5.login(140117977, password="...", server="DerivVU-Server-03")

account = mt5.account_info()
print(f"Balance: ${account.balance}")
print(f"Equity: ${account.equity}")
print(f"Margin Level: {account.margin_level}%")
```

### View Trade History
```python
from datetime import datetime
history = mt5.history_deals_get(
 datetime(2024, 1, 1),
 datetime.now()
)

for deal in history:
 print(f"{deal.symbol} | {deal.type} | P/L: ${deal.profit:.2f}")
```

---

## Important Notes

### Security
- **NEVER** commit `.env` file to Git
- Keep Telegram bot token secure
- Use demo account for testing
- Monitor margin levels closely

### Recommendations
1. **Start with demo account** - Test for at least 1 week
2. **Small lot sizes** - Begin with 0.01 lot
3. **Monitor closely** - Watch first few hours
4. **Set alerts** - Enable Telegram for critical events
5. **Regular backups** - Keep trade history logs

### Known Limitations
- M1 Mac requires x86 emulation (Colima)
- VNC required for MT5 GUI access
- Async operations require running event loop
- Deriv synthetic indices have specific trading hours

---

## Additional Resources

- **M1 Setup Guide**: [personal-docs/M1_MAC_SETUP_GUIDE.md](personal-docs/M1_MAC_SETUP_GUIDE.md)
- **Integration Complete**: [personal-docs/INTEGRATION_COMPLETE.md](personal-docs/INTEGRATION_COMPLETE.md)
- **Setup Complete**: [personal-docs/SETUP_COMPLETE.md](personal-docs/SETUP_COMPLETE.md)
- **Quick Reference**: [commands.sh](commands.sh)

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review documentation in `docs/` folder
3. Check Telegram alerts for error messages
4. Review `bot.log` for detailed errors

---

## Integration Checklist

- [x] Core bot with 5 strategies
- [x] M1 Mac setup automation
- [x] Telegram alert integration with existing system
- [x] Environment variable configuration
- [x] Synthetic indices support (Deriv)
- [x] Risk management with dynamic lot sizing
- [x] Comprehensive documentation
- [x] Service control scripts
- [x] Error handling and logging
- [x] VNC-based MT5 access

**Status**: **READY FOR DEPLOYMENT**

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
**Author**: MT5 Scalp Bot Development Team
