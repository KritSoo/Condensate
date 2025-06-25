"""
Device adapter module for different conductivity meters.
Provides interfaces and implementations for various meter models.
"""

import re
from abc import ABC, abstractmethod
import importlib

class ConductivityMeterAdapter(ABC):
    """
    Abstract base class for conductivity meter adapters.
    Implement this class to add support for different meter models.
    """
    
    @property
    @abstractmethod
    def name(self):
        """Return the name of the meter model."""
        pass
    
    @property
    @abstractmethod
    def description(self):
        """Return a description of the meter model."""
        pass
    
    @abstractmethod
    def parse_data(self, raw_data):
        """
        Parse raw data from the meter.
        
        Parameters:
        -----------
        raw_data : str
            Raw data string from the meter
            
        Returns:
        --------
        tuple
            (float, str, float or None) - (conductivity_value, unit, temperature or None)
        """
        pass
    
    @abstractmethod
    def get_command_string(self):
        """
        Get command string to request data from meter (if applicable).
        
        Returns:
        --------
        bytes or None
            Command to send to meter, or None if not needed
        """
        pass


class HACHSension7Adapter(ConductivityMeterAdapter):
    """Adapter for HACH Sension7 conductivity meter."""
    
    @property
    def name(self):
        return "HACH Sension7"
        
    @property
    def description(self):
        return "HACH Sension7 conductivity meter with serial output"
    
    def parse_data(self, raw_data):
        """Parse HACH Sension7 data format."""
        try:
            cleaned_data = raw_data.strip()
            
            # Try to extract conductivity
            cond_pattern = r"(\d+\.?\d*)\s*(µS/cm|uS/cm|mS/cm)"
            match = re.search(cond_pattern, cleaned_data, re.IGNORECASE)
            
            if match:
                value_str, unit = match.groups()
                unit = unit.replace('µ', 'u')
                
                # Try to extract temperature if present
                temp_pattern = r"(\d+\.?\d*)\s*[°]?C"
                temp_match = re.search(temp_pattern, cleaned_data)
                
                if temp_match:
                    temp_value = float(temp_match.group(1))
                else:
                    temp_value = None
                    
                return float(value_str), unit, temp_value
                
            return None, None, None
            
        except (AttributeError, ValueError) as e:
            print(f"Error parsing HACH Sension7 data: {e}")
            return None, None, None
    
    def get_command_string(self):
        """HACH Sension7 doesn't need a command to send data."""
        return None


class OaktonCon150Adapter(ConductivityMeterAdapter):
    """Adapter for Oakton CON150 conductivity meter."""
    
    @property
    def name(self):
        return "Oakton CON150"
        
    @property
    def description(self):
        return "Oakton CON150 conductivity/TDS meter with RS232 output"
    
    def parse_data(self, raw_data):
        """Parse Oakton CON150 data format."""
        try:
            cleaned_data = raw_data.strip()
            
            # Oakton format: "COND: 123.4 uS/cm, TEMP: 25.3 C"
            cond_pattern = r"COND:\s*(\d+\.?\d*)\s*(µS/cm|uS/cm|mS/cm)"
            temp_pattern = r"TEMP:\s*(\d+\.?\d*)\s*[°]?C"
            
            cond_match = re.search(cond_pattern, cleaned_data, re.IGNORECASE)
            temp_match = re.search(temp_pattern, cleaned_data, re.IGNORECASE)
            
            if cond_match:
                value_str, unit = cond_match.groups()
                unit = unit.replace('µ', 'u')
                
                temp_value = float(temp_match.group(1)) if temp_match else None
                    
                return float(value_str), unit, temp_value
                
            return None, None, None
            
        except (AttributeError, ValueError) as e:
            print(f"Error parsing Oakton CON150 data: {e}")
            return None, None, None
    
    def get_command_string(self):
        """Send command to request data from Oakton CON150."""
        return b'D\r'  # 'D' command for data


class MilwaukeeMW301Adapter(ConductivityMeterAdapter):
    """Adapter for Milwaukee MW301 EC meter."""
    
    @property
    def name(self):
        return "Milwaukee MW301"
        
    @property
    def description(self):
        return "Milwaukee MW301 EC meter with digital output"
    
    def parse_data(self, raw_data):
        """Parse Milwaukee MW301 data format."""
        try:
            cleaned_data = raw_data.strip()
            
            # Milwaukee format is a simple floating point number
            # followed by mS/cm or uS/cm
            pattern = r"(\d+\.?\d*)\s*(µS/cm|uS/cm|mS/cm)"
            match = re.search(pattern, cleaned_data, re.IGNORECASE)
            
            if match:
                value_str, unit = match.groups()
                unit = unit.replace('µ', 'u')
                
                # This model doesn't output temperature
                return float(value_str), unit, None
                
            return None, None, None
            
        except (AttributeError, ValueError) as e:
            print(f"Error parsing Milwaukee MW301 data: {e}")
            return None, None, None
    
    def get_command_string(self):
        """No command needed for Milwaukee MW301."""
        return None


# Dictionary of available adapters
AVAILABLE_ADAPTERS = {
    "HACH Sension7": HACHSension7Adapter,
    "Oakton CON150": OaktonCon150Adapter,
    "Milwaukee MW301": MilwaukeeMW301Adapter
}

def get_adapter(model_name):
    """
    Get adapter instance for the specified model.
    
    Parameters:
    -----------
    model_name : str
        Name of the meter model
        
    Returns:
    --------
    ConductivityMeterAdapter
        Adapter instance for the specified model
    """
    if model_name in AVAILABLE_ADAPTERS:
        return AVAILABLE_ADAPTERS[model_name]()
    else:
        # Return default adapter
        print(f"Warning: Unknown model '{model_name}'. Using default adapter.")
        return HACHSension7Adapter()
