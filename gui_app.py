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

selected_date_str = datetime.now().strftime("%Y-%m-%d")

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
    global conductivity_value_label, temperature_value_label, time_label
    global graph_type_combobox, max_value_label, min_value_label, avg_value_label  # Add stats labels
    
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
    ttk.Label(stats_frame, text="Maximum:").pack(anchor="w")
    max_value_label = ttk.Label(stats_frame, text="0.00")
    max_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 10))
    
    # Minimum
    ttk.Label(stats_frame, text="Minimum:").pack(anchor="w")
    min_value_label = ttk.Label(stats_frame, text="0.00")
    min_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 10))
    
    # Average
    ttk.Label(stats_frame, text="Average:").pack(anchor="w")
    avg_value_label = ttk.Label(stats_frame, text="0.00")
    avg_value_label.pack(anchor="w", padx=(20, 0), pady=(0, 10))

def on_new_data(timestamp, value, unit, temperature=None):
    """Handle new data from serial reader."""
    update_gui(timestamp, value, unit, temperature=temperature)
    root.update_idletasks()

def update_gui(timestamp, conductivity, unit, temperature=None):
    """Update GUI elements with new data and plot."""
    try:
        update_current_readings(timestamp, conductivity, unit, temperature)
        timestamps, conductivities, temperatures, plot_unit = read_csv_data(selected_date_str)
        
        if timestamps:
            selected_type = graph_type_combobox.get()
            values = temperatures if selected_type == "Temperature" else conductivities
            
            update_plot(timestamps, conductivities, temperatures, plot_unit, selected_type)
            
            # Update statistics directly
            if values and len(values) > 0:
                max_val = max(values)
                min_val = min(values)
                avg_val = sum(values) / len(values)
                
                max_value_label.config(text=f"{max_val:.2f}")
                min_value_label.config(text=f"{min_val:.2f}")
                avg_value_label.config(text=f"{avg_val:.2f}")
            else:
                max_value_label.config(text="0.00")
                min_value_label.config(text="0.00")
                avg_value_label.config(text="0.00")
            
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
            
        timestamps, conductivities, temperatures, plot_unit = read_csv_data(selected_date_str)
        
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

def refresh_data():
    """Refresh data from CSV and update GUI"""
    # Update available dates in combobox
    available_dates = get_available_dates()
    if available_dates:
        date_combobox['values'] = available_dates
        # Keep current selection if it exists, otherwise select most recent
        if selected_date_str not in available_dates:
            date_combobox.set(available_dates[-1])
    
    # Force data reload and update GUI
    update_gui(datetime.now(), None, None, None)
