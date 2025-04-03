# TradingBot Widgets User Guide

This guide provides detailed instructions on how to use the TradingBot widgets in ShellAgent, including how to configure each widget and how to connect them together to create a complete trading bot workflow.

## Quick Start

1. In ShellAgent, navigate to the "Custom Widgets/Trading Bot" section in the widget list
2. Add the widgets to your workflow
3. Configure each widget as described in this guide
4. Connect the widgets according to the workflow diagram provided

## Widget Configuration Guide

### StrategyLibrary Widget

The StrategyLibrary widget manages your trading strategies. You can list, add, retrieve, update, and delete strategies.

#### Configuration Instructions:

1. **Action** [required]: Choose one of the following actions:
   - `list`: Display all available strategies
   - `get`: Retrieve a specific strategy
   - `add`: Add a new strategy
   - `update`: Update an existing strategy
   - `delete`: Delete a strategy

2. **Strategy ID** [for get/update/delete]: 
   - Enter the unique ID of the strategy (required for update/delete operations)
   - Leave empty if using strategy name for retrieval

3. **Strategy Name** [for add]:
   - Enter a name for your strategy (must be unique)

4. **Script Content** [for add/update]:
   - Enter the Pine script content directly in this field
   - Recommended for cloud deployment
   - Format: `//@version=4` followed by your strategy code

5. **Script Path** [optional, local use only]:
   - Path to a local Pine script file
   - Not recommended for cloud deployment

6. **Config Content** [for add/update]:
   - Enter the strategy configuration as JSON
   - Example:
     ```json
     {
       "symbol": "BTCUSD",
       "timeframe": "1D",
       "parameters": {
         "fast_length": 10,
         "slow_length": 20
       }
     }
     ```

7. **Config Path** [optional, local use only]:
   - Path to a local configuration file
   - Not recommended for cloud deployment

8. **Tags** [optional]:
   - List of tags/categories for the strategy
   - Example: `["BTC", "SMA", "Trend"]`

#### Outputs:

- **Status**: Success or error
- **Message**: Informational message about the operation
- **Strategies**: List of strategies (when using the "list" action)
- **Selected Strategy**: Details of a specific strategy (when using the "get" action)

### ConfigurationManager Widget

The ConfigurationManager widget handles configuration files for your trading strategies.

#### Configuration Instructions:

1. **Action** [required]: Choose one of the following actions:
   - `load`: Load a configuration
   - `save`: Save a configuration
   - `update`: Update an existing configuration

2. **Config Content** [for load]:
   - Enter the configuration JSON content directly
   - Recommended for cloud deployment
   - Example:
     ```json
     {
       "symbol": "BTCUSD",
       "timeframe": "1D",
       "parameters": {
         "fast_length": 10,
         "slow_length": 20
       }
     }
     ```

3. **Config Path** [optional, local use only]:
   - Path to a local configuration file
   - Not recommended for cloud deployment

4. **Strategy Name** [optional]:
   - Name of the strategy to load configuration for
   - Used when you have predefined configurations

5. **Config Data** [for save/update]:
   - JSON configuration data to save/update
   - Used when you want to modify an existing configuration

#### Outputs:

- **Status**: Success or error
- **Message**: Informational message about the operation
- **Config Data**: The loaded or modified configuration data

### PineScriptExecutor Widget

The PineScriptExecutor widget executes TradingView Pine scripts for backtesting trading strategies.

#### Configuration Instructions:

1. **Script Content** [required if no script_path]:
   - Enter the Pine script content directly
   - Recommended for cloud deployment
   - Example:
     ```
     //@version=4
     strategy("SMA Crossover", overlay=true)
     fast_sma = sma(close, 10)
     slow_sma = sma(close, 20)
     long_entry = crossover(fast_sma, slow_sma)
     if (long_entry)
         strategy.entry("Long", strategy.long)
     ```

2. **Script Path** [optional, local use only]:
   - Path to a local Pine script file
   - Not recommended for cloud deployment

3. **Symbol** [required]:
   - Trading symbol to backtest on (e.g., "BTCUSD")

4. **Timeframe** [required]:
   - Timeframe for the backtest (e.g., "1D", "4H", "1H")

5. **Start Date** [required]:
   - Start date for the backtest in "YYYY-MM-DD" format

6. **End Date** [optional]:
   - End date for the backtest in "YYYY-MM-DD" format
   - Leave empty to use the current date

7. **Initial Capital** [required]:
   - Starting capital for the backtest (e.g., 10000.0)

8. **Position Size** [required]:
   - Position size as a percentage of capital (e.g., 100.0 for full capital)

9. **Commission Percent** [required]:
   - Commission percentage per trade (e.g., 0.1)

10. **Simulation Mode** [required]:
    - Set to True to run in simulation mode without TradingView API
    - Currently, only simulation mode is supported

#### Outputs:

- **Status**: Success or error
- **Message**: Informational message about the operation
- **Backtest Results**: Comprehensive backtest results including trades, performance metrics, and chart data

### BacktestReportGenerator Widget

The BacktestReportGenerator widget creates visual reports from backtest results.

#### Configuration Instructions:

1. **Backtest Results** [required]:
   - Results from the PineScriptExecutor widget
   - Connect this input to the "backtest_results" output of PineScriptExecutor

2. **Strategy Name** [required]:
   - Name of the strategy for the report title

3. **Format** [required]:
   - Report format: "html", "json", or "csv"
   - HTML provides interactive charts
   - JSON is useful for further processing
   - CSV is simple and easily importable

4. **Include Charts** [optional]:
   - Set to True to include performance charts (for HTML and JSON formats)
   - Set to False to omit charts

5. **Include Trades** [optional]:
   - Set to True to include individual trade details
   - Set to False to omit trade details

#### Outputs:

- **Status**: Success or error
- **Message**: Informational message about the operation
- **Report Path**: Path to the generated report file
- **Report Data**: Content of the report
- **Download URL**: URL to download the report

## Connecting Widgets Together

To create a complete trading bot workflow, connect the widgets in the following way:

```
1. StrategyLibrary (get) -> 2. ConfigurationManager (load) -> 3. PineScriptExecutor -> 4. BacktestReportGenerator
```

### Step-by-Step Connection Guide:

1. **Use StrategyLibrary to get a strategy**:
   - Configure the StrategyLibrary widget with action="get" and a strategy name or ID
   - The output "selected_strategy" contains the strategy details

2. **Use ConfigurationManager to load the configuration**:
   - Connect StrategyLibrary.selected_strategy.config to ConfigurationManager.config_content
   - Or manually configure the ConfigurationManager with your configuration
   - The output "config_data" contains the loaded configuration

3. **Use PineScriptExecutor to run the backtest**:
   - Connect StrategyLibrary.selected_strategy.script to PineScriptExecutor.script_content
   - Configure the other parameters (symbol, timeframe, etc.) based on the configuration
   - The output "backtest_results" contains the backtest results

4. **Use BacktestReportGenerator to create a report**:
   - Connect PineScriptExecutor.backtest_results to BacktestReportGenerator.backtest_results
   - Set the format, include_charts, and include_trades parameters
   - The output "report_data" contains the generated report

## Example JSON Input for Each Widget

### StrategyLibrary - Add Strategy:
```json
{
  "action": "add",
  "strategy_name": "SMA Crossover",
  "script_content": "//@version=4\nstrategy(\"SMA Crossover\", overlay=true)\nfast_sma = sma(close, 10)\nslow_sma = sma(close, 20)\nlong_entry = crossover(fast_sma, slow_sma)\nif (long_entry)\n    strategy.entry(\"Long\", strategy.long)",
  "config_content": "{\"symbol\": \"BTCUSD\", \"timeframe\": \"1D\", \"parameters\": {\"fast_length\": 10, \"slow_length\": 20}}",
  "tags": ["BTC", "SMA"]
}
```

### ConfigurationManager - Load Configuration:
```json
{
  "action": "load",
  "config_content": "{\"symbol\": \"BTCUSD\", \"timeframe\": \"1D\", \"parameters\": {\"fast_length\": 10, \"slow_length\": 20}}"
}
```

### PineScriptExecutor:
```json
{
  "script_content": "//@version=4\nstrategy(\"SMA Crossover\", overlay=true)\nfast_sma = sma(close, 10)\nslow_sma = sma(close, 20)\nlong_entry = crossover(fast_sma, slow_sma)\nif (long_entry)\n    strategy.entry(\"Long\", strategy.long)",
  "symbol": "BTCUSD",
  "timeframe": "1D",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 10000.0,
  "position_size": 100.0,
  "commission_percent": 0.1,
  "simulation_mode": true
}
```

### BacktestReportGenerator:
```json
{
  "backtest_results": {
    "strategy_name": "SMA Crossover",
    "symbol": "BTCUSD",
    "timeframe": "1D",
    "total_trades": 42,
    "winning_trades": 28,
    "losing_trades": 14,
    "win_rate": 66.67,
    "profit_factor": 2.35,
    "net_profit_percent": 145.8,
    "max_drawdown_percent": 18.2,
    "sharpe_ratio": 1.78,
    "trades": [
      {
        "id": 1,
        "entry_date": "2020-01-05",
        "exit_date": "2020-01-10",
        "side": "Long",
        "entry_price": 30000,
        "exit_price": 31500,
        "profit_percent": 5.0,
        "profit_amount": 1500
      }
    ]
  },
  "strategy_name": "SMA Crossover",
  "format": "html",
  "include_charts": true,
  "include_trades": true
}
```

## Cloud Deployment Tips

For cloud deployment:
- Always use the "script_content" and "config_content" fields instead of file paths
- Ensure all required dependencies are installed (check requirements.txt)
- Test your workflow locally before deploying to the cloud

## Troubleshooting

If you encounter issues:
1. Check the widget status and message outputs for error details
2. Ensure all required inputs are provided
3. Verify that the Pine script syntax is correct
4. Check that JSON configurations are properly formatted
5. Make sure dependencies are installed (plotly, pandas, pydantic) 