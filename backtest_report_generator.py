import os
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import Field
import base64
import shutil
import pathlib

from proconfig.widgets.base import WIDGETS, BaseWidget

@WIDGETS.register_module()
class BacktestReportGenerator(BaseWidget):
    CATEGORY = "Custom Widgets/Trading Bot"
    NAME = "Backtest Report Generator"
    
    class InputsSchema(BaseWidget.InputsSchema):
        backtest_results: Dict[str, Any] = Field({}, description="Backtest results to include in the report (object mode)")
        backtest_results_json: Union[str, Dict[str, Any]] = Field("", description="Backtest results as JSON string or object (legacy)")
        strategy_name: str = Field("", description="Name of the strategy")
        format: str = Field("html", description="Output format (html, json, csv)")
        include_charts: bool = Field(True, description="Whether to include charts in the report")
        include_trades: bool = Field(True, description="Whether to include individual trades in the report")
        
    class OutputsSchema(BaseWidget.OutputsSchema):
        status: str
        message: str
        report_path: str
        report_data: str
        download_url: str
        
    def execute(self, environ, config):
        try:
            # Extract parameters
            # Legacy compatibility: accept both object and JSON string
            if config.backtest_results:
                backtest_results = config.backtest_results
            elif config.backtest_results_json:
                if isinstance(config.backtest_results_json, str):
                    backtest_results = json.loads(config.backtest_results_json)
                else:
                    backtest_results = config.backtest_results_json  # already a dict
            else:
                backtest_results = {}
            strategy_name = config.strategy_name
            report_format = config.format.lower()
            include_charts = config.include_charts
            include_trades = config.include_trades
            
            # Validate input
            if not backtest_results:
                return {
                    "status": "error",
                    "message": "No backtest results provided",
                    "report_path": "",
                    "report_data": "",
                    "download_url": ""
                }
                
            # Create report based on format
            if report_format == "html":
                report_path, report_data = self._generate_html_report(
                    backtest_results, strategy_name, include_charts, include_trades)
            elif report_format == "json":
                report_path, report_data = self._generate_json_report(
                    backtest_results, strategy_name, include_charts, include_trades)
            elif report_format == "csv":
                report_path, report_data = self._generate_csv_report(
                    backtest_results, strategy_name, include_trades)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported format: {report_format}",
                    "report_path": "",
                    "report_data": "",
                    "download_url": ""
                }
                
            # If running inside ShellAgent server, expose file via /static/ path
            static_reports_dir = pathlib.Path("data/app/reports")
            static_reports_dir.mkdir(parents=True, exist_ok=True)
            static_report_path = static_reports_dir / os.path.basename(report_path)
            try:
                shutil.copy(report_path, static_report_path)
            except Exception:
                pass  # ignore if copy fails

            download_url = f"/static/reports/{os.path.basename(report_path)}"
            
            return {
                "status": "success",
                "message": f"Generated {report_format.upper()} report for {strategy_name}",
                "report_path": report_path,
                "report_data": report_data,
                "download_url": download_url
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate report: {str(e)}",
                "report_path": "",
                "report_data": "",
                "download_url": ""
            }
            
    def _generate_html_report(self, backtest_results, strategy_name, include_charts, include_trades):
        """Generate an HTML report"""
        
        # Create a temporary file for the report
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        report_filename = f"{strategy_name.replace(' ', '_')}_{timestamp}.html"
        report_path = os.path.join(tempfile.gettempdir(), report_filename)
        
        # Start building the HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report: {strategy_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    color: #333;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .summary-box {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #dee2e6;
                    padding: 8px 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #e9ecef;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .chart-container {{
                    margin-bottom: 30px;
                }}
                .profit {{
                    color: green;
                }}
                .loss {{
                    color: red;
                }}
            </style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <h1>Backtest Report: {strategy_name}</h1>
            <div class="summary-box">
                <h2>Performance Summary</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Net Profit</td>
                        <td>{backtest_results.get('net_profit_percent', 'N/A')}%</td>
                    </tr>
                    <tr>
                        <td>Total Trades</td>
                        <td>{backtest_results.get('total_trades', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Win Rate</td>
                        <td>{backtest_results.get('win_rate', 'N/A')}%</td>
                    </tr>
                    <tr>
                        <td>Profit Factor</td>
                        <td>{backtest_results.get('profit_factor', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Max Drawdown</td>
                        <td>{backtest_results.get('max_drawdown_percent', 'N/A')}%</td>
                    </tr>
                    <tr>
                        <td>Sharpe Ratio</td>
                        <td>{backtest_results.get('sharpe_ratio', 'N/A')}</td>
                    </tr>
                </table>
            </div>
        """
        
        # Add charts if requested
        if include_charts and 'chart_data' in backtest_results:
            html_content += """
            <h2>Performance Charts</h2>
            <div class="chart-container">
                <div id="equity-chart" style="width: 100%; height: 400px;"></div>
            </div>
            <div class="chart-container">
                <div id="drawdown-chart" style="width: 100%; height: 300px;"></div>
            </div>
            <div class="chart-container">
                <div id="monthly-returns-chart" style="width: 100%; height: 300px;"></div>
            </div>
            
            <script>
            """
            
            # Add chart data and plotting code
            if 'equity_curve' in backtest_results.get('chart_data', {}):
                equity_data = backtest_results['chart_data']['equity_curve']
                html_content += f"""
                var equityData = {{
                    x: {json.dumps(equity_data.get('x', []))},
                    y: {json.dumps(equity_data.get('y', []))},
                    mode: 'lines',
                    name: 'Equity Curve',
                    line: {{
                        color: 'rgb(31, 119, 180)',
                        width: 2
                    }}
                }};
                
                var equityLayout = {{
                    title: 'Equity Curve',
                    xaxis: {{
                        title: 'Time'
                    }},
                    yaxis: {{
                        title: 'Equity (%)'
                    }}
                }};
                
                Plotly.newPlot('equity-chart', [equityData], equityLayout);
                """
            
            if 'drawdown_curve' in backtest_results.get('chart_data', {}):
                drawdown_data = backtest_results['chart_data']['drawdown_curve']
                html_content += f"""
                var drawdownData = {{
                    x: {json.dumps(drawdown_data.get('x', []))},
                    y: {json.dumps(drawdown_data.get('y', []))},
                    mode: 'lines',
                    name: 'Drawdown',
                    line: {{
                        color: 'rgb(214, 39, 40)',
                        width: 2
                    }},
                    fill: 'tozeroy'
                }};
                
                var drawdownLayout = {{
                    title: 'Drawdown Chart',
                    xaxis: {{
                        title: 'Time'
                    }},
                    yaxis: {{
                        title: 'Drawdown (%)'
                    }}
                }};
                
                Plotly.newPlot('drawdown-chart', [drawdownData], drawdownLayout);
                """
            
            if 'monthly_returns' in backtest_results.get('chart_data', {}):
                monthly_data = backtest_results['chart_data']['monthly_returns']
                html_content += f"""
                var monthlyData = {{
                    x: {json.dumps(monthly_data.get('x', []))},
                    y: {json.dumps(monthly_data.get('y', []))},
                    type: 'bar',
                    marker: {{
                        color: {json.dumps(['rgb(44, 160, 44)' if y >= 0 else 'rgb(214, 39, 40)' for y in monthly_data.get('y', [])])}
                    }}
                }};
                
                var monthlyLayout = {{
                    title: 'Monthly Returns',
                    xaxis: {{
                        title: 'Month'
                    }},
                    yaxis: {{
                        title: 'Return (%)'
                    }}
                }};
                
                Plotly.newPlot('monthly-returns-chart', [monthlyData], monthlyLayout);
                """
            
            html_content += """
            </script>
            """
        
        # Add trades table if requested
        if include_trades and 'trades' in backtest_results:
            html_content += """
            <h2>Trade History</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>Entry Date</th>
                    <th>Exit Date</th>
                    <th>Side</th>
                    <th>Entry Price</th>
                    <th>Exit Price</th>
                    <th>Profit/Loss</th>
                    <th>P/L (%)</th>
                </tr>
            """
            
            for trade in backtest_results['trades']:
                profit_class = "profit" if trade.get('profit_percent', 0) >= 0 else "loss"
                html_content += f"""
                <tr>
                    <td>{trade.get('id', 'N/A')}</td>
                    <td>{trade.get('entry_date', 'N/A')}</td>
                    <td>{trade.get('exit_date', 'N/A')}</td>
                    <td>{trade.get('side', 'N/A')}</td>
                    <td>{trade.get('entry_price', 'N/A')}</td>
                    <td>{trade.get('exit_price', 'N/A')}</td>
                    <td class="{profit_class}">{trade.get('profit_amount', 0)}</td>
                    <td class="{profit_class}">{trade.get('profit_percent', 0)}%</td>
                </tr>
                """
                
            html_content += """
            </table>
            """
        
        # Close HTML
        html_content += """
        </body>
        </html>
        """
        
        # Write to file
        with open(report_path, 'w') as f:
            f.write(html_content)
            
        return report_path, html_content
        
    def _generate_json_report(self, backtest_results, strategy_name, include_charts, include_trades):
        """Generate a JSON report"""
        
        # Create a temporary file for the report
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        report_filename = f"{strategy_name.replace(' ', '_')}_{timestamp}.json"
        report_path = os.path.join(tempfile.gettempdir(), report_filename)
        
        # Copy the results and add metadata
        report_data = {
            "strategy_name": strategy_name,
            "generation_time": datetime.now().isoformat(),
            "summary": {
                "net_profit_percent": backtest_results.get('net_profit_percent', None),
                "total_trades": backtest_results.get('total_trades', None),
                "winning_trades": backtest_results.get('winning_trades', None),
                "losing_trades": backtest_results.get('losing_trades', None),
                "win_rate": backtest_results.get('win_rate', None),
                "profit_factor": backtest_results.get('profit_factor', None),
                "max_drawdown_percent": backtest_results.get('max_drawdown_percent', None),
                "sharpe_ratio": backtest_results.get('sharpe_ratio', None),
            }
        }
        
        # Add charts if requested
        if include_charts and 'chart_data' in backtest_results:
            report_data["charts"] = backtest_results.get('chart_data', {})
            
        # Add trades if requested
        if include_trades and 'trades' in backtest_results:
            report_data["trades"] = backtest_results.get('trades', [])
            
        # Add configuration
        if 'strategy_config' in backtest_results:
            report_data["configuration"] = backtest_results.get('strategy_config', {})
            
        # Write to file
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        return report_path, json.dumps(report_data, indent=2)
        
    def _generate_csv_report(self, backtest_results, strategy_name, include_trades):
        """Generate a CSV report"""
        
        # Create a temporary file for the report
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        report_filename = f"{strategy_name.replace(' ', '_')}_{timestamp}.csv"
        report_path = os.path.join(tempfile.gettempdir(), report_filename)
        
        # Start with headers and summary
        csv_content = f"# Backtest Report: {strategy_name}\n"
        csv_content += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        csv_content += "## Performance Summary\n"
        csv_content += "Metric,Value\n"
        csv_content += f"Net Profit,{backtest_results.get('net_profit_percent', 'N/A')}%\n"
        csv_content += f"Total Trades,{backtest_results.get('total_trades', 'N/A')}\n"
        csv_content += f"Winning Trades,{backtest_results.get('winning_trades', 'N/A')}\n"
        csv_content += f"Losing Trades,{backtest_results.get('losing_trades', 'N/A')}\n"
        csv_content += f"Win Rate,{backtest_results.get('win_rate', 'N/A')}%\n"
        csv_content += f"Profit Factor,{backtest_results.get('profit_factor', 'N/A')}\n"
        csv_content += f"Max Drawdown,{backtest_results.get('max_drawdown_percent', 'N/A')}%\n"
        csv_content += f"Sharpe Ratio,{backtest_results.get('sharpe_ratio', 'N/A')}\n\n"
        
        # Add trades if requested
        if include_trades and 'trades' in backtest_results:
            csv_content += "## Trade History\n"
            csv_content += "ID,Entry Date,Exit Date,Side,Entry Price,Exit Price,Profit/Loss,P/L (%)\n"
            
            for trade in backtest_results['trades']:
                csv_content += f"{trade.get('id', '')},{trade.get('entry_date', '')},{trade.get('exit_date', '')},"
                csv_content += f"{trade.get('side', '')},{trade.get('entry_price', '')},{trade.get('exit_price', '')},"
                csv_content += f"{trade.get('profit_amount', '')},{trade.get('profit_percent', '')}%\n"
        
        # Write to file
        with open(report_path, 'w') as f:
            f.write(csv_content)
            
        return report_path, csv_content

if __name__ == "__main__":
    import time
    import os
    import traceback
    
    # Test the widget
    widget = BacktestReportGenerator()
    
    def run_test_case(test_name, config, expected_status=None):
        """Run a test case and print results"""
        print(f"\n{'='*20} TEST: {test_name} {'='*20}")
        print(f"Config: {config}")
        start_time = time.time()
        
        try:
            # Execute widget
            output = widget({}, config)
            execution_time = time.time() - start_time
            
            # Print results
            print(f"Status: {output['status']}")
            print(f"Message: {output['message']}")
            print(f"Execution time: {execution_time:.2f}s")
            
            if output['status'] == 'success':
                print(f"Report path: {output['report_path']}")
                print(f"Download URL: {output['download_url']}")
                
                # Check if file was created
                if os.path.exists(output['report_path']):
                    print(f"✅ Report file created successfully")
                    file_size = os.path.getsize(output['report_path'])
                    print(f"File size: {file_size} bytes")
                else:
                    print(f"❌ Report file not found at {output['report_path']}")
                
                # Print a sample of the report data (first 100 chars)
                if output['report_data']:
                    print(f"Report data sample: {output['report_data'][:100]}...")
            
            # Validate expected status if provided
            if expected_status and output['status'] != expected_status:
                print(f"❌ Test FAILED: Expected status '{expected_status}', got '{output['status']}'")
                return False, None
            
            print(f"✅ Test PASSED")
            return True, output['report_path'] if output['status'] == 'success' else None
            
        except Exception as e:
            print(f"❌ Test FAILED with exception:")
            traceback.print_exc()
            return False, None
    
    # Sample backtest results
    sample_backtest_results = {
        "total_trades": 42,
        "winning_trades": 28,
        "losing_trades": 14,
        "win_rate": 66.67,
        "profit_factor": 2.35,
        "net_profit_percent": 145.8,
        "max_drawdown_percent": 18.2,
        "sharpe_ratio": 1.78,
        "symbol": "BTCUSD",
        "timeframe": "1D",
        "position_size": 100.0,
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
            },
            {
                "id": 2,
                "entry_date": "2020-02-05",
                "exit_date": "2020-02-10",
                "side": "Short",
                "entry_price": 32000,
                "exit_price": 31040,
                "profit_percent": 3.0,
                "profit_amount": 960
            },
            {
                "id": 3,
                "entry_date": "2020-03-05",
                "exit_date": "2020-03-10",
                "side": "Long",
                "entry_price": 33000,
                "exit_price": 32010,
                "profit_percent": -3.0,
                "profit_amount": -990
            },
        ],
        "chart_data": {
            "equity_curve": {
                "x": ["Day 0", "Day 10", "Day 20", "Day 30", "Day 40", "Day 50", "Day 60", "Day 70", "Day 80", "Day 90"],
                "y": [100, 105, 103, 110, 115, 113, 120, 125, 130, 145]
            },
            "drawdown_curve": {
                "x": ["Day 0", "Day 10", "Day 20", "Day 30", "Day 40", "Day 50", "Day 60", "Day 70", "Day 80", "Day 90"],
                "y": [0, 0, -1.9, 0, 0, -1.7, 0, 0, 0, 0]
            },
            "monthly_returns": {
                "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "y": [3.2, -1.1, 4.5, 2.8, -2.1, 5.6]
            }
        }
    }
    
    # List to track test results
    test_results = []
    report_files = []
    
    # Test 1: Generate HTML report with full data
    result, report_path = run_test_case(
        "HTML Report with Charts and Trades",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "html",
            "include_charts": True,
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 2: Generate HTML report without charts
    result, report_path = run_test_case(
        "HTML Report without Charts",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "html",
            "include_charts": False,
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 3: Generate HTML report without trades
    result, report_path = run_test_case(
        "HTML Report without Trades",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "html",
            "include_charts": True,
            "include_trades": False
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 4: Generate JSON report
    result, report_path = run_test_case(
        "JSON Report",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "json",
            "include_charts": True,
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 5: Generate CSV report
    result, report_path = run_test_case(
        "CSV Report",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "csv",
            "include_charts": True,  # Charts should be ignored in CSV
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 6: Invalid format
    result, report_path = run_test_case(
        "Invalid Format",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "pdf",  # Not supported
            "include_charts": True,
            "include_trades": True
        },
        expected_status="error"
    )
    test_results.append(result)
    
    # Test 7: Empty backtest results
    result, report_path = run_test_case(
        "Empty Backtest Results",
        {
            "backtest_results": {},
            "strategy_name": "BTC MA CrossOver",
            "format": "html",
            "include_charts": True,
            "include_trades": True
        },
        expected_status="error"
    )
    test_results.append(result)
    
    # Test 8: Missing chart data
    no_charts_results = sample_backtest_results.copy()
    no_charts_results.pop("chart_data", None)
    
    result, report_path = run_test_case(
        "Missing Chart Data",
        {
            "backtest_results": no_charts_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "html",
            "include_charts": True,
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 9: Missing trades data
    no_trades_results = sample_backtest_results.copy()
    no_trades_results.pop("trades", None)
    
    result, report_path = run_test_case(
        "Missing Trades Data",
        {
            "backtest_results": no_trades_results,
            "strategy_name": "BTC MA CrossOver",
            "format": "html",
            "include_charts": True,
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Test 10: Unicode in strategy name
    result, report_path = run_test_case(
        "Unicode Strategy Name",
        {
            "backtest_results": sample_backtest_results,
            "strategy_name": "比特币均线交叉策略",  # Chinese characters
            "format": "html",
            "include_charts": True,
            "include_trades": True
        },
        expected_status="success"
    )
    test_results.append(result)
    if report_path:
        report_files.append(report_path)
    
    # Summary of all tests
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result)
    
    print(f"Total tests: {total_tests}")
    print(f"Passed tests: {passed_tests}")
    print(f"Failed tests: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n❌ {total_tests - passed_tests} TESTS FAILED!")
    
    # Clean up report files
    print(f"\nCleaning up {len(report_files)} report files...")
    for file_path in report_files:
        try:
            os.unlink(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {str(e)}") 