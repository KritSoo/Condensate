"""
Comparison GUI module for comparing data between multiple days.
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import pandas as pd
import os

# Make sure to import the ScrollableFrame class
from gui_scrollable import ScrollableFrame
from gui_config import *
from data_analyzer import (
    compare_days_data, plot_comparison_graph,
    create_comparison_report, find_days_with_similar_patterns
)

class ComparisonWindow:
    """Class for comparison window that allows comparing data between days."""
    
    def __init__(self, parent, available_dates, csv_file=LOG_FILE):
        """
        Initialize comparison window.
        
        Parameters:
        -----------
        parent : tk.Tk or tk.Toplevel
            Parent window
        available_dates : list
            List of available dates to compare
        csv_file : str
            Path to CSV data file
        """
        # Configure Thai fonts for matplotlib
        from gui_utils import configure_thai_font
        configure_thai_font()
        
        self.parent = parent
        self.available_dates = available_dates
        self.csv_file = csv_file
        self.selected_dates = []
        
        # Create main window
        self.window = tk.Toplevel(parent)
        self.window.title("เปรียบเทียบข้อมูลระหว่างวัน")
        self.window.geometry("1200x800")
        self.window.minsize(800, 600)
        
        # Create main layout
        self.create_widgets()
    
    def create_widgets(self):
        """Create widgets for comparison window."""
        # Main layout - split into left (controls) and right (graph) panels
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Left panel - Control panel
        control_frame = ttk.LabelFrame(main_frame, text="ตัวควบคุม", padding="10")
        control_frame.pack(side="left", fill="y", padx=(0, 10))
        
        # Right panel - Graph panel
        self.graph_frame = ttk.LabelFrame(main_frame, text="กราฟเปรียบเทียบ", padding="10")
        self.graph_frame.pack(side="right", fill="both", expand=True)
        
        # Date selection
        date_frame = ttk.LabelFrame(control_frame, text="เลือกวันที่", padding="10")
        date_frame.pack(fill="x", pady=(0, 10))
        
        # Available dates
        ttk.Label(date_frame, text="วันที่ที่มีข้อมูล:").pack(anchor="w")
        self.date_listbox = tk.Listbox(date_frame, selectmode=tk.MULTIPLE, height=10, width=15)
        self.date_listbox.pack(fill="x", pady=5)
        
        # Populate date listbox
        for date in self.available_dates:
            self.date_listbox.insert(tk.END, date)
        
        # Add scrollbar to listbox
        scrollbar = ttk.Scrollbar(date_frame, orient="vertical", command=self.date_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.date_listbox.config(yscrollcommand=scrollbar.set)
        
        # Date selection buttons
        btn_frame = ttk.Frame(date_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="เลือกที่เลือกไว้", 
                  command=self.select_marked_dates).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="เลือกทั้งหมด", 
                  command=self.select_all_dates).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="ล้างเลือก", 
                  command=self.clear_selection).pack(side="left", padx=5)
        
        # Find similar dates option
        similar_frame = ttk.LabelFrame(control_frame, text="ค้นหาวันที่มีรูปแบบคล้ายกัน", padding="10")
        similar_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(similar_frame, text="วันที่ต้นแบบ:").pack(anchor="w")
        self.reference_date_var = tk.StringVar()
        reference_date_cb = ttk.Combobox(similar_frame, textvariable=self.reference_date_var, state="readonly")
        reference_date_cb["values"] = self.available_dates
        if self.available_dates:
            reference_date_cb.set(self.available_dates[-1])
        reference_date_cb.pack(fill="x", pady=5)
        
        ttk.Button(similar_frame, text="ค้นหาวันที่คล้ายกัน", 
                  command=self.find_similar_days).pack(fill="x")
        
        # Data type selection
        data_frame = ttk.LabelFrame(control_frame, text="ข้อมูลที่แสดง", padding="10")
        data_frame.pack(fill="x", pady=(0, 10))
        
        self.data_type_var = tk.StringVar(value="Conductivity")
        ttk.Radiobutton(data_frame, text="ค่าการนำไฟฟ้า", 
                       variable=self.data_type_var, value="Conductivity", 
                       command=self.update_graph).pack(anchor="w")
        ttk.Radiobutton(data_frame, text="อุณหภูมิ", 
                       variable=self.data_type_var, value="Temperature", 
                       command=self.update_graph).pack(anchor="w")
        
        # Options frame
        options_frame = ttk.LabelFrame(control_frame, text="ตัวเลือก", padding="10")
        options_frame.pack(fill="x", pady=(0, 10))
        
        self.show_trend_lines_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="แสดงเส้นแนวโน้ม", 
                       variable=self.show_trend_lines_var, 
                       command=self.update_graph).pack(anchor="w")
        
        # Action buttons
        btn_frame = ttk.Frame(control_frame, padding="10")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(btn_frame, text="แสดงกราฟ", 
                  command=self.update_graph).pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="แสดงรายงานสถิติ", 
                  command=self.show_statistics_report).pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="บันทึกกราฟ", 
                  command=self.save_graph).pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="ส่งออกรายงาน", 
                  command=self.export_report).pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="ปิด", 
                  command=self.window.destroy).pack(fill="x", pady=(20, 5))
        
        # Create initial empty graph
        self.create_empty_graph()
    
    def select_marked_dates(self):
        """Select dates marked in listbox."""
        selection = self.date_listbox.curselection()
        if not selection:
            messagebox.showinfo("", "กรุณาเลือกวันที่อย่างน้อยหนึ่งวัน")
            return
            
        self.selected_dates = [self.date_listbox.get(idx) for idx in selection]
        self.update_graph()
    
    def select_all_dates(self):
        """Select all available dates."""
        self.date_listbox.selection_set(0, tk.END)
        self.selected_dates = self.available_dates.copy()
        self.update_graph()
    
    def clear_selection(self):
        """Clear date selection."""
        self.date_listbox.selection_clear(0, tk.END)
        self.selected_dates = []
        self.create_empty_graph()
    
    def find_similar_days(self):
        """Find days with similar patterns to reference date."""
        reference_date = self.reference_date_var.get()
        if not reference_date:
            messagebox.showinfo("", "กรุณาเลือกวันที่ต้นแบบ")
            return
            
        # Get data type (column index)
        data_type = self.data_type_var.get()
        column_index = 1 if data_type == "Conductivity" else 3
        
        # Find similar days
        similar_days = find_days_with_similar_patterns(
            self.csv_file, reference_date, 
            column_index=column_index, top_n=5
        )
        
        if not similar_days:
            messagebox.showinfo("", "ไม่พบวันที่มีรูปแบบคล้ายกัน")
            return
            
        # Show similar days in a new window
        similar_window = tk.Toplevel(self.window)
        similar_window.title(f"วันที่มีรูปแบบคล้ายกับ {reference_date}")
        similar_window.geometry("500x400")
        
        main_frame = ttk.Frame(similar_window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, 
                 text=f"วันที่มีรูปแบบคล้ายกับ {reference_date} ({data_type})",
                 font=("Helvetica", 12, "bold")).pack(pady=10)
        
        # Create scrollable container for table
        scroll_container = ScrollableFrame(main_frame)
        scroll_container.pack(fill="both", expand=True, pady=5)
        
        # Get the frame to add content to
        table_frame = scroll_container.get_frame()
        
        # Create table headers
        header_frame = ttk.Frame(table_frame)
        header_frame.pack(fill="x", pady=5)
        
        ttk.Label(header_frame, text="วันที่", width=15, anchor="w", 
                 font=("Helvetica", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(header_frame, text="ค่าความคล้าย", width=15, anchor="w",
                 font=("Helvetica", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(header_frame, text="", width=8).grid(row=0, column=2, padx=5, pady=5)
        
        # Add separator line
        separator = ttk.Separator(table_frame, orient="horizontal")
        separator.pack(fill="x", pady=5)
        
        # Add similar days to table
        for i, (day, score) in enumerate(similar_days):
            row_frame = ttk.Frame(table_frame)
            row_frame.pack(fill="x", pady=2)
            
            ttk.Label(row_frame, text=day, width=15, anchor="w").grid(
                row=0, column=0, padx=5, pady=5)
            ttk.Label(row_frame, text=f"{score:.4f}", width=15, anchor="w").grid(
                row=0, column=1, padx=5, pady=5)
            
            # Add button to select this day for comparison
            ttk.Button(row_frame, text="เลือก", width=8,
                      command=lambda d=day: self.select_day_for_comparison(d)).grid(
                          row=0, column=2, padx=5, pady=5)
            
            # Add alternating row colors
            if i % 2 == 1:
                row_frame.configure(style="Alt.TFrame")
        
        # Add button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="เลือกทั้งหมด", 
                  command=lambda: self.select_days_for_comparison([d for d, _ in similar_days])).pack(side="right", padx=5)
    
    def select_day_for_comparison(self, day):
        """Select a single day for comparison."""
        if day not in self.selected_dates:
            self.selected_dates.append(day)
            
            # Update selection in listbox
            for i in range(self.date_listbox.size()):
                if self.date_listbox.get(i) == day:
                    self.date_listbox.selection_set(i)
                    break
            
            self.update_graph()
    
    def select_days_for_comparison(self, days):
        """Select multiple days for comparison."""
        for day in days:
            if day not in self.selected_dates:
                self.selected_dates.append(day)
                
                # Update selection in listbox
                for i in range(self.date_listbox.size()):
                    if self.date_listbox.get(i) == day:
                        self.date_listbox.selection_set(i)
                        break
        
        self.update_graph()
    
    def create_empty_graph(self):
        """Create empty graph."""
        # Clear graph frame
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.set_title("เลือกวันที่เพื่อแสดงกราฟเปรียบเทียบ")
        self.ax.set_xlabel("เวลา")
        self.ax.set_ylabel("ค่า")
        self.ax.grid(True)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def update_graph(self):
        """Update graph with selected dates."""
        if not self.selected_dates:
            self.create_empty_graph()
            return
            
        # Get data type
        data_type = self.data_type_var.get()
        column_index = 1 if data_type == "Conductivity" else 3
        
        # Get comparison data
        comparison_data = compare_days_data(
            self.csv_file, self.selected_dates, 
            column_index=column_index, data_name=data_type
        )
        
        if not comparison_data:
            messagebox.showinfo("", "ไม่พบข้อมูลสำหรับวันที่เลือก")
            self.create_empty_graph()
            return
            
        # Clear graph frame
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        
        # Plot comparison graph
        plot_comparison_graph(
            comparison_data, ax=self.ax, 
            data_name=data_type, 
            show_trends=self.show_trend_lines_var.get()
        )
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def show_statistics_report(self):
        """Show statistics report for selected dates."""
        if not self.selected_dates:
            messagebox.showinfo("", "กรุณาเลือกวันที่อย่างน้อยหนึ่งวัน")
            return
            
        # Get data type
        data_type = self.data_type_var.get()
        column_index = 1 if data_type == "Conductivity" else 3
        
        # Get comparison data
        comparison_data = compare_days_data(
            self.csv_file, self.selected_dates, 
            column_index=column_index, data_name=data_type
        )
        
        if not comparison_data:
            messagebox.showinfo("", "ไม่พบข้อมูลสำหรับวันที่เลือก")
            return
            
        # Create report
        report_df = create_comparison_report(comparison_data, data_name=data_type)
        
        if report_df.empty:
            messagebox.showinfo("", "ไม่สามารถสร้างรายงานได้")
            return
            
        # Show report in a new window
        report_window = tk.Toplevel(self.window)
        report_window.title(f"รายงานสถิติเปรียบเทียบ - {data_type}")
        report_window.geometry("800x600")  # Make window taller for better viewing
        
        # Add a main frame
        main_frame = ttk.Frame(report_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add title at the top
        ttk.Label(main_frame, 
                 text=f"รายงานสถิติเปรียบเทียบ - {data_type}",
                 font=("Helvetica", 12, "bold")).pack(pady=10)
        
        # Create scrollable frame for table with both vertical and horizontal scrolling
        table_container = ScrollableFrame(main_frame, horizontal_scroll=True)
        table_container.pack(fill="both", expand=True, pady=5)
        
        # Get the frame to add content to
        table_frame = table_container.get_frame()
        
        # Create header row
        header_frame = ttk.Frame(table_frame)
        header_frame.pack(fill="x", pady=2)
        
        # Set column headers with consistent widths
        column_width = 120
        for col_idx, col in enumerate(report_df.columns):
            header_label = ttk.Label(header_frame, text=col, width=column_width//10, 
                                   font=("Helvetica", 10, "bold"), anchor="center")
            header_label.grid(row=0, column=col_idx, padx=2, pady=2)
        
        # Add separator
        separator = ttk.Separator(table_frame, orient="horizontal")
        separator.pack(fill="x", pady=2)
        
        # Add data rows
        for row_idx, (_, row) in enumerate(report_df.iterrows(), start=1):
            row_frame = ttk.Frame(table_frame)
            row_frame.pack(fill="x", pady=1)
            
            # Add each cell in the row
            for col_idx, value in enumerate(row):
                # Format value with 3 decimal places if it's a number
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.3f}" if isinstance(value, float) else str(value)
                else:
                    formatted_value = str(value)
                
                cell_label = ttk.Label(row_frame, text=formatted_value, width=column_width//10, anchor="center")
                cell_label.grid(row=0, column=col_idx, padx=2, pady=2)
                
                # Add alternating row colors
                if row_idx % 2 == 0:
                    cell_label.configure(background="#f0f0f0")
        
        # Add export button at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="ส่งออกรายงาน", 
                  command=lambda: self.export_report()).pack(side="right", padx=5)
    
    def save_graph(self):
        """Save current graph to file."""
        if not hasattr(self, 'fig') or not self.selected_dates:
            messagebox.showinfo("", "ไม่มีกราฟให้บันทึก")
            return
            
        from tkinter import filedialog
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), 
                      ("PDF Document", "*.pdf"), ("SVG Image", "*.svg")]
        )
        
        if not file_path:
            return
            
        # Save figure
        try:
            self.fig.savefig(file_path, dpi=300, bbox_inches="tight")
            messagebox.showinfo("", f"บันทึกกราฟไปยัง {file_path} สำเร็จ")
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {str(e)}")
    
    def export_report(self):
        """Export statistics report to file."""
        if not self.selected_dates:
            messagebox.showinfo("", "กรุณาเลือกวันที่อย่างน้อยหนึ่งวัน")
            return
            
        from tkinter import filedialog
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel File", "*.xlsx"), ("CSV File", "*.csv")]
        )
        
        if not file_path:
            return
            
        # Get data type
        data_type = self.data_type_var.get()
        column_index = 1 if data_type == "Conductivity" else 3
        
        # Get comparison data
        comparison_data = compare_days_data(
            self.csv_file, self.selected_dates, 
            column_index=column_index, data_name=data_type
        )
        
        if not comparison_data:
            messagebox.showinfo("", "ไม่พบข้อมูลสำหรับวันที่เลือก")
            return
            
        # Create report
        report_df = create_comparison_report(comparison_data, data_name=data_type)
        
        if report_df.empty:
            messagebox.showinfo("", "ไม่สามารถสร้างรายงานได้")
            return
            
        # Export report
        try:
            if file_path.endswith(".xlsx"):
                report_df.to_excel(file_path, index=False)
            else:  # CSV
                report_df.to_csv(file_path, index=False)
                
            messagebox.showinfo("", f"ส่งออกรายงานไปยัง {file_path} สำเร็จ")
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {str(e)}")


def open_comparison_window(parent):
    """Open comparison window."""
    from gui_utils import get_available_dates
    
    # Get available dates
    available_dates = get_available_dates()
    
    if not available_dates:
        messagebox.showinfo("", "ไม่พบข้อมูลในระบบ")
        return
        
    # Create comparison window
    comparison_window = ComparisonWindow(parent, available_dates)
    
    return comparison_window
