"""Configuration and global variables for GUI application."""

from datetime import datetime

# File configuration
LOG_FILE = "sension7_data.csv"
THRESHOLD_VALUE = 500.0
TIME_WINDOW_MINUTES = 30

# Plot configuration
PLOT_DPI = 100
PLOT_FIGSIZE = (8, 6)
POINT_SIZE = 6
THRESHOLD_POINT_SIZE = 50

# Data validation
MAX_CONDUCTIVITY = 10000.0
MIN_CONDUCTIVITY = 0.0
DEFAULT_Y_RANGE = (0, 1000)

# Global state
selected_date_str = datetime.now().strftime('%Y-%m-%d')

# GUI elements (initialized as None)
root = None
conductivity_value_label = None
unit_label = None
time_label = None
date_combobox = None
filter_min = None
filter_max = None
stats_frame = None

# Plot elements
figure = None
ax = None
canvas = None
line = None
red_marks = None
zoom_active = False
zoom_rect = None
zoom_start = None
