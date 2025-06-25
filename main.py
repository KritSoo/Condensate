"""
HACH Sension7 Conductivity Data Logger - Main Entry Point
"""

import threading
from datetime import datetime
#commit ผ่าน vscode ยากชิบหาย

# Import from our modules
from serial_reader import (
    MOCK_DATA_MODE, SERIAL_PORT, BAUD_RATE, TIMEOUT,
    read_and_process_data, save_to_csv
)
from gui_app import setup_gui, update_gui, run_gui
from gui_config import selected_date_str  # Updated import

def on_new_data(timestamp, conductivity, unit, temperature=None):
    """
    Callback function for handling new data from the serial reader.
    Updates GUI and logs data to CSV file.
    """
    print(f"[{timestamp}] Conductivity: {conductivity} {unit}, Temp: {temperature}°C")
    
    current_date = timestamp.strftime("%Y-%m-%d")
    if current_date == selected_date_str:
        update_gui(timestamp, conductivity, unit, temperature)
    
    save_to_csv(timestamp, conductivity, unit, temperature)

def main():
    """Main program entry point."""
    print("Starting HACH Sension7 Data Logger")
    print(f"Serial Port: {SERIAL_PORT}, Baud Rate: {BAUD_RATE}")
    
    # Initialize GUI
    setup_gui()
    
    # Create and start serial reading thread
    serial_thread = threading.Thread(
        target=read_and_process_data,
        args=(SERIAL_PORT, BAUD_RATE, TIMEOUT, on_new_data),
        daemon=True  # Thread will be terminated when main program exits
    )
    
    try:
        serial_thread.start()
        print("Serial communication started")
        
        # Run GUI (blocks until window is closed)
        run_gui()
        
    finally:
        if serial_thread.is_alive():
            print("Waiting for serial communication to stop...")
            serial_thread.join(timeout=2.0)  # Wait up to 2 seconds
        print("Program terminated")

if __name__ == "__main__":
    main()
