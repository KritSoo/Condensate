"""
Main GUI application module.
"""

import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
from tkinter import messagebox

from gui_config import *
from gui_plot import setup_graph, update_plot
from gui_utils import (
    read_csv_data, get_available_dates,
    update_statistics, export_to_excel
)

def setup_gui():
    """Initialize and configure the main GUI window."""
    global root
    
    root = tk.Tk()
    root.title("HACH Sension7 Conductivity Monitor")
    root.geometry("1024x768")  # ขยายหน้าต่างให้ใหญ่ขึ้น
    
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
    setup_graph(graph_frame, reset_callback=reset_zoom)
    
    return root

def setup_controls(parent):
    """Setup control panel elements"""
    global date_combobox, filter_min, filter_max, stats_frame
    global conductivity_value_label, unit_label, time_label
    
    # Date selection
    date_frame = ttk.LabelFrame(parent, text="Date Selection", padding="5")
    date_frame.pack(fill="x", pady=(0, 10))
    
    date_combobox = ttk.Combobox(date_frame, state='readonly', width=15)
    date_combobox['values'] = get_available_dates()
    date_combobox.set(selected_date_str)  # Fixed: removed underscore
    date_combobox.bind('<<ComboboxSelected>>', on_date_selected)
    date_combobox.pack(side="left", padx=5)
    
    ttk.Button(date_frame, text="Refresh",
              command=lambda: on_date_selected()).pack(side="left", padx=5)
    
    # Current readings
    readings_frame = ttk.LabelFrame(parent, text="Current Readings", padding="5")
    readings_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(readings_frame, text="Conductivity:").pack(anchor="w")
    conductivity_value_label = ttk.Label(readings_frame, text="N/A",
                                        style='Display.TLabel')
    conductivity_value_label.pack(anchor="w")
    
    ttk.Label(readings_frame, text="Unit:").pack(anchor="w")
    unit_label = ttk.Label(readings_frame, text="N/A")
    unit_label.pack(anchor="w")
    
    ttk.Label(readings_frame, text="Last Updated:").pack(anchor="w")
    time_label = ttk.Label(readings_frame, text="N/A")
    time_label.pack(anchor="w")
    
    # Filters
    filter_frame = ttk.LabelFrame(parent, text="Data Filters", padding="5")
    filter_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(filter_frame, text="Min Value:").pack(anchor="w")
    filter_min = ttk.Entry(filter_frame, width=10)
    filter_min.pack(anchor="w")
    
    ttk.Label(filter_frame, text="Max Value:").pack(anchor="w")
    filter_max = ttk.Entry(filter_frame, width=10)
    filter_max.pack(anchor="w")
    
    ttk.Button(filter_frame, text="Apply Filter",
              command=apply_filter).pack(pady=5)
    
    # Statistics
    stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="5")
    stats_frame.pack(fill="x", pady=(0, 10))
    
    # Export
    export_frame = ttk.LabelFrame(parent, text="Export", padding="5")
    export_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Button(export_frame, text="Export to Excel",
              command=export_to_excel).pack(pady=5)

def update_gui(timestamp, conductivity, unit, filter_min=None, filter_max=None):
    """Update GUI elements with new data and plot."""
    try:
        update_current_readings(timestamp, conductivity, unit)
        x_timestamps, y_conductivities = read_csv_data(selected_date_str)
        
        if filter_min is not None or filter_max is not None:
            x_timestamps, y_conductivities = apply_filters(
                x_timestamps, y_conductivities, filter_min, filter_max)
        
        update_plot(x_timestamps, y_conductivities, unit)
        update_statistics(y_conductivities)
        
    except Exception as e:
        print(f"Error in update_gui: {e}")

def run_gui():
    """Start the Tkinter event loop."""
    if root:
        root.mainloop()

def on_date_selected(event=None):
    """Handle date selection from combobox."""
    global selected_date_str  # Add global declaration
    if date_combobox and date_combobox.get():
        selected_date_str = date_combobox.get()
        update_gui(datetime.now(), None, None)

def apply_filter():
    """Apply min/max filters to the graph."""
    try:
        if filter_min is None or filter_max is None:
            messagebox.showerror("Error", "Filter controls not initialized")
            return
            
        min_val = float(filter_min.get()) if filter_min.get().strip() else None
        max_val = float(filter_max.get()) if filter_max.get().strip() else None
        
        if min_val is not None and max_val is not None and min_val > max_val:
            messagebox.showerror("Error", "Minimum value cannot be greater than maximum value")
            return
            
        update_gui(datetime.now(), None, None, min_val, max_val)
        
    except ValueError:
        messagebox.showerror("Error", "Invalid filter values")

def update_current_readings(timestamp, conductivity, unit):
    """Update current reading labels."""
    if conductivity is not None:
        if all(widget is not None for widget in 
              [conductivity_value_label, unit_label, time_label]):
            conductivity_value_label.config(text=f"{conductivity:.2f}")
            unit_label.config(text=unit)
            time_label.config(text=timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            print("Warning: Some GUI elements not initialized")

def apply_filters(x_timestamps, y_conductivities, filter_min, filter_max):
    """Apply min/max filters to data."""
    filtered_data = [(x, y) for x, y in zip(x_timestamps, y_conductivities)
                    if ((filter_min is None or y >= filter_min) and
                        (filter_max is None or y <= filter_max))]
    return zip(*filtered_data) if filtered_data else ([], [])

def reset_zoom():
    """Reset zoom to show full data range."""
    update_gui(datetime.now(), None, None)
