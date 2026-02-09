# Deriv ScalpBot

Algorithmic trading bot for Deriv.com with 5 scalping strategies, real-time WebSocket streaming, and risk management.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**DISCLAIMER**: Educational purposes only. Trading involves substantial risk. Use at your own risk.

---

## Installation

```bash
git clone https://github.com/1cbyc/deriv-scalpbot.git
cd deriv-scalpbot
pip install -r requirements.txt
```

---

## Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```bash
DERIV_APP_ID=your_app_id_here
DERIV_API_TOKEN=your_api_token_here
DERIV_ACCOUNT_ID=your_account_id_here
```

Get credentials at: https://api.deriv.com/dashboard

**Important**: Use DEMO account (starts with VRTC) for testing.

---

## Running

Test system:
```bash
python test_system.py
```

Start bot:
```bash
python main.py
```

## Features

- 5 scalping strategies (Triple EMA, ADX/DI, Bollinger, Stochastic, Breakout)
- Real-time WebSocket tick streaming
- Risk management (daily limits, position sizing)
- Performance tracking (win rate, P/L, Sharpe ratio)
- Optional Telegram alerts

---

## Strategies

1. **Triple EMA** - Trend following with EMA(6/22/300)
2. **ADX/DI** - Momentum trades when ADX > 25
3. **Bollinger Bands** - Mean reversion with RSI
4. **Stochastic** - Overbought/oversold reversals
5. **Breakout** - Price breakouts with volume confirmation

---

## Configuration Options

Edit `.env` for settings:

```bash
# Contract settings
CONTRACT_DURATION=5
BASE_STAKE_USD=0.50
MAX_STAKE_USD=2.00

# Risk management
DAILY_LOSS_LIMIT_USD=5.00
MAX_POSITIONS=3

# Symbols
TRADING_SYMBOLS=frxEURUSD,frxGBPUSD,frxAUDUSD
```

Full configuration in `.env.example`

---

## Troubleshooting

**Invalid API token**: Regenerate at https://api.deriv.com/dashboard with Trading + Read permissions

**WebSocket failed**: Check internet connection, verify credentials with `python test_deriv_connection.py`

**Insufficient balance**: Use DEMO account (VRTC), reduce stake amount

---

## License

MIT License. See [LICENSE](LICENSE) file. Not financial advice. Use at your own risk.

---

**Documentation**: [Deriv API Docs](https://api.deriv.com/docs)  
**Issues**: [GitHub Issues](https://github.com/1cbyc/deriv-scalpbot/issues)  
**Security**: See [SECURITY.md](SECURITY.md)
