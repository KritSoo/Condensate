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

# Serial port configuration
SERIAL_PORT = "COM3"  # Change to match your USB-to-Serial adapter port
BAUD_RATE = 9600     # Verify baud rate in HACH Sension7 manual
TIMEOUT = 1.0        # Serial timeout in seconds
MOCK_DATA_MODE = True  # Set to False for real serial connection

# Data logging configuration
LOG_FILE = "sension7_data.csv"
MEASUREMENT_INTERVAL = 0.1  # Time between measurements in seconds

# Data validation constants
MIN_MOCK_VALUE = 100.0
MAX_MOCK_VALUE = 500.0
MIN_MOCK_TEMP = 100.0
MAX_MOCK_TEMP = 200.0
SPIKE_PROBABILITY = 0.05  # 5% chance of spike in historical data

def parse_sension_data(raw_data_string):
    """
    Parse raw data string from HACH Sension7 meter.
    Expected format: "123.45 uS/cm" or "1.23 mS/cm"
    
    Returns:
        tuple: (float or None, str or None) - (conductivity value, unit)
    """
    try:
        cleaned_data = raw_data_string.strip()
        pattern = r"(\d+\.?\d*)\s*(µS/cm|uS/cm|mS/cm)"
        
        match = re.search(pattern, cleaned_data, re.IGNORECASE)
        if match:
            value_str, unit = match.groups()
            unit = unit.replace('µ', 'u')
            return float(value_str), unit
        return None, None
        
    except (AttributeError, ValueError) as e:
        print(f"Error parsing data: {e}")
        return None, None

def save_to_csv(timestamp, conductivity_value, unit, temperature=None, filename=LOG_FILE):
    """Save measurement data to CSV file with headers if new file."""
    try:
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Timestamp', 'Conductivity', 'Unit', 'Temperature'])
            writer.writerow([
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                conductivity_value,
                unit,
                temperature
            ])
    except IOError as e:
        print(f"Error saving to CSV: {e}")

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

def read_and_process_data(ser_port=SERIAL_PORT, baud_rate=BAUD_RATE, 
                         timeout=TIMEOUT, data_callback=None):
    """Continuously read and process data."""
    ser = None
    try:
        if MOCK_DATA_MODE:
            if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
                generate_mock_historical_data(num_days=7)
            
            print("Running in MOCK DATA mode")
            while True:
                timestamp = datetime.now()  # Use exact current time
                mock_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE)
                mock_temp = random.uniform(MIN_MOCK_TEMP, MAX_MOCK_TEMP)
                mock_unit = random.choice(["uS/cm", "mS/cm"])
                
                save_to_csv(timestamp, mock_value, mock_unit, mock_temp)
                
                if data_callback:
                    data_callback(timestamp, mock_value, mock_unit, mock_temp)
                    
                time.sleep(1800.0)
                continue

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
            if ser.in_waiting:
                raw_data = ser.readline().decode('utf-8', errors='ignore')
                print(f"Raw data: {raw_data.strip()}")
                
                value, unit = parse_sension_data(raw_data)
                if value is not None and data_callback:
                    timestamp = datetime.now()
                    # เพิ่ม None สำหรับค่า temperature ในกรณีใช้งานจริง
                    data_callback(timestamp, value, unit, None)
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
