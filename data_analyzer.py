"""
Data Analysis module for HACH Sension7 Conductivity Data Logger.
Provides advanced statistical analysis, trend detection, and anomaly detection.
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import csv

# Constants for anomaly detection
ANOMALY_DETECTION_METHODS = ['zscore', 'iqr', 'isolation_forest']
DEFAULT_ANOMALY_METHOD = 'zscore'
Z_SCORE_THRESHOLD = 3.0
IQR_MULTIPLIER = 1.5
CONTAMINATION_FACTOR = 0.05  # For Isolation Forest (expected proportion of anomalies)

def calculate_advanced_statistics(values):
    """
    Calculate advanced statistical metrics beyond simple min/max/average.
    
    Parameters:
    -----------
    values : list or numpy.ndarray
        List of numerical values to analyze
        
    Returns:
    --------
    dict
        Dictionary containing various statistical metrics
    """
    # Convert input to numpy array for calculations
    values_array = np.array(values)
    values_clean = values_array[~np.isnan(values_array)]  # Remove NaN values
    
    if len(values_clean) == 0:
        return {
            'count': 0,
            'min': np.nan,
            'max': np.nan,
            'mean': np.nan,
            'std': np.nan,
            'percentile_25': np.nan,
            'median': np.nan,
            'percentile_75': np.nan,
            'percentile_95': np.nan,
            'skewness': np.nan,
            'kurtosis': np.nan,
            'range': np.nan
        }
    
    # Basic statistics
    result = {
        'count': len(values_clean),
        'min': np.min(values_clean),
        'max': np.max(values_clean),
        'mean': np.mean(values_clean),
        'std': np.std(values_clean),
        'percentile_25': np.percentile(values_clean, 25),
        'median': np.median(values_clean),
        'percentile_75': np.percentile(values_clean, 75),
        'percentile_95': np.percentile(values_clean, 95),
        'skewness': stats.skew(values_clean),
        'kurtosis': stats.kurtosis(values_clean),
        'range': np.max(values_clean) - np.min(values_clean)
    }
    
    return result

def format_statistics_for_display(stats_dict):
    """Format statistics dictionary for display in the UI."""
    formatted = {}
    
    # Format all numerical values to 2 decimal places
    for key, value in stats_dict.items():
        if isinstance(value, (int, float)) and not np.isnan(value):
            if key == 'count':
                formatted[key] = f"{value:d}"  # Integer format for count
            else:
                formatted[key] = f"{value:.2f}"
        else:
            formatted[key] = "N/A"
    
    # Rename keys for better display
    display_names = {
        'count': 'จำนวนข้อมูล',
        'min': 'ค่าต่ำสุด',
        'max': 'ค่าสูงสุด',
        'mean': 'ค่าเฉลี่ย',
        'std': 'ค่าเบี่ยงเบนมาตรฐาน',
        'percentile_25': 'เปอร์เซ็นไทล์ที่ 25',
        'median': 'มัธยฐาน',
        'percentile_75': 'เปอร์เซ็นไทล์ที่ 75',
        'percentile_95': 'เปอร์เซ็นไทล์ที่ 95',
        'skewness': 'ความเบ้',
        'kurtosis': 'ความโด่ง',
        'range': 'พิสัย'
    }
    
    # Create new dictionary with display names
    display_dict = {display_names.get(k, k): v for k, v in formatted.items()}
    
    return display_dict

def detect_anomalies(timestamps, values, method=DEFAULT_ANOMALY_METHOD):
    """
    Detect anomalies/outliers in the data series.
    
    Parameters:
    -----------
    timestamps : list
        List of datetime objects corresponding to values
    values : list
        List of numerical values to analyze
    method : str
        Method to use for anomaly detection: 'zscore', 'iqr', or 'isolation_forest'
        
    Returns:
    --------
    tuple
        (anomaly_indices, anomaly_timestamps, anomaly_values)
    """
    if not values or len(values) < 3:
        return [], [], []
    
    # Convert to numpy array and remove NaN
    values_array = np.array(values)
    valid_indices = ~np.isnan(values_array)
    clean_values = values_array[valid_indices]
    clean_timestamps = [timestamps[i] for i, valid in enumerate(valid_indices) if valid]
    
    anomaly_indices = []
    
    if method == 'zscore':
        # Z-score method: flag values more than Z_SCORE_THRESHOLD standard deviations from the mean
        z_scores = stats.zscore(clean_values)
        anomaly_indices = np.where(np.abs(z_scores) > Z_SCORE_THRESHOLD)[0].tolist()
    
    elif method == 'iqr':
        # IQR method: flag values beyond Q1 - IQR_MULTIPLIER*IQR and Q3 + IQR_MULTIPLIER*IQR
        q1 = np.percentile(clean_values, 25)
        q3 = np.percentile(clean_values, 75)
        iqr = q3 - q1
        lower_bound = q1 - IQR_MULTIPLIER * iqr
        upper_bound = q3 + IQR_MULTIPLIER * iqr
        anomaly_indices = np.where((clean_values < lower_bound) | (clean_values > upper_bound))[0].tolist()
    
    elif method == 'isolation_forest':
        # Isolation Forest algorithm
        if len(clean_values) >= 10:  # Need enough samples for this method
            # Reshape for sklearn
            X = clean_values.reshape(-1, 1)
            model = IsolationForest(contamination=CONTAMINATION_FACTOR, random_state=42)
            model.fit(X)
            predictions = model.predict(X)
            # In isolation forest, anomalies are labeled as -1
            anomaly_indices = np.where(predictions == -1)[0].tolist()
        else:
            # Fall back to Z-score for small datasets
            z_scores = stats.zscore(clean_values)
            anomaly_indices = np.where(np.abs(z_scores) > Z_SCORE_THRESHOLD)[0].tolist()
    
    # Get corresponding timestamps and values
    anomaly_timestamps = [clean_timestamps[i] for i in anomaly_indices]
    anomaly_values = [clean_values[i] for i in anomaly_indices]
    
    # Map back to original indices (accounting for NaN values)
    original_indices = [i for i, valid in enumerate(valid_indices) if valid]
    original_anomaly_indices = [original_indices[i] for i in anomaly_indices]
    
    return original_anomaly_indices, anomaly_timestamps, anomaly_values

def analyze_trend(timestamps, values, window_size=5):
    """
    Analyze trend in time series data using moving averages and linear regression.
    
    Parameters:
    -----------
    timestamps : list
        List of datetime objects
    values : list
        List of numerical values
    window_size : int
        Size of moving average window
        
    Returns:
    --------
    dict
        Dictionary containing trend information
    """
    if not values or len(values) < 3:
        return {
            'trend_direction': 'insufficient_data',
            'trend_strength': 0.0,
            'moving_average': [],
            'slope': 0.0,
            'r_squared': 0.0,
            'p_value': 1.0
        }
    
    # Convert timestamps to numeric (seconds since start)
    if len(timestamps) > 0:
        base_time = timestamps[0]
        time_seconds = [(t - base_time).total_seconds() for t in timestamps]
    else:
        time_seconds = list(range(len(values)))
    
    # Calculate moving average
    values_array = np.array(values)
    moving_avg = []
    
    for i in range(len(values)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(values), i + window_size // 2 + 1)
        window = values_array[start_idx:end_idx]
        window_clean = window[~np.isnan(window)]
        if len(window_clean) > 0:
            moving_avg.append(np.mean(window_clean))
        else:
            moving_avg.append(np.nan)
    
    # Perform linear regression (ignoring NaN values)
    valid_indices = ~np.isnan(values_array)
    if np.sum(valid_indices) >= 2:
        x = np.array(time_seconds)[valid_indices]
        y = values_array[valid_indices]
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend direction and strength
        if p_value < 0.05:  # Statistically significant trend
            trend_direction = 'increasing' if slope > 0 else 'decreasing'
            r_squared = r_value ** 2
            trend_strength = r_squared
        else:
            trend_direction = 'stable'
            r_squared = r_value ** 2
            trend_strength = 0.0
    else:
        slope = 0.0
        p_value = 1.0
        r_squared = 0.0
        trend_direction = 'insufficient_data'
        trend_strength = 0.0
    
    return {
        'trend_direction': trend_direction,
        'trend_strength': trend_strength,
        'moving_average': moving_avg,
        'slope': slope,
        'r_squared': r_squared,
        'p_value': p_value
    }

def get_daily_statistics_from_csv(csv_file, date_str, column_index=1):
    """
    Extract values for a specific date from CSV and calculate statistics.
    
    Parameters:
    -----------
    csv_file : str
        Path to CSV file
    date_str : str
        Date string in format 'YYYY-MM-DD'
    column_index : int
        Index of the column to analyze (1 for Conductivity, 3 for Temperature)
    
    Returns:
    --------
    dict
        Dictionary containing statistics
    """
    values = []
    timestamps = []
    
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            
            for row in reader:
                try:
                    timestamp_str = row[0]
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    if timestamp.strftime('%Y-%m-%d') == date_str:
                        value = float(row[column_index])
                        values.append(value)
                        timestamps.append(timestamp)
                except (ValueError, IndexError):
                    continue
    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None
    
    if not values:
        return None, None
    
    # Calculate statistics
    statistics = calculate_advanced_statistics(values)
    
    return timestamps, values, statistics

def add_trend_line_to_plot(ax, timestamps, values, color='g', line_style='--', alpha=0.7):
    """
    Add trend line to an existing matplotlib plot.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        The axes to add trend line to
    timestamps : list
        List of datetime objects
    values : list
        List of numerical values
    color : str
        Color of trend line
    line_style : str
        Line style of trend line
    alpha : float
        Transparency of trend line
    """
    # Convert to numpy arrays and remove NaN values
    values_array = np.array(values)
    valid_indices = ~np.isnan(values_array)
    
    if np.sum(valid_indices) < 2:
        return
    
    clean_values = values_array[valid_indices]
    clean_timestamps = [timestamps[i] for i, valid in enumerate(valid_indices) if valid]
    
    # Convert timestamps to numeric (days since epoch for matplotlib)
    x_numeric = np.array([(t - datetime(1970, 1, 1)).total_seconds() / (24*3600) for t in clean_timestamps])
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, clean_values)
    
    # Create points for line
    x_line = np.array([min(x_numeric), max(x_numeric)])
    y_line = slope * x_line + intercept
    
    # Convert back to datetime for plotting
    x_dates = [datetime(1970, 1, 1) + timedelta(days=x) for x in x_line]
    
    # Add trend line to plot
    ax.plot(x_dates, y_line, color=color, linestyle=line_style, alpha=alpha, 
            label=f'Trend (r²={r_value**2:.2f})')
    
    # Add text for trend information
    if p_value < 0.05:
        trend_text = f"Trend: {'↑' if slope > 0 else '↓'} ({p_value:.3f})"
    else:
        trend_text = "No significant trend"
    
    # Add text annotation for trend information
    ax.text(0.05, 0.95, trend_text, transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

def compare_days_data(csv_file, date_strings, column_index=1, data_name="Conductivity"):
    """
    เปรียบเทียบข้อมูลจากหลายวันที่กำหนด
    
    Parameters:
    -----------
    csv_file : str
        ที่อยู่ของไฟล์ CSV
    date_strings : list
        รายการวันที่ที่ต้องการเปรียบเทียบในรูปแบบ 'YYYY-MM-DD'
    column_index : int
        ลำดับคอลัมน์ที่ต้องการวิเคราะห์ (1 สำหรับค่าการนำไฟฟ้า, 3 สำหรับอุณหภูมิ)
    data_name : str
        ชื่อของข้อมูลที่วิเคราะห์ (Conductivity หรือ Temperature)
        
    Returns:
    --------
    dict
        พจนานุกรมที่มีข้อมูลแยกตามวันที่
    """
    result = {}
    
    try:
        # อ่านไฟล์ CSV ในรูปแบบ pandas DataFrame
        df = pd.read_csv(csv_file)
        
        # แปลงคอลัมน์เวลาให้เป็น datetime
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # สำหรับแต่ละวันที่ต้องการ
        for date_str in date_strings:
            # กรองข้อมูลเฉพาะวันที่ต้องการ
            day_data = df[df['Timestamp'].dt.strftime('%Y-%m-%d') == date_str]
            
            if not day_data.empty:
                # เลือกเฉพาะคอลัมน์เวลาและค่าที่ต้องการวิเคราะห์
                column_name = "Conductivity" if column_index == 1 else "Temperature"
                timestamps = day_data['Timestamp'].tolist()
                values = day_data[column_name].tolist()
                
                # คำนวณสถิติของวันนี้
                stats = calculate_advanced_statistics(values)
                
                # วิเคราะห์แนวโน้ม
                trend_info = analyze_trend(timestamps, values)
                
                # เก็บข้อมูลในผลลัพธ์
                result[date_str] = {
                    'timestamps': timestamps,
                    'values': values,
                    'statistics': stats,
                    'trend': trend_info
                }
    
    except Exception as e:
        print(f"Error comparing days: {e}")
    
    return result

def plot_comparison_graph(comparison_data, ax=None, data_name="Conductivity", show_trends=True):
    """
    สร้างกราฟเปรียบเทียบข้อมูลระหว่างวัน
    
    Parameters:
    -----------
    comparison_data : dict
        ข้อมูลเปรียบเทียบจากฟังก์ชัน compare_days_data
    ax : matplotlib.axes.Axes หรือ None
        แกนของกราฟที่จะวาดลงไป ถ้าไม่กำหนด จะสร้างใหม่
    data_name : str
        ชื่อของข้อมูล (Conductivity หรือ Temperature)
    show_trends : bool
        เปิดหรือปิดการแสดงเส้นแนวโน้ม
        
    Returns:
    --------
    tuple
        (fig, ax) คู่ของ Figure และ Axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure
    
    # รูปแบบสีและเส้นสำหรับแต่ละวัน
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    line_styles = ['-', '--', '-.', ':']
    marker_styles = ['o', 's', '^', 'D', '*']
    
    legend_items = []
    
    # เตรียม x-axis เป็นเวลาของวัน (ไม่มีวันที่)
    all_min_hour = 23
    all_max_hour = 0
    
    # สำหรับแต่ละวันที่มีข้อมูล
    for i, (date_str, data) in enumerate(comparison_data.items()):
        if 'values' not in data or not data['values']:
            continue
            
        timestamps = data['timestamps']
        values = data['values']
        
        # จัดการเวลาให้แสดงเฉพาะชั่วโมง-นาที-วินาที
        hours = []
        for ts in timestamps:
            # เก็บค่าชั่วโมงเพื่อกำหนดช่วงของกราฟ
            hour_val = ts.hour + ts.minute/60 + ts.second/3600  # แปลงเป็นเลขทศนิยม
            hours.append(hour_val)
            all_min_hour = min(all_min_hour, ts.hour)
            all_max_hour = max(all_max_hour, ts.hour)
        
        # เลือกสี เส้น และสัญลักษณ์
        color = colors[i % len(colors)]
        line_style = line_styles[(i // len(colors)) % len(line_styles)]
        marker = marker_styles[(i // (len(colors) * len(line_styles))) % len(marker_styles)]
        
        # วาดกราฟเส้นสำหรับวันนี้
        ax.plot(hours, values, 
                linestyle=line_style, marker=marker, color=color, 
                markersize=5, alpha=0.8, label=date_str)
        
        # ถ้าต้องการแสดงเส้นแนวโน้ม และมีข้อมูลแนวโน้ม
        if show_trends and 'trend' in data:
            trend = data['trend']
            if trend['trend_direction'] != 'insufficient_data' and trend['p_value'] < 0.1:
                # คำนวณเส้นแนวโน้มจากข้อมูล
                trend_x = [min(hours), max(hours)]
                x_array = np.array(hours)
                y_array = np.array(values)
                valid_indices = ~np.isnan(y_array)
                
                if np.sum(valid_indices) >= 2:
                    x_clean = x_array[valid_indices]
                    y_clean = y_array[valid_indices]
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
                    trend_y = [slope * x + intercept for x in trend_x]
                    
                    # วาดเส้นแนวโน้ม
                    ax.plot(trend_x, trend_y, 
                            linestyle='--', color=color, alpha=0.6, 
                            label=f'{date_str} Trend (r²={r_value**2:.2f})')
    
    # ตั้งค่ากราฟ
    unit = "uS/cm" if data_name == "Conductivity" else "°C"
    ax.set_xlabel('เวลา (ชั่วโมง)')
    ax.set_ylabel(f'{data_name} ({unit})')
    ax.set_title(f'เปรียบเทียบข้อมูล {data_name} ระหว่างวัน')
    ax.grid(True, alpha=0.3)
    
    # ตั้งค่าแกน x ให้แสดงชั่วโมง
    ax.set_xlim(all_min_hour - 0.5, all_max_hour + 0.5)
    
    # เพิ่มแกน x ที่เป็นชั่วโมง
    hour_ticks = list(range(all_min_hour, all_max_hour + 1))
    ax.set_xticks(hour_ticks)
    ax.set_xticklabels([f"{h:02d}:00" for h in hour_ticks])
    
    # เพิ่มเส้นตาราง
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # แสดงคำอธิบายกราฟ
    ax.legend()
    
    # จัดรูปแบบและขนาดให้เหมาะสม
    plt.tight_layout()
    
    return fig, ax

def create_comparison_report(comparison_data, data_name="Conductivity"):
    """
    สร้างรายงานการเปรียบเทียบข้อมูลในรูปแบบตาราง
    
    Parameters:
    -----------
    comparison_data : dict
        ข้อมูลเปรียบเทียบจากฟังก์ชัน compare_days_data
    data_name : str
        ชื่อของข้อมูล (Conductivity หรือ Temperature)
        
    Returns:
    --------
    pandas.DataFrame
        ตารางเปรียบเทียบสถิติระหว่างวัน
    """
    # เตรียมข้อมูลสำหรับตาราง
    data = []
    columns = ['วันที่', 'ค่าต่ำสุด', 'ค่าสูงสุด', 'ค่าเฉลี่ย', 'ค่าเบี่ยงเบนมาตรฐาน', 
               'จำนวนข้อมูล', 'แนวโน้ม']
    
    # สำหรับแต่ละวันที่มีข้อมูล
    for date_str, day_data in comparison_data.items():
        if 'statistics' not in day_data:
            continue
            
        stats = day_data['statistics']
        trend_info = day_data.get('trend', {})
        
        # กำหนดข้อความแนวโน้ม
        trend_direction = trend_info.get('trend_direction', 'insufficient_data')
        p_value = trend_info.get('p_value', 1.0)
        
        if p_value < 0.05:
            if trend_direction == 'increasing':
                trend_text = 'เพิ่มขึ้น ↑'
            elif trend_direction == 'decreasing':
                trend_text = 'ลดลง ↓'
            else:
                trend_text = 'คงที่ →'
        else:
            trend_text = 'ไม่มีแนวโน้มชัดเจน'
        
        # เพิ่มข้อมูลลงในตาราง
        data.append([
            date_str,
            f"{stats['min']:.2f}",
            f"{stats['max']:.2f}",
            f"{stats['mean']:.2f}",
            f"{stats['std']:.2f}",
            int(stats['count']),
            trend_text
        ])
    
    # สร้างตาราง DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    return df

def find_days_with_similar_patterns(csv_file, target_date_str, column_index=1, 
                                   top_n=5, method='correlation'):
    """
    ค้นหาวันที่มีรูปแบบข้อมูลคล้ายกับวันที่กำหนด
    
    Parameters:
    -----------
    csv_file : str
        ที่อยู่ของไฟล์ CSV
    target_date_str : str
        วันที่เป้าหมายที่ต้องการเปรียบเทียบ ในรูปแบบ 'YYYY-MM-DD'
    column_index : int
        ลำดับคอลัมน์ที่ต้องการวิเคราะห์ (1 สำหรับค่าการนำไฟฟ้า, 3 สำหรับอุณหภูมิ)
    top_n : int
        จำนวนวันที่คล้ายกันมากที่สุดที่จะแสดง
    method : str
        วิธีการวัดความคล้ายคลึง ('correlation', 'euclidean', 'dtw')
        
    Returns:
    --------
    list
        รายการวันที่ที่มีรูปแบบคล้ายกัน พร้อมค่าความคล้ายคลึง
    """
    similarity_scores = []
    result = []
    
    try:
        # อ่านไฟล์ CSV ในรูปแบบ pandas DataFrame
        df = pd.read_csv(csv_file)
        
        # แปลงคอลัมน์เวลาให้เป็น datetime
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # กรองข้อมูลของวันที่เป้าหมาย
        column_name = "Conductivity" if column_index == 1 else "Temperature"
        target_data = df[df['Timestamp'].dt.strftime('%Y-%m-%d') == target_date_str]
        if target_data.empty:
            return []
        
        target_values = target_data[column_name].values
        
        # หาวันที่ทั้งหมดในข้อมูล
        all_dates = df['Timestamp'].dt.strftime('%Y-%m-%d').unique().tolist()
        
        # สำหรับแต่ละวัน คำนวณความคล้าย
        for date_str in all_dates:
            if date_str == target_date_str:
                continue  # ข้ามวันที่เป้าหมาย
                
            # กรองข้อมูลของวันนี้
            day_data = df[df['Timestamp'].dt.strftime('%Y-%m-%d') == date_str]
            if day_data.empty:
                continue
                
            day_values = day_data[column_name].values
            
            # คำนวณค่าความคล้าย
            if method == 'correlation':
                # Make sure arrays are the same length for correlation
                min_len = min(len(target_values), len(day_values))
                if min_len < 2:  # Need at least 2 points for correlation
                    continue
                
                # Calculate correlation with matching sizes
                similarity = np.corrcoef(target_values[:min_len], day_values[:min_len])[0, 1]
                if np.isnan(similarity):
                    continue
                # แปลงเป็นค่าระหว่าง 0-1 (1 = คล้ายกันมาก)
                similarity = (similarity + 1) / 2
                
            elif method == 'euclidean':
                # ใช้ระยะห่างแบบยุคลิด (Euclidean distance)
                # อาจต้องจัดการกับขนาดข้อมูลที่ต่างกัน
                min_len = min(len(target_values), len(day_values))
                distance = np.sqrt(np.sum((target_values[:min_len] - day_values[:min_len])**2))
                # แปลงระยะห่างเป็นความคล้าย (น้อย = คล้ายกันมาก)
                similarity = 1 / (1 + distance)
                
            else:
                # ใช้การหาความคล้ายแบบอื่น
                continue
                
            # เก็บค่าความคล้าย
            similarity_scores.append((date_str, similarity))
        
        # เรียงลำดับตามความคล้าย (มากไปน้อย)
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # เลือก top_n วันที่คล้ายกันมากที่สุด
        result = similarity_scores[:top_n]
        
    except Exception as e:
        print(f"Error finding similar days: {e}")
    
    return result
