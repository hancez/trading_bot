# TradingBot Widgets for ShellAgent

This directory contains custom widgets for ShellAgent that enable trading bot functionality with TradingView Pine scripts.

## Widgets Overview

1. **PineScriptExecutor**: Executes TradingView Pine scripts for backtesting trading strategies.
2. **ConfigurationManager**: Manages configuration files for trading strategies.
3. **BacktestReportGenerator**: Generates visual reports from backtesting results.
4. **StrategyLibrary**: Manages a collection of trading strategies.

## Requirements

- ShellAgent environment
- Python 3.7+
- Required Python packages:
  - plotly (for visualizations)
  - pandas (for data manipulation)

## Installation

The widgets are designed to work with ShellAgent's custom widget system. No separate installation is required beyond placing the files in the ShellAgent's custom_widgets directory.

## Usage Workflow

A typical workflow for using these widgets:

1. **Load a strategy** using the StrategyLibrary widget:
   - Get a strategy by name or ID
   - View the list of available strategies
   - Add new strategies to the library

2. **Configure the strategy** using the ConfigurationManager widget:
   - Load a configuration for a specific strategy
   - Modify parameters for the strategy
   - Save the updated configuration

3. **Execute the Pine script** using the PineScriptExecutor widget:
   - Provide the script content or file path
   - Set the execution parameters (symbol, timeframe, etc.)
   - Run in simulation mode for testing

4. **Generate a backtest report** using the BacktestReportGenerator widget:
   - Use the results from the PineScriptExecutor
   - Choose format (HTML, JSON, CSV)
   - Include charts and trade history in the report

## Widget Inputs and Outputs

### PineScriptExecutor

**Inputs**:
- `script_path`: Path to the Pine script file
- `script_content`: Direct Pine script content
- `symbol`: Symbol to backtest on (e.g., "BTCUSD")
- `timeframe`: Timeframe to backtest on (e.g., "1D")
- `start_date`: Start date for backtest
- `end_date`: End date for backtest
- `initial_capital`: Initial capital for backtest
- `position_size`: Position size in percent of capital
- `commission_percent`: Commission percent per trade
- `simulation_mode`: Run in simulation mode without TradingView API

**Outputs**:
- `status`: Success or error
- `message`: Status message
- `backtest_results`: Results of the backtest execution

### ConfigurationManager

**Inputs**:
- `action`: Action to perform (load, save, update)
- `config_path`: Path to the configuration file
- `strategy_name`: Name of the strategy
- `config_data`: JSON configuration data (for save/update)
- `config_content`: Direct JSON configuration content

**Outputs**:
- `status`: Success or error
- `message`: Status message
- `config_data`: Configuration data

### BacktestReportGenerator

**Inputs**:
- `backtest_results`: Backtest results to include in the report
- `strategy_name`: Name of the strategy
- `format`: Output format (html, json, csv)
- `include_charts`: Whether to include charts in the report
- `include_trades`: Whether to include individual trades in the report

**Outputs**:
- `status`: Success or error
- `message`: Status message
- `report_path`: Path to the generated report file
- `report_data`: Content of the report
- `download_url`: URL to download the report

### StrategyLibrary

**Inputs**:
- `action`: Action to perform (list, get, add, update, delete)
- `strategy_id`: ID of the strategy (for get, update, delete)
- `strategy_name`: Name of the strategy (for add)
- `script_path`: Path to the Pine script file (for add/update)
- `script_content`: Direct Pine script content (for add/update)
- `config_path`: Path to configuration file (for add/update)
- `config_content`: Direct JSON configuration content (for add/update)
- `tags`: Tags/categories for the strategy (for add/update)

**Outputs**:
- `status`: Success or error
- `message`: Status message
- `strategies`: List of strategies (for list action)
- `selected_strategy`: Details of a specific strategy (for get/add/update actions)

## Example Pine Scripts

The repository includes example Pine scripts in the root directory:
- `BTC spot position.pine`: A strategy for BTC spot trading
- `1x BTC-margined perpetual contract position.pine`: A strategy for BTC futures trading

## Notes

- Currently, the PineScriptExecutor operates in simulation mode only
- A real TradingView API integration could be added in the future
- All widgets support both file paths and direct content inputs for cloud compatibility 