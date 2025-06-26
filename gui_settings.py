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
        ttk.Button(button_frame, text="ใช้งานทันที", command=self.on_apply).pack(side="right", padx=5)
        ttk.Button(button_frame, text="ยกเลิก", command=self.on_cancel).pack(side="right", padx=5)
        ttk.Button(button_frame, text="ค่าเริ่มต้น", command=self.on_reset_defaults).pack(side="left", padx=5)
    
    def create_connection_tab(self):
        """Create connection settings tab."""
        # Mock data mode - move to top for visibility
        self.mock_data_var = tk.BooleanVar()
        mock_frame = ttk.LabelFrame(self.connection_tab, text="โหมดการทำงาน", padding="10")
        mock_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        
        mock_check = ttk.Checkbutton(mock_frame, text="ใช้โหมดข้อมูลจำลอง (ไม่เชื่อมต่อกับเครื่องจริง)", 
                        variable=self.mock_data_var)
        mock_check.pack(fill="x", pady=5)
        
        mock_info = ttk.Label(mock_frame, 
                            text="หากต้องการใช้เครื่อง HACH Sension7 จริง ให้ยกเลิกการเลือกตัวเลือกนี้\n"
                                 "และตรวจสอบว่าได้เลือกพอร์ตและอัตราบอดที่ถูกต้อง",
                            wraplength=450)
        mock_info.pack(fill="x", pady=5)
        
        # Serial port settings
        conn_frame = ttk.LabelFrame(self.connection_tab, text="การเชื่อมต่อซีเรียล", padding="10")
        conn_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        ttk.Label(conn_frame, text="พอร์ตอนุกรม (Serial Port):").grid(row=0, column=0, sticky="w", pady=5)
        
        # Combobox for serial ports with auto-detection
        self.port_combobox = ttk.Combobox(conn_frame, width=20)
        self.port_combobox.grid(row=0, column=1, sticky="w", pady=5)
        
        # Get available serial ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        
        # Refresh button
        ttk.Button(conn_frame, text="รีเฟรช", 
                  command=self.refresh_serial_ports).grid(row=0, column=2, padx=5)
        
        # Baud rate
        ttk.Label(conn_frame, text="อัตราบอด (Baud Rate):").grid(row=1, column=0, sticky="w", pady=5)
        
        # Combobox for common baud rates
        self.baud_combobox = ttk.Combobox(conn_frame, width=20)
        self.baud_combobox.grid(row=1, column=1, sticky="w", pady=5)
        self.baud_combobox['values'] = ['1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200']
        
        # Timeout
        ttk.Label(conn_frame, text="หมดเวลา (Timeout) (วินาที):").grid(row=2, column=0, sticky="w", pady=5)
        self.timeout_entry = ttk.Entry(conn_frame, width=20)
        self.timeout_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        # Connection test button
        ttk.Button(self.connection_tab, text="ทดสอบการเชื่อมต่อ", 
                  command=self.test_connection).grid(row=2, column=0, sticky="w", pady=10)
    
    def create_logging_tab(self):
        """Create logging settings tab."""
        # Log directory path
        ttk.Label(self.logging_tab, text="โฟลเดอร์บันทึกข้อมูล:").grid(row=0, column=0, sticky="w", pady=5)
        
        # Frame for directory path and browse button
        dir_frame = ttk.Frame(self.logging_tab)
        dir_frame.grid(row=0, column=1, sticky="w", pady=5)
        
        self.log_dir_entry = ttk.Entry(dir_frame, width=30)
        self.log_dir_entry.pack(side="left")
        
        ttk.Button(dir_frame, text="เลือก...", 
                  command=self.browse_log_directory).pack(side="left", padx=5)

        # Log file path
        ttk.Label(self.logging_tab, text="ไฟล์บันทึกข้อมูล:").grid(row=1, column=0, sticky="w", pady=5)
        
        # Frame for file path and browse button
        file_frame = ttk.Frame(self.logging_tab)
        file_frame.grid(row=1, column=1, sticky="w", pady=5)
        
        self.log_file_entry = ttk.Entry(file_frame, width=30)
        self.log_file_entry.pack(side="left")
        
        # Enable backup option
        self.backup_var = tk.BooleanVar()
        ttk.Checkbutton(self.logging_tab, text="เปิดใช้งานการสำรองข้อมูล", 
                        variable=self.backup_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        # Test file writing
        test_frame = ttk.Frame(self.logging_tab)
        test_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        
        ttk.Button(test_frame, text="ทดสอบการบันทึกไฟล์", 
                  command=self.test_file_writing).pack(side="left", padx=5)
                  
        ttk.Button(test_frame, text="ตรวจสอบสิทธิ์", 
                  command=self.check_permissions).pack(side="left", padx=5)
                  
        # Directory status display
        self.dir_status_var = tk.StringVar(value="")
        ttk.Label(self.logging_tab, textvariable=self.dir_status_var,
                 foreground="blue").grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
    
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
        
        # Theme selection - ย้ายมาไว้ในกรอบแยกต่างหากให้เห็นชัดเจนขึ้น
        theme_frame = ttk.LabelFrame(self.display_tab, text="ธีม", padding="10")
        theme_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(theme_frame, text="เลือกธีม:").grid(row=0, column=0, sticky="w", pady=5)
        
        self.theme_combobox = ttk.Combobox(theme_frame, width=20)
        self.theme_combobox.grid(row=0, column=1, sticky="w", pady=5)
        self.theme_combobox['values'] = ['light', 'dark']
        
        # เพิ่มคำอธิบายเกี่ยวกับธีม
        ttk.Label(theme_frame, 
                 text="- light: ธีมสว่าง (ค่าเริ่มต้น)\n- dark: ธีมมืด",
                 wraplength=300).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # เพิ่มปุ่มทดลองใช้ธีมทันที
        ttk.Button(theme_frame, text="ทดลองธีม", 
                  command=self.apply_theme_preview).grid(row=2, column=0, sticky="w", pady=5)
                  
        # เพิ่มปุ่มรีเซ็ตธีม (ใช้ในกรณีที่มีปัญหาการแสดงผล)
        ttk.Button(theme_frame, text="รีเซ็ตธีม", 
                  command=self.reset_theme_emergency).grid(row=2, column=1, sticky="w", pady=5)
                  
        # เพิ่มคำเตือนเกี่ยวกับการเปลี่ยนธีม
        warning_label = ttk.Label(theme_frame, 
                                text="หมายเหตุ: หากพบปัญหาการแสดงผลหลังจากเปลี่ยนธีม "
                                     "กรุณาคลิกปุ่ม \"รีเซ็ตธีม\" เพื่อกลับไปใช้ค่าเริ่มต้น",
                                foreground="red", wraplength=400)
        warning_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
    
    def load_settings(self):
        """Load current settings into the form."""
        # Connection settings
        self.port_combobox.set(self.config.get('serial', 'port', fallback='COM3'))
        self.baud_combobox.set(str(self.config.get('serial', 'baud_rate', fallback='9600')))
        self.timeout_entry.insert(0, str(self.config.get('serial', 'timeout', fallback='1.0')))
        self.mock_data_var.set(self.config.get('device', 'mock_data', fallback=True))
        
        # Logging settings
        log_dir = self.config.get('logging', 'log_directory', fallback='')
        self.log_dir_entry.insert(0, log_dir)
        self.log_file_entry.insert(0, self.config.get('logging', 'log_file', fallback='sension7_data.csv'))
        self.backup_var.set(self.config.get('logging', 'backup_enabled', fallback=True))
        
        # Check directory status if specified
        if log_dir:
            if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
                self.dir_status_var.set(f"สถานะ: สามารถเขียนไฟล์ได้")
            else:
                self.dir_status_var.set(f"สถานะ: ไม่สามารถเขียนไฟล์ได้!")
        
        # Device settings
        self.device_combobox.set(self.config.get('device', 'model', fallback='HACH Sension7'))
        self.interval_entry.insert(0, str(self.config.get('device', 'measurement_interval', fallback='0.1')))
        self.update_device_info(None)  # Update device info text
        
        # Display settings
        self.update_interval_entry.insert(0, str(self.config.get('display', 'update_interval', fallback='2.0')))
        self.show_grid_var.set(self.config.get('display', 'show_grid', fallback=True))
        self.theme_combobox.set(self.config.get('display', 'theme', fallback='light'))
    
    def save_settings(self):
        """Save settings to configuration."""
        # Connection settings
        self.config.set('serial', 'port', self.port_combobox.get())
        self.config.set('serial', 'baud_rate', self.baud_combobox.get())
        self.config.set('serial', 'timeout', self.timeout_entry.get())
        self.config.set('device', 'mock_data', self.mock_data_var.get())
        
        # Logging settings
        self.config.set('logging', 'log_directory', self.log_dir_entry.get())
        self.config.set('logging', 'log_file', self.log_file_entry.get())
        self.config.set('logging', 'backup_enabled', self.backup_var.get())
        
        # Device settings
        self.config.set('device', 'model', self.device_combobox.get())
        self.config.set('device', 'measurement_interval', self.interval_entry.get())
        
        # Display settings
        self.config.set('display', 'update_interval', self.update_interval_entry.get())
        self.config.set('display', 'show_grid', self.show_grid_var.get())
        self.config.set('display', 'theme', self.theme_combobox.get())
        
        # Save configuration
        success = self.config.save()
        if not success:
            messagebox.showwarning(
                "คำเตือน",
                "ไม่สามารถบันทึกการตั้งค่าได้\n"
                "ตรวจสอบว่าโปรแกรมมีสิทธิ์ในการเขียนไฟล์"
            )
        
        return success
    
    def on_save(self):
        """Save settings and close dialog."""
        # Get directory path from entry
        log_dir = self.log_dir_entry.get()
        
        # Create log directory if it doesn't exist
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"Created log directory: {log_dir}")
            except Exception as e:
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    f"ไม่สามารถสร้างโฟลเดอร์บันทึกข้อมูลได้:\n{str(e)}\n\n"
                    "ตรวจสอบว่าตำแหน่งนี้มีอยู่และสามารถเขียนได้"
                )
                return
                
        # Save all settings
        if self.save_settings():
            # Verify the settings were saved successfully
            try:
                # Re-load config to verify settings were properly saved
                self.config.load()
                
                # Check if user switched from mock data to real device mode
                previous_mock_mode = self.config.get('device', 'mock_data', fallback=True)
                current_mock_mode = self.mock_data_var.get()
                
                if previous_mock_mode and not current_mock_mode:
                    # User is switching from mock data to real device mode
                    # Show guidance dialog
                    try:
                        from gui_guidance import show_real_device_guidance
                        show_real_device_guidance(self.parent)
                    except ImportError:
                        print("Could not import guidance module")
                
                # Notify success
                messagebox.showinfo(
                    "บันทึกการตั้งค่า",
                    "บันทึกการตั้งค่าเรียบร้อยแล้ว\n"
                    "การตั้งค่าจะมีผลเมื่อรีสตาร์ทโปรแกรม"
                )
                
                # Close dialog
                self.window.destroy()
            except Exception as e:
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    f"เกิดข้อผิดพลาดในการตรวจสอบการตั้งค่า:\n{str(e)}"
                )
    
    def on_apply(self):
        """Save settings and apply changes immediately without closing dialog."""
        # Get directory path from entry
        log_dir = self.log_dir_entry.get()
        
        # Create log directory if it doesn't exist
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"Created log directory: {log_dir}")
            except Exception as e:
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    f"ไม่สามารถสร้างโฟลเดอร์บันทึกข้อมูลได้:\n{str(e)}\n\n"
                    "ตรวจสอบว่าตำแหน่งนี้มีอยู่และสามารถเขียนได้"
                )
                return
                
        # Check if switching from mock data to real device mode
        previous_mock_mode = self.config.get('device', 'mock_data', fallback=True)
        current_mock_mode = self.mock_data_var.get()
        
        # Save all settings
        if self.save_settings():
            try:
                # Import the refresh UI function
                from gui_app import refresh_ui
                
                # Check if user switched from mock data to real device mode
                if previous_mock_mode and not current_mock_mode:
                    # User is switching from mock data to real device mode
                    # Show guidance dialog
                    try:
                        from gui_guidance import show_real_device_guidance
                        show_real_device_guidance(self.parent)
                    except ImportError:
                        print("Could not import guidance module")
                
                # Apply changes immediately
                refresh_ui()
                
                # Show notification
                messagebox.showinfo(
                    "นำการตั้งค่าไปใช้",
                    "นำการตั้งค่าไปใช้เรียบร้อยแล้ว"
                )
                
            except Exception as e:
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    f"เกิดข้อผิดพลาดในการนำการตั้งค่าไปใช้:\n{str(e)}"
                )
    
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
        self.log_dir_entry.delete(0, tk.END)
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
    
    def browse_log_directory(self):
        """Open directory browser dialog to select log directory."""
        # Get current directory from entry or config as starting point
        current_dir = self.log_dir_entry.get()
        if not current_dir:
            current_dir = self.config.get('logging', 'log_directory')
        
        # If still empty, use home directory
        if not current_dir:
            current_dir = os.path.expanduser('~')
            
        # Open directory dialog
        directory = filedialog.askdirectory(
            initialdir=current_dir,
            title="เลือกโฟลเดอร์สำหรับบันทึกข้อมูล"
        )
        
        # Update entry if directory selected
        if directory:
            self.log_dir_entry.delete(0, tk.END)
            self.log_dir_entry.insert(0, directory)
            
            # Test if directory is writable
            if os.access(directory, os.W_OK):
                self.dir_status_var.set(f"สถานะ: สามารถเขียนไฟล์ได้")
            else:
                self.dir_status_var.set(f"สถานะ: ไม่สามารถเขียนไฟล์ได้!")
                messagebox.showwarning(
                    "คำเตือนสิทธิ์การเข้าถึง",
                    f"ไม่สามารถเขียนไฟล์ในโฟลเดอร์ {directory} ได้\n"
                    f"กรุณาเลือกโฟลเดอร์อื่นหรือตรวจสอบสิทธิ์การเข้าถึง"
                )
    
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
        """Test serial port connection with current settings."""
        # Get current settings from form
        port = self.port_combobox.get()
        try:
            baud = int(self.baud_combobox.get())
        except ValueError:
            baud = 9600
            
        try:
            timeout = float(self.timeout_entry.get())
        except ValueError:
            timeout = 1.0
            
        # Check if in mock mode
        if self.mock_data_var.get():
            messagebox.showinfo("ทดสอบการเชื่อมต่อ",
                              "โปรแกรมอยู่ในโหมดข้อมูลจำลอง\n"
                              "โปรดยกเลิกการเลือก 'โหมดข้อมูลจำลอง' เพื่อทดสอบการเชื่อมต่อจริง")
            return
            
        # Check if port is selected
        if not port:
            messagebox.showwarning("ทดสอบการเชื่อมต่อ",
                                 "โปรดเลือกพอร์ตอนุกรมก่อนทดสอบการเชื่อมต่อ")
            return
            
        # Try to connect
        try:
            import serial
            
            # Tell user we're testing
            self.window.config(cursor="wait")
            test_label = ttk.Label(self.connection_tab, text="กำลังทดสอบการเชื่อมต่อ...", foreground="blue")
            test_label.grid(row=3, column=0, columnspan=3, pady=5)
            self.window.update()
            
            # Try to open port
            ser = serial.Serial(port, baud, timeout=timeout)
            
            # Get device model from config
            device_model = self.device_combobox.get()
            
            # Import adapter for proper command
            from device_adapters import get_adapter
            adapter = get_adapter(device_model)
            
            # Send command if adapter provides it
            if hasattr(adapter, 'get_command_string'):
                command = adapter.get_command_string()
                if command:
                    ser.write(command.encode())
                    
            # Read response (waiting briefly)
            import time
            time.sleep(0.5)
            response = ser.read(100)  # Read up to 100 bytes
            
            # Close port
            ser.close()
            
            # Check if we got data
            if response:
                messagebox.showinfo("ทดสอบการเชื่อมต่อ",
                                  f"เชื่อมต่อสำเร็จ!\n"
                                  f"ได้รับการตอบกลับจากอุปกรณ์:\n{response}")
            else:
                messagebox.showinfo("ทดสอบการเชื่อมต่อ",
                                  f"เปิดพอร์ต {port} สำเร็จ แต่ไม่ได้รับข้อมูลจากอุปกรณ์\n"
                                  f"โปรดตรวจสอบว่าเครื่อง {device_model} เปิดอยู่และเชื่อมต่อถูกต้อง")
            
        except Exception as e:
            messagebox.showerror("ทดสอบการเชื่อมต่อ",
                               f"เกิดข้อผิดพลาดในการเชื่อมต่อ:\n{str(e)}\n\n"
                               f"โปรดตรวจสอบว่า:\n"
                               f"1. เครื่อง {device_model} เปิดอยู่\n"
                               f"2. สายเชื่อมต่อกับคอมพิวเตอร์ถูกต้อง\n"
                               f"3. ไม่มีโปรแกรมอื่นใช้พอร์ต {port} อยู่")
        finally:
            # Reset cursor
            self.window.config(cursor="")
            try:
                test_label.destroy()
            except:
                pass
    
    def test_file_writing(self):
        """Test if the application can write to the log file."""
        # Get directory and file from entries
        log_dir = self.log_dir_entry.get()
        log_file = self.log_file_entry.get()
        
        # If directory is not specified, use current directory
        if not log_dir:
            log_dir = os.getcwd()
            self.log_dir_entry.delete(0, tk.END)
            self.log_dir_entry.insert(0, log_dir)
        
        # If file is not specified, use default
        if not log_file:
            log_file = "test_log.csv"
            self.log_file_entry.delete(0, tk.END)
            self.log_file_entry.insert(0, log_file)
        
        # Create complete path
        file_path = os.path.join(log_dir, log_file)
        
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir)
                    messagebox.showinfo("ทดสอบการเขียนไฟล์", f"สร้างโฟลเดอร์สำเร็จ: {log_dir}")
                except Exception as e:
                    messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้างโฟลเดอร์ได้: {str(e)}")
                    return
            
            # Try to write to the file
            with open(file_path, 'a') as f:
                f.write(f"Test entry at {tk.datetime.now()}\n")
            
            messagebox.showinfo("ทดสอบการเขียนไฟล์", 
                               f"สามารถเขียนไฟล์ได้สำเร็จที่:\n{file_path}")
            self.dir_status_var.set(f"สถานะ: สามารถเขียนไฟล์ได้")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเขียนไฟล์ได้:\n{str(e)}")
            self.dir_status_var.set(f"สถานะ: ไม่สามารถเขียนไฟล์ได้!")
            
            # Suggest a fallback location
            user_home = os.path.expanduser("~")
            fallback_dir = os.path.join(user_home, "Condensate_Logs")
            
            response = messagebox.askquestion("ใช้ตำแหน่งสำรอง?", 
                                            f"ต้องการลองใช้ตำแหน่งสำรองที่:\n{fallback_dir}?")
            if response == "yes":
                self.log_dir_entry.delete(0, tk.END)
                self.log_dir_entry.insert(0, fallback_dir)
                self.test_file_writing()  # Recursively try with new location
    
    def check_permissions(self):
        """Check if selected directory is writable and show detailed report."""
        # Get directory from entry
        log_dir = self.log_dir_entry.get()
        
        if not log_dir:
            messagebox.showinfo("ข้อมูลสิทธิ์", "กรุณาเลือกโฟลเดอร์ก่อน")
            return
        
        report = []
        
        # Check if directory exists
        if not os.path.exists(log_dir):
            report.append(f"โฟลเดอร์ไม่มีอยู่: {log_dir}")
            
            # Try to create the directory
            try:
                os.makedirs(log_dir, exist_ok=True)
                report.append(f"สร้างโฟลเดอร์ใหม่สำเร็จ: {log_dir}")
                
                # Now check permissions of newly created directory
                if os.access(log_dir, os.R_OK):
                    report.append("สิทธิ์การอ่าน: มี")
                else:
                    report.append("สิทธิ์การอ่าน: ไม่มี")
                    
                if os.access(log_dir, os.W_OK):
                    report.append("สิทธิ์การเขียน: มี")
                else:
                    report.append("สิทธิ์การเขียน: ไม่มี")
                
                # Try to create a test file in the new directory
                test_file = os.path.join(log_dir, ".permission_test")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    report.append("ทดสอบสร้างไฟล์: สำเร็จ")
                    
                    try:
                        os.remove(test_file)
                        report.append("ทดสอบลบไฟล์: สำเร็จ")
                    except Exception as e:
                        report.append(f"ทดสอบลบไฟล์: ไม่สำเร็จ - {str(e)}")
                except Exception as e:
                    report.append(f"ทดสอบสร้างไฟล์: ไม่สำเร็จ - {str(e)}")
                    
            except Exception as e:
                report.append(f"ไม่สามารถสร้างโฟลเดอร์ได้: {str(e)}")
                
                # Check if parent directory exists and is writable
                parent_dir = os.path.dirname(log_dir)
                if os.path.exists(parent_dir):
                    if os.access(parent_dir, os.W_OK):
                        report.append(f"ปัญหาอาจเกิดจากสิทธิ์การเข้าถึง แต่โฟลเดอร์หลักสามารถเขียนได้")
                    else:
                        report.append(f"ไม่มีสิทธิ์เขียนในโฟลเดอร์หลัก: {parent_dir}")
                else:
                    report.append(f"โฟลเดอร์หลักไม่มีอยู่: {parent_dir}")
                    
                    # Try to recursively create parent directory
                    try:
                        os.makedirs(parent_dir, exist_ok=True)
                        report.append(f"สร้างโฟลเดอร์หลักสำเร็จ: {parent_dir}")
                        
                        # Try again to create the target directory
                        try:
                            os.makedirs(log_dir, exist_ok=True)
                            report.append(f"สร้างโฟลเดอร์เป้าหมายสำเร็จ: {log_dir}")
                        except Exception as e:
                            report.append(f"ยังไม่สามารถสร้างโฟลเดอร์เป้าหมายได้: {str(e)}")
                    except Exception as e:
                        report.append(f"ไม่สามารถสร้างโฟลเดอร์หลัก: {str(e)}")
        else:
            report.append(f"โฟลเดอร์มีอยู่: {log_dir}")
            
            # Check read/write permissions
            if os.access(log_dir, os.R_OK):
                report.append("สิทธิ์การอ่าน: มี")
            else:
                report.append("สิทธิ์การอ่าน: ไม่มี")
                
            if os.access(log_dir, os.W_OK):
                report.append("สิทธิ์การเขียน: มี")
            else:
                report.append("สิทธิ์การเขียน: ไม่มี")
            
            # Try to create a test file
            test_file = os.path.join(log_dir, ".permission_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                report.append("ทดสอบสร้างไฟล์: สำเร็จ")
                
                # Try to delete the test file
                try:
                    os.remove(test_file)
                    report.append("ทดสอบลบไฟล์: สำเร็จ")
                except Exception as e:
                    report.append(f"ทดสอบลบไฟล์: ไม่สำเร็จ - {str(e)}")
            except Exception as e:
                report.append(f"ทดสอบสร้างไฟล์: ไม่สำเร็จ - {str(e)}")
        
        # Show report
        report_text = "\n".join(report)
        messagebox.showinfo("รายงานสิทธิ์การเข้าถึง", report_text)
        
        # Update status label
        if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
            self.dir_status_var.set(f"สถานะ: สามารถเขียนไฟล์ได้")
        else:
            self.dir_status_var.set(f"สถานะ: ไม่สามารถเขียนไฟล์ได้!")
    
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
    
    def apply_theme_preview(self):
        """Apply the selected theme as a preview without saving settings."""
        try:
            # Get selected theme
            selected_theme = self.theme_combobox.get()
            if not selected_theme:
                messagebox.showinfo("ทดลองธีม", "กรุณาเลือกธีมก่อน")
                return
            
            # ตั้งค่าชั่วคราวในคอนฟิก (ไม่บันทึกลงไฟล์)
            self.config.set('display', 'theme', selected_theme)
            
            # ใช้ theme กับหน้าต่างปัจจุบัน
            from gui_app import apply_theme
            apply_theme(self.window)
            
            # แสดงข้อความ
            messagebox.showinfo(
                "ทดลองธีม", 
                f"กำลังทดลองใช้ธีม: {selected_theme}\n"
                "คลิก 'ใช้งานทันที' เพื่อนำไปใช้กับทั้งโปรแกรม\n"
                "หรือคลิก 'บันทึก' เพื่อบันทึกการตั้งค่านี้"
            )
            
        except Exception as e:
            messagebox.showerror(
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการทดลองใช้ธีม:\n{str(e)}"
            )
    
    def reset_theme_emergency(self):
        """รีเซ็ตธีมกลับไปยังค่าเริ่มต้นในกรณีที่มีปัญหาการแสดงผล"""
        try:
            # ตั้งค่า theme เป็น light ในตัวเลือกของหน้าตั้งค่า
            self.theme_combobox.set('light')
            
            # นำเข้าฟังก์ชันรีเซ็ตฉุกเฉิน
            from gui_app import reset_theme_emergency
            reset_theme_emergency()
            
            # อัปเดตหน้าตั้งค่าด้วย
            style = ttk.Style(self.window)
            style.theme_use('default')  # กลับไปใช้ธีมเริ่มต้น
            
            messagebox.showinfo(
                "รีเซ็ตธีม",
                "ได้รีเซ็ตธีมเรียบร้อยแล้ว\nธีมจะกลับเป็นธีมเริ่มต้น (light)"
            )
            
        except Exception as e:
            messagebox.showerror(
                "ข้อผิดพลาด", 
                f"เกิดข้อผิดพลาดในการรีเซ็ตธีม: {str(e)}"
            )
