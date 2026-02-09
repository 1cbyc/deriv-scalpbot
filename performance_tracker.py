"""
Performance Tracker Module
Tracks strategy and symbol performance metrics for optimization and analysis
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks performance metrics for strategies and symbols
    Provides analytics for optimization decisions
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize performance tracker
        
        Args:
            data_dir: Directory to store performance data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Performance data structures
        self.strategy_stats = defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'total_stake': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'avg_duration': 0.0,
            'total_duration': 0.0,
            'last_trade_time': None,
            'trades_by_hour': defaultdict(int),
            'wins_by_hour': defaultdict(int)
        })
        
        self.symbol_stats = defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'total_stake': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'avg_duration': 0.0,
            'total_duration': 0.0,
            'last_trade_time': None,
            'trades_by_hour': defaultdict(int),
            'wins_by_hour': defaultdict(int)
        })
        
        # Combined strategy-symbol performance
        self.strategy_symbol_stats = defaultdict(lambda: defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0
        }))
        
        # Trade history for detailed analysis
        self.trade_history = []
        
        # Load existing data
        self._load_data()
    
    def record_trade(self, strategy: str, symbol: str, profit: float,
                    stake: float, duration: float, entry_time: datetime,
                    contract_type: str, reason: str = ""):
        """
        Record a completed trade
        
        Args:
            strategy: Strategy name
            symbol: Trading symbol
            profit: Profit/loss amount
            stake: Stake amount
            duration: Trade duration in seconds
            entry_time: Trade entry timestamp
            contract_type: CALL or PUT
            reason: Trade reason/signal
        """
        is_win = profit > 0
        hour = entry_time.hour
        
        # Update strategy stats
        s_stats = self.strategy_stats[strategy]
        s_stats['trades'] += 1
        s_stats['wins'] += 1 if is_win else 0
        s_stats['losses'] += 0 if is_win else 1
        s_stats['total_pnl'] += profit
        s_stats['total_stake'] += stake
        s_stats['best_trade'] = max(s_stats['best_trade'], profit)
        s_stats['worst_trade'] = min(s_stats['worst_trade'], profit)
        s_stats['total_duration'] += duration
        s_stats['avg_duration'] = s_stats['total_duration'] / s_stats['trades']
        s_stats['last_trade_time'] = entry_time.isoformat()
        s_stats['trades_by_hour'][hour] += 1
        s_stats['wins_by_hour'][hour] += 1 if is_win else 0
        
        # Update symbol stats
        sym_stats = self.symbol_stats[symbol]
        sym_stats['trades'] += 1
        sym_stats['wins'] += 1 if is_win else 0
        sym_stats['losses'] += 0 if is_win else 1
        sym_stats['total_pnl'] += profit
        sym_stats['total_stake'] += stake
        sym_stats['best_trade'] = max(sym_stats['best_trade'], profit)
        sym_stats['worst_trade'] = min(sym_stats['worst_trade'], profit)
        sym_stats['total_duration'] += duration
        sym_stats['avg_duration'] = sym_stats['total_duration'] / sym_stats['trades']
        sym_stats['last_trade_time'] = entry_time.isoformat()
        sym_stats['trades_by_hour'][hour] += 1
        sym_stats['wins_by_hour'][hour] += 1 if is_win else 0
        
        # Update combined stats
        self.strategy_symbol_stats[strategy][symbol]['trades'] += 1
        self.strategy_symbol_stats[strategy][symbol]['wins'] += 1 if is_win else 0
        self.strategy_symbol_stats[strategy][symbol]['losses'] += 0 if is_win else 1
        self.strategy_symbol_stats[strategy][symbol]['total_pnl'] += profit
        
        # Add to trade history
        trade_record = {
            'timestamp': entry_time.isoformat(),
            'strategy': strategy,
            'symbol': symbol,
            'contract_type': contract_type,
            'stake': stake,
            'profit': profit,
            'duration': duration,
            'reason': reason,
            'hour': hour
        }
        self.trade_history.append(trade_record)
        
        # Keep only last 1000 trades in memory
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
        
        # Save to disk every 10 trades
        if len(self.trade_history) % 10 == 0:
            self._save_data()
        
        logger.info(f"Recorded trade: {strategy} on {symbol} - P/L: ${profit:.2f}")
    
    def get_strategy_performance(self, strategy: str = None) -> Dict:
        """
        Get performance metrics for a strategy or all strategies
        
        Args:
            strategy: Strategy name (None for all strategies)
            
        Returns:
            Dictionary of performance metrics
        """
        if strategy:
            stats = dict(self.strategy_stats[strategy])
            stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            stats['avg_pnl'] = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
            stats['roi'] = (stats['total_pnl'] / stats['total_stake'] * 100) if stats['total_stake'] > 0 else 0
            stats['strategy'] = strategy
            return stats
        else:
            # All strategies
            all_stats = {}
            for strat_name, strat_data in self.strategy_stats.items():
                all_stats[strat_name] = self.get_strategy_performance(strat_name)
            return all_stats
    
    def get_symbol_performance(self, symbol: str = None) -> Dict:
        """
        Get performance metrics for a symbol or all symbols
        
        Args:
            symbol: Trading symbol (None for all symbols)
            
        Returns:
            Dictionary of performance metrics
        """
        if symbol:
            stats = dict(self.symbol_stats[symbol])
            stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            stats['avg_pnl'] = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
            stats['roi'] = (stats['total_pnl'] / stats['total_stake'] * 100) if stats['total_stake'] > 0 else 0
            stats['symbol'] = symbol
            return stats
        else:
            # All symbols
            all_stats = {}
            for sym_name, sym_data in self.symbol_stats.items():
                all_stats[sym_name] = self.get_symbol_performance(sym_name)
            return all_stats
    
    def get_best_strategies(self, top_n: int = 3, metric: str = 'roi') -> List[Dict]:
        """
        Get top performing strategies
        
        Args:
            top_n: Number of top strategies to return
            metric: Metric to rank by ('roi', 'win_rate', 'total_pnl', 'trades')
            
        Returns:
            List of strategy performance dictionaries
        """
        all_strategies = self.get_strategy_performance()
        
        # Filter strategies with minimum trades (at least 5)
        valid_strategies = {k: v for k, v in all_strategies.items() if v['trades'] >= 5}
        
        if not valid_strategies:
            return []
        
        # Sort by metric
        sorted_strategies = sorted(
            valid_strategies.items(),
            key=lambda x: x[1].get(metric, 0),
            reverse=True
        )
        
        return [v for k, v in sorted_strategies[:top_n]]
    
    def get_worst_strategies(self, bottom_n: int = 3, metric: str = 'roi') -> List[Dict]:
        """
        Get worst performing strategies
        
        Args:
            bottom_n: Number of bottom strategies to return
            metric: Metric to rank by ('roi', 'win_rate', 'total_pnl')
            
        Returns:
            List of strategy performance dictionaries
        """
        all_strategies = self.get_strategy_performance()
        
        # Filter strategies with minimum trades
        valid_strategies = {k: v for k, v in all_strategies.items() if v['trades'] >= 5}
        
        if not valid_strategies:
            return []
        
        # Sort by metric (ascending for worst)
        sorted_strategies = sorted(
            valid_strategies.items(),
            key=lambda x: x[1].get(metric, 0),
            reverse=False
        )
        
        return [v for k, v in sorted_strategies[:bottom_n]]
    
    def get_best_symbols(self, top_n: int = 3, metric: str = 'roi') -> List[Dict]:
        """
        Get top performing symbols
        
        Args:
            top_n: Number of top symbols to return
            metric: Metric to rank by ('roi', 'win_rate', 'total_pnl', 'trades')
            
        Returns:
            List of symbol performance dictionaries
        """
        all_symbols = self.get_symbol_performance()
        
        # Filter symbols with minimum trades
        valid_symbols = {k: v for k, v in all_symbols.items() if v['trades'] >= 5}
        
        if not valid_symbols:
            return []
        
        # Sort by metric
        sorted_symbols = sorted(
            valid_symbols.items(),
            key=lambda x: x[1].get(metric, 0),
            reverse=True
        )
        
        return [v for k, v in sorted_symbols[:top_n]]
    
    def get_worst_symbols(self, bottom_n: int = 3, metric: str = 'roi') -> List[Dict]:
        """
        Get worst performing symbols
        
        Args:
            bottom_n: Number of bottom symbols to return
            metric: Metric to rank by ('roi', 'win_rate', 'total_pnl')
            
        Returns:
            List of symbol performance dictionaries
        """
        all_symbols = self.get_symbol_performance()
        
        # Filter symbols with minimum trades
        valid_symbols = {k: v for k, v in all_symbols.items() if v['trades'] >= 5}
        
        if not valid_symbols:
            return []
        
        # Sort by metric (ascending for worst)
        sorted_symbols = sorted(
            valid_symbols.items(),
            key=lambda x: x[1].get(metric, 0),
            reverse=False
        )
        
        return [v for k, v in sorted_symbols[:bottom_n]]
    
    def get_strategy_symbol_matrix(self) -> Dict:
        """
        Get performance matrix showing which strategies work best on which symbols
        
        Returns:
            Dictionary with strategy-symbol combinations and their performance
        """
        matrix = {}
        
        for strategy, symbols in self.strategy_symbol_stats.items():
            matrix[strategy] = {}
            for symbol, stats in symbols.items():
                if stats['trades'] >= 3:  # Minimum 3 trades for inclusion
                    win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
                    matrix[strategy][symbol] = {
                        'trades': stats['trades'],
                        'wins': stats['wins'],
                        'losses': stats['losses'],
                        'win_rate': win_rate,
                        'total_pnl': stats['total_pnl']
                    }
        
        return matrix
    
    def get_hourly_performance(self) -> Dict:
        """
        Get performance by hour of day to identify best trading times
        
        Returns:
            Dictionary with hourly statistics
        """
        hourly_stats = defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0
        })
        
        # Aggregate from all strategies
        for strategy, stats in self.strategy_stats.items():
            for hour, trades in stats['trades_by_hour'].items():
                hourly_stats[hour]['trades'] += trades
                hourly_stats[hour]['wins'] += stats['wins_by_hour'].get(hour, 0)
        
        # Calculate win rates
        for hour, stats in hourly_stats.items():
            stats['losses'] = stats['trades'] - stats['wins']
            stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        
        return dict(hourly_stats)
    
    def get_recent_trades(self, count: int = 20) -> List[Dict]:
        """
        Get most recent trades
        
        Args:
            count: Number of recent trades to return
            
        Returns:
            List of trade records
        """
        return self.trade_history[-count:]
    
    def generate_performance_report(self) -> str:
        """
        Generate comprehensive performance report
        
        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 70)
        report.append("PERFORMANCE REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Strategy Performance
        report.append("STRATEGY PERFORMANCE")
        report.append("-" * 70)
        all_strategies = self.get_strategy_performance()
        
        if all_strategies:
            for strategy, stats in sorted(all_strategies.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
                report.append(f"\n{strategy}:")
                report.append(f"  Trades: {stats['trades']} | Wins: {stats['wins']} | Losses: {stats['losses']}")
                report.append(f"  Win Rate: {stats['win_rate']:.1f}% | ROI: {stats['roi']:.1f}%")
                report.append(f"  Total P/L: ${stats['total_pnl']:.2f} | Avg P/L: ${stats['avg_pnl']:.2f}")
                report.append(f"  Best: ${stats['best_trade']:.2f} | Worst: ${stats['worst_trade']:.2f}")
                report.append(f"  Avg Duration: {stats['avg_duration']:.0f}s")
        else:
            report.append("  No trades recorded yet")
        
        report.append("")
        report.append("SYMBOL PERFORMANCE")
        report.append("-" * 70)
        all_symbols = self.get_symbol_performance()
        
        if all_symbols:
            for symbol, stats in sorted(all_symbols.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
                report.append(f"\n{symbol}:")
                report.append(f"  Trades: {stats['trades']} | Wins: {stats['wins']} | Losses: {stats['losses']}")
                report.append(f"  Win Rate: {stats['win_rate']:.1f}% | ROI: {stats['roi']:.1f}%")
                report.append(f"  Total P/L: ${stats['total_pnl']:.2f} | Avg P/L: ${stats['avg_pnl']:.2f}")
                report.append(f"  Best: ${stats['best_trade']:.2f} | Worst: ${stats['worst_trade']:.2f}")
        else:
            report.append("  No trades recorded yet")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def _save_data(self):
        """Save performance data to disk"""
        try:
            data = {
                'strategy_stats': {k: dict(v) for k, v in self.strategy_stats.items()},
                'symbol_stats': {k: dict(v) for k, v in self.symbol_stats.items()},
                'strategy_symbol_stats': {
                    k: {sk: dict(sv) for sk, sv in v.items()}
                    for k, v in self.strategy_symbol_stats.items()
                },
                'trade_history': self.trade_history,
                'last_updated': datetime.now().isoformat()
            }
            
            # Convert defaultdicts to regular dicts for JSON serialization
            def convert_defaultdicts(obj):
                if isinstance(obj, defaultdict):
                    return {k: convert_defaultdicts(v) for k, v in obj.items()}
                return obj
            
            data['strategy_stats'] = {
                k: convert_defaultdicts(v) for k, v in data['strategy_stats'].items()
            }
            data['symbol_stats'] = {
                k: convert_defaultdicts(v) for k, v in data['symbol_stats'].items()
            }
            
            # Save to file
            save_path = self.data_dir / 'performance_data.json'
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Performance data saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save performance data: {e}")
    
    def _load_data(self):
        """Load performance data from disk"""
        try:
            load_path = self.data_dir / 'performance_data.json'
            
            if not load_path.exists():
                logger.info("No existing performance data found, starting fresh")
                return
            
            with open(load_path, 'r') as f:
                data = json.load(f)
            
            # Restore strategy stats
            for strategy, stats in data.get('strategy_stats', {}).items():
                self.strategy_stats[strategy].update(stats)
                # Convert trades_by_hour and wins_by_hour back to defaultdicts
                if 'trades_by_hour' in stats:
                    self.strategy_stats[strategy]['trades_by_hour'] = defaultdict(
                        int, {int(k): v for k, v in stats['trades_by_hour'].items()}
                    )
                if 'wins_by_hour' in stats:
                    self.strategy_stats[strategy]['wins_by_hour'] = defaultdict(
                        int, {int(k): v for k, v in stats['wins_by_hour'].items()}
                    )
            
            # Restore symbol stats
            for symbol, stats in data.get('symbol_stats', {}).items():
                self.symbol_stats[symbol].update(stats)
                if 'trades_by_hour' in stats:
                    self.symbol_stats[symbol]['trades_by_hour'] = defaultdict(
                        int, {int(k): v for k, v in stats['trades_by_hour'].items()}
                    )
                if 'wins_by_hour' in stats:
                    self.symbol_stats[symbol]['wins_by_hour'] = defaultdict(
                        int, {int(k): v for k, v in stats['wins_by_hour'].items()}
                    )
            
            # Restore strategy-symbol stats
            for strategy, symbols in data.get('strategy_symbol_stats', {}).items():
                for symbol, stats in symbols.items():
                    self.strategy_symbol_stats[strategy][symbol].update(stats)
            
            # Restore trade history
            self.trade_history = data.get('trade_history', [])
            
            logger.info(f"Loaded performance data: {len(self.strategy_stats)} strategies, {len(self.symbol_stats)} symbols, {len(self.trade_history)} trades")
            
        except Exception as e:
            logger.error(f"Failed to load performance data: {e}")
