"""
Deriv API Client - WebSocket and REST API wrapper
Handles connection, authentication, and trading operations with Deriv.com
"""

import json
import time
import threading
from typing import Optional, Dict, List, Callable
from pathlib import Path
import websocket
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DerivAPI:
    """
    Deriv API client with WebSocket streaming and REST operations
    """
    
    def __init__(self, app_id: str, api_token: str, endpoint: str = "wss://ws.derivws.com/websockets/v3"):
        """
        Initialize Deriv API client
        
        Args:
            app_id: Your Deriv app ID from api.deriv.com/dashboard
            api_token: API token for authentication
            endpoint: WebSocket endpoint (default: production)
        """
        self.app_id = app_id
        self.api_token = api_token
        self.endpoint = f"{endpoint}?app_id={app_id}"
        
        self.ws = None
        self.connected = False
        self.authorized = False
        
        # Message handling
        self.response_callbacks = {}
        self.subscription_callbacks = {}
        self.req_id = 1000
        
        # Account info
        self.account_info = None
        self.balance = 0.0
        
        # Heartbeat and reconnection
        self.heartbeat_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # JSON logging
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "trade_log.json"
        self.logs = []
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
    def connect(self) -> bool:
        """
        Establish WebSocket connection to Deriv
        
        Returns:
            bool: True if connected successfully
        """
        try:
            self.ws = websocket.WebSocketApp(
                self.endpoint,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Run WebSocket in background thread
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("Connected to Deriv WebSocket")
                # Authorize after connection
                return self.authorize()
            else:
                logger.error("Failed to connect to Deriv WebSocket")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def authorize(self) -> bool:
        """
        Authorize with API token
        
        Returns:
            bool: True if authorized successfully
        """
        try:
            response = self._send_and_wait({
                "authorize": self.api_token
            })
            
            if response and 'authorize' in response:
                self.authorized = True
                self.account_info = response['authorize']
                self.balance = float(response['authorize'].get('balance', 0))
                logger.info(f"Authorized account: {self.account_info.get('loginid')}")
                return True
            else:
                logger.error(f"Authorization failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            return False
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.connected = False
            self.authorized = False
            logger.info("Disconnected from Deriv")
    
    def get_ticks_history(self, symbol: str, count: int = 500) -> Optional[List[Dict]]:
        """
        Get historical tick data
        
        Args:
            symbol: Trading symbol (e.g., 'R_100', 'frxEURUSD')
            count: Number of ticks to retrieve
            
        Returns:
            List of tick dictionaries or None if failed
        """
        try:
            response = self._send_and_wait({
                "ticks_history": symbol,
                "count": count,
                "end": "latest",
                "style": "ticks"
            })
            
            if response and 'history' in response:
                ticks = []
                times = response['history']['times']
                prices = response['history']['prices']
                
                for t, p in zip(times, prices):
                    ticks.append({
                        'time': int(t),
                        'price': float(p)
                    })
                
                return ticks
            else:
                logger.error(f"Failed to get tick history: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting tick history: {e}")
            return None
    
    def subscribe_ticks(self, symbol: str, callback: Callable):
        """
        Subscribe to real-time tick stream
        
        Args:
            symbol: Trading symbol
            callback: Function to call on each tick (receives tick dict)
        """
        try:
            req_id = self._get_req_id()
            self.subscription_callbacks[symbol] = callback
            
            self._send({
                "ticks": symbol,
                "subscribe": 1,
                "req_id": req_id
            })
            
            logger.info(f"Subscribed to {symbol} ticks")
            
        except Exception as e:
            logger.error(f"Error subscribing to ticks: {e}")
    
    def unsubscribe_ticks(self, symbol: str):
        """
        Unsubscribe from tick stream
        
        Args:
            symbol: Trading symbol
        """
        try:
            self._send({
                "forget_all": "ticks"
            })
            
            if symbol in self.subscription_callbacks:
                del self.subscription_callbacks[symbol]
            
            logger.info(f"Unsubscribed from {symbol} ticks")
            
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
    
    def buy_contract(self, symbol: str, contract_type: str, amount: float, 
                     duration: int = 5, duration_unit: str = 't',
                     barrier: Optional[float] = None, 
                     barrier2: Optional[float] = None) -> Optional[Dict]:
        """
        Buy a contract
        
        Args:
            symbol: Trading symbol (e.g., 'R_100', 'frxEURUSD')
            contract_type: 'CALL', 'PUT', 'DIGITEVEN', 'DIGITODD', etc.
            amount: Stake amount in account currency
            duration: Contract duration
            duration_unit: 't' (ticks), 's' (seconds), 'm' (minutes), 'h' (hours), 'd' (days)
            barrier: Optional barrier/strike price
            barrier2: Optional second barrier for range contracts
            
        Returns:
            Contract info dict or None if failed
        """
        try:
            # First, get contract proposal
            proposal_params = {
                "proposal": 1,
                "amount": amount,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": self.account_info.get('currency', 'USD'),
                "duration": duration,
                "duration_unit": duration_unit,
                "symbol": symbol
            }
            
            if barrier:
                proposal_params["barrier"] = str(barrier)
            if barrier2:
                proposal_params["barrier2"] = str(barrier2)
            
            proposal = self._send_and_wait(proposal_params)
            
            if not proposal or 'proposal' not in proposal:
                logger.error(f"Proposal failed: {proposal}")
                return None
            
            # Buy the contract
            buy_response = self._send_and_wait({
                "buy": proposal['proposal']['id'],
                "price": amount
            })
            
            if buy_response and 'buy' in buy_response:
                contract = buy_response['buy']
                logger.info(f"Bought contract {contract['contract_id']}: {contract_type} {symbol}")
                return contract
            else:
                logger.error(f"Buy failed: {buy_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error buying contract: {e}")
            return None
    
    def sell_contract(self, contract_id: int, price: Optional[float] = None) -> Optional[Dict]:
        """
        Sell an open contract
        
        Args:
            contract_id: Contract ID to sell
            price: Minimum price to sell at (None for market price)
            
        Returns:
            Sell transaction info or None if failed
        """
        try:
            sell_params = {
                "sell": contract_id
            }
            
            if price:
                sell_params["price"] = price
            
            response = self._send_and_wait(sell_params)
            
            if response and 'sell' in response:
                logger.info(f"Sold contract {contract_id}")
                return response['sell']
            else:
                logger.error(f"Sell failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error selling contract: {e}")
            return None
    
    def get_portfolio(self) -> Optional[List[Dict]]:
        """
        Get all open contracts
        
        Returns:
            List of open contracts or None if failed
        """
        try:
            response = self._send_and_wait({
                "portfolio": 1
            })
            
            if response and 'portfolio' in response:
                return response['portfolio'].get('contracts', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return None
    
    def get_balance(self) -> float:
        """
        Get current account balance
        
        Returns:
            Current balance
        """
        try:
            response = self._send_and_wait({
                "balance": 1,
                "subscribe": 0
            })
            
            if response and 'balance' in response:
                self.balance = float(response['balance']['balance'])
                return self.balance
            else:
                return self.balance
                
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return self.balance
    
    def _send(self, request: Dict):
        """Send request without waiting for response"""
        if not self.connected:
            raise ConnectionError("Not connected to Deriv WebSocket")
        
        self.ws.send(json.dumps(request))
    
    def _send_and_wait(self, request: Dict, timeout: int = 10) -> Optional[Dict]:
        """
        Send request and wait for response (with logging)
        
        Args:
            request: Request dictionary
            timeout: Timeout in seconds
            
        Returns:
            Response dictionary or None if timeout
        """
        if not self.connected:
            raise ConnectionError("Not connected to Deriv WebSocket")
        
        req_id = self._get_req_id()
        request['req_id'] = req_id
        
        # Log outgoing request
        self._log_request(request)
        
        # Set up callback for response
        response_event = threading.Event()
        response_data = {'result': None}
        
        def callback(resp):
            response_data['result'] = resp
            response_event.set()
        
        with self.lock:
            self.response_callbacks[req_id] = callback
        
        # Send request
        self.ws.send(json.dumps(request))
        
        # Wait for response
        if response_event.wait(timeout):
            response = response_data['result']
            # Log incoming response
            if response:
                self._log_response(response)
            return response
        else:
            logger.warning(f"Request {req_id} timed out")
            with self.lock:
                if req_id in self.response_callbacks:
                    del self.response_callbacks[req_id]
            return None
    
    def _get_req_id(self) -> int:
        """Generate unique request ID"""
        with self.lock:
            self.req_id += 1
            return self.req_id
    
    def _start_heartbeat(self):
        """Send ping every 30 seconds to keep connection alive"""
        def heartbeat():
            while self.connected:
                try:
                    if self.ws and self.connected:
                        self._send({"ping": 1})
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
        
        self.heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Heartbeat mechanism started")
    
    def _log_request(self, request: Dict):
        """Log outgoing request"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "data": request
        }
        self.logs.append(log_entry)
        self._write_logs()
    
    def _log_response(self, response: Dict):
        """Log incoming response"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "data": response
        }
        self.logs.append(log_entry)
        self._write_logs()
    
    def _write_logs(self):
        """Write logs to file (keep last 1000)"""
        try:
            # Keep only last 1000 entries
            if len(self.logs) > 1000:
                self.logs = self.logs[-1000:]
            
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write logs: {e}")
    
    def _on_open(self, ws):
        """WebSocket opened"""
        self.connected = True
        self.reconnect_attempts = 0  # Reset on success
        logger.info("WebSocket connection opened")
        self._start_heartbeat()
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle errors
            if 'error' in data:
                logger.error(f"API error: {data['error']}")
                return
            
            # Handle subscription updates (ticks)
            if 'tick' in data:
                symbol = data['tick'].get('symbol')
                if symbol in self.subscription_callbacks:
                    tick_data = {
                        'time': int(data['tick']['epoch']),
                        'price': float(data['tick']['quote']),
                        'symbol': symbol
                    }
                    self.subscription_callbacks[symbol](tick_data)
                return
            
            # Handle request responses
            req_id = data.get('req_id')
            if req_id and req_id in self.response_callbacks:
                with self.lock:
                    callback = self.response_callbacks.pop(req_id, None)
                    if callback:
                        callback(data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket error"""
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle disconnection with auto-reconnect"""
        self.connected = False
        self.authorized = False
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(2 ** self.reconnect_attempts, 60)
            logger.info(f"Reconnecting in {wait_time}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            time.sleep(wait_time)
            self.connect()
        else:
            logger.error("Max reconnection attempts reached. Manual restart required.")
