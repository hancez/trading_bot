import os
import json
import tempfile
import re  # Added import
from typing import Dict, Any, List, Optional
from pydantic import Field

from proconfig.widgets.base import WIDGETS, BaseWidget

# ------------------------ helper wrappers (module-level) ------------------------
def Input(*args, **kwargs):
    if "type" not in kwargs:
        default_val = args[0] if args else None
        if isinstance(default_val, bool):
            kwargs["type"] = "boolean"
        elif isinstance(default_val, int):
            kwargs["type"] = "integer"
        elif isinstance(default_val, float):
            kwargs["type"] = "number"
        elif isinstance(default_val, (list, tuple)):
            kwargs["type"] = "array"
        elif isinstance(default_val, dict):
            kwargs["type"] = "object"
        else:
            kwargs["type"] = "string"
    return Field(*args, **kwargs)


def Output(*args, **kwargs):
    return Input(*args, **kwargs)

# ------------------------------------------------------------------------------

@WIDGETS.register_module()
class PineScriptExecutor(BaseWidget):
    CATEGORY = "Custom Widgets/Trading Bot"
    NAME = "Pine Script Executor"
    
    class InputsSchema(BaseWidget.InputsSchema):
        script_content: str = Input("", description="Direct Pine script content (preferred for cloud deployment)", type="string")
        script_path: str = Input("", description="Path to the Pine script file (local file system only)", type="string")
        symbol: str = Input("BTCUSD", description="Symbol to backtest on", type="string")
        timeframe: str = Input("1D", description="Timeframe to backtest on", type="string")
        start_date: str = Input("2020-01-01", description="Start date for backtest", type="string")
        end_date: str = Input("", description="End date for backtest (leave empty for now)", type="string")
        initial_capital: float = Input(10000.0, description="Initial capital for backtest", type="number")
        position_size: float = Input(100.0, description="Position size in percent of capital", type="number")
        commission_percent: float = Input(0.1, description="Commission percent per trade", type="number")
        simulation_mode: bool = Input(True, description="Run in simulation mode without TradingView API", type="boolean")
        config_json: str = Input("", description="Optional JSON config to override script inputs", type="string")
        
    class OutputsSchema(BaseWidget.OutputsSchema):
        status: str = Output("", description="Execution status", type="string")
        message: str = Output("", description="Human-readable message", type="string")
        backtest_results: Dict[str, Any] = Output({}, description="Backtest result object", type="object")
        
    def execute(self, environ, config):
        try:
            # Determine if we're using file path or direct content
            use_direct_content = bool(config.script_content and config.script_content.strip())
            script_content = None
            
            if use_direct_content:
                script_content = config.script_content
            elif config.script_path and os.path.isfile(config.script_path):
                with open(config.script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
            else:
                return {
                    "status": "error",
                    "message": "No valid Pine script provided. Please provide either a script_path or script_content.",
                    "backtest_results": {}
                }
                
            # Parse JSON config and apply it
            cfg = {}
            if config.config_json:
                try:
                    cfg = json.loads(config.config_json)
                except Exception:
                    pass # Ignore invalid JSON

            # Override common parameters from config if present
            start_date = cfg.get("回测起始日期") or cfg.get("开始日期") or config.start_date
            end_date   = cfg.get("回测结束日期") or cfg.get("结束日期") or config.end_date
            
            # Apply other config values directly to the script content
            if cfg:
                script_content = self._apply_config(script_content, cfg)

            # Check if we're in simulation mode
            if config.simulation_mode:
                # In simulation mode, we'll generate a mock backtest result
                backtest_results = self._simulate_backtest(
                    script_content=script_content,
                    symbol=config.symbol,
                    timeframe=config.timeframe,
                    start_date=start_date[:10] if start_date else "", # Use potentially overridden date
                    end_date=end_date[:10] if end_date else "",       # Use potentially overridden date
                    initial_capital=config.initial_capital,
                    position_size=config.position_size,
                    commission_percent=config.commission_percent
                )
                
                return {
                    "status": "success",
                    "message": f"Executed Pine script in simulation mode for {config.symbol} on {config.timeframe} timeframe",
                    "backtest_results": backtest_results
                }
            else:
                # In real mode, we would call the TradingView API
                # This is a placeholder for future implementation
                return {
                    "status": "error",
                    "message": "Real TradingView API execution is not implemented yet",
                    "backtest_results": {}
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to execute Pine script: {str(e)}",
                "backtest_results": {}
            }
            
    def _apply_config(self, script: str, cfg: dict) -> str:
        """Applies config values to the Pine script content using regex substitution."""
        mapping = {
            # 策略1 specific keys
            r"(benchmarkSymbol\\s*=\\s*input\\.symbol\\()\\s*[^,)]*": ("对标标的", '"{}"'),
            r"(ma_length1\\s*=\\s*input\\.int\\()\\s*[^,)]*": ("MAX1长度", '{}'),
            r"(ma_length2\\s*=\\s*input\\.int\\()\\s*[^,)]*": ("MAX2长度", '{}'),
            r"(threshold\\s*=\\s*input\\.float\\()\\s*[^,)]*": ("突破门槛(%)", '{} / 100'),
            # 策略2 specific keys
            r"(ma120_length\\s*=\\s*input\\.int\\()\\s*[^,)]*": ("MA120Length", '{}'),
            r"(adx_length\\s*=\\s*input\\.int\\()\\s*[^,)]*": ("ADXLength", '{}'),
            r"(adx_smoothing\\s*=\\s*input\\.int\\()\\s*[^,)]*": ("ADX平滑", '{}'),
            r"(threshold\\s*=\\s*input\\.float\\()\\s*[^,)]*": ("Threshold(%)", '{} / 100'),
            r"(adxhlin\\s*=\\s*input\\.int\\()\\s*[^,)]*": ("Adx阈值", '{}'),
            # Note: start/end dates are handled separately in execute method
        }
        for pattern, (cfg_key, fmt) in mapping.items():
            if cfg_key in cfg:
                value = fmt.format(cfg[cfg_key])
                # Substitute the first argument in the input function call
                script = re.sub(pattern, rf"\\1{value}", script, count=1)
        return script

    def _simulate_backtest(self, script_content, symbol, timeframe, start_date, end_date, 
                         initial_capital, position_size, commission_percent):
        """
        Simulate a backtest without actually executing the Pine script.
        This is a placeholder for testing the widget workflow.
        """
        
        def _fetch_current_price(sym: str) -> Optional[float]:
            """Return current USD price for a given crypto symbol using CoinGecko simple API."""
            try:
                import requests, re
                sym_low = sym.lower()
                # quick symbol→id mapping
                mapping = {
                    "btc": "bitcoin",
                    "btcusd": "bitcoin",
                    "btc-usd": "bitcoin",
                    "btc/usd": "bitcoin",
                    "eth": "ethereum",
                    "ethusd": "ethereum",
                    "eth-usd": "ethereum",
                    "eth/usd": "ethereum",
                }
                # strip non-alpha chars for generic mapping (e.g. BTCUSDT -> btcusdt -> btc)
                if sym_low not in mapping:
                    pure = re.sub(r"[^a-z]", "", sym_low)
                    if pure.endswith("usd"):
                        pure = pure[:-3]
                    if pure in mapping:
                        sym_low = pure
                cg_id = mapping.get(sym_low)
                if not cg_id:
                    return None
                resp = requests.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": cg_id, "vs_currencies": "usd"},
                    timeout=5,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return float(data[cg_id]["usd"])
            except Exception:
                pass
            return None
        
        # Parse the script content to extract strategy name
        strategy_name = "Unknown Strategy"
        for line in script_content.split('\n'):
            if "strategy(" in line:
                # Extract the strategy name from the strategy declaration
                parts = line.split('"')
                if len(parts) > 1:
                    strategy_name = parts[1]
                break
                
        # Fetch a baseline current price (if available)
        current_price = _fetch_current_price(symbol) or 0
        
        # Generate a simple simulation based on the script and parameters
        # This is not a real backtest, just a mock result for demonstration
        
        # Generate mock trades
        import random
        from datetime import datetime, timedelta
        
        random.seed(hash(script_content + symbol + timeframe))
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end = datetime.now()
            
        # Generate dates for trades
        dates = []
        current = start
        while current < end:
            if random.random() < 0.1:  # 10% chance of a trade on any day
                dates.append(current)
            current += timedelta(days=1)
            
        # Generate trades
        trades = []
        equity = initial_capital
        high_watermark = initial_capital
        max_drawdown = 0
        
        for i, date in enumerate(dates):
            # Decide if long or short
            side = "Long" if random.random() < 0.6 else "Short"
            
            # Generate entry and exit dates
            entry_date = date
            hold_days = random.randint(1, 10)
            exit_date = entry_date + timedelta(days=hold_days)
            
            if exit_date > end:
                exit_date = end
                
            # Generate prices for this trade (use current_price as baseline if available)
            base_price = None
            base_price = current_price

            if base_price == 0:
                # Fallback: previous mock range (1k-2k) adjusted to larger range for BTC
                if symbol.lower().startswith("btc"):
                    base_price = 20000 + random.random() * 40000  # 20k-60k
                else:
                    base_price = 1000 + random.random() * 1000
            price_change = (random.random() - 0.3) * 10  # -3% to +7% change
            
            if side == "Long":
                entry_price = base_price
                exit_price = base_price * (1 + price_change / 100)
                profit_percent = price_change - commission_percent
            else:  # Short
                entry_price = base_price
                exit_price = base_price * (1 + price_change / 100)
                profit_percent = -price_change - commission_percent
                
            # Calculate profit
            trade_size = equity * position_size / 100
            profit_amount = trade_size * profit_percent / 100
            
            # Update equity
            equity += profit_amount
            
            # Update drawdown
            if equity > high_watermark:
                high_watermark = equity
            drawdown_percent = (high_watermark - equity) / high_watermark * 100
            if drawdown_percent > max_drawdown:
                max_drawdown = drawdown_percent
                
            trades.append({
                "id": i + 1,
                "entry_date": entry_date.strftime("%Y-%m-%d"),
                "exit_date": exit_date.strftime("%Y-%m-%d"),
                "side": side,
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "profit_percent": round(profit_percent, 2),
                "profit_amount": round(profit_amount, 2)
            })
            
        # Calculate performance metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t["profit_percent"] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = sum(t["profit_amount"] for t in trades if t["profit_percent"] > 0)
        gross_loss = abs(sum(t["profit_amount"] for t in trades if t["profit_percent"] <= 0))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        net_profit = sum(t["profit_amount"] for t in trades)
        net_profit_percent = (net_profit / initial_capital) * 100
        
        # Determine last price for current market snapshot. Use fetched current_price if available.
        last_price = round(current_price if current_price else trades[-1]["exit_price"] if trades else base_price, 2)

        # Mark price unavailability flag (for UI display) if we still don't have a price > 0
        price_unavailable = last_price == 0

        # Generate chart data for equity curve
        equity_curve = {"x": [], "y": []}
        current_equity = initial_capital
        equity_curve["x"].append("Day 0")
        equity_curve["y"].append(100)  # Start at 100%
        
        sorted_trades = sorted(trades, key=lambda t: t["entry_date"])
        for i, trade in enumerate(sorted_trades):
            current_equity += trade["profit_amount"]
            equity_pct = (current_equity / initial_capital) * 100
            equity_curve["x"].append(f"Trade {i+1}")
            equity_curve["y"].append(round(equity_pct, 2))
            
        # Generate drawdown curve
        drawdown_curve = {"x": equity_curve["x"], "y": []}
        high_watermark = 100
        for equity_pct in equity_curve["y"]:
            if equity_pct > high_watermark:
                high_watermark = equity_pct
            drawdown = (high_watermark - equity_pct) / high_watermark * 100
            drawdown_curve["y"].append(round(-drawdown, 2))  # negative to show drawdown going down
            
        # Generate monthly returns
        monthly_returns = {"x": [], "y": []}
        months = {}
        
        for trade in trades:
            entry_month = trade["entry_date"][:7]  # YYYY-MM format
            if entry_month not in months:
                months[entry_month] = 0
            months[entry_month] += trade["profit_amount"]
            
        for month, profit in sorted(months.items()):
            monthly_returns["x"].append(month)
            monthly_returns["y"].append(round((profit / initial_capital) * 100, 2))
            
        # Return the simulated backtest results
        return {
            "strategy_name": strategy_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date if end_date else datetime.now().strftime("%Y-%m-%d"),
            "initial_capital": initial_capital,
            "position_size": position_size,
            "commission_percent": commission_percent,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "net_profit": round(net_profit, 2),
            "net_profit_percent": round(net_profit_percent, 2),
            "max_drawdown_percent": round(max_drawdown, 2),
            "sharpe_ratio": round(random.uniform(0.8, 2.5), 2),  # Mock sharpe ratio
            "trades": trades,
            "chart_data": {
                "equity_curve": equity_curve,
                "drawdown_curve": drawdown_curve,
                "monthly_returns": monthly_returns
            },
            "execution_mode": "simulation",
            "last_price": round(last_price, 2),
            "price_unavailable": price_unavailable
        }

if __name__ == "__main__":
    import time
    import traceback
    
    # Test the widget
    widget = PineScriptExecutor()
    
    # Define test configuration
    test_config = {
        "script_path": "test_strategy.pine",
        "script_content": """
        //@version=4
        strategy("Test Strategy", overlay=true)
        
        // Calculate EMAs
        ema20 = ema(close, 20)
        ema50 = ema(close, 50)
        
        // Entry conditions
        long_entry = crossover(ema20, ema50)
        short_entry = crossunder(ema20, ema50)
        
        // Exit conditions
        long_exit = crossunder(ema20, ema50)
        short_exit = crossover(ema20, ema50)
        
        // Strategy orders
        if (long_entry)
            strategy.entry("Long", strategy.long)
        
        if (long_exit)
            strategy.close("Long")
        
        if (short_entry)
            strategy.entry("Short", strategy.short)
        
        if (short_exit)
            strategy.close("Short")
        """,
        "symbol": "BTCUSD",
        "timeframe": "1D",
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 10000.0,
        "position_size": 100.0,
        "commission_percent": 0.1,
        "simulation_mode": True
    }
    
    # Execute the test
    print("Testing PineScriptExecutor widget...")
    start_time = time.time()
    
    try:
        output = widget({}, test_config)
        execution_time = time.time() - start_time
        
        print(f"Status: {output['status']}")
        print(f"Message: {output['message']}")
        print(f"Execution time: {execution_time:.2f}s")
        
        if output['status'] == 'success':
            results = output['backtest_results']
            print(f"\nStrategy: {results['strategy_name']}")
            print(f"Symbol: {results['symbol']}, Timeframe: {results['timeframe']}")
            print(f"Period: {results['start_date']} to {results['end_date']}")
            print(f"Total trades: {results['total_trades']}")
            print(f"Win rate: {results['win_rate']}%")
            print(f"Net profit: {results['net_profit_percent']}%")
            print(f"Max drawdown: {results['max_drawdown_percent']}%")
            
            print(f"\nSample trades ({min(3, len(results['trades']))} of {len(results['trades'])}):")
            for i, trade in enumerate(results['trades'][:3]):
                print(f"  {trade['entry_date']} - {trade['side']} - {trade['profit_percent']}%")
                
            print(f"\nTest completed successfully.")
        else:
            print(f"Test FAILED: {output['message']}")
        
    except Exception as e:
        print(f"Test FAILED with exception:")
        traceback.print_exc() 