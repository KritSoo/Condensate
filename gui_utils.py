"""Utility functions for GUI application."""

import csv
import pandas as pd
from datetime import datetime
from tkinter import messagebox, filedialog
import tkinter as ttk

from gui_config import *

_data_cache = {}

def clear_cache():
    """Clear the data cache to force fresh data load"""
    global _data_cache
    _data_cache = {}

def get_available_dates():
    """Get list of available dates from CSV file."""
    available_dates = set()
    try:
        with open('sension7_data.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamp = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                available_dates.add(timestamp.strftime('%Y-%m-%d'))
        
        return sorted(list(available_dates))
    except Exception as e:
        print(f"Error reading dates from CSV: {e}")
        return []

def calculate_statistics(data):
    """Calculate basic statistics from conductivity data."""
    return {
        'Minimum': data.min(),
        'Maximum': data.max(),
        'Average': data.mean(),
        'Std Dev': data.std(),
        'Count': len(data)
    }

def update_statistics(values):
    """Update statistics display."""
    try:
        if values and len(values) > 0:
            max_val = max(values)
            min_val = min(values)
            avg_val = sum(values) / len(values)
            
            return {
                "max": f"{max_val:.2f}",
                "min": f"{min_val:.2f}",
                "avg": f"{avg_val:.2f}"
            }
        return {"max": "0.00", "min": "0.00", "avg": "0.00"}
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return {"max": "0.00", "min": "0.00", "avg": "0.00"}

def export_to_excel():
    """Export data to Excel file."""
    try:
        from openpyxl import Workbook
        from tkinter import filedialog
        
        # Get save file location
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*")]
        )
        
        if not filename:
            return
            
        # Create workbook and select active sheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Sensor Data"
        
        # Write headers
        ws['A1'] = 'Timestamp'
        ws['B1'] = 'Conductivity'
        ws['C1'] = 'Unit'
        ws['D1'] = 'Temperature'
        
        # Read and write data
        with open('sension7_data.csv', 'r') as file:
            reader = csv.DictReader(file)
            for idx, row in enumerate(reader, start=2):
                ws[f'A{idx}'] = row['Timestamp']
                ws[f'B{idx}'] = float(row['Conductivity'])
                ws[f'C{idx}'] = row['Unit']
                ws[f'D{idx}'] = float(row['Temperature']) if row['Temperature'] else None
        
        # Save workbook
        wb.save(filename)
        messagebox.showinfo("Success", "Data exported successfully!")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {str(e)}")

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

def read_csv_data(date_str):
    """Read data from CSV file for given date."""
    timestamps = []
    conductivities = []
    temperatures = []
    unit = "uS/cm"
    
    try:
        with open('sension7_data.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamp = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                if timestamp.strftime('%Y-%m-%d') == date_str:
                    timestamps.append(timestamp)
                    conductivities.append(float(row['Conductivity']))
                    temperatures.append(float(row['Temperature']) if row['Temperature'] else None)
                    unit = row['Unit']
                    
        return timestamps, conductivities, temperatures, unit
        
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return [], [], [], "uS/cm"

# ... Move other utility functions from gui_app.py ...
