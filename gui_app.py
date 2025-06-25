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
    
    # Setup controls in control_frame
    setup_controls(control_frame)
    
    # Setup graph in graph_frame
    setup_graph(graph_frame, reset_callback=reset_zoom, 
               date_str=selected_date_str, graph_combo=graph_type_combobox)
    
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

def on_new_data(timestamp, value, unit, temperature=None):
    """Handle new data from serial reader."""
    update_gui(timestamp, value, unit, temperature=temperature)
    root.update_idletasks()

def show_advanced_statistics():
    """Show advanced statistics in a new window."""
    try:
        # Get selected graph type
        selected_type = graph_type_combobox.get()
        data_type = "temperature" if selected_type == "Temperature" else "conductivity"
        
        # Read data with analysis
        timestamps, conductivities, temperatures, unit, analysis, statistics = read_csv_data_with_analysis(
            selected_date_str, force_refresh=False
        )
        
        if not timestamps or not statistics:
            messagebox.showinfo("ไม่มีข้อมูล", "ไม่พบข้อมูลสำหรับวันที่เลือก")
            return
            
        # Create new window
        stats_window = Toplevel(root)
        stats_window.title(f"สถิติขั้นสูง - {selected_date_str} ({selected_type})")
        stats_window.geometry("500x600")
        
        # Get statistics for the selected data type
        stats = statistics[data_type]
        formatted_stats = format_statistics_for_display(stats)
        
        # Create scrollable frame
        main_frame = ttk.Frame(stats_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add statistics to scrollable frame
        ttk.Label(scrollable_frame, text=f"สถิติสำหรับ {selected_type}", 
                 font=("Helvetica", 12, "bold")).pack(pady=(0, 10))
                 
        # Add each statistic
        for stat_name, stat_value in formatted_stats.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            ttk.Label(frame, text=f"{stat_name}:", width=25, anchor="w").pack(side="left")
            ttk.Label(frame, text=stat_value).pack(side="left")
        
        # Add trend information if available
        if analysis and data_type in analysis and 'trend' in analysis[data_type]:
            trend = analysis[data_type]['trend']
            
            ttk.Label(scrollable_frame, text="ข้อมูลแนวโน้ม", 
                     font=("Helvetica", 12, "bold")).pack(pady=(20, 10))
            
            trend_direction = trend['trend_direction']
            direction_text = {
                'increasing': 'เพิ่มขึ้น',
                'decreasing': 'ลดลง',
                'stable': 'คงที่',
                'insufficient_data': 'ข้อมูลไม่เพียงพอ',
            }.get(trend_direction, 'ไม่ทราบ')
            
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text="แนวโน้ม:", width=25, anchor="w").pack(side="left")
            ttk.Label(frame, text=direction_text).pack(side="left")
            
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text="ความแรงของแนวโน้ม:", width=25, anchor="w").pack(side="left")
            ttk.Label(frame, text=f"{trend['trend_strength']:.4f}").pack(side="left")
            
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text="ค่า p:", width=25, anchor="w").pack(side="left")
            ttk.Label(frame, text=f"{trend['p_value']:.4f}").pack(side="left")
            
        # Add anomalies information if available
        if analysis and data_type in analysis and 'anomalies' in analysis[data_type]:
            anomaly_indices, anomaly_timestamps, anomaly_values = analysis[data_type]['anomalies']
            
            if anomaly_indices:
                ttk.Label(scrollable_frame, text="ข้อมูลความผิดปกติ", 
                         font=("Helvetica", 12, "bold")).pack(pady=(20, 10))
                
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill="x", pady=2)
                ttk.Label(frame, text="จำนวนจุดผิดปกติ:", width=25, anchor="w").pack(side="left")
                ttk.Label(frame, text=str(len(anomaly_indices))).pack(side="left")
                
                # List anomalies
                if anomaly_timestamps:
                    anomaly_frame = ttk.LabelFrame(scrollable_frame, text="รายการจุดผิดปกติ")
                    anomaly_frame.pack(fill="x", pady=(10, 0))
                    
                    # Create headers
                    header_frame = ttk.Frame(anomaly_frame)
                    header_frame.pack(fill="x")
                    ttk.Label(header_frame, text="เวลา", width=20, anchor="w").pack(side="left")
                    ttk.Label(header_frame, text="ค่า", width=15, anchor="w").pack(side="left")
                    
                    # Add up to 10 anomalies
                    for i, (t, v) in enumerate(zip(anomaly_timestamps, anomaly_values)):
                        if i >= 10:  # Limit to 10 entries
                            ttk.Label(anomaly_frame, text=f"... และอีก {len(anomaly_timestamps) - 10} รายการ").pack(anchor="w")
                            break
                        
                        row = ttk.Frame(anomaly_frame)
                        row.pack(fill="x")
                        ttk.Label(row, text=t.strftime("%Y-%m-%d %H:%M:%S"), width=20).pack(side="left")
                        ttk.Label(row, text=f"{v:.2f}", width=15).pack(side="left")
        
        # Add export button
        ttk.Button(stats_window, text="ส่งออกข้อมูล", 
                  command=lambda: export_statistics_to_csv(statistics, selected_date_str)).pack(pady=10)
        
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {str(e)}")

def export_statistics_to_csv(statistics, date_str):
    """Export statistics to CSV file."""
    try:
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*")]
        )
        
        if not filename:
            return
            
        # Create dataframe for statistics
        cond_stats = statistics['conductivity']
        temp_stats = statistics['temperature']
        
        # Create statistics dataframe
        df = pd.DataFrame({
            'Metric': list(cond_stats.keys()),
            'Conductivity': list(cond_stats.values()),
            'Temperature': list(temp_stats.values())
        })
        
        # Save to CSV
        df.to_csv(filename, index=False)
        messagebox.showinfo("Success", "ส่งออกข้อมูลสำเร็จ!")
        
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการส่งออกข้อมูล: {str(e)}")

def update_gui(timestamp, conductivity, unit, temperature=None):
    """Update GUI elements with new data and plot."""
    try:
        update_current_readings(timestamp, conductivity, unit, temperature)
        
        # Force refresh of cache only when new data arrives for today
        force_refresh = (selected_date_str == timestamp.strftime('%Y-%m-%d'))
        timestamps, conductivities, temperatures, plot_unit, analysis, statistics = read_csv_data_with_analysis(
            selected_date_str, force_refresh=force_refresh
        )
        
        if timestamps:
            selected_type = graph_type_combobox.get()
            values = temperatures if selected_type == "Temperature" else conductivities
            data_type = "temperature" if selected_type == "Temperature" else "conductivity"
            
            # Only use analysis features if enabled
            show_analysis = False
            if 'show_trend_var' in globals() and 'show_anomalies_var' in globals():
                show_analysis = True
                show_trend = show_trend_var.get()
                show_anomalies = show_anomalies_var.get()
                
                # Filter analysis based on settings
                if not show_trend and analysis:
                    if 'conductivity' in analysis and 'trend' in analysis['conductivity']:
                        analysis['conductivity']['trend'] = None
                    if 'temperature' in analysis and 'trend' in analysis['temperature']:
                        analysis['temperature']['trend'] = None
                
                if not show_anomalies and analysis:
                    if 'conductivity' in analysis and 'anomalies' in analysis['conductivity']:
                        analysis['conductivity']['anomalies'] = ([], [], [])
                    if 'temperature' in analysis and 'anomalies' in analysis['temperature']:
                        analysis['temperature']['anomalies'] = ([], [], [])
            
            # Update plot with analysis data if available
            update_plot(timestamps, conductivities, temperatures, plot_unit, selected_type, analysis)
            
            # Update statistics
            if statistics and data_type in statistics and values and len(values) > 0:
                stats = statistics[data_type]
                
                # Update basic statistics display
                max_value_label.config(text=f"{stats['max']:.2f}")
                min_value_label.config(text=f"{stats['min']:.2f}")
                avg_value_label.config(text=f"{stats['mean']:.2f}")
                
                # Update standard deviation if available
                if 'std_value_label' in globals():
                    std_value_label.config(text=f"{stats['std']:.2f}")
            else:
                # Fallback to simple stats if advanced stats not available
                if values and len(values) > 0:
                    max_val = max(values)
                    min_val = min(values)
                    avg_val = sum(values) / len(values)
                    std_val = np.std(values) if 'np' in globals() else 0.0
                    
                    max_value_label.config(text=f"{max_val:.2f}")
                    min_value_label.config(text=f"{min_val:.2f}")
                    avg_value_label.config(text=f"{avg_val:.2f}")
                    
                    if 'std_value_label' in globals():
                        std_value_label.config(text=f"{std_val:.2f}")
                else:
                    max_value_label.config(text="0.00")
                    min_value_label.config(text="0.00")
                    avg_value_label.config(text="0.00")
                    if 'std_value_label' in globals():
                        std_value_label.config(text="0.00")
            
    except Exception as e:
        print(f"Error in update_gui: {e}")

def run_gui():
    """Start the Tkinter event loop."""
    if root:
        root.mainloop()

def on_date_selected(event=None):
    """Handle date selection from combobox."""
    global selected_date_str
    if date_combobox:
        new_date = date_combobox.get()
        if new_date:
            selected_date_str = new_date
            from gui_plot import selected_date_str as plot_date_str
            # Update the selected_date_str in gui_plot.py as well
            if hasattr(plot_date_str, '__call__'):
                plot_date_str = new_date
            update_gui(datetime.now(), None, None)
        else:
            messagebox.showwarning("Warning", "No date selected")

def on_graph_type_selected(event=None):
    """Handle graph type selection change"""
    update_gui(datetime.now(), None, None)

def apply_filter():
    """Apply min/max filters to the graph."""
    try:
        min_val = float(filter_min.get()) if filter_min.get().strip() else None
        max_val = float(filter_max.get()) if filter_max.get().strip() else None
        
        if min_val is not None and max_val is not None and min_val > max_val:
            messagebox.showerror("Error", "Minimum value cannot be greater than maximum value")
            return
            
        timestamps, conductivities, temperatures, plot_unit = read_csv_data(
            selected_date_str, force_refresh=False  # Use cached data when applying filters
        )
        
        if timestamps:
            selected_type = graph_type_combobox.get()
            values = temperatures if selected_type == "Temperature" else conductivities
            
            if min_val is not None or max_val is not None:
                filtered_data = [(t, v) for t, v in zip(timestamps, values)
                               if ((min_val is None or v >= min_val) and
                                   (max_val is None or v <= max_val))]
                if filtered_data:
                    timestamps, values = zip(*filtered_data)
                    if selected_type == "Temperature":
                        temperatures = values
                    else:
                        conductivities = values
                else:
                    messagebox.showwarning("Warning", "No data points match the filter criteria")
                    return
            
            update_plot(timestamps, conductivities, temperatures, plot_unit, selected_type)
            update_statistics(values)
            
    except ValueError:
        messagebox.showerror("Error", "Invalid filter values")

def reset_filters():
    """Reset filter values and update plot"""
    filter_min.delete(0, tk.END)
    filter_max.delete(0, tk.END)
    update_gui(datetime.now(), None, None)

def update_current_readings(timestamp, conductivity, unit, temperature=None):
    """Update current reading labels."""
    if conductivity is not None:
        conductivity_value_label.config(text=f"{conductivity:.2f} {unit}")
        if temperature is not None:
            temperature_value_label.config(text=f"{temperature:.2f} °C")
        time_label.config(text=timestamp.strftime("%Y-%m-%d %H:%M:%S"))

def apply_filters(x_timestamps, y_conductivities, filter_min, filter_max):
    """Apply min/max filters to data."""
    filtered_data = [(x, y) for x, y in zip(x_timestamps, y_conductivities)
                    if ((filter_min is None or y >= filter_min) and
                        (filter_max is None or y <= filter_max))]
    return zip(*filtered_data) if filtered_data else ([], [])

def reset_zoom():
    """Reset zoom to show full data range."""
    update_gui(datetime.now(), None, None)

def refresh_data(event=None):
    """Refresh data from CSV and update GUI"""
    from gui_utils import clear_cache
    
    # Clear the cache to force fresh data read
    clear_cache()
    
    # Update available dates in combobox
    available_dates = get_available_dates(force_refresh=True)
    if available_dates:
        date_combobox['values'] = available_dates
        # Keep current selection if it exists, otherwise select most recent
        if selected_date_str not in available_dates:
            date_combobox.set(available_dates[-1])
    
    # Update anomaly method in config if available
    global ANOMALY_METHOD
    if 'anomaly_method_var' in globals() and anomaly_method_var.get():
        ANOMALY_METHOD = anomaly_method_var.get()
    
    # Force data reload and update GUI
    update_gui(datetime.now(), None, None, None)

def open_comparison_window():
    """Open the data comparison window."""
    try:
        # Get available dates
        available_dates = get_available_dates()
        if not available_dates:
            messagebox.showinfo("ไม่มีข้อมูล", "ไม่พบข้อมูลในระบบ")
            return
            
        # Create comparison window
        comparison_window = ComparisonWindow(root, available_dates, csv_file=LOG_FILE)
        
        # Make window modal (block interaction with main window)
        comparison_window.window.transient(root)
        comparison_window.window.grab_set()
        
        # Wait until window is closed
        root.wait_window(comparison_window.window)
        
    except Exception as e:
        messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการเปิดหน้าต่างเปรียบเทียบ: {str(e)}")

def show_settings_dialog(parent):
    """Show the settings dialog."""
    # Import here to avoid circular import
    from gui_settings import SettingsDialog
    settings_dialog = SettingsDialog(parent)
    
    # สร้าง main container
