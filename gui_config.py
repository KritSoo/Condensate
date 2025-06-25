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

# Data decimation configuration
MAX_POINTS_TO_DISPLAY = 100  # Maximum number of points to display at once
DECIMATION_METHOD = 'lttb'   # 'lttb', 'minmax', or 'uniform'
DECIMATION_ENABLED = True    # Turn on/off decimation

# Data analysis configuration
SHOW_TREND_LINES = True      # แสดงเส้นแนวโน้ม
SHOW_ANOMALIES = True        # แสดงจุดที่ผิดปกติ
ANOMALY_METHOD = 'zscore'    # วิธีการตรวจจับความผิดปกติ ('zscore', 'iqr', 'isolation_forest')
TREND_WINDOW_SIZE = 5        # ขนาดหน้าต่างสำหรับการคำนวณค่าเฉลี่ยเคลื่อนที่

# Data validation
MAX_CONDUCTIVITY = 10000.0
MIN_CONDUCTIVITY = 0.0
DEFAULT_Y_RANGE = (0, 1000)

# Global state
selected_date_str = datetime.now().strftime('%Y-%m-%d')

# Graph types
GRAPH_TYPE_CONDUCTIVITY = "Conductivity"
GRAPH_TYPE_TEMPERATURE = "Temperature"

selected_graph_type = GRAPH_TYPE_CONDUCTIVITY

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
