"""
Main GUI application module.
"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
from tkinter import messagebox, Toplevel, StringVar, BooleanVar, filedialog
import pandas as pd
import numpy as np

from gui_config import *
from gui_plot import setup_graph, update_plot
from gui_utils import (
    read_csv_data, read_csv_data_with_analysis, get_available_dates,
    update_statistics, export_to_excel, detect_data_anomalies,
    get_data_trend_analysis, format_statistics_for_display
)
from gui_compare import ComparisonWindow
from config_manager import get_config  # เพิ่ม import ตรงนี้

selected_date_str = datetime.now().strftime("%Y-%m-%d")

def setup_gui():
    """Initialize and configure the main GUI window."""
    global root
    
    root = tk.Tk()
    root.title("Conductivity Monitoring System")
    root.geometry("1024x768")  # ขยายหน้าต่างให้ใหญ่ขึ้น
    
    # สร้างเมนูบาร์
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # เมนูไฟล์
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="ไฟล์", menu=file_menu)
    file_menu.add_command(label="รีเฟรชข้อมูล", command=refresh_data)
    file_menu.add_separator()
    file_menu.add_command(label="ส่งออกข้อมูล", command=lambda: export_to_excel(selected_date_str))
    file_menu.add_separator()
    file_menu.add_command(label="ปิดโปรแกรม", command=root.quit)
    
    # เมนูเครื่องมือ
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="เครื่องมือ", menu=tools_menu)
    tools_menu.add_command(label="ตั้งค่า", command=lambda: show_settings_dialog(root))
    tools_menu.add_command(label="สถิติขั้นสูง", command=show_advanced_statistics)
    tools_menu.add_command(label="เปรียบเทียบข้อมูลระหว่างวัน", command=open_comparison_window)
    
    # สร้าง main container
    container = ttk.Frame(root, padding="10")
    container.grid(row=0, column=0, sticky="nsew")
    
    # แบ่งเป็น 2 ส่วน: ควบคุมด้านซ้าย, กราฟด้านขวา
    control_frame = ttk.LabelFrame(container, text="Controls", padding="5")
    control_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
    
    graph_frame = ttk.LabelFrame(container, text="Graph", padding="5")
    graph_frame.grid(row=0, column=1, sticky="nsew")
    
    # Configure grid weights
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    container.grid_columnconfigure(1, weight=1)
    container.grid_rowconfigure(0, weight=1)
    
    # Set minimum width for control panel
    control_frame.config(width=280)
    
    # Set initial size for graph area
    graph_frame.config(width=700, height=700)
    
    # Setup controls in control_frame
    setup_controls(control_frame)
    
    # Setup graph in graph_frame
    setup_graph(graph_frame, reset_callback=reset_zoom, 
               date_str=selected_date_str, graph_combo=graph_type_combobox)
    
    # ใช้ธีมตามการตั้งค่า
    apply_theme(root)
    
    return root

def setup_controls(parent):
    """Setup control panel elements"""
    global date_combobox, filter_min, filter_max, stats_frame
    global conductivity_value_label, temperature_value_label, time_label
    global graph_type_combobox, max_value_label, min_value_label, avg_value_label, std_value_label
    global show_trend_var, show_anomalies_var, anomaly_method_var  # Analysis controls
    
    # Date selection
    date_frame = ttk.LabelFrame(parent, text="Date Selection", padding="5")
    date_frame.pack(fill="x", pady=(0, 10))
    
    available_dates = get_available_dates()
    date_combobox = ttk.Combobox(date_frame, state='readonly', width=15)
    if available_dates:
        date_combobox['values'] = available_dates
        date_combobox.set(available_dates[-1])  # Select most recent date
    else:
        date_combobox['values'] = [selected_date_str]
        date_combobox.set(selected_date_str)
    
    date_combobox.bind('<<ComboboxSelected>>', on_date_selected)
    date_combobox.pack(side="left", padx=5)
    
    ttk.Button(date_frame, text="Refresh",
              command=refresh_data).pack(side="left", padx=5)
    
    # Current readings
    readings_frame = ttk.LabelFrame(parent, text="Current Readings", padding="5")
    readings_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(readings_frame, text="Conductivity:").pack(anchor="w")
    conductivity_value_label = ttk.Label(readings_frame, text="N/A")
    conductivity_value_label.pack(anchor="w")
    
    # Remove separate unit label
    ttk.Label(readings_frame, text="Temperature:").pack(anchor="w")
    temperature_value_label = ttk.Label(readings_frame, text="N/A")
    temperature_value_label.pack(anchor="w")
    
    ttk.Label(readings_frame, text="Last Updated:").pack(anchor="w")
    time_label = ttk.Label(readings_frame, text="N/A")
    time_label.pack(anchor="w")
    
    # Add graph type selection before filters
    graph_type_frame = ttk.LabelFrame(parent, text="Graph Type", padding="5")
    graph_type_frame.pack(fill="x", pady=(0, 10))
    
    graph_type_combobox = ttk.Combobox(graph_type_frame, state='readonly', width=15)
    graph_type_combobox['values'] = ["Conductivity", "Temperature"]
    graph_type_combobox.set("Conductivity")
    graph_type_combobox.bind('<<ComboboxSelected>>', on_graph_type_selected)
    graph_type_combobox.pack(pady=5)
    
    # Filters
    filter_frame = ttk.LabelFrame(parent, text="Data Filters", padding="5")
    filter_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(filter_frame, text="Min Value:").pack(anchor="w")
    filter_min = ttk.Entry(filter_frame, width=10)
    filter_min.pack(anchor="w")
    
    ttk.Label(filter_frame, text="Max Value:").pack(anchor="w")
    filter_max = ttk.Entry(filter_frame, width=10)
    filter_max.pack(anchor="w")
    
    ttk.Button(filter_frame, text="Apply Filter", command=apply_filter).pack(pady=5)
    ttk.Button(filter_frame, text="Reset Filters", command=reset_filters).pack(pady=5)

    # Export
    export_frame = ttk.LabelFrame(parent, text="Export", padding="5")
    export_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Button(export_frame, text="Export to Excel",
              command=export_to_excel).pack(pady=5)

    # Statistics section
    stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="5")
    stats_frame.pack(fill="x", pady=(0, 10))
    
    # Maximum
    ttk.Label(stats_frame, text="ค่าสูงสุด:").pack(anchor="w")
    max_value_label = ttk.Label(stats_frame, text="0.00")
    max_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 5))
    
    # Minimum
    ttk.Label(stats_frame, text="ค่าต่ำสุด:").pack(anchor="w")
    min_value_label = ttk.Label(stats_frame, text="0.00")
    min_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 5))
    
    # Average
    ttk.Label(stats_frame, text="ค่าเฉลี่ย:").pack(anchor="w")
    avg_value_label = ttk.Label(stats_frame, text="0.00")
    avg_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 5))
    
    # Standard deviation 
    ttk.Label(stats_frame, text="ค่าเบี่ยงเบนมาตรฐาน:").pack(anchor="w")
    std_value_label = ttk.Label(stats_frame, text="0.00")
    std_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 5))
    
    # Show advanced statistics button
    ttk.Button(stats_frame, text="สถิติขั้นสูง", 
              command=show_advanced_statistics).pack(anchor="w", pady=(10, 5))
    
    # Show analysis options
    analysis_frame = ttk.LabelFrame(parent, text="การวิเคราะห์", padding="5")
    analysis_frame.pack(fill="x", pady=(0, 10))
    
    # Analysis options
    show_trend_var = BooleanVar(value=SHOW_TREND_LINES)
    ttk.Checkbutton(analysis_frame, text="แสดงเส้นแนวโน้ม", 
                   variable=show_trend_var, command=refresh_data).pack(anchor="w")
    
    show_anomalies_var = BooleanVar(value=SHOW_ANOMALIES)
    ttk.Checkbutton(analysis_frame, text="แสดงจุดที่ผิดปกติ", 
                   variable=show_anomalies_var, command=refresh_data).pack(anchor="w")
    
    # Anomaly detection method
    ttk.Label(analysis_frame, text="วิธีตรวจจับความผิดปกติ:").pack(anchor="w")
    anomaly_method_var = StringVar(value=ANOMALY_METHOD)
    anomaly_method_combo = ttk.Combobox(analysis_frame, textvariable=anomaly_method_var, 
                                       state='readonly', width=15)
    anomaly_method_combo['values'] = ["zscore", "iqr", "isolation_forest"]
    anomaly_method_combo.pack(anchor="w", pady=(0, 5))
    anomaly_method_combo.bind('<<ComboboxSelected>>', refresh_data)
    
    # Add comparison button
    ttk.Separator(analysis_frame, orient="horizontal").pack(fill="x", pady=10)
    ttk.Button(analysis_frame, text="เปรียบเทียบข้อมูลระหว่างวัน", 
              command=open_comparison_window).pack(anchor="w", pady=5)

def update_current_readings(timestamp, conductivity, unit, temperature=None):
    """Update current reading labels."""
    global last_reading_time
    
    try:
        if conductivity is not None:
            # มีการรับข้อมูลใหม่ จึงแสดงผล
            conductivity_value_label.config(text=f"{conductivity:.2f} {unit}")
            if temperature is not None:
                temperature_value_label.config(text=f"{temperature:.2f} °C")
            time_label.config(text=timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            
            # บันทึกเวลาล่าสุดที่ได้รับข้อมูล
            last_reading_time = timestamp
            
            # ตั้งค่าสถานะที่บอกว่ามีข้อมูลแล้ว และเก็บค่าล่าสุดไว้
            update_current_readings.has_data = True
            update_current_readings.last_conductivity = conductivity
            update_current_readings.last_unit = unit
            update_current_readings.last_temperature = temperature
            
            # อัพเดต UI เพื่อให้แน่ใจว่าข้อมูลแสดงทันที
            root.update_idletasks()
        elif not hasattr(update_current_readings, 'has_data') or not update_current_readings.has_data:
            # ไม่เคยมีข้อมูลมาก่อน ให้แสดงสถานะรอข้อมูล
            conductivity_value_label.config(text="กำลังรอข้อมูล...")
            temperature_value_label.config(text="กำลังรอข้อมูล...")
            time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # อัพเดต UI เพื่อให้แน่ใจว่าข้อมูลแสดงทันที
            root.update_idletasks()
    except Exception as e:
        print(f"Error updating readings: {e}")
    # ไม่ต้อง reset ค่าถ้าไม่มีข้อมูลใหม่ เพื่อให้ค่าเดิมยังคงแสดงอยู่
