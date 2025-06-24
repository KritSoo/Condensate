"""Utility functions for GUI application."""

import csv
import pandas as pd
from datetime import datetime
from tkinter import messagebox, filedialog
import tkinter as ttk

from gui_config import *

def get_available_dates():
    """Get unique dates from the CSV file."""
    dates = set()
    try:
        with open(LOG_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                try:
                    ts = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                    dates.add(ts.strftime('%Y-%m-%d'))
                except (ValueError, IndexError):
                    continue
    except FileNotFoundError:
        print(f"Warning: {LOG_FILE} not found")
    return sorted(list(dates))

def calculate_statistics(data):
    """Calculate basic statistics from conductivity data."""
    return {
        'Minimum': data.min(),
        'Maximum': data.max(),
        'Average': data.mean(),
        'Std Dev': data.std(),
        'Count': len(data)
    }

def update_statistics(data):
    """Update statistics display."""
    global stats_frame
    if stats_frame is None:
        print("Warning: Statistics frame not initialized")
        return
        
    try:
        stats = calculate_statistics(data)
        for widget in stats_frame.winfo_children():
            widget.destroy()
        
        for key, value in stats.items():
            text = f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}"
            ttk.Label(stats_frame, text=text).pack(anchor="w")
    except Exception as e:
        print(f"Error updating statistics: {e}")

def export_to_excel():
    """Export current day's data to Excel file."""
    try:
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror(
                "Module Missing",
                "Please install openpyxl module first:\n"
                "1. Open Command Prompt\n"
                "2. Run: pip install openpyxl\n"
                "3. Restart the application"
            )
            return

        # ... copy existing export code from gui_app.py ...

    except Exception as e:
        print(f"Error exporting to Excel: {e}")

def refresh_date_list():
    """Update the date combobox with available dates."""
    global date_combobox
    if date_combobox is None:
        print("Warning: Date combobox not initialized")
        return
    
    try:
        dates = get_available_dates()
        date_combobox['values'] = dates
        if dates:
            date_combobox.current(0)
    except Exception as e:
        print(f"Error refreshing date list: {e}")

def read_csv_data(selected_date):
    """Read and validate data from CSV for given date."""
    x_timestamps = []
    y_conductivities = []
    
    try:
        with open(LOG_FILE, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                ts = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                if ts.strftime('%Y-%m-%d') == selected_date:
                    x_timestamps.append(ts)
                    y_conductivities.append(float(row[1]))
    except Exception as e:
        print(f"Error reading CSV: {e}")
        
    return x_timestamps, y_conductivities

# ... Move other utility functions from gui_app.py ...
