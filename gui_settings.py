"""
Settings dialog for the application.
Allows users to configure serial ports, data logging, and device settings.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import serial.tools.list_ports

from config_manager import get_config
from device_adapters import AVAILABLE_ADAPTERS

class SettingsDialog:
    """Dialog for configuring application settings."""
    
    def __init__(self, parent):
        """Initialize settings dialog."""
        self.parent = parent
        self.config = get_config()
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("ตั้งค่าโปรแกรม")
        self.window.geometry("600x500")
        self.window.minsize(500, 400)
        self.window.resizable(True, True)
        self.window.transient(parent)  # Set as transient to parent
        self.window.grab_set()  # Modal dialog
        
        # Make sure dialog is destroyed when closed with X button
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Create UI
        self.create_widgets()
        
        # Load current settings
        self.load_settings()
        
        # Center the dialog window relative to parent
        self.center_window()
    
    def create_widgets(self):
        """Create UI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Connection settings tab
        self.connection_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.connection_tab, text="การเชื่อมต่อ")
        self.create_connection_tab()
        
        # Logging settings tab
        self.logging_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.logging_tab, text="การบันทึกข้อมูล")
        self.create_logging_tab()
        
        # Device settings tab
        self.device_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.device_tab, text="อุปกรณ์")
        self.create_device_tab()
        
        # Display settings tab
        self.display_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.display_tab, text="การแสดงผล")
        self.create_display_tab()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=10)
        
        # Save and cancel buttons
        ttk.Button(button_frame, text="บันทึก", command=self.on_save).pack(side="right", padx=5)
        ttk.Button(button_frame, text="ยกเลิก", command=self.on_cancel).pack(side="right", padx=5)
        ttk.Button(button_frame, text="ค่าเริ่มต้น", command=self.on_reset_defaults).pack(side="left", padx=5)
    
    def create_connection_tab(self):
        """Create connection settings tab."""
        # Serial port settings
        ttk.Label(self.connection_tab, text="พอร์ตอนุกรม (Serial Port):").grid(row=0, column=0, sticky="w", pady=5)
        
        # Combobox for serial ports with auto-detection
        self.port_combobox = ttk.Combobox(self.connection_tab, width=20)
        self.port_combobox.grid(row=0, column=1, sticky="w", pady=5)
        
        # Get available serial ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        
        # Refresh button
        ttk.Button(self.connection_tab, text="รีเฟรช", 
                  command=self.refresh_serial_ports).grid(row=0, column=2, padx=5)
        
        # Baud rate
        ttk.Label(self.connection_tab, text="อัตราบอด (Baud Rate):").grid(row=1, column=0, sticky="w", pady=5)
        
        # Combobox for common baud rates
        self.baud_combobox = ttk.Combobox(self.connection_tab, width=20)
        self.baud_combobox.grid(row=1, column=1, sticky="w", pady=5)
        self.baud_combobox['values'] = ['1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200']
        
        # Timeout
        ttk.Label(self.connection_tab, text="หมดเวลา (Timeout) (วินาที):").grid(row=2, column=0, sticky="w", pady=5)
        self.timeout_entry = ttk.Entry(self.connection_tab, width=20)
        self.timeout_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        # Mock data mode
        self.mock_data_var = tk.BooleanVar()
        ttk.Checkbutton(self.connection_tab, text="โหมดข้อมูลจำลอง (ไม่ใช้การเชื่อมต่อจริง)", 
                        variable=self.mock_data_var).grid(row=3, column=0, columnspan=3, sticky="w", pady=10)
        
        # Connection test button
        ttk.Button(self.connection_tab, text="ทดสอบการเชื่อมต่อ", 
                  command=self.test_connection).grid(row=4, column=0, sticky="w", pady=10)
    
    def create_logging_tab(self):
        """Create logging settings tab."""
        # Log file path
        ttk.Label(self.logging_tab, text="ไฟล์บันทึกข้อมูล:").grid(row=0, column=0, sticky="w", pady=5)
        
        # Frame for file path and browse button
        file_frame = ttk.Frame(self.logging_tab)
        file_frame.grid(row=0, column=1, sticky="w", pady=5)
        
        self.log_file_entry = ttk.Entry(file_frame, width=30)
        self.log_file_entry.pack(side="left")
        
        ttk.Button(file_frame, text="เลือก...", 
                  command=self.browse_log_file).pack(side="left", padx=5)
        
        # Enable backup option
        self.backup_var = tk.BooleanVar()
        ttk.Checkbutton(self.logging_tab, text="เปิดใช้งานการสำรองข้อมูล", 
                        variable=self.backup_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Test file writing
        ttk.Button(self.logging_tab, text="ทดสอบการบันทึกไฟล์", 
                  command=self.test_file_writing).grid(row=2, column=0, sticky="w", pady=10)
    
    def create_device_tab(self):
        """Create device settings tab."""
        # Device model selection
        ttk.Label(self.device_tab, text="รุ่นเครื่องวัด:").grid(row=0, column=0, sticky="w", pady=5)
        
        # Combobox for device models
        self.device_combobox = ttk.Combobox(self.device_tab, width=30)
        self.device_combobox.grid(row=0, column=1, sticky="w", pady=5)
        self.device_combobox['values'] = list(AVAILABLE_ADAPTERS.keys())
        
        # Device info display
        ttk.Label(self.device_tab, text="ข้อมูลอุปกรณ์:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        
        # Text widget for device info
        self.device_info = tk.Text(self.device_tab, height=5, width=40, wrap="word")
        self.device_info.grid(row=1, column=1, sticky="w", pady=5)
        self.device_info.config(state="disabled")
        
        # Bind selection event
        self.device_combobox.bind("<<ComboboxSelected>>", self.update_device_info)
        
        # Measurement interval
        ttk.Label(self.device_tab, text="ระยะเวลาวัด (วินาที):").grid(row=2, column=0, sticky="w", pady=5)
        self.interval_entry = ttk.Entry(self.device_tab, width=10)
        self.interval_entry.grid(row=2, column=1, sticky="w", pady=5)
    
    def create_display_tab(self):
        """Create display settings tab."""
        # Update interval
        ttk.Label(self.display_tab, text="รีเฟรชการแสดงผล (วินาที):").grid(row=0, column=0, sticky="w", pady=5)
        self.update_interval_entry = ttk.Entry(self.display_tab, width=10)
        self.update_interval_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Show grid option
        self.show_grid_var = tk.BooleanVar()
        ttk.Checkbutton(self.display_tab, text="แสดงเส้นตาราง", 
                        variable=self.show_grid_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Theme selection
        ttk.Label(self.display_tab, text="ธีม:").grid(row=2, column=0, sticky="w", pady=5)
        
        self.theme_combobox = ttk.Combobox(self.display_tab, width=20)
        self.theme_combobox.grid(row=2, column=1, sticky="w", pady=5)
        self.theme_combobox['values'] = ['light', 'dark']
    
    def load_settings(self):
        """Load current settings into the form."""
        # Connection settings
        self.port_combobox.set(self.config.get('serial', 'port', fallback='COM3'))
        self.baud_combobox.set(str(self.config.get('serial', 'baud_rate', fallback='9600')))
        self.timeout_entry.insert(0, str(self.config.get('serial', 'timeout', fallback='1.0')))
        self.mock_data_var.set(self.config.get('device', 'mock_data', fallback=True))
        
        # Logging settings
        self.log_file_entry.insert(0, self.config.get('logging', 'log_file', fallback='sension7_data.csv'))
        self.backup_var.set(self.config.get('logging', 'backup_enabled', fallback=True))
        
        # Device settings
        device_model = self.config.get('device', 'model', fallback='HACH Sension7')
        self.device_combobox.set(device_model)
        self.interval_entry.insert(0, str(self.config.get('device', 'measurement_interval', fallback='0.1')))
        self.update_device_info(None)  # Update device info display
        
        # Display settings
        self.update_interval_entry.insert(0, str(self.config.get('display', 'update_interval', fallback='2.0')))
        self.show_grid_var.set(self.config.get('display', 'show_grid', fallback=True))
        self.theme_combobox.set(self.config.get('display', 'theme', fallback='light'))
    
    def save_settings(self):
        """Save settings from the form to configuration."""
        try:
            # Connection settings
            self.config.set('serial', 'port', self.port_combobox.get())
            self.config.set('serial', 'baud_rate', self.baud_combobox.get())
            self.config.set('serial', 'timeout', self.timeout_entry.get())
            self.config.set('device', 'mock_data', str(self.mock_data_var.get()))
            
            # Logging settings
            self.config.set('logging', 'log_file', self.log_file_entry.get())
            self.config.set('logging', 'backup_enabled', str(self.backup_var.get()))
            
            # Device settings
            self.config.set('device', 'model', self.device_combobox.get())
            self.config.set('device', 'measurement_interval', self.interval_entry.get())
            
            # Display settings
            self.config.set('display', 'update_interval', self.update_interval_entry.get())
            self.config.set('display', 'show_grid', str(self.show_grid_var.get()))
            self.config.set('display', 'theme', self.theme_combobox.get())
            
            # Save to file
            self.config.save()
            return True
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่า: {e}")
            return False
    
    def on_save(self):
        """Handle save button click."""
        if self.save_settings():
            messagebox.showinfo("บันทึกการตั้งค่า", "บันทึกการตั้งค่าเรียบร้อยแล้ว")
            self.window.destroy()
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.window.destroy()
    
    def on_reset_defaults(self):
        """Handle reset to defaults button click."""
        if messagebox.askyesno("ยืนยัน", "คุณต้องการรีเซ็ตการตั้งค่าทั้งหมดเป็นค่าเริ่มต้นหรือไม่?"):
            from config_manager import DEFAULT_CONFIG
            
            # Reset all settings to defaults
            for section, options in DEFAULT_CONFIG.items():
                for key, value in options.items():
                    self.config.set(section, key, str(value))
            
            # Reload form
            self.clear_form()
            self.load_settings()
            
            messagebox.showinfo("รีเซ็ตการตั้งค่า", "รีเซ็ตการตั้งค่าเป็นค่าเริ่มต้นแล้ว")
    
    def clear_form(self):
        """Clear all form fields."""
        self.port_combobox.set('')
        self.baud_combobox.set('')
        self.timeout_entry.delete(0, tk.END)
        self.log_file_entry.delete(0, tk.END)
        self.device_combobox.set('')
        self.interval_entry.delete(0, tk.END)
        self.update_interval_entry.delete(0, tk.END)
        self.theme_combobox.set('')
    
    def refresh_serial_ports(self):
        """Refresh available serial ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        
        if not ports:
            messagebox.showinfo("พอร์ตอนุกรม", "ไม่พบพอร์ตอนุกรมในระบบ")
    
    def browse_log_file(self):
        """Open file dialog to choose log file."""
        current_file = self.log_file_entry.get()
        current_dir = os.path.dirname(current_file) if current_file else os.getcwd()
        
        filename = filedialog.asksaveasfilename(
            initialdir=current_dir,
            title="เลือกไฟล์บันทึกข้อมูล",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            defaultextension=".csv"
        )
        
        if filename:
            self.log_file_entry.delete(0, tk.END)
            self.log_file_entry.insert(0, filename)
    
    def update_device_info(self, event):
        """Update device info when selection changes."""
        try:
            selected_device = self.device_combobox.get()
            
            # Enable editing
            self.device_info.config(state="normal")
            self.device_info.delete(1.0, tk.END)
            
            if selected_device in AVAILABLE_ADAPTERS:
                adapter = AVAILABLE_ADAPTERS[selected_device]()
                self.device_info.insert(tk.END, f"รุ่น: {adapter.name}\n")
                self.device_info.insert(tk.END, f"คำอธิบาย: {adapter.description}\n")
                
                command = adapter.get_command_string()
                if command:
                    self.device_info.insert(tk.END, f"ต้องการคำสั่ง: ใช่\n")
                else:
                    self.device_info.insert(tk.END, f"ต้องการคำสั่ง: ไม่ใช่\n")
            else:
                self.device_info.insert(tk.END, "ไม่พบข้อมูลอุปกรณ์")
            
            # Disable editing
            self.device_info.config(state="disabled")
            
        except Exception as e:
            print(f"Error updating device info: {e}")
    
    def test_connection(self):
        """Test serial connection with current settings."""
        port = self.port_combobox.get()
        
        if self.mock_data_var.get():
            messagebox.showinfo("ทดสอบการเชื่อมต่อ", 
                               "โหมดข้อมูลจำลองเปิดใช้งานอยู่\nไม่สามารถทดสอบการเชื่อมต่อได้")
            return
            
        try:
            baud = int(self.baud_combobox.get())
            timeout = float(self.timeout_entry.get())
            
            import serial
            ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
            ser.close()
            
            messagebox.showinfo("ทดสอบการเชื่อมต่อ", 
                               f"เชื่อมต่อกับพอร์ต {port} สำเร็จ!")
            
        except Exception as e:
            messagebox.showerror("ทดสอบการเชื่อมต่อ", 
                               f"ไม่สามารถเชื่อมต่อกับพอร์ต {port}\nข้อผิดพลาด: {e}")
    
    def test_file_writing(self):
        """Test file writing with current settings."""
        log_file = self.log_file_entry.get()
        
        try:
            # Get directory path
            log_dir = os.path.dirname(log_file)
            
            # Create directory if it doesn't exist
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Try to write a test line
            with open(log_file, 'a') as f:
                f.write("# Test write from settings dialog\n")
                
            messagebox.showinfo("ทดสอบการบันทึกไฟล์", 
                               f"บันทึกข้อมูลทดสอบลงในไฟล์ {log_file} สำเร็จ!")
            
        except Exception as e:
            messagebox.showerror("ทดสอบการบันทึกไฟล์", 
                               f"ไม่สามารถบันทึกข้อมูลลงในไฟล์ {log_file}\nข้อผิดพลาด: {e}")
    
    def center_window(self):
        """Center the dialog window relative to parent."""
        self.window.update_idletasks()
        
        # Get parent and dialog dimensions
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        
        dw = self.window.winfo_width()
        dh = self.window.winfo_height()
        
        # Calculate position
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        
        # Set position
        self.window.geometry(f"+{x}+{y}")
