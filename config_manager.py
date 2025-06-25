"""
Configuration manager module for the application.
Handles loading, saving, and accessing user settings.
"""

import os
import json
import configparser
from pathlib import Path

# Default configuration values
DEFAULT_CONFIG = {
    "serial": {
        "port": "COM3",
        "baud_rate": 9600,
        "timeout": 1.0
    },
    "logging": {
        "log_file": "sension7_data.csv",
        "backup_enabled": True
    },
    "display": {
        "update_interval": 2.0,
        "show_grid": True,
        "theme": "light"
    },
    "device": {
        "model": "HACH Sension7",
        "mock_data": True,
        "measurement_interval": 0.1
    }
}

class ConfigManager:
    """
    Manages application configuration settings.
    Handles loading, saving, and accessing settings.
    """
    
    def __init__(self, config_file="settings.ini"):
        """Initialize the configuration manager."""
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Load existing config or create with defaults
        if os.path.exists(config_file):
            self.load()
        else:
            self._set_defaults()
            self.save()
    
    def _set_defaults(self):
        """Set default configuration values."""
        for section, options in DEFAULT_CONFIG.items():
            self.config[section] = {}
            for key, value in options.items():
                self.config[section][key] = str(value)
    
    def load(self):
        """Load configuration from file."""
        try:
            self.config.read(self.config_file)
            # Add any missing default sections/options
            for section, options in DEFAULT_CONFIG.items():
                if section not in self.config:
                    self.config[section] = {}
                for key, value in options.items():
                    if key not in self.config[section]:
                        self.config[section][key] = str(value)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self._set_defaults()
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get(self, section, option, fallback=None):
        """Get a configuration value with proper type conversion."""
        if section not in self.config or option not in self.config[section]:
            return fallback
        
        value = self.config[section][option]
        
        # Try to convert to appropriate type
        try:
            # Check if it's a boolean
            if value.lower() in ("true", "false"):
                return value.lower() == "true"
            
            # Check if it's a number
            try:
                if "." in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                pass
            
            # Otherwise return as string
            return value
        except:
            return fallback
    
    def set(self, section, option, value):
        """Set a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][option] = str(value)
    
    def export_json(self, filepath):
        """Export configuration as JSON."""
        config_dict = {}
        for section in self.config:
            if section == "DEFAULT":
                continue
            config_dict[section] = {}
            for key, val in self.config[section].items():
                # Convert types
                if val.lower() in ("true", "false"):
                    config_dict[section][key] = val.lower() == "true"
                else:
                    try:
                        if "." in val:
                            config_dict[section][key] = float(val)
                        else:
                            config_dict[section][key] = int(val)
                    except ValueError:
                        config_dict[section][key] = val
        
        try:
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def import_json(self, filepath):
        """Import configuration from JSON."""
        try:
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
            
            # Update config
            for section, options in config_dict.items():
                if section not in self.config:
                    self.config[section] = {}
                for key, val in options.items():
                    self.config[section][key] = str(val)
            
            # Save updated config
            self.save()
            return True
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return False

# Singleton instance
_config_instance = None

def get_config():
    """Get the singleton configuration manager instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def initialize_config():
    """Initialize configuration system."""
    return get_config()
