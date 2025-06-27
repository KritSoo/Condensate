"""
Conductivity Data Logger - Main Entry Point
Supports multiple conductivity meter models.
"""

import threading
import tkinter as tk
from datetime import datetime

# Import from our modules
from config_manager import initialize_config, get_config
from db_manager import get_connection, init_database, save_data, get_data_table_name
from serial_reader import (
    MOCK_DATA_MODE, SERIAL_PORT, BAUD_RATE, TIMEOUT, DEVICE_MODEL,
    read_and_process_data
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
    
    # บันทึกข้อมูลลงฐานข้อมูล
    try:
        # บันทึกข้อมูล
        save_data(timestamp, conductivity, unit, temperature)
    except Exception as e:
        print(f"ไม่สามารถบันทึกข้อมูลได้: {e}")

def show_settings_dialog(root_window):
    """Show the settings dialog."""
    settings_dialog = SettingsDialog(root_window)
    
    # รอให้หน้าต่างตั้งค่าถูกปิด
    root_window.wait_window(settings_dialog.window)
    
    # เมื่อปิดหน้าต่างตั้งค่าแล้ว รีเฟรช UI ตามการตั้งค่าใหม่
    from gui_app import refresh_ui
    refresh_ui()

# ฟังก์ชัน initialize_csv_files ถูกแทนที่ด้วย manage_data_files ใน serial_reader.py

def verify_db_connection():
    """ตรวจสอบสถานะการเชื่อมต่อกับฐานข้อมูล"""
    print("\n===== VERIFYING DATABASE CONNECTION =====")
    
    # ทดสอบการเชื่อมต่อกับฐานข้อมูล
    connection = get_connection()
    if connection:
        print("Database connection: Success")
        
        # ตรวจสอบชื่อตาราง
        mock_table = get_data_table_name(mock_mode=True)
        real_table = get_data_table_name(mock_mode=False)
        
        # ตรวจสอบว่าตารางมีอยู่จริงหรือไม่
        try:
            with connection.cursor() as cursor:
                # ตรวจสอบตารางข้อมูลจำลอง
                cursor.execute(f"SHOW TABLES LIKE '{mock_table}'")
                mock_exists = cursor.fetchone() is not None
                
                # ตรวจสอบตารางข้อมูลจริง
                cursor.execute(f"SHOW TABLES LIKE '{real_table}'")
                real_exists = cursor.fetchone() is not None
                
            print(f"Mock data table: {mock_table} - {'Exists' if mock_exists else 'Not found'}")
            print(f"Real data table: {real_table} - {'Exists' if real_exists else 'Not found'}")
            
            # ปิดการเชื่อมต่อ
            connection.close()
            
            # ถ้าตารางไม่มีอยู่ ให้สร้างใหม่
            if not (mock_exists and real_exists):
                print("Some tables are missing, initializing database...")
                return init_database()
            
            return True
            
        except Exception as e:
            print(f"Error checking tables: {e}")
            connection.close()
            return False
    else:
        print("Database connection: Failed")
        print("Please check your database configuration")
        return False

def main():
    """Main program entry point."""
    try:
        # Initialize configuration
        initialize_config()
        config = get_config()
        
        print(f"Starting Conductivity Data Logger")
        print(f"Device Model: {DEVICE_MODEL}")
        print(f"Serial Port: {SERIAL_PORT}, Baud Rate: {BAUD_RATE}")
        
        # Check and display mock data mode status
        mock_mode = config.get('device', 'mock_data', fallback=True)
        print(f"Mode: {'MOCK' if mock_mode else 'REAL'}")
        
        # ตรวจสอบและสร้างโฟลเดอร์โปรเจคหากยังไม่มี
        import os
        project_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(project_dir):
            try:
                os.makedirs(project_dir, exist_ok=True)
                print(f"Created project directory: {project_dir}")
            except Exception as e:
                print(f"Could not create project directory: {e}")
        
        # ตรวจสอบสิทธิ์การเขียน
        if not os.access(project_dir, os.W_OK):
            print(f"Warning: Project directory {project_dir} is not writable")
            print("Data will be saved to temporary directory instead")
        
        # เตรียมและตรวจสอบฐานข้อมูลโดยใช้ db_manager
        print("\n===== INITIALIZING DATABASE =====")
        init_success = init_database()
        print(f"Database initialization: {'Success' if init_success else 'Warning: Database setup failed'}")
        
        # ตรวจสอบการเชื่อมต่อกับฐานข้อมูล
        verified = verify_db_connection()
        print(f"Database verification: {'Success' if verified else 'Failed, will attempt to create when saving'}")
        
        # เลือกตารางตามโหมดการทำงาน
    except Exception as startup_e:
        print(f"\n❌ ERROR DURING STARTUP: {startup_e}")
        print("Attempting to continue despite errors...")
        import os
        project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ตรวจสอบสิทธิ์การเขียนในโฟลเดอร์โปรเจค
    print("\n--- Project Directory Permissions Check ---")
    print(f"Project directory: {project_dir}")
    print(f"Directory exists: {os.path.exists(project_dir)}")
    print(f"Directory writable: {os.access(project_dir, os.W_OK) if os.path.exists(project_dir) else 'N/A'}")
    
    # ตรวจสอบว่าโฟลเดอร์โปรเจคมีอยู่
    try:
        if not os.path.exists(project_dir):
            print(f"Creating project directory: {project_dir}")
            os.makedirs(project_dir, exist_ok=True)
    except Exception as fs_e:
        print(f"Error creating project directory: {fs_e}")
    
    if mock_mode:
        data_table = get_data_table_name(mock_mode=True)
        print("โปรแกรมกำลังทำงานในโหมดข้อมูลจำลอง (Mock Data Mode)")
        print(f"จะใช้ตารางข้อมูลคือ: {data_table}")
        
        print("หากต้องการเชื่อมต่อเครื่อง HACH Sension7 จริง โปรดทำตามขั้นตอนนี้:")
        print("1. คลิกที่เมนู 'ไฟล์' และเลือก 'ตั้งค่า...'")
        print("2. ในแท็บ 'การเชื่อมต่อ' ให้ยกเลิกการเลือก 'โหมดข้อมูลจำลอง'")
        print("3. เลือกพอร์ตที่เชื่อมต่อกับเครื่อง (เช่น COM3)")
        print("4. บันทึกการตั้งค่าและรีสตาร์ทโปรแกรม")
    else:
        data_table = get_data_table_name(mock_mode=False)
        print("โปรแกรมกำลังทำงานในโหมดวัดค่าจากเครื่องจริง")
        print(f"จะบันทึกข้อมูลลงในตาราง: {data_table}")
        print(f"เชื่อมต่อกับพอร์ต: {SERIAL_PORT}, ความเร็ว: {BAUD_RATE}")
    
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
    
    # แสดงชื่อตารางที่ใช้
    data_table = get_data_table_name()
    print(f"Using data table: {data_table}")
    
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
    try:
        main()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("Program encountered a critical error.")
        print("Please check the log files and the filesystem permissions.")
        
        # พยายามรายงานข้อผิดพลาดเพิ่มเติม
        import traceback
        print("\nError details:")
        traceback.print_exc()
        
        # รอให้ผู้ใช้กด Enter ก่อนปิดโปรแกรม
        input("\nPress Enter to exit...")
