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

# Data validation constants (add these)
MIN_MOCK_VALUE = 100.0
MAX_MOCK_VALUE = 1000.0
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

def save_to_csv(timestamp, conductivity_value, unit, filename=LOG_FILE):
    """Save measurement data to CSV file with headers if new file."""
    try:
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Timestamp', 'Conductivity', 'Unit'])
            writer.writerow([
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                conductivity_value,
                unit
            ])
    except IOError as e:
        print(f"Error saving to CSV: {e}")

def generate_mock_historical_data(num_days=7):
    """Generate mock historical conductivity data."""
    print(f"Generating {num_days} days of mock historical data...")
    
    end_time = datetime.now() - timedelta(days=1)  # Stop at yesterday
    start_time = end_time - timedelta(days=num_days)
    current_time = start_time
    
    while current_time < end_time:
        # Generate base conductivity with some natural variation
        base_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE * 0.6)
        
        # Occasionally add spikes
        if random.random() < SPIKE_PROBABILITY:
            base_value = random.uniform(MAX_MOCK_VALUE * 0.7, MAX_MOCK_VALUE)
        
        # Randomly choose unit
        unit = random.choice(["uS/cm", "mS/cm"])
        
        # Save to CSV
        save_to_csv(current_time, base_value, unit)
        
        # Increment by 10 minutes
        current_time += timedelta(minutes=10)
    
    print("Historical mock data generation complete")

def read_and_process_data(ser_port=SERIAL_PORT, baud_rate=BAUD_RATE, 
                         timeout=TIMEOUT, data_callback=None):
    """
    Continuously read and process data from the HACH Sension7.
    In mock mode, generates random conductivity values for testing.
    
    Args:
        ser_port (str): Serial port name
        baud_rate (int): Baud rate for serial communication
        timeout (float): Serial timeout in seconds
        data_callback (callable): Function to call with (timestamp, value, unit)
    """
    ser = None
    try:
        if MOCK_DATA_MODE:
            # Check if historical data needs to be generated
            if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
                generate_mock_historical_data(num_days=7)
            
            print("Running in MOCK DATA mode")
            print("Generated data will be random values")
            while True:
                # Generate mock conductivity data
                mock_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE)
                mock_unit = random.choice(["uS/cm", "mS/cm"])
                mock_raw = f"{mock_value:.2f} {mock_unit} (MOCK)"
                
                print(f"Raw data: {mock_raw}")
                
                if data_callback:
                    timestamp = datetime.now()
                    data_callback(timestamp, mock_value, mock_unit)
                    
                time.sleep(120.0)  # Sleep for 2 minutes in mock mode
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
                    data_callback(timestamp, value, unit)
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
