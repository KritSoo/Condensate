"""
Serial communication module for HACH Sension7 Conductivity Meter.
Handles data reading, parsing, and logging functions.

Author: User
Date: 2024
"""

import serial
import time
from datetime import datetime, timedelta
import re
import os
import random  # Add import for random number generation
import logging  # เพิ่ม logging เพื่อดี bug ได้ง่ายขึ้น
import sys
import tempfile
import csv  # ยังคงต้องใช้สำหรับการอ่านไฟล์เดิมที่อาจมีอยู่
from db_manager import save_data, init_database, get_connection, get_data_table_name

# ตรวจสอบและสร้างไฟล์ log ในตำแหน่งที่เขียนได้
try:
    # พยายามใช้โฟลเดอร์ logs ในไดเรกทอรีของแอป
    app_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(app_dir, "logs")
    
    # สร้างโฟลเดอร์ถ้าไม่มี
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            log_file = os.path.join(log_dir, "serial_debug.log")
        except:
            # หากไม่สามารถสร้างโฟลเดอร์ logs ได้ ให้ใช้ไดเรกทอรีของแอป
            log_file = os.path.join(app_dir, "serial_debug.log")
    else:
        log_file = os.path.join(log_dir, "serial_debug.log")

    # ทดสอบเขียนไฟล์
    with open(log_file, 'a'):
        pass
except:
    # หากไม่สามารถเขียนในไดเรกทอรีหลักได้ ให้ใช้โฟลเดอร์ temporary
    log_file = os.path.join(tempfile.gettempdir(), "condensate_serial_debug.log")
    print(f"Cannot write to app directory, using temp file: {log_file}")

# ตั้งค่า logging สำหรับแสดงข้อมูล debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logging.info(f"Logging initialized. Log file: {log_file}")

# Import configuration and adapter modules
from config_manager import get_config
from device_adapters import get_adapter

# Load configuration
config = get_config()

# Serial port configuration (loaded from config)
SERIAL_PORT = config.get('serial', 'port', fallback="COM3")
BAUD_RATE = config.get('serial', 'baud_rate', fallback=9600)
TIMEOUT = config.get('serial', 'timeout', fallback=1.0)
MOCK_DATA_MODE = config.get('device', 'mock_data', fallback=True)

# Data logging configuration - use get_log_file_path for complete path
LOG_FILE = config.get('logging', 'log_file', fallback="sension7_data.csv")
BACKUP_ENABLED = config.get('logging', 'backup_enabled', fallback=True)
MEASUREMENT_INTERVAL = config.get('device', 'measurement_interval', fallback=0.1)

# Get device model and adapter
DEVICE_MODEL = config.get('device', 'model', fallback="HACH Sension7")
device_adapter = get_adapter(DEVICE_MODEL)

# Data validation constants
MIN_MOCK_VALUE = 100.0
MAX_MOCK_VALUE = 500.0
MIN_MOCK_TEMP = 100.0
MAX_MOCK_TEMP = 200.0
SPIKE_PROBABILITY = 0.05  # 5% chance of spike in historical data

def parse_data(raw_data_string):
    """
    Parse raw data string from conductivity meter using the configured device adapter.
    
    Returns:
        tuple: (float or None, str or None, float or None) - (conductivity value, unit, temperature)
    """
    try:
        # Log the raw data received for debugging
        logging.debug(f"Parsing raw data: {repr(raw_data_string)}")
        
        # Try to clean the data if it has garbage characters
        cleaned_data = raw_data_string.strip()
        
        # Use the device adapter to parse the data
        result = device_adapter.parse_data(cleaned_data)
        logging.debug(f"Parse result: {result}")
        return result
    except Exception as e:
        logging.error(f"Error parsing data: {e}", exc_info=True)
        return None, None, None

def save_to_csv(timestamp, conductivity_value, unit, temperature=None, filename=None):
    """บันทึกข้อมูลลงในฐานข้อมูลโดยใช้ระบบ db_manager"""
    # เรียกใช้ฟังก์ชันบันทึกข้อมูลจาก db_manager
    success = save_data(timestamp, conductivity_value, unit, temperature)
    
    # แสดงสถานะการบันทึก
    config = get_config()
    mock_mode = config.get('device', 'mock_data', fallback=True)
    mode_text = "MOCK" if mock_mode else "REAL"
    
    # แสดงชื่อตาราง
    table_name = get_data_table_name()
    
    if success:
        print(f"\n[{mode_text} MODE] บันทึกข้อมูลสำเร็จที่ตาราง: {table_name}")
    else:
        print(f"\n[{mode_text} MODE] เกิดข้อผิดพลาดในการบันทึกข้อมูลที่ตาราง: {table_name}")
    
    return success


def generate_mock_historical_data(num_days=7):
    """Generate mock historical conductivity and temperature data using data_manager."""
    from data_manager import generate_mock_data
    generate_mock_data(num_days)


def read_and_process_data(ser_port=None, baud_rate=None, 
                         timeout=None, data_callback=None):
    """Continuously read and process data."""
    # Use provided values or fallback to config
    ser_port = ser_port or SERIAL_PORT
    baud_rate = baud_rate or BAUD_RATE
    timeout = timeout or TIMEOUT
    
    # Get command string from device adapter
    command_string = device_adapter.get_command_string()
    
    ser = None
    try:
        # Run diagnostic checks before starting
        ensure_database_connection()
        
        # Log starting configuration
        logging.info(f"Starting serial reading with: PORT={ser_port}, BAUD={baud_rate}, TIMEOUT={timeout}")
        logging.info(f"Using device model: {DEVICE_MODEL}")
        logging.info(f"Using data table: {get_data_table_name()}")
        
        # Use direct file writes to verify system is working
        test_file = "serial_reader_test.txt"
        try:
            with open(test_file, 'w') as f:
                f.write(f"Test file created at {datetime.now()}\n")
            logging.info(f"Successfully created test file: {test_file}")
            logging.info(f"Using device: {DEVICE_MODEL}")
        except Exception as e:
            logging.warning(f"WARNING: Could not create test file: {e}")
        
        if MOCK_DATA_MODE:
            # เตรียมไฟล์ข้อมูลจำลอง
            from data_manager import init_data_files
            init_data_files()
            
            print("Running in MOCK DATA mode")
            while True:
                try:
                    timestamp = datetime.now()  # Use exact current time
                    mock_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE)
                    mock_temp = random.uniform(MIN_MOCK_TEMP, MAX_MOCK_TEMP)
                    mock_unit = random.choice(["uS/cm", "mS/cm"])
                    
                    # บันทึกข้อมูลด้วยระบบใหม่
                    try:
                        success = save_to_csv(timestamp, mock_value, mock_unit, mock_temp)
                        if success:
                            print(f"Successfully saved data point at {timestamp}")
                        else:
                            print(f"Failed to save data point at {timestamp}")
                        
                        if data_callback:
                            data_callback(timestamp, mock_value, mock_unit, mock_temp)
                    except Exception as inner_e:
                        print(f"Error during data processing: {inner_e}")
                        logging.error(f"Error during data processing: {inner_e}")
                        # Continue running even if a single data point fails
                    
                    # Reduced sleep time for debugging - change back to 1800 for production
                    print("Waiting 2 minutes for next data point...")
                    time.sleep(120.0)  # 120 seconds (2 minutes) between readings
                except KeyboardInterrupt:
                    print("\nStopping data collection...")
                    break
                except Exception as loop_e:
                    print(f"Error in data generation loop: {loop_e}")
                    time.sleep(120)  # Wait 2 minutes before trying again

        # Real serial connection code
        ser = serial.Serial(
            port=ser_port,
            baudrate=baud_rate,
            timeout=timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        logging.info(f"Serial port opened successfully: {ser_port}")
        buffer = ""  # Buffer to accumulate incoming data
        
        while True:
            # Send command if needed by device
            if command_string:
                try:
                    ser.write(command_string)
                    logging.debug(f"Command sent: {command_string}")
                except Exception as cmd_e:
                    logging.error(f"Error sending command: {cmd_e}")
            
            # สำหรับ Sension7 เมื่อกด Print ปุ่มที่เครื่อง
            try:
                # ตรวจสอบว่ามีข้อมูลรอการอ่านหรือไม่
                if ser.in_waiting:
                    # อ่านข้อมูลจาก serial port
                    new_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += new_data
                    logging.debug(f"Received data: {repr(new_data)}")
                    
                    # ตรวจสอบว่าข้อมูลสมบูรณ์แล้วหรือไม่ (มีตัวขึ้นบรรทัดใหม่หรือไม่)
                    if '\n' in buffer:
                        lines = buffer.split('\n')
                        # เก็บบรรทัดสุดท้ายที่อาจจะไม่สมบูรณ์ไว้ในบัฟเฟอร์ต่อไป
                        buffer = lines.pop()
                        
                        # ประมวลผลแต่ละบรรทัด
                        for line in lines:
                            if line.strip():  # ตรวจสอบว่าไม่ใช่บรรทัดว่าง
                                logging.info(f"Processing line: {repr(line)}")
                                value, unit, temperature = parse_data(line)
                                
                                if value is not None:
                                    timestamp = datetime.now()
                                    logging.info(f"Valid data received: {value} {unit}, Temp: {temperature}")
                                    
                                    # บันทึกข้อมูลลงไฟล์ CSV
                                    success = save_to_csv(timestamp, value, unit, temperature)
                                    if success:
                                        logging.info(f"Data successfully saved to CSV at {timestamp}")
                                    else:
                                        logging.error("Failed to save data to CSV")
                                    
                                    # เรียก callback function ถ้ามี
                                    if data_callback:
                                        data_callback(timestamp, value, unit, temperature)
                                else:
                                    logging.warning(f"Failed to parse line: {repr(line)}")
                    
                    # หากบัฟเฟอร์ยาวเกินไป (อาจมีข้อมูลที่ไม่สมบูรณ์ค้างอยู่) ให้ล้างทิ้ง
                    if len(buffer) > 1024:
                        logging.warning(f"Buffer too long ({len(buffer)} bytes), clearing it")
                        buffer = ""
            except Exception as read_error:
                logging.error(f"Error reading data: {read_error}", exc_info=True)
                
            # รอสักครู่ก่อนอ่านข้อมูลใหม่
            time.sleep(MEASUREMENT_INTERVAL)
                
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except KeyboardInterrupt:
        print("\nStopping data collection...")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed")

def ensure_database_connection():
    """Ensure database connection is working (using db_manager)."""
    from db_manager import init_database, get_connection
    
    # เตรียมฐานข้อมูล
    success = init_database()
    
    # ทดสอบการเชื่อมต่อ
    connection = get_connection()
    connection_success = connection is not None
    
    if connection:
        connection.close()
    
    print(f"Database connection status: {'Success' if connection_success else 'Failed'}")
    logging.info(f"Database connection status: {'Success' if connection_success else 'Failed'}")
    
    # ถ้าไม่สำเร็จ
    if not success or not connection_success:
        print("Warning: Database connection failed")
        logging.warning("Database connection failed")
        return False
        
    return True

def check_filesystem_permissions():
    """Check permissions and state of the filesystem for the log file."""
    print("\n--- File System Check ---")
    
    try:
        # Current working directory
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        print(f"Directory exists: {os.path.exists(cwd)}")
        try:
            print(f"Directory writable: {os.access(cwd, os.W_OK)}")
        except Exception as e:
            print(f"Can't check directory permissions: {e}")
        
        # Check if LOG_FILE exists
        if os.path.isabs(LOG_FILE):
            log_path = LOG_FILE
        else:
            log_path = os.path.join(cwd, LOG_FILE)
        
        print(f"Log file path: {log_path}")
        print(f"Log file exists: {os.path.isfile(log_path)}")
        
        if os.path.isfile(log_path):
            try:
                print(f"Log file size: {os.path.getsize(log_path)} bytes")
                print(f"Log file readable: {os.access(log_path, os.R_OK)}")
                print(f"Log file writable: {os.access(log_path, os.W_OK)}")
            except Exception as e:
                print(f"Can't check file permissions: {e}")
        
        # Check parent directory
        log_dir = os.path.dirname(log_path) or cwd
        print(f"Log directory: {log_dir}")
        print(f"Log directory exists: {os.path.exists(log_dir)}")
        try:
            print(f"Log directory writable: {os.access(log_dir, os.W_OK)}")
        except Exception as e:
            print(f"Can't check directory permissions: {e}")
            
        # Try to create a test file
        try:
            test_path = os.path.join(cwd, ".permission_test")
            with open(test_path, 'w') as test_file:
                test_file.write("test")
            print(f"Successfully created test file: {test_path}")
            os.remove(test_path)
            print("Successfully removed test file")
        except Exception as e:
            print(f"Failed to create/remove test file: {e}")
            
    except Exception as e:
        print(f"Error checking filesystem: {e}")
    
    print("--- End File System Check ---\n")
    return

# Update MOCK_DATA_MODE based on serial port availability
def check_serial_availability():
    """Check if the configured serial port is available."""
    try:
        test_ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        test_ser.close()
        return True
    except:
        return False

def is_file_locked(filepath):
    """ตรวจสอบว่าไฟล์ถูกล็อคหรือไม่ - เวอร์ชั่นเรียบง่ายและมีการตรวจสอบเพิ่มเติม"""
    if not os.path.exists(filepath):
        return False
        
    try:
        # พยายามเปิดไฟล์ในโหมดเขียนและทดสอบเขียน
        with open(filepath, 'a') as f:
            # ทดสอบ flush และ fsync เพื่อให้แน่ใจว่าเขียนได้จริง
            f.flush()
            os.fsync(f.fileno())
        return False  # สามารถเขียนได้ แสดงว่าไม่ถูกล็อค
    except IOError as e:
        print(f"File appears to be locked: {e}")
        return True  # เขียนไม่ได้ แสดงว่าถูกล็อค

def force_create_directory(dir_path):
    """สร้างโฟลเดอร์แบบบังคับ พร้อมตั้งค่าสิทธิ์การเข้าถึง"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"สร้างโฟลเดอร์สำเร็จ: {dir_path}")
            # พยายามให้สิทธิ์เข้าถึง (เฉพาะ Windows)
            try:
                import stat
                os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                print(f"กำหนดสิทธิ์การเข้าถึงเต็มที่ให้กับโฟลเดอร์: {dir_path}")
            except Exception as perm_e:
                print(f"ไม่สามารถกำหนดสิทธิ์โฟลเดอร์: {perm_e}")
        except Exception as e:
            print(f"ไม่สามารถสร้างโฟลเดอร์: {dir_path}, error: {e}")
            return False
    
    # ตรวจสอบว่าโฟลเดอร์เขียนได้หรือไม่
    if not os.access(dir_path, os.W_OK):
        print(f"⚠️ โฟลเดอร์ไม่สามารถเขียนได้: {dir_path}")
        try:
            # พยายามกำหนดสิทธิ์อีกครั้ง
            import stat
            os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            print(f"พยายามกำหนดสิทธิ์การเข้าถึงอีกครั้ง")
            
            # ตรวจสอบอีกครั้งหลังกำหนดสิทธิ์
            if os.access(dir_path, os.W_OK):
                print(f"✅ สามารถเขียนโฟลเดอร์ได้แล้ว")
                return True
            else:
                print(f"❌ ยังไม่สามารถเขียนโฟลเดอร์ได้หลังจากกำหนดสิทธิ์แล้ว")
                return False
        except Exception as perm2_e:
            print(f"ไม่สามารถกำหนดสิทธิ์โฟลเดอร์: {perm2_e}")
            return False
    
    return True

def get_log_file_path():
    """คืนค่าพาธของไฟล์ CSV ตามโหมดการทำงาน (wrapper สำหรับ backward compatibility)"""
    # เรียกใช้จาก data_manager
    from data_manager import get_data_file_path
    return get_data_file_path()


def ensure_files_ready():
    """ตรวจสอบและเตรียมไฟล์ข้อมูลให้พร้อมใช้งาน"""
    from data_manager import init_data_files
    return init_data_files()


# Only run initialization if this module is run directly
if __name__ == "__main__":
    # Ensure database connection is working
    ensure_database_connection()
    # Initialize database
    init_database()

def repair_csv_file(filepath):
    """ตรวจสอบและซ่อมแซมไฟล์ CSV ที่เสียหาย"""
    if not os.path.exists(filepath):
        print(f"File does not exist, nothing to repair: {filepath}")
        return False
    
    try:
        print(f"Attempting to repair CSV file: {filepath}")
        
        # อ่านข้อมูลจากไฟล์เดิม
        rows = []
        valid_data = False
        
        try:
            with open(filepath, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # ถ้าไม่ใช่แถวว่าง
                        rows.append(row)
                        valid_data = True
        except Exception as read_e:
            print(f"Error reading original file: {read_e}")
            # สร้างไฟล์ใหม่ด้วยเฮดเดอร์
            rows = [['Timestamp', 'Conductivity', 'Unit', 'Temperature']]
        
        # ถ้าไฟล์ว่างหรือไม่มีข้อมูล
        if not valid_data or len(rows) == 0:
            rows = [['Timestamp', 'Conductivity', 'Unit', 'Temperature']]
        
        # สร้างไฟล์ชั่วคราวและเขียนข้อมูล
        temp_file = filepath + '.temp'
        with open(temp_file, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)
        
        # ตรวจสอบว่าสร้างไฟล์ชั่วคราวสำเร็จ
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            # สำรองไฟล์เดิม
            backup_file = filepath + '.bak'
            try:
                if os.path.exists(filepath):
                    import shutil
                    shutil.copy2(filepath, backup_file)
                    print(f"Backed up original file to: {backup_file}")
            except Exception as backup_e:
                print(f"Could not backup original file: {backup_e}")
            
            # ลบไฟล์เดิม
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as remove_e:
                print(f"Could not remove original file: {remove_e}")
                # ใช้ชื่อไฟล์ใหม่แทน
                filepath = filepath + '.new'
            
            # เปลี่ยนชื่อไฟล์ชั่วคราว
            try:
                os.rename(temp_file, filepath)
                print(f"Successfully repaired CSV file: {filepath}")
                return True
            except Exception as rename_e:
                print(f"Error renaming temp file: {rename_e}")
                print(f"Repaired data is available in: {temp_file}")
                return False
        else:
            print(f"Failed to create temp file")
            return False
    
    except Exception as e:
        print(f"Error repairing CSV file: {e}")
        return False

def create_safe_csv(filepath, headers=['Timestamp', 'Conductivity', 'Unit', 'Temperature']):
    """สร้างไฟล์ CSV ใหม่ด้วยวิธีที่ปลอดภัยกับปัญหาสิทธิ์การเข้าถึง"""
    print(f"Attempting to safely create CSV file: {filepath}")
    
    # ตรวจสอบว่าไฟล์มีอยู่แล้วหรือไม่
    file_exists = os.path.exists(filepath) and os.path.isfile(filepath)
    
    if file_exists:
        # ตรวจสอบสิทธิ์การเขียน
        if not os.access(filepath, os.W_OK):
            print(f"Warning: File exists but is not writable: {filepath}")
            
            try:
                # พยายามเปลี่ยนสิทธิ์
                import stat
                os.chmod(filepath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                print(f"Changed file permissions to allow writing")
            except Exception as chmod_e:
                print(f"Could not change file permissions: {chmod_e}")
                return False
            
            # ตรวจสอบอีกครั้งว่าสามารถเขียนได้แล้ว
            if not os.access(filepath, os.W_OK):
                print(f"Still cannot write to file after permission change")
                return False
        
        # ตรวจสอบว่าไฟล์ว่างหรือไม่
        if os.path.getsize(filepath) == 0:
            try:
                # เขียนเฮดเดอร์
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                print(f"Added headers to empty file: {filepath}")
                return True
            except Exception as write_e:
                print(f"Error adding headers to empty file: {write_e}")
                return False
        else:
            # มีข้อมูลอยู่แล้ว
            print(f"File already exists and has content: {filepath}")
            return True
    else:
        # ไฟล์ยังไม่มี ตรวจสอบสิทธิ์โฟลเดอร์
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
            except Exception as mkdir_e:
                print(f"Could not create directory: {mkdir_e}")
                return False
        
        # ตรวจสอบสิทธิ์การเขียนในโฟลเดอร์
        if not os.access(directory, os.W_OK):
            print(f"Directory is not writable: {directory}")
            return False
        
        # พยายามสร้างไฟล์และเขียนเฮดเดอร์
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            print(f"Created new CSV file with headers: {filepath}")
            return True
        except Exception as create_e:
            print(f"Failed to create CSV file: {create_e}")
            
            # ลองใช้วิธี low-level
            try:
                import io
                with io.open(filepath, 'w', newline='') as f:
                    f.write(','.join(headers) + '\n')
                print(f"Created file using alternate method: {filepath}")
                return True
            except Exception as alt_e:
                print(f"All attempts to create file failed: {alt_e}")
                return False

def ensure_file_ready_for_writing(filepath):
    """ตรวจสอบว่าไฟล์พร้อมสำหรับการเขียนหรือไม่ และพยายามแก้ไขถ้าไม่พร้อม
    
    Returns:
        bool: True ถ้าพร้อม, False ถ้าไม่สามารถทำให้พร้อมได้
    """
    # 1. ตรวจสอบว่าโฟลเดอร์มีอยู่
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
            
    # 2. ตรวจสอบว่าไฟล์ล็อคหรือไม่
    if os.path.exists(filepath) and is_file_locked(filepath):
        print(f"File is locked: {filepath}")
        # พยายามสร้างใหม่
        if not force_create_csv_file(filepath):
            print("Could not recreate locked file")
            return False
            
    # 3. ตรวจสอบว่าไฟล์มีอยู่หรือไม่
    if not os.path.exists(filepath):
        # สร้างไฟล์ใหม่พร้อมเฮดเดอร์
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Conductivity', 'Unit', 'Temperature'])
            print(f"Created new file: {filepath}")
        except Exception as e:
            print(f"Error creating file: {e}")
            return False
            
    # 4. ตรวจสอบว่าเขียนได้จริงหรือไม่
    try:
        # ทดสอบเปิดไฟล์ในโหมดเขียน
        with open(filepath, 'a') as _:
            pass
        return True
    except Exception as e:
        print(f"File is not writable: {e}")
        return False

def force_create_csv_file(filepath):
    """บังคับสร้างไฟล์ CSV พร้อมหัวคอลัมน์ ลบไฟล์เดิมถ้าจำเป็น พร้อมทั้งสำรองข้อมูลเดิม"""
    backup_data = []
    backup_created = False
    
    # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
    if os.path.exists(filepath):
        # พยายามสำรองข้อมูลเดิมก่อน
        try:
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                backup_data = list(reader)
                if len(backup_data) > 0:
                    print(f"Backed up {len(backup_data)} rows of data in memory")
                    backup_created = True
        except Exception as backup_e:
            print(f"Could not back up existing data: {backup_e}")
        
        # ลบไฟล์เดิม
        try:
            # พยายามปิด file descriptor ที่อาจค้างอยู่
            try:
                os.close(os.open(filepath, os.O_RDONLY))
            except:
                pass
                
            time.sleep(0.5)  # รอเล็กน้อย
            os.remove(filepath)
            print(f"Removed existing file: {filepath}")
        except Exception as e:
            print(f"Could not remove file: {e}")
            
            # พยายามใช้วิธีอื่นๆ
            try:
                import os.path
                if os.name == 'nt':  # Windows
                    os.system(f'del /f "{filepath}"')
                else:  # Linux/Mac
                    os.system(f'rm -f "{filepath}"')
                print(f"Tried to remove file using system command")
            except:
                pass
    
    # สร้างไดเรกทอรีถ้าไม่มี
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            # ปรับสิทธิ์โฟลเดอร์
            try:
                import stat
                os.chmod(directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            except:
                pass
        except Exception as e:
            print(f"Could not create directory: {e}")
            return False
    
    # สร้างไฟล์ใหม่พร้อมหัวคอลัมน์
    try:
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Conductivity', 'Unit', 'Temperature'])
            # เขียนข้อมูลที่สำรองไว้กลับลงไป (ถ้ามี)
            if backup_created and len(backup_data) > 1:  # มีข้อมูลมากกว่าแค่หัวคอลัมน์
                writer.writerows(backup_data[1:])  # เขียนทุกแถวยกเว้นหัวคอลัมน์
                print(f"Restored {len(backup_data)-1} rows of data")
        print(f"Successfully created file: {filepath}")
        return True
    except Exception as e:
        print(f"Could not create file: {e}")
        # ลองใช้วิธี low-level
        try:
            with open(filepath, 'w') as f:
                f.write("Timestamp,Conductivity,Unit,Temperature\n")
            print(f"Created file using alternate method: {filepath}")
            return True
        except:
            return False

def manage_data_files():
    """จัดการไฟล์ข้อมูลตามโหมดการทำงาน
    - โหมด mock: สร้างไฟล์จำลอง (ไม่ลบไฟล์จริง)
    - โหมด real: ลบไฟล์จำลอง และเตรียมไฟล์จริง
    """
    print("\n===== MANAGING DATA FILES =====")
    
    config = get_config()
    mock_mode = config.get('device', 'mock_data', fallback=True)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    mock_file = os.path.join(project_dir, "sension7_data.csv")
    real_file = os.path.join(project_dir, "collect_data_sension.csv")
    
    # ลบไฟล์ backup ที่อาจมีอยู่
    backup_extensions = [".bak", ".backup", ".old", ".tmp"]
    for base_file in ["sension7_data.csv", "collect_data_sension.csv"]:
        for ext in backup_extensions:
            backup_path = os.path.join(project_dir, f"{base_file}{ext}")
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    print(f"✓ Removed old backup file: {backup_path}")
                except Exception as e:
                    print(f"✗ Could not remove backup file: {e}")
    
    print(f"Project directory: {project_dir}")
    print(f"Directory exists: {'✓ Yes' if os.path.exists(project_dir) else '✗ No'}")
    is_writable = os.access(project_dir, os.W_OK) if os.path.exists(project_dir) else False
    print(f"Directory writable: {'✓ Yes' if is_writable else '✗ No'}")
    
    # สร้างโฟลเดอร์โปรเจคหากไม่มี
    if not os.path.exists(project_dir):
        try:
            os.makedirs(project_dir, exist_ok=True)
            # ปรับสิทธิ์โฟลเดอร์
            try:
                import stat
                os.chmod(project_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            except:
                pass
            print(f"✓ Created project directory: {project_dir}")
        except Exception as e:
            print(f"✗ Could not create project directory: {e}")
    
    if mock_mode:
        # โหมดจำลอง: ตรวจสอบและสร้างไฟล์จำลอง (ไม่ลบไฟล์จริง)
        print("\n⚠️ Running in MOCK MODE - using simulated data")
        
        # ตรวจสอบไฟล์จำลอง
        mock_file_needs_recreation = False
        mock_file_status = "Unknown"
        
        if not os.path.exists(mock_file):
            mock_file_status = "Missing"
            mock_file_needs_recreation = True
        elif os.path.getsize(mock_file) == 0:
            mock_file_status = "Empty"
            mock_file_needs_recreation = True
        elif is_file_locked(mock_file):
            mock_file_status = "Locked"
            mock_file_needs_recreation = True
        else:
            # ตรวจสอบว่าไฟล์มีโครงสร้างที่ถูกต้อง
            try:
                with open(mock_file, 'r', newline='') as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    if not headers or len(headers) < 4 or 'Timestamp' not in headers:
                        mock_file_status = "Invalid Structure"
                        mock_file_needs_recreation = True
                    else:
                        # ตรวจสอบว่ามีข้อมูลหรือไม่
                        try:
                            row = next(reader, None)
                            if not row:
                                mock_file_status = "No Data"
                                mock_file_needs_recreation = True
                            else:
                                mock_file_status = "Valid"
                        except:
                            mock_file_status = "Corrupted"
                            mock_file_needs_recreation = True
            except Exception as e:
                mock_file_status = f"Error: {str(e)}"
                mock_file_needs_recreation = True
        
        print(f"Mock data file status: {mock_file_status}")
        
        if mock_file_needs_recreation:
            print(f"⚙️ Recreating mock data file...")
            # สร้างไฟล์เปล่าก่อน
            if force_create_csv_file(mock_file):
                print("✓ Created empty mock data file")
                print("⚙️ Generating mock historical data...")
                generate_mock_historical_data(num_days=7)
            else:
                print("✗ Failed to create mock data file")
        else:
            print(f"✓ Using existing mock data file: {mock_file}")
            
        # แสดงสถานะไฟล์จริง (ไม่ลบ)
        if os.path.exists(real_file):
            print(f"\nℹ️ Note: Real data file exists: {real_file}")
            print(f"   It will not be used in mock mode but will be kept for real mode.")
    else:
        # โหมดจริง: เตรียมไฟล์จริง ลบไฟล์จำลอง
        print("\n🔴 Running in REAL MODE - using actual sensor data")
        
        # ลบไฟล์จำลองถ้ามี
        if os.path.exists(mock_file):
            try:
                os.remove(mock_file)
                print(f"✓ Removed mock data file: {mock_file}")
            except Exception as e:
                print(f"✗ Could not remove mock data file: {e}")
                # พยายามอีกครั้งด้วยวิธีอื่น
                try:
                    if os.name == 'nt':  # Windows
                        os.system(f'del /f "{mock_file}"')
                    else:  # Linux/Mac
                        os.system(f'rm -f "{mock_file}"')
                    if not os.path.exists(mock_file):
                        print(f"✓ Removed mock file using system command")
                except:
                    pass
        
        # เตรียมไฟล์จริง
        real_file_needs_recreation = False
        if not os.path.exists(real_file):
            print("Real data file missing, creating new one...")
            real_file_needs_recreation = True
        elif os.path.getsize(real_file) == 0:
            print("Real data file is empty, recreating...")
            real_file_needs_recreation = True
        elif is_file_locked(real_file):
            print("Real data file is locked, recreating...")
            real_file_needs_recreation = True
        
        if real_file_needs_recreation:
            print(f"⚙️ Creating/recreating real data file...")
            if force_create_csv_file(real_file):
                print(f"✓ Ready to collect data to: {real_file}")
            else:
                print(f"✗ Failed to create real data file!")
        else:
            print(f"✓ Using existing real data file: {real_file}")
    
    print("\n===== DATA FILES READY =====\n")

def check_filesystem_health():
    """ตรวจสอบสถานะระบบไฟล์และพยายามซ่อมแซม"""
    print("\n===== CHECKING FILESYSTEM HEALTH =====")
    
    # ตรวจสอบโฟลเดอร์โปรเจค
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Project directory: {project_dir}")
    
    # 1. ตรวจสอบการมีอยู่ของโฟลเดอร์
    if not os.path.exists(project_dir):
        print("Project directory doesn't exist, creating...")
        try:
            os.makedirs(project_dir, exist_ok=True)
            print("✓ Created project directory")
        except Exception as e:
            print(f"✗ Failed to create project directory: {e}")
    else:
        print("✓ Project directory exists")
        
    # 2. ตรวจสอบสิทธิ์การเขียน
    if not os.access(project_dir, os.W_OK):
        print("✗ Project directory is not writable, attempting to fix...")
        try:
            import stat
            os.chmod(project_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            if os.access(project_dir, os.W_OK):
                print("✓ Fixed directory permissions")
            else:
                print("✗ Failed to fix directory permissions")
        except Exception as e:
            print(f"✗ Error setting permissions: {e}")
    else:
        print("✓ Project directory is writable")
    
    # 3. ตรวจสอบพื้นที่ว่าง
    try:
        import shutil
        free_space = shutil.disk_usage(project_dir).free
        free_space_mb = free_space / (1024 * 1024)  # แปลงเป็น MB
        print(f"Available disk space: {free_space_mb:.2f} MB")
        
        if free_space_mb < 10:  # น้อยกว่า 10 MB
            print("⚠️ WARNING: Very low disk space!")
        elif free_space_mb < 100:  # น้อยกว่า 100 MB
            print("⚠️ Warning: Low disk space")
    except Exception as e:
        print(f"Could not check disk space: {e}")
    
    # 4. ตรวจสอบไฟล์ CSV
    config = get_config()
    mock_mode = config.get('device', 'mock_data', fallback=True)
    
    if mock_mode:
        filename = "sension7_data.csv"
    else:
        filename = "collect_data_sension.csv"
    
    filepath = os.path.join(project_dir, filename)
    
    if os.path.exists(filepath):
        print(f"File exists: {filepath}")
        
        # ตรวจสอบไฟล์ล็อค
        if is_file_locked(filepath):
            print("⚠️ File is locked, will attempt to repair at runtime")
        else:
            print("✓ File is not locked")
            
        # ตรวจสอบขนาดไฟล์
        try:
            file_size = os.path.getsize(filepath)
            print(f"File size: {file_size} bytes")
            
            if file_size == 0:
                print("⚠️ File is empty, will be recreated at runtime")
        except Exception as e:
            print(f"Error checking file size: {e}")
    else:
        print(f"File doesn't exist yet: {filepath}")
        print("File will be created when needed")
    
    print("===== FILESYSTEM CHECK COMPLETE =====\n")
    return True
