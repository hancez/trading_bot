"""
Trading bot widgets for ShellAgent.
"""

# Initialize widget variables with None
PineScriptExecutor = None
ConfigurationManager = None
BacktestReportGenerator = None
StrategyLibrary = None

# Define a function to load widgets with lazy loading
def _load_widgets():
    """
    Lazy load the widget implementations to avoid import errors during ShellAgent startup.
    """
    global PineScriptExecutor, ConfigurationManager, BacktestReportGenerator, StrategyLibrary
    
    try:
        from .pine_script_executor import PineScriptExecutor
    except ImportError:
        pass
    
    try:
        from .configuration_manager import ConfigurationManager
    except ImportError:
        pass
    
    try:
        from .backtest_report_generator import BacktestReportGenerator
    except ImportError:
        pass
    
    try:
        from .strategy_library import StrategyLibrary
    except ImportError:
        pass

# Load widgets when the module is imported
_load_widgets()

# Export available widgets
__all__ = [
    "PineScriptExecutor",
    "ConfigurationManager", 
    "BacktestReportGenerator",
    "StrategyLibrary"
]

# Define a workflow example
WORKFLOW_EXAMPLE = """
# TradingBot Workflow Example

This is an example of how to use the TradingBot widgets together:

1. **Load a strategy** using the StrategyLibrary widget
   - Action: "get"
   - Strategy name: "SMA Crossover"

2. **Configure the strategy** using the ConfigurationManager widget
   - Action: "load"
   - Strategy name: "SMA Crossover"
   - Or load from a config file path

3. **Execute the Pine script** using the PineScriptExecutor widget
   - Use script from the strategy library
   - Configure with parameters from ConfigurationManager
   - Run in simulation mode for testing

4. **Generate a backtest report** using the BacktestReportGenerator widget
   - Use results from the PineScriptExecutor
   - Choose format (HTML, JSON, CSV)
   - Include charts and trade history

Each widget can also be used independently as needed.
"""
