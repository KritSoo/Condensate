"""Plot handling module for GUI application."""

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import dates as mdates
import matplotlib.patches as patches
import tkinter as ttk
from datetime import timedelta

from gui_config import *

def setup_graph(parent, reset_callback):
    """Setup graph and its controls."""
    global figure, ax, canvas
    
    # Setup control buttons
    controls_frame = ttk.Frame(parent)
    controls_frame.pack(fill="x", pady=(0, 5))
    
    ttk.Button(controls_frame, text="Reset Zoom",
              command=reset_callback).pack(side="left", padx=5)
    
    # Create plot
    figure = Figure(figsize=PLOT_FIGSIZE, dpi=PLOT_DPI)
    ax = figure.add_subplot(111)
    
    # Configure axis
    ax.grid(True)
    ax.set_xlabel('Time')
    ax.set_ylabel('Conductivity')
    
    # Create canvas
    canvas = FigureCanvasTkAgg(figure, master=parent)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    canvas.draw()
    
    # Setup zoom functionality
    setup_zoom_handlers(canvas)
    return ax, canvas

def setup_zoom_handlers(canvas):
    """Setup zoom functionality for the plot."""
    canvas.mpl_connect('button_press_event', on_zoom_start)
    canvas.mpl_connect('button_release_event', on_zoom_end)
    canvas.mpl_connect('motion_notify_event', on_zoom_motion)

def update_plot(x_timestamps, y_conductivities, unit=None):
    """Update plot with new data."""
    if not x_timestamps or not y_conductivities:
        setup_empty_plot(unit)
        return
        
    plot_data(x_timestamps, y_conductivities)
    add_value_labels(x_timestamps, y_conductivities)
    mark_threshold_points(x_timestamps, y_conductivities)
    setup_time_axis(x_timestamps)
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
    
    line, = ax.plot(x_timestamps, y_conductivities, 'b-o',
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
