"""
Conductivity Data Logger - Main Entry Point
Supports multiple conductivity meter models.
"""

import threading
import tkinter as tk
from datetime import datetime

# Import from our modules
from config_manager import initialize_config, get_config
from serial_reader import (
    MOCK_DATA_MODE, SERIAL_PORT, BAUD_RATE, TIMEOUT, DEVICE_MODEL,
    read_and_process_data, save_to_csv
)
from gui_app import setup_gui, update_gui, run_gui
from gui_settings import SettingsDialog
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
    
    # Data is already saved in read_and_process_data

def show_settings_dialog(root_window):
    """Show the settings dialog."""
    settings_dialog = SettingsDialog(root_window)
    
def main():
    """Main program entry point."""
    # Initialize configuration
    initialize_config()
    config = get_config()
    
    print(f"Starting Conductivity Data Logger")
    print(f"Device Model: {DEVICE_MODEL}")
    print(f"Serial Port: {SERIAL_PORT}, Baud Rate: {BAUD_RATE}")
    
    # Initialize GUI
    main_window = setup_gui()
    
    # Add settings menu to main window if it's a Tk instance
    if isinstance(main_window, tk.Tk):
        menu_bar = tk.Menu(main_window)
        main_window.config(menu=menu_bar)
        
        # Add File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="ไฟล์", menu=file_menu)
        
        # Add Settings option
        file_menu.add_command(label="ตั้งค่า...", 
                              command=lambda: show_settings_dialog(main_window))
        file_menu.add_separator()
        file_menu.add_command(label="ออกจากโปรแกรม", command=main_window.quit)
    
    # Check filesystem permissions and create directories
    from serial_reader import ensure_log_directory_exists, check_filesystem_permissions
    
    # Run diagnostic checks
    if not ensure_log_directory_exists():
        print("WARNING: Log directory may not be writable. Logging may fail.")
    
    # Check detailed filesystem permissions
    check_filesystem_permissions()
    
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
