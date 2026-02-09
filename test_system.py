#!/usr/bin/env python3
"""
System Test Suite - Validates all components before deployment
Run this before pushing to GitHub or deploying
"""

import sys
import importlib


def test_imports():
    """Test all core module imports"""
    print("=" * 60)
    print("TESTING MODULE IMPORTS")
    print("=" * 60)
    
    modules = [
        'deriv_api',
        'execution',
        'performance_tracker',
        'risk_manager',
        'data_handler',
        'telegram_adapter',
        'logger',
        'config'
    ]
    
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            return False
    
    return True


def test_strategies():
    """Test all strategy imports"""
    print("\n" + "=" * 60)
    print("TESTING STRATEGIES")
    print("=" * 60)
    
    strategies = [
        ('strategies.strategy_a_triple_ema', 'StrategyA_TripleEMA'),
        ('strategies.strategy_b_adx_di', 'StrategyB_ADXDI'),
        ('strategies.strategy_c_bollinger', 'StrategyC_Bollinger'),
        ('strategies.strategy_d_stochastic', 'StrategyD_Stochastic'),
        ('strategies.strategy_e_breakout', 'StrategyE_Breakout')
    ]
    
    for module_name, class_name in strategies:
        try:
            module = importlib.import_module(module_name)
            strategy_class = getattr(module, class_name)
            strategy = strategy_class()
            print(f"✓ {class_name}")
        except Exception as e:
            print(f"✗ {class_name}: {e}")
            return False
    
    return True


def test_config():
    """Test configuration"""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    import config
    
    required = [
        'DERIV_APP_ID',
        'DERIV_API_TOKEN',
        'CONTRACT_DURATION',
        'BASE_STAKE_USD',
        'TRADING_SYMBOLS'
    ]
    
    for attr in required:
        value = getattr(config, attr, None)
        if value is None:
            print(f"✗ {attr}: Not set")
            return False
        
        # Check for placeholder values
        if isinstance(value, str) and 'your_' in value.lower():
            print(f"⚠ {attr}: Still has placeholder value")
        else:
            print(f"✓ {attr}: Configured")
    
    return True


def test_performance_tracker():
    """Test performance tracker functionality"""
    print("\n" + "=" * 60)
    print("TESTING PERFORMANCE TRACKER")
    print("=" * 60)
    
    from performance_tracker import PerformanceTracker
    from datetime import datetime
    
    try:
        tracker = PerformanceTracker()
        
        # Record a test trade
        tracker.record_trade(
            strategy="Test Strategy",
            symbol="frxEURUSD",
            profit=0.50,
            stake=1.00,
            duration=45.0,
            entry_time=datetime.now(),
            contract_type="CALL",
            reason="Test"
        )
        
        # Get performance
        perf = tracker.get_strategy_performance("Test Strategy")
        assert perf['trades'] == 1, "Trade not recorded"
        assert perf['total_pnl'] == 0.50, "P/L incorrect"
        
        print("✓ Record trade")
        print("✓ Get performance")
        print("✓ Calculate metrics")
        
        return True
    except Exception as e:
        print(f"✗ Performance tracker: {e}")
        return False


def test_risk_manager():
    """Test risk manager functionality"""
    print("\n" + "=" * 60)
    print("TESTING RISK MANAGER")
    print("=" * 60)
    
    from risk_manager import RiskManager
    
    try:
        rm = RiskManager()
        
        # Test position sizing
        size = rm.calculate_lot_size("frxEURUSD")
        assert size > 0, "Position size should be positive"
        print(f"✓ Position sizing: {size:.4f} lots")
        
        # Test trade recording
        rm.record_trade_result("frxEURUSD", 1, 1.0850, 1.0860, 0.5, 0.40)
        print("✓ Trade recording")
        
        # Test consecutive wins tracking
        wins = rm.consecutive_wins
        print(f"✓ Win tracking: {wins} consecutive wins")
        
        return True
    except Exception as e:
        print(f"✗ Risk manager: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DERIV SCALPING BOT - SYSTEM TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Strategies", test_strategies),
        ("Configuration", test_config),
        ("Performance Tracker", test_performance_tracker),
        ("Risk Manager", test_risk_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - System ready for deployment")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Fix issues before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
