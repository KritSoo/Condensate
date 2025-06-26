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
            import logging
            logging.debug(f"HACHSension7Adapter parsing: {repr(raw_data)}")
            
            # เริ่มต้นทำความสะอาดข้อมูล
            cleaned_data = raw_data.strip().replace('\x00', '')
            
            # ข้อความแบบต่างๆ ที่อาจมาจากเครื่อง Sension7 เวลากด Print
            logging.debug(f"Cleaned data: {repr(cleaned_data)}")
            
            # ลองหาแพทเทิร์นหลักๆ จากข้อมูล
            patterns = [
                # แพทเทิร์นแบบที่ 1: ค่าการนำไฟฟ้าและอุณหภูมิอยู่แยกบรรทัด
                r"(?:Cond)?\.?[:\s]*(\d+\.?\d*)\s*(µS\/cm|uS\/cm|mS\/cm).*?(?:Temp)?\.?[:\s]*(\d+\.?\d*)\s*[°]?C",
                
                # แพทเทิร์นแบบที่ 2: ค่าการนำไฟฟ้าอย่างเดียว
                r"(?:Cond)?\.?[:\s]*(\d+\.?\d*)\s*(µS\/cm|uS\/cm|mS\/cm)",
                
                # แพทเทิร์นแบบที่ 3: แบบตัวเลขล้วนๆ
                r"(\d+\.?\d*)\s*(µS\/cm|uS\/cm|mS\/cm)",
                
                # แพทเทิร์นแบบที่ 4: เลขล้วนๆ และหน่วยแยกกัน (เช่น "123.4 uS/cm")
                r"(\d+\.?\d*)\s*(?:µ|u|m)?S\/cm",
                
                # แพทเทิร์นแบบที่ 5: สำหรับรูปแบบกรณีพิเศษของ Sension7
                r"(\d+\.?\d*)"
            ]
            
            # ลองหาแพทเทิร์นทั้งหมด
            for pattern in patterns:
                match = re.search(pattern, cleaned_data, re.IGNORECASE | re.DOTALL)
                if match:
                    groups = match.groups()
                    logging.debug(f"Matched pattern with groups: {groups}")
                    
                    if len(groups) >= 1:  # มีค่าการนำไฟฟ้า
                        value_str = groups[0]
                        
                        # ถ้ามีหน่วยด้วย (2 กลุ่มหรือมากกว่า)
                        if len(groups) >= 2 and groups[1]:
                            unit = groups[1].replace('µ', 'u')
                        else:
                            # ถ้าไม่มีหน่วย ลองค้นหาหน่วยในข้อความ
                            if "ms" in cleaned_data.lower() or "mS" in cleaned_data:
                                unit = "mS/cm"
                            else:
                                unit = "uS/cm"  # ค่าเริ่มต้นเป็น uS/cm
                        
                        # ถ้ามีอุณหภูมิด้วย (3 กลุ่ม)
                        if len(groups) >= 3 and groups[2]:
                            temp_value = float(groups[2])
                        else:
                            # ถ้าไม่มีในแพทเทิร์นนี้ ลองหาแพทเทิร์นอุณหภูมิแยก
                            temp_pattern = r"(?:Temp)?\.?[:\s]*(\d+\.?\d*)\s*[°]?C"
                            temp_match = re.search(temp_pattern, cleaned_data, re.IGNORECASE)
                            temp_value = float(temp_match.group(1)) if temp_match else None
                        
                        try:
                            value = float(value_str)
                            logging.debug(f"Parsed values: {value}, {unit}, {temp_value}")
                            return value, unit, temp_value
                        except ValueError as ve:
                            logging.error(f"Cannot convert value to float: {value_str} - {ve}")
                            continue  # ลองแพทเทิร์นถัดไป
            
            # ถ้าไม่พบแพทเทิร์นที่รองรับ ลองหาตัวเลขแบบง่ายมากๆ
            # บางครั้งเครื่อง Sension7 อาจส่งข้อมูลมาในรูปแบบที่แปลก
            simple_value_pattern = r"(\d+\.?\d+)"
            simple_match = re.search(simple_value_pattern, cleaned_data)
            
            if simple_match:
                try:
                    value = float(simple_match.group(1))
                    logging.debug(f"Found simple numeric value: {value}")
                    # สมมติว่าเป็น uS/cm ถ้าไม่มีหน่วยระบุ
                    return value, "uS/cm", None
                except ValueError as ve:
                    logging.error(f"Cannot convert simple value to float: {simple_match.group(1)} - {ve}")
                
            logging.warning(f"Could not match any pattern in: {cleaned_data}")
            return None, None, None
            
        except Exception as e:
            import logging
            logging.error(f"Error parsing HACH Sension7 data: {e}", exc_info=True)
            return None, None, None
    
    def get_command_string(self):
        """HACH Sension7 doesn't need a command to send data."""
        # เครื่อง Sension7 ใช้การกดปุ่ม Print ที่เครื่องเพื่อส่งข้อมูล ไม่ต้องส่งคำสั่งจากคอมพิวเตอร์
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
