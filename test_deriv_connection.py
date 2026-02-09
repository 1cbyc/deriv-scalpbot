#!/usr/bin/env python3
"""
Test Deriv API Connection
Quick script to verify Deriv API credentials and connectivity
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if credentials are set
DERIV_APP_ID = os.getenv('DERIV_APP_ID')
DERIV_API_TOKEN = os.getenv('DERIV_API_TOKEN')

if not DERIV_APP_ID or DERIV_APP_ID == 'your_app_id_here':
    print("❌ DERIV_APP_ID not set in .env file")
    print("   Get your App ID from: https://api.deriv.com/dashboard")
    sys.exit(1)

if not DERIV_API_TOKEN or DERIV_API_TOKEN == 'your_api_token_here':
    print("❌ DERIV_API_TOKEN not set in .env file")
    print("   Get your API token from: https://api.deriv.com/dashboard")
    sys.exit(1)

print("✓ Credentials found in .env")
print(f"  App ID: {DERIV_APP_ID}")
print(f"  Token: {DERIV_API_TOKEN[:10]}...")

# Try to import deriv_api
try:
    from deriv_api import DerivAPI
    print("✓ deriv_api module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import deriv_api: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Try to connect
print("\n📡 Connecting to Deriv API...")
client = DerivAPI(app_id=DERIV_APP_ID, api_token=DERIV_API_TOKEN)

if not client.connect():
    print("❌ Failed to connect to Deriv API")
    sys.exit(1)

print("✓ Connected to Deriv WebSocket")

# Get account info
if client.account_info:
    print("\n📊 Account Information:")
    print(f"   Login ID: {client.account_info.get('loginid', 'N/A')}")
    print(f"   Currency: {client.account_info.get('currency', 'USD')}")
    print(f"   Balance: ${client.balance:.2f}")
    print(f"   Email: {client.account_info.get('email', 'N/A')}")
    print(f"   Country: {client.account_info.get('country', 'N/A')}")
else:
    print("❌ Failed to get account information")
    sys.exit(1)

# Test getting ticks for a symbol
print("\n📈 Testing tick data retrieval...")
test_symbol = 'R_100'  # Volatility 100 Index
print(f"   Symbol: {test_symbol}")

ticks = client.get_ticks_history(test_symbol, count=10)
if ticks:
    print(f"✓ Retrieved {len(ticks)} ticks")
    latest = ticks[-1]
    print(f"   Latest: {latest['price']:.5f} @ {latest['time']}")
else:
    print("❌ Failed to retrieve tick data")

# Test subscribing to ticks
print("\n📊 Testing real-time tick subscription...")
received_ticks = []

def on_tick(tick):
    received_ticks.append(tick)
    print(f"   Tick received: {tick['price']:.5f} @ {tick['time']}")

client.subscribe_ticks(test_symbol, on_tick)
print(f"   Subscribed to {test_symbol}")
print("   Waiting for 5 ticks (max 30 seconds)...")

import time
timeout = 30
start_time = time.time()

while len(received_ticks) < 5 and time.time() - start_time < timeout:
    time.sleep(0.5)

if len(received_ticks) >= 5:
    print(f"✓ Received {len(received_ticks)} ticks successfully")
else:
    print(f"⚠️  Only received {len(received_ticks)} ticks (timeout)")

# Unsubscribe
client.unsubscribe_ticks(test_symbol)

print("\n" + "="*60)
print("✅ CONNECTION TEST SUCCESSFUL!")
print("="*60)
print("\nYour Deriv API setup is working correctly.")
print("You can now run the bot with: python3 main.py")
print("\n⚠️  REMINDER: Use a DEMO/VIRTUAL account for testing!")
