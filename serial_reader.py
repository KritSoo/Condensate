"""
Serial communication module for HACH Sension7 Conductivity Meter.
Handles data reading, parsing, and logging functions.

Author: User
Date: 2024
"""

import serial
import time
from datetime import datetime, timedelta
import csv
import re
import os
import random  # Add import for random number generation

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

# Data logging configuration
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
        # Use the device adapter to parse the data
        return device_adapter.parse_data(raw_data_string)
    except Exception as e:
        print(f"Error parsing data: {e}")
        return None, None, None

def save_to_csv(timestamp, conductivity_value, unit, temperature=None, filename=LOG_FILE):
    """Save measurement data to CSV file with headers if new file."""
    # Prepare data row
    data_row = [
        timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        conductivity_value,
        unit,
        temperature
    ]
    
    # Create absolute path for the file if it's not already
    if not os.path.isabs(filename):
        filepath = os.path.join(os.getcwd(), filename)
    else:
        filepath = filename
    
    # Try to write to the main file
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        file_exists = os.path.isfile(filepath)
        # Use explicit mode 'a' for append
        with open(filepath, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Timestamp', 'Conductivity', 'Unit', 'Temperature'])
            writer.writerow(data_row)
        
        # Verify file was written
        if os.path.isfile(filepath):
            return True  # Successfully wrote to the file
        else:
            print(f"Warning: File doesn't exist after write: {filepath}")
            
    except IOError as e:
        print(f"Error saving to main CSV: {e}")
        
        # If main file has issues, try to save to a backup file
        try:
            # Use current directory for backup to avoid permission issues
            backup_filename = f"{os.path.splitext(os.path.basename(filepath))[0]}_backup.csv"
            backup_filepath = os.path.join(os.getcwd(), backup_filename)
            
            backup_exists = os.path.isfile(backup_filepath)
            
            print(f"Attempting to save to backup file: {backup_filepath}")
            with open(backup_filepath, 'a', newline='') as backup_file:
                writer = csv.writer(backup_file)
                if not backup_exists:
                    writer.writerow(['Timestamp', 'Conductivity', 'Unit', 'Temperature'])
                writer.writerow(data_row)
            print(f"Data saved to backup file: {backup_filepath}")
            return True  # Successfully wrote to backup file
        except Exception as backup_e:
            print(f"Error saving to backup CSV: {backup_e}")
            
            # Last resort: Try to write to user's home directory
            try:
                home_dir = os.path.expanduser("~")
                last_resort_file = os.path.join(home_dir, "sension7_emergency_backup.csv")
                with open(last_resort_file, 'a', newline='') as emergency_file:
                    writer = csv.writer(emergency_file)
                    if not os.path.getsize(last_resort_file):
                        writer.writerow(['Timestamp', 'Conductivity', 'Unit', 'Temperature'])
                    writer.writerow(data_row)
                print(f"Data saved to emergency backup: {last_resort_file}")
                return True
            except Exception as e_backup:
                print(f"All backup attempts failed: {e_backup}")
                return False
    except Exception as e:
        print(f"Unexpected error saving to CSV: {e}")
        return False

def generate_mock_historical_data(num_days=7):
    """Generate mock historical conductivity and temperature data."""
    print(f"Generating {num_days} days of mock historical data...")
    
    end_time = datetime.now()  # Use exact current time
    start_time = end_time - timedelta(days=num_days)
    current_time = start_time
    
    while current_time < end_time:
        base_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE * 0.6)
        temperature = random.uniform(MIN_MOCK_TEMP, MAX_MOCK_TEMP)
        
        if random.random() < SPIKE_PROBABILITY:
            base_value = random.uniform(MAX_MOCK_VALUE * 0.7, MAX_MOCK_VALUE)
        
        unit = random.choice(["uS/cm", "mS/cm"])
        
        # Add random minutes and seconds
        current_time = current_time + timedelta(
            hours=2,
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        save_to_csv(current_time, base_value, unit, temperature)
    
    print("Historical mock data generation complete")

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
        ensure_log_directory_exists()
        check_filesystem_permissions()
        
        # Use direct file writes to verify system is working
        test_file = "serial_reader_test.txt"
        try:
            with open(test_file, 'w') as f:
                f.write(f"Test file created at {datetime.now()}\n")
            print(f"Successfully created test file: {test_file}")
            print(f"Using device: {DEVICE_MODEL}")
        except Exception as e:
            print(f"WARNING: Could not create test file: {e}")
        
        if MOCK_DATA_MODE:
            if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
                generate_mock_historical_data(num_days=7)
            
            print("Running in MOCK DATA mode")
            while True:
                try:
                    timestamp = datetime.now()  # Use exact current time
                    mock_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE)
                    mock_temp = random.uniform(MIN_MOCK_TEMP, MAX_MOCK_TEMP)
                    mock_unit = random.choice(["uS/cm", "mS/cm"])
                    
                    # Added try-except block inside the loop
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
        
        while True:
            # Send command if needed by device
            if command_string:
                try:
                    ser.write(command_string)
                    print(f"Command sent: {command_string}")
                except Exception as cmd_e:
                    print(f"Error sending command: {cmd_e}")
                
            # Wait for response
            if ser.in_waiting:
                raw_data = ser.readline().decode('utf-8', errors='ignore')
                print(f"Raw data: {raw_data.strip()}")
                
                value, unit, temperature = parse_data(raw_data)
                if value is not None and data_callback:
                    timestamp = datetime.now()
                    # ใช้ค่าอุณหภูมิจากเครื่องวัด (ถ้ามี)
                    data_callback(timestamp, value, unit, temperature)
                elif value is None:
                    print("Failed to parse data")
                    
            time.sleep(MEASUREMENT_INTERVAL)
                
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except KeyboardInterrupt:
        print("\nStopping data collection...")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed")

def ensure_log_directory_exists():
    """Ensure that the directory for the log file exists and is writable."""
    try:
        # Get absolute path of current working directory
        current_dir = os.getcwd()
        print(f"Current working directory: {current_dir}")
        
        # Get the directory part of the log file path
        log_dir = os.path.dirname(LOG_FILE)
        
        # If LOG_FILE is just a filename without directory
        if not log_dir:
            # Use the current directory
            log_path = os.path.join(current_dir, LOG_FILE)
            log_dir = current_dir
        else:
            # Create absolute path if it's relative
            if not os.path.isabs(log_dir):
                log_dir = os.path.join(current_dir, log_dir)
                log_path = os.path.join(current_dir, LOG_FILE)
            else:
                log_path = LOG_FILE
        
        # Create directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"Created log directory: {log_dir}")
        
        print(f"Log file will be saved to: {log_path}")
        
        # Test if we can write to the directory with explicit path
        test_file = os.path.join(log_dir, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"Directory is writable: {log_dir}")
        except Exception as write_error:
            print(f"WARNING: Directory is not writable: {log_dir}")
            print(f"Write error: {write_error}")
            return False
        
        return True
    except Exception as e:
        print(f"Error ensuring log directory exists: {e}")
        print(f"Log file may not be writable: {LOG_FILE}")
        return False

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

# Only run initialization if this module is run directly
if __name__ == "__main__":
    # Ensure the log directory exists at the start
    ensure_log_directory_exists()
    # Check filesystem permissions
    check_filesystem_permissions()
