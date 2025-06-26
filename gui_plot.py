"""Plot handling module for GUI application."""

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import dates as mdates
import matplotlib.patches as patches
import tkinter as tk
from tkinter import ttk
from datetime import timedelta
import numpy as np

from gui_config import *
from gui_utils import read_csv_data
from data_analyzer import add_trend_line_to_plot

# Global variables for plot
selected_date_str = None
graph_type_combobox = None
fig = None
ax = None
canvas = None
figure_canvas = None  # เพิ่มตัวแปรเพื่อให้สามารถเข้าถึง canvas ได้จากไฟล์อื่น
toolbar = None
original_xlim = None
original_ylim = None

def setup_graph(parent, reset_callback=None, date_str=None, graph_combo=None):
    """Setup graph and its controls."""
    global fig, ax, canvas, figure_canvas, toolbar, selected_date_str, graph_type_combobox
    
    # Set global variables
    selected_date_str = date_str
    graph_type_combobox = graph_combo
    
    # Configure Thai fonts before creating the plot
    from gui_utils import configure_thai_font
    configure_thai_font()
    
    # Create plot
    fig = Figure(figsize=PLOT_FIGSIZE, dpi=PLOT_DPI)
    ax = fig.add_subplot(111)
    
    # Configure axis
    ax.grid(True)
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')  # Generic label that will be updated
    
    # Create canvas
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    canvas.draw()
    
    # กำหนดให้ figure_canvas มีค่าเดียวกับ canvas เพื่อให้สามารถเข้าถึงได้จากไฟล์อื่น
    global figure_canvas
    figure_canvas = canvas
    
    # Add navigation toolbar
    toolbar = NavigationToolbar2Tk(canvas, parent)
    toolbar.update()
    
    def on_first_draw(event):
        # Store original view limits when data is first plotted
        global original_xlim, original_ylim
        original_xlim = ax.get_xlim()
        original_ylim = ax.get_ylim()
        
    canvas.mpl_connect('draw_event', on_first_draw)
    
    # Setup zoom functionality
    setup_zoom_handlers(canvas)
    
    return ax, canvas

def setup_zoom_handlers(canvas):
    """Setup zoom functionality for the plot."""
    canvas.mpl_connect('button_press_event', on_zoom_start)
    canvas.mpl_connect('button_release_event', on_zoom_end)
    canvas.mpl_connect('motion_notify_event', on_zoom_motion)

def adjust_annotation_position(x, y, ax, text):
    """Adjust annotation position to avoid overlapping with plot elements."""
    positions = [(0, 10), (10, 0), (-10, 0), (0, -10)]  # ทดลองตำแหน่งต่างๆ
    
    bbox = dict(boxstyle='round,pad=0.5', fc='white', ec='gray', alpha=0.8)
    for dx, dy in positions:
        annotation = ax.annotate(
            text, 
            (x, y),
            xytext=(dx, dy),
            textcoords='offset points',
            ha='center',
            va='center',
            fontsize=8,
            bbox=bbox
        )
        
        # ตรวจสอบการทับซ้อน
        canvas = ax.figure.canvas
        if canvas:
            try:
                annotation.draw(canvas.get_renderer())
                # ถ้าไม่มี overlap จะใช้ตำแหน่งนี้
                return annotation
            except:
                continue
    
    # ถ้าไม่มีตำแหน่งที่เหมาะสม ใช้ตำแหน่งเริ่มต้น
    return ax.annotate(
        text,
        (x, y),
        xytext=(0, 10),
        textcoords='offset points',
        ha='center',
        va='center',
        fontsize=8,
        bbox=bbox
    )

def decimate_data(timestamps, values, max_points=None, method=None):
    """
    Reduce the number of data points for efficient plotting while preserving important features.
    
    Parameters:
    -----------
    timestamps : list
        List of datetime objects
    values : list
        List of values corresponding to timestamps
    max_points : int
        Maximum number of points to return (defaults to MAX_POINTS_TO_DISPLAY from config)
    method : str
        Decimation method ('lttb', 'minmax', or 'uniform')
        
    Returns:
    --------
    tuple
        (downsampled_timestamps, downsampled_values)
    """
    # If decimation is disabled in config, return original data
    if not DECIMATION_ENABLED:
        return timestamps, values
        
    # Use config values if not specified
    if max_points is None:
        max_points = MAX_POINTS_TO_DISPLAY
    if method is None:
        method = DECIMATION_METHOD
        
    # If data points are fewer than max_points, return original data
    if len(timestamps) <= max_points:
        return timestamps, values
    
    if method == 'uniform':
        # Simple uniform downsampling
        indices = np.linspace(0, len(timestamps) - 1, max_points, dtype=int)
        return [timestamps[i] for i in indices], [values[i] for i in indices]
    
    elif method == 'minmax':
        # Min-max downsampling preserves extrema
        # Convert to numpy arrays for easier manipulation
        times_array = np.array(timestamps)
        values_array = np.array(values)
        
        # Divide data into chunks
        chunk_size = len(timestamps) // (max_points // 2)
        downsampled_times = []
        downsampled_values = []
        
        # Always include first and last points
        downsampled_times.append(timestamps[0])
        downsampled_values.append(values[0])
        
        # Process each chunk
        for i in range(0, len(timestamps), chunk_size):
            chunk = values_array[i:i+chunk_size]
            if len(chunk) == 0:
                continue
                
            # Find min and max in this chunk
            min_idx = np.argmin(chunk) + i
            max_idx = np.argmax(chunk) + i
            
            # Add min point (unless it's the same as max)
            if min_idx != max_idx:
                downsampled_times.append(timestamps[min_idx])
                downsampled_values.append(values[min_idx])
            
            # Add max point
            downsampled_times.append(timestamps[max_idx])
            downsampled_values.append(values[max_idx])
        
        # Add last point if not already added
        if timestamps[-1] != downsampled_times[-1]:
            downsampled_times.append(timestamps[-1])
            downsampled_values.append(values[-1])
            
        return downsampled_times, downsampled_values
    
    elif method == 'lttb':
        # Largest-Triangle-Three-Buckets (LTTB) algorithm
        # More sophisticated algorithm that preserves visual characteristics
        
        # Always include first and last points
        result_times = [timestamps[0]]
        result_values = [values[0]]
        
        if len(timestamps) <= 2:
            return timestamps, values
            
        # Bucket size
        bucket_size = (len(timestamps) - 2) / (max_points - 2)
        
        # Process all buckets except last
        for i in range(max_points - 2):
            # Bucket start and end
            a_idx = int(i * bucket_size) + 1
            b_idx = int((i + 1) * bucket_size) + 1
            
            # Last point in current bucket
            if b_idx >= len(timestamps):
                b_idx = len(timestamps) - 1
            
            # Last selected point
            a_time, a_value = timestamps[a_idx - 1], values[a_idx - 1]
            
            max_area = -1
            max_idx = a_idx
            
            # Find point in current bucket that creates largest triangle with 
            # last selected point and next bucket representative
            for j in range(a_idx, b_idx):
                # Calculate triangle area
                area = abs(
                    (mdates.date2num(a_time) - mdates.date2num(timestamps[b_idx])) * 
                    (values[j] - a_value) - 
                    (mdates.date2num(a_time) - mdates.date2num(timestamps[j])) * 
                    (values[b_idx] - a_value)
                ) * 0.5
                
                if area > max_area:
                    max_area = area
                    max_idx = j
            
            # Add the point that gives largest triangle
            result_times.append(timestamps[max_idx])
            result_values.append(values[max_idx])
        
        # Add last point
        result_times.append(timestamps[-1])
        result_values.append(values[-1])
        
        return result_times, result_values
    
    else:
        # Default: return original
        print(f"Unknown decimation method: {method}")
        return timestamps, values

def update_plot(timestamps, conductivities, temperatures, unit, graph_type, analysis=None):
    """Update plot with new data."""
    global fig, ax, canvas
    
    if not all([fig, ax, canvas]):
        print("Plot components not initialized")
        return
        
    try:
        ax.clear()
        
        # Set x-axis to show all hours regardless of data
        if timestamps:
            start_time = timestamps[0].replace(hour=0, minute=0, second=0)
            end_time = timestamps[-1].replace(hour=23, minute=59, second=59)
            ax.set_xlim(start_time, end_time)
        
        # Apply data decimation for better performance
        if graph_type == "Conductivity":
            # Get anomalies if available
            anomalies = None
            if analysis and 'conductivity' in analysis and 'anomalies' in analysis['conductivity']:
                anomalies = analysis['conductivity']['anomalies']
            
            # Decimate data for plotting
            plot_timestamps, plot_values = decimate_data(timestamps, conductivities)
            line = ax.plot(plot_timestamps, plot_values, 'b.-', label='Conductivity')
            values = conductivities
            
            # Add trend line if analysis is available
            if analysis and 'conductivity' in analysis and 'trend' in analysis['conductivity']:
                trend_info = analysis['conductivity']['trend']
                if trend_info['p_value'] < 0.1:  # Only show significant trends
                    add_trend_line_to_plot(ax, timestamps, conductivities, color='g')
            
        else:
            # Get anomalies if available
            anomalies = None
            if analysis and 'temperature' in analysis and 'anomalies' in analysis['temperature']:
                anomalies = analysis['temperature']['anomalies']
                
            # Decimate data for plotting
            plot_timestamps, plot_values = decimate_data(timestamps, temperatures)
            line = ax.plot(plot_timestamps, plot_values, 'r.-', label='Temperature')
            values = temperatures
            
            # Add trend line if analysis is available
            if analysis and 'temperature' in analysis and 'trend' in analysis['temperature']:
                trend_info = analysis['temperature']['trend']
                if trend_info['p_value'] < 0.1:  # Only show significant trends
                    add_trend_line_to_plot(ax, timestamps, temperatures, color='orange')
                    
        # Add anomaly markers if available
        if anomalies:
            anomaly_indices, anomaly_times, anomaly_vals = anomalies
            if anomaly_times and len(anomaly_times) > 0:
                ax.scatter(anomaly_times, anomaly_vals, color='red', marker='o', s=100, 
                          label='Anomalies', zorder=5, edgecolors='black')
            
        # Add value annotations with smart positioning (only for decimated points)
        for x, y in zip(plot_timestamps, plot_values):
            text = f'{y:.1f}'
            adjust_annotation_position(x, y, ax, text)
        
        # Format time axis to show all hours
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))  # Show every 2 hours
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_minor_locator(mdates.HourLocator())  # Show minor ticks for every hour
        
        # Set labels and grid
        if graph_type == "Conductivity":
            ax.set_ylabel(f'Conductivity ({unit})')
        else:
            ax.set_ylabel('Temperature (°C)')
        ax.set_xlabel('Time')
        ax.grid(True)
        ax.legend()
        
        # Show data count in corner
        ax.annotate(
            f'Points: {len(timestamps)} (showing {len(plot_timestamps)})', 
            xy=(0.02, 0.98),
            xycoords='axes fraction',
            va='top',
            fontsize=8,
            alpha=0.7
        )
        
        # Enable better zoom interaction
        ax.set_picker(True)
        fig.tight_layout()
        canvas.draw()
        
    except Exception as e:
        print(f"Error updating plot: {e}")

def reset_zoom():
    """Reset view to original limits."""
    if hasattr(reset_zoom, 'original_xlim') and hasattr(reset_zoom, 'original_ylim'):
        ax.set_xlim(original_xlim)
        ax.set_ylim(original_ylim)
        canvas.draw()
    else:
        # If original limits not stored, do full reset
        timestamps, conductivities, temperatures, plot_unit = read_csv_data(selected_date_str, force_refresh=False)
        if timestamps:
            start_time = timestamps[0].replace(hour=0, minute=0, second=0)
            end_time = timestamps[-1].replace(hour=23, minute=59, second=59)
            ax.set_xlim(start_time, end_time)
            
            if graph_type_combobox.get() == "Temperature":
                values = temperatures
            else:
                values = conductivities
                
            if values:
                margin = (max(values) - min(values)) * 0.1
                ax.set_ylim(min(values) - margin, max(values) + margin)
                
        canvas.draw()

def setup_empty_plot(unit=None):
    """Setup empty plot with default settings."""
    ax.clear()
    ax.set_title('No Data Available')
    ax.set_ylim(DEFAULT_Y_RANGE)
    ax.grid(True)
    ax.set_xlabel('Time')
    ax.set_ylabel(f'Conductivity ({unit if unit else ""})')
    canvas.draw()

def plot_data(x_timestamps, y_conductivities):
    """Plot the main data line."""
    global line
    ax.clear()
    ax.grid(True)
    
    # Apply data decimation
    plot_timestamps, plot_values = decimate_data(x_timestamps, y_conductivities)
    
    line, = ax.plot(plot_timestamps, plot_values, 'b-o',
                    label='Conductivity',
                    markersize=POINT_SIZE,
                    markerfacecolor='white',
                    picker=5)
    ax.legend()

def add_value_labels(x_timestamps, y_conductivities):
    """Add value labels next to each point."""
    for i, (x, y) in enumerate(zip(x_timestamps, y_conductivities)):
        # Determine label position
        if i < len(y_conductivities) - 1:
            next_y = y_conductivities[i + 1]
            xytext = (10, -10) if y < next_y else (10, 10)
        else:
            xytext = (10, 10)

        # Add annotation
        ax.annotate(
            f'{y:.1f}',
            (x, y),
            xytext=xytext,
            textcoords='offset points',
            fontsize=8,
            bbox=dict(
                boxstyle='round,pad=0.5',
                fc='white',
                ec='gray',
                alpha=0.7
            )
        )

def mark_threshold_points(x_timestamps, y_conductivities):
    """Mark points that exceed threshold."""
    global red_marks
    
    threshold_points = [
        (x, y) for x, y in zip(x_timestamps, y_conductivities)
        if y > THRESHOLD_VALUE
    ]
    
    if threshold_points:
        x_thresh, y_thresh = zip(*threshold_points)
        red_marks = ax.scatter(x_thresh, y_thresh,
                             color='red', s=THRESHOLD_POINT_SIZE,
                             label='Threshold Exceeded')
        ax.legend()

def setup_time_axis(x_timestamps):
    """Configure time axis formatting."""
    if not x_timestamps:
        return
        
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.tick_params(axis='x', rotation=0)
    
    # Set x-axis limits to show full day
    start_time = x_timestamps[0].replace(hour=0, minute=0, second=0)
    end_time = start_time + timedelta(days=1)
    ax.set_xlim(start_time, end_time)

def on_zoom_start(event):
    """Handle start of zoom selection."""
    global zoom_active, zoom_start, zoom_rect
    if event.button == 1 and event.inaxes == ax:
        zoom_active = True
        zoom_start = (event.xdata, event.ydata)
        zoom_rect = patches.Rectangle(
            (event.xdata, event.ydata), 0, 0,
            fill=False, color='gray', linestyle='dashed'
        )
        ax.add_patch(zoom_rect)

def on_zoom_motion(event):
    """Handle zoom rectangle drawing."""
    global zoom_rect
    if zoom_active and event.inaxes == ax:
        # Update the rectangle's width and height
        zoom_rect.set_width(event.xdata - zoom_start[0])
        zoom_rect.set_height(event.ydata - zoom_start[1])
        figure.canvas.draw_idle()

def on_zoom_end(event):
    """Handle end of zoom selection."""
    global zoom_active, zoom_rect
    if zoom_active and event.inaxes == ax:
        x0, y0 = zoom_start
        x1, y1 = event.xdata, event.ydata
        
        # Convert to data coordinates
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        
        # Remove the zoom rectangle
        zoom_rect.remove()
        figure.canvas.draw()
        
    zoom_active = False
