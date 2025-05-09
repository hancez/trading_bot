import os
import json
import tempfile
from typing import Dict, Any, List
from pydantic import Field
import base64

from proconfig.widgets.base import WIDGETS, BaseWidget

# ------------------------ helper wrappers (module-level)
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
            if "items" not in kwargs:
                kwargs["items"] = {"type": "string"}
        elif isinstance(default_val, dict):
            kwargs["type"] = "object"
        else:
            kwargs["type"] = "string"
    return Field(*args, **kwargs)


def Output(*args, **kwargs):
    return Input(*args, **kwargs)

# ------------------------------------------------------------------------------

@WIDGETS.register_module()
class StrategyLibrary(BaseWidget):
    CATEGORY = "Custom Widgets/Trading Bot"
    NAME = "Strategy Library"
    
    class InputsSchema(BaseWidget.InputsSchema):
        action: str = Input("list", description="Action to perform (list, get, add, update, delete)", type="string")
        strategy_id: str = Input("", description="ID of the strategy (for get, update, delete)", type="string")
        strategy_name: str = Input("", description="Name of the strategy (for add)", type="string")
        script_content: str = Input("", description="Direct Pine script content (preferred for cloud deployment)", type="string")
        script_path: str = Input("", description="Path to the Pine script file (local file system only)", type="string")
        config_content: str = Input("", description="Direct JSON configuration content (preferred for cloud deployment)", type="string")
        config_path: str = Input("", description="Path to configuration file (local file system only)", type="string")
        tags: List[str] = Input([], description="Tags/categories for the strategy (for add/update)", type="array", items={"type": "string"})
        
    class OutputsSchema(BaseWidget.OutputsSchema):
        status: str = Output("", description="Execution status", type="string")
        message: str = Output("", description="Human-readable message", type="string")
        strategies: List[Dict[str, Any]] = Output([], description="List of strategies", type="array", items={"type": "object"})
        selected_strategy: Dict[str, Any] = Output({}, description="Selected strategy full detail", type="object")
        
    def execute(self, environ, config):
        try:
            action = config.action.lower()
            
            if action == "list":
                return self._list_strategies()
            elif action == "get":
                return self._get_strategy(config.strategy_id, config.strategy_name)
            elif action == "add":
                return self._add_strategy(config.strategy_name, config.script_path, 
                                        config.script_content, config.config_path, 
                                        config.config_content, config.tags)
            elif action == "update":
                return self._update_strategy(config.strategy_id, config.strategy_name, 
                                           config.script_path, config.script_content, 
                                           config.config_path, config.config_content, 
                                           config.tags)
            elif action == "delete":
                return self._delete_strategy(config.strategy_id)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "strategies": [],
                    "selected_strategy": {}
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to execute: {str(e)}",
                "strategies": [],
                "selected_strategy": {}
            }
            
    def _get_library_path(self):
        """Get the path to the strategy library file"""
        # Create directory if it doesn't exist
        library_dir = os.path.join(tempfile.gettempdir(), "trading_bot")
        if not os.path.exists(library_dir):
            os.makedirs(library_dir)
            
        return os.path.join(library_dir, "strategy_library.json")
        
    def _load_library(self):
        """Load the strategy library from file"""
        library_path = self._get_library_path()
        
        if not os.path.exists(library_path):
            # Create an empty library
            return []
            
        try:
            with open(library_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, return an empty library
            return []
            
    def _save_library(self, strategies):
        """Save the strategy library to file"""
        library_path = self._get_library_path()
        
        with open(library_path, 'w', encoding='utf-8') as f:
            json.dump(strategies, f, ensure_ascii=False, indent=2)
            
    def _list_strategies(self):
        """List all strategies in the library"""
        strategies = self._load_library()
        
        # Filter out sensitive information
        simplified_strategies = []
        for strategy in strategies:
            simplified_strategies.append({
                "id": strategy.get("id", ""),
                "name": strategy.get("name", ""),
                "description": strategy.get("description", ""),
                "tags": strategy.get("tags", []),
                "created_at": strategy.get("created_at", ""),
                "updated_at": strategy.get("updated_at", "")
            })
            
        return {
            "status": "success",
            "message": f"Found {len(strategies)} strategies",
            "strategies": simplified_strategies,
            "selected_strategy": {}
        }
        
    def _get_strategy(self, strategy_id, strategy_name=None):
        """Get a specific strategy from the library"""
        strategies = self._load_library()
        
        # Find by ID
        if strategy_id:
            for strategy in strategies:
                if strategy.get("id") == strategy_id:
                    return {
                        "status": "success",
                        "message": f"Found strategy: {strategy.get('name')}",
                        "strategies": [],
                        "selected_strategy": strategy
                    }
                    
        # Find by name if no ID provided
        elif strategy_name:
            for strategy in strategies:
                if strategy.get("name") == strategy_name:
                    return {
                        "status": "success",
                        "message": f"Found strategy: {strategy.get('name')}",
                        "strategies": [],
                        "selected_strategy": strategy
                    }
                    
        # Not found
        return {
            "status": "error",
            "message": f"Strategy not found with ID: {strategy_id or 'None'} or name: {strategy_name or 'None'}",
            "strategies": [],
            "selected_strategy": {}
        }
        
    def _add_strategy(self, strategy_name, script_path=None, script_content=None, 
                    config_path=None, config_content=None, tags=None):
        """Add a new strategy to the library"""
        if not strategy_name:
            return {
                "status": "error",
                "message": "Strategy name is required",
                "strategies": [],
                "selected_strategy": {}
            }
            
        # Load the script content
        if script_content:
            script_data = script_content
        elif script_path and os.path.isfile(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = f.read()
        else:
            return {
                "status": "error",
                "message": "Either script_path or script_content is required",
                "strategies": [],
                "selected_strategy": {}
            }
            
        # Load the config content
        config_data = {}
        if config_content:
            try:
                if isinstance(config_content, str):
                    config_data = json.loads(config_content)
                else:
                    config_data = config_content
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Invalid JSON configuration content",
                    "strategies": [],
                    "selected_strategy": {}
                }
        elif config_path and os.path.isfile(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to load configuration: {str(e)}",
                    "strategies": [],
                    "selected_strategy": {}
                }
                
        # Extract strategy description from script
        description = "No description"
        for line in script_data.split('\n'):
            if "///" in line:
                description = line.split("///")[1].strip()
                break
                
        # Generate a unique ID
        from datetime import datetime
        import uuid
        strategy_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create the strategy object
        new_strategy = {
            "id": strategy_id,
            "name": strategy_name,
            "description": description,
            "script": script_data,
            "config": config_data,
            "tags": tags or [],
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        # Add to library
        strategies = self._load_library()
        
        # Check for duplicate name
        for strategy in strategies:
            if strategy.get("name") == strategy_name:
                return {
                    "status": "error",
                    "message": f"Strategy with name '{strategy_name}' already exists",
                    "strategies": [],
                    "selected_strategy": {}
                }
                
        strategies.append(new_strategy)
        self._save_library(strategies)
        
        return {
            "status": "success",
            "message": f"Added strategy: {strategy_name}",
            "strategies": [],
            "selected_strategy": new_strategy
        }
        
    def _update_strategy(self, strategy_id, strategy_name=None, script_path=None, 
                       script_content=None, config_path=None, config_content=None, 
                       tags=None):
        """Update an existing strategy in the library"""
        if not strategy_id:
            return {
                "status": "error",
                "message": "Strategy ID is required for update",
                "strategies": [],
                "selected_strategy": {}
            }
            
        # Load the library
        strategies = self._load_library()
        
        # Find the strategy to update
        for i, strategy in enumerate(strategies):
            if strategy.get("id") == strategy_id:
                # Update fields if provided
                if strategy_name:
                    strategy["name"] = strategy_name
                    
                # Update script if provided
                if script_content:
                    strategy["script"] = script_content
                elif script_path and os.path.isfile(script_path):
                    with open(script_path, 'r', encoding='utf-8') as f:
                        strategy["script"] = f.read()
                        
                # Update config if provided
                if config_content:
                    try:
                        if isinstance(config_content, str):
                            strategy["config"] = json.loads(config_content)
                        else:
                            strategy["config"] = config_content
                    except json.JSONDecodeError:
                        return {
                            "status": "error",
                            "message": "Invalid JSON configuration content",
                            "strategies": [],
                            "selected_strategy": {}
                        }
                elif config_path and os.path.isfile(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            strategy["config"] = json.load(f)
                    except Exception as e:
                        return {
                            "status": "error",
                            "message": f"Failed to load configuration: {str(e)}",
                            "strategies": [],
                            "selected_strategy": {}
                        }
                        
                # Update tags if provided
                if tags:
                    strategy["tags"] = tags
                    
                # Update description if script was updated
                if script_content or (script_path and os.path.isfile(script_path)):
                    description = "No description"
                    for line in strategy["script"].split('\n'):
                        if "///" in line:
                            description = line.split("///")[1].strip()
                            break
                    strategy["description"] = description
                    
                # Update timestamp
                from datetime import datetime
                strategy["updated_at"] = datetime.now().isoformat()
                
                # Save the library
                strategies[i] = strategy
                self._save_library(strategies)
                
                return {
                    "status": "success",
                    "message": f"Updated strategy: {strategy.get('name')}",
                    "strategies": [],
                    "selected_strategy": strategy
                }
                
        # Not found
        return {
            "status": "error",
            "message": f"Strategy not found with ID: {strategy_id}",
            "strategies": [],
            "selected_strategy": {}
        }
        
    def _delete_strategy(self, strategy_id):
        """Delete a strategy from the library"""
        if not strategy_id:
            return {
                "status": "error",
                "message": "Strategy ID is required for deletion",
                "strategies": [],
                "selected_strategy": {}
            }
            
        # Load the library
        strategies = self._load_library()
        original_count = len(strategies)
        
        # Filter out the strategy to delete
        strategies = [s for s in strategies if s.get("id") != strategy_id]
        
        # If no strategies were removed, the ID wasn't found
        if len(strategies) == original_count:
            return {
                "status": "error",
                "message": f"Strategy not found with ID: {strategy_id}",
                "strategies": [],
                "selected_strategy": {}
            }
            
        # Save the updated library
        self._save_library(strategies)
        
        return {
            "status": "success",
            "message": f"Deleted strategy with ID: {strategy_id}",
            "strategies": [],
            "selected_strategy": {}
        }

if __name__ == "__main__":
    import time
    import traceback
    
    # Test the widget
    widget = StrategyLibrary()
    
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
            
            if output['strategies']:
                print(f"Strategies: {len(output['strategies'])}")
                for s in output['strategies']:
                    print(f"  - {s.get('name')}")
            
            if output['selected_strategy']:
                print(f"Selected strategy: {output['selected_strategy'].get('name')}")
                
            # Validate expected status if provided
            if expected_status and output['status'] != expected_status:
                print(f"❌ Test FAILED: Expected status '{expected_status}', got '{output['status']}'")
                return False
            
            print(f"✅ Test PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Test FAILED with exception:")
            traceback.print_exc()
            return False
    
    # Sample script and config
    sample_script = """
    //@version=4
    /// Simple Moving Average Crossover Strategy
    strategy("SMA Crossover", overlay=true)
    
    // Calculate SMAs
    fast_length = input(10, "Fast Length")
    slow_length = input(20, "Slow Length")
    
    fast_sma = sma(close, fast_length)
    slow_sma = sma(close, slow_length)
    
    // Entry conditions
    long_entry = crossover(fast_sma, slow_sma)
    
    // Exit conditions
    long_exit = crossunder(fast_sma, slow_sma)
    
    // Strategy orders
    if (long_entry)
        strategy.entry("Long", strategy.long)
    
    if (long_exit)
        strategy.close("Long")
    """
    
    sample_config = {
        "symbol": "BTCUSD",
        "timeframe": "1D",
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "parameters": {
            "fast_length": 10,
            "slow_length": 20
        }
    }
    
    # Test 1: List strategies (initially empty)
    run_test_case(
        "List Strategies",
        {
            "action": "list"
        },
        expected_status="success"
    )
    
    # Test 2: Add a strategy
    run_test_case(
        "Add Strategy",
        {
            "action": "add",
            "strategy_name": "SMA Crossover",
            "script_content": sample_script,
            "config_content": json.dumps(sample_config),
            "tags": ["BTC", "SMA"]
        },
        expected_status="success"
    )
    
    # Test 3: List strategies (should have one)
    strategies_output = run_test_case(
        "List Strategies After Add",
        {
            "action": "list"
        },
        expected_status="success"
    )
    
    # Store the strategy ID for later tests if present
    strategy_id = None
    strategies_response = widget({}, {"action": "list"})
    if strategies_response['status'] == 'success' and strategies_response['strategies']:
        strategy_id = strategies_response['strategies'][0].get('id')
    
    if strategy_id:
        # Test 4: Get strategy by ID
        run_test_case(
            "Get Strategy",
            {
                "action": "get",
                "strategy_id": strategy_id
            },
            expected_status="success"
        )
        
        # Test 5: Update strategy
        run_test_case(
            "Update Strategy",
            {
                "action": "update",
                "strategy_id": strategy_id,
                "strategy_name": "SMA Crossover - Updated",
                "tags": ["BTC", "SMA", "Updated"]
            },
            expected_status="success"
        )
        
        # Test 6: Delete strategy
        run_test_case(
            "Delete Strategy",
            {
                "action": "delete",
                "strategy_id": strategy_id
            },
            expected_status="success"
        )
    
    # Test 7: Get non-existent strategy
    run_test_case(
        "Get Non-existent Strategy",
        {
            "action": "get",
            "strategy_id": "non-existent-id"
        },
        expected_status="error"
    )
    
    # Test 8: Add strategy with duplicate name
    run_test_case(
        "Add Strategy",
        {
            "action": "add",
            "strategy_name": "SMA Crossover - Test",
            "script_content": sample_script,
            "config_content": json.dumps(sample_config),
            "tags": ["BTC", "SMA"]
        },
        expected_status="success"
    )
    
    run_test_case(
        "Add Duplicate Strategy",
        {
            "action": "add",
            "strategy_name": "SMA Crossover - Test",  # Same name
            "script_content": sample_script,
            "config_content": json.dumps(sample_config),
            "tags": ["BTC", "SMA"]
        },
        expected_status="error"
    )
    
    # Final test: List all strategies to ensure clean up
    run_test_case(
        "Final List Strategies",
        {
            "action": "list"
        },
        expected_status="success"
    ) 