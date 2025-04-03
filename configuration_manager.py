import os
import json
from typing import Dict, Any
from pydantic import Field

from proconfig.widgets.base import WIDGETS, BaseWidget

@WIDGETS.register_module()
class ConfigurationManager(BaseWidget):
    CATEGORY = "Custom Widgets/Trading Bot"
    NAME = "Configuration Manager"
    
    class InputsSchema(BaseWidget.InputsSchema):
        action: str = Field("load", description="Action to perform (load, save, update)")
        config_content: str = Field("{}", description="Direct JSON configuration content (preferred for cloud deployment)")
        config_path: str = Field("", description="Path to the configuration file (local file system only)")
        strategy_name: str = Field("", description="Name of the strategy")
        config_data: str = Field("{}", description="JSON configuration data (for save/update)")
        
    class OutputsSchema(BaseWidget.OutputsSchema):
        status: str
        message: str
        config_data: Dict[str, Any]
        
    def execute(self, environ, config):
        try:
            action = config.action.lower()
            
            if action == "load":
                return self._load_config(config.config_path, config.strategy_name, config.config_content)
            elif action == "save":
                return self._save_config(config.config_path, config.config_data)
            elif action == "update":
                return self._update_config(config.config_path, config.config_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "config_data": {}
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "config_data": {}
            }
            
    def _load_config(self, config_path, strategy_name, config_content=None):
        """Load a configuration file or use direct content"""
        
        # If direct content is provided, use it
        if config_content and config_content != "{}":
            try:
                if isinstance(config_content, str):
                    config_data = json.loads(config_content)
                else:
                    config_data = config_content
                return {
                    "status": "success",
                    "message": "Loaded configuration from direct content",
                    "config_data": config_data
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Invalid JSON configuration content provided",
                    "config_data": {}
                }
        
        # If config_path is provided, load from the specific file
        if config_path and os.path.isfile(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return {
                    "status": "success",
                    "message": f"Loaded configuration from {config_path}",
                    "config_data": config_data
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to load configuration: {str(e)}",
                    "config_data": {}
                }
        
        # If strategy_name is provided, find corresponding config
        elif strategy_name:
            # Example: Look for known config files
            if strategy_name.lower() == "btc spot position":
                config_path = "trading_config1.JSON"
            elif strategy_name.lower() == "btc ma+adx":
                config_path = "trading_config2.JSON"
            else:
                return {
                    "status": "error",
                    "message": f"No configuration found for strategy: {strategy_name}",
                    "config_data": {}
                }
                
            # Try to load the identified config file
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return {
                    "status": "success",
                    "message": f"Loaded configuration for {strategy_name}",
                    "config_data": config_data
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to load configuration: {str(e)}",
                    "config_data": {}
                }
        
        else:
            return {
                "status": "error",
                "message": "No configuration path, content, or strategy name provided",
                "config_data": {}
            }
            
    def _save_config(self, config_path, config_data_str):
        """Save a configuration file"""
        
        if not config_path:
            return {
                "status": "error",
                "message": "No configuration path provided",
                "config_data": {}
            }
            
        try:
            # Parse the config data
            if isinstance(config_data_str, str):
                config_data = json.loads(config_data_str)
            else:
                config_data = config_data_str
                
            # Save to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "message": f"Saved configuration to {config_path}",
                "config_data": config_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save configuration: {str(e)}",
                "config_data": {}
            }
            
    def _update_config(self, config_path, config_data_str):
        """Update an existing configuration file"""
        
        if not config_path or not os.path.isfile(config_path):
            return {
                "status": "error",
                "message": f"Configuration file not found: {config_path}",
                "config_data": {}
            }
            
        try:
            # Parse the update data
            if isinstance(config_data_str, str):
                update_data = json.loads(config_data_str)
            else:
                update_data = config_data_str
                
            # Load existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
                
            # Update the config
            existing_config.update(update_data)
            
            # Save back to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "message": f"Updated configuration in {config_path}",
                "config_data": existing_config
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update configuration: {str(e)}",
                "config_data": {}
            } 