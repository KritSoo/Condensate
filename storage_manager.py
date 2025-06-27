"""
ปรับปรุงโค้ดให้สามารถทำงานได้โดยไม่ต้องเชื่อมต่อกับฐานข้อมูล MySQL
โดยจะกลับไปใช้ระบบไฟล์แบบเดิมถ้าไม่สามารถเชื่อมต่อกับฐานข้อมูลได้
"""

import os
import csv
import time
import tempfile
from datetime import datetime, timedelta
import random
import shutil
from config_manager import get_config
import logging
import traceback

# ลองนำเข้าโมดูล pymysql ถ้าติดตั้งแล้ว
try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

# Constants
HEADER_ROW = ['Timestamp', 'Conductivity', 'Unit', 'Temperature']
REAL_DATA_FILE = "collect_data_sension.csv"
MOCK_DATA_FILE = "sension7_data.csv"
CONFIG_FILE = "database_config.ini"

# Mock data constants
MIN_MOCK_VALUE = 100.0
MAX_MOCK_VALUE = 500.0
MIN_MOCK_TEMP = 100.0 
MAX_MOCK_TEMP = 200.0
SPIKE_PROBABILITY = 0.05

# สถานะการเชื่อมต่อกับฐานข้อมูล
DB_CONNECTION_AVAILABLE = False

def get_project_dir():
    """คืนค่าพาธของโฟลเดอร์โปรเจค"""
    return os.path.dirname(os.path.abspath(__file__))

def test_db_connection():
    """ทดสอบการเชื่อมต่อกับฐานข้อมูล
    
    Returns:
        bool: True ถ้าสามารถเชื่อมต่อกับฐานข้อมูลได้, False ถ้าไม่สามารถเชื่อมต่อได้
    """
    global DB_CONNECTION_AVAILABLE
    
    # ถ้าไม่มี pymysql ไม่ต้องทดสอบ
    if not HAS_MYSQL:
        print("ไม่พบโมดูล pymysql กรุณาติดตั้งโดยใช้คำสั่ง: pip install pymysql")
        DB_CONNECTION_AVAILABLE = False
        return False
    
    try:
        # ลองเชื่อมต่อกับฐานข้อมูล
        db_config = get_db_config()
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            connect_timeout=3
        )
        connection.close()
        DB_CONNECTION_AVAILABLE = True
        return True
    except Exception as e:
        print(f"ไม่สามารถเชื่อมต่อกับฐานข้อมูล MySQL ได้: {e}")
        DB_CONNECTION_AVAILABLE = False
        return False

def get_db_config():
    """อ่านค่า configuration สำหรับฐานข้อมูล
    
    Returns:
        dict: ข้อมูล configuration สำหรับการเชื่อมต่อฐานข้อมูล
    """
    import configparser
    
    # ค่า default
    DEFAULT_DB_CONFIG = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "conductivity_data"
    }
    
    config_path = os.path.join(get_project_dir(), CONFIG_FILE)
    config = configparser.ConfigParser()
    
    # ถ้าไม่มีไฟล์ config ให้สร้างไฟล์ใหม่ด้วยค่าเริ่มต้น
    if not os.path.exists(config_path):
        config['database'] = DEFAULT_DB_CONFIG
        try:
            with open(config_path, 'w') as f:
                config.write(f)
            logging.info(f"สร้างไฟล์ config ฐานข้อมูลใหม่: {config_path}")
        except Exception as e:
            logging.error(f"ไม่สามารถสร้างไฟล์ config ฐานข้อมูล: {e}")
    else:
        try:
            config.read(config_path)
        except Exception as e:
            logging.error(f"ไม่สามารถอ่านไฟล์ config ฐานข้อมูล: {e}")
    
    # ตรวจสอบว่ามีส่วน database หรือไม่ ถ้าไม่มีให้ใช้ค่าเริ่มต้น
    if 'database' not in config:
        config['database'] = DEFAULT_DB_CONFIG
    
    return {
        'host': config.get('database', 'host', fallback=DEFAULT_DB_CONFIG['host']),
        'port': config.getint('database', 'port', fallback=DEFAULT_DB_CONFIG['port']),
        'user': config.get('database', 'user', fallback=DEFAULT_DB_CONFIG['user']),
        'password': config.get('database', 'password', fallback=DEFAULT_DB_CONFIG['password']),
        'database': config.get('database', 'database', fallback=DEFAULT_DB_CONFIG['database'])
    }

def get_data_path(mock_mode=None):
    """คืนค่าพาธของไฟล์ CSV หรือชื่อตารางตามโหมดการทำงาน
    
    Args:
        mock_mode: ถ้าระบุ ใช้ค่าที่ให้มา ถ้าไม่ระบุ ใช้ค่าจาก config
        
    Returns:
        str: พาธเต็มของไฟล์ CSV หรือชื่อตาราง
    """
    # ตรวจสอบโหมดการทำงาน
    if mock_mode is None:
        config = get_config()
        mock_mode = config.get('device', 'mock_data', fallback=True)
    
    # เลือกชื่อไฟล์หรือตารางตามโหมด
    name = MOCK_DATA_FILE if mock_mode else REAL_DATA_FILE
    
    # ถ้าใช้ฐานข้อมูล ให้ตัดนามสกุล .csv ออก
    if DB_CONNECTION_AVAILABLE:
        return os.path.splitext(name)[0]  # ชื่อตารางไม่มี .csv
    
    # ถ้าใช้ไฟล์ ให้สร้างพาธเต็ม
    return os.path.join(get_project_dir(), name)

def db_save_data(timestamp, conductivity, unit, temperature):
    """บันทึกข้อมูลลงฐานข้อมูล MySQL
    
    Args:
        timestamp: เวลาที่บันทึกข้อมูล (datetime object)
        conductivity: ค่าการนำไฟฟ้า
        unit: หน่วยของค่าการนำไฟฟ้า
        temperature: อุณหภูมิ
        
    Returns:
        bool: True ถ้าบันทึกสำเร็จ False ถ้าล้มเหลว
    """
    # เตรียมข้อมูลสำหรับบันทึก
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    # เลือกตารางตามโหมดการทำงาน
    table_name = get_data_path()
    
    success = False
    
    try:
        # สร้างการเชื่อมต่อกับฐานข้อมูล
        db_config = get_db_config()
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        
        # ตรวจสอบว่าตารางมีอยู่หรือไม่ ถ้าไม่มีให้สร้าง
        with connection.cursor() as cursor:
            # สร้างตาราง
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                conductivity FLOAT NOT NULL,
                unit VARCHAR(10) NOT NULL,
                temperature FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_sql)
            connection.commit()
            
        # บันทึกข้อมูล
        with connection.cursor() as cursor:
            sql = f"""
            INSERT INTO {table_name} (timestamp, conductivity, unit, temperature)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (timestamp_str, conductivity, unit, temperature))
            connection.commit()
        
        logging.info(f"บันทึกข้อมูลสำเร็จ: {timestamp_str}")
        success = True
        
        # ปิดการเชื่อมต่อ
        connection.close()
    
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลลงฐานข้อมูล: {e}")
        success = False
    
    return success

def file_save_data(timestamp, conductivity, unit, temperature):
    """บันทึกข้อมูลลงไฟล์ CSV แบบเรียบง่าย
    
    Args:
        timestamp: เวลาที่บันทึกข้อมูล (datetime object)
        conductivity: ค่าการนำไฟฟ้า
        unit: หน่วยของค่าการนำไฟฟ้า
        temperature: อุณหภูมิ
        
    Returns:
        bool: True ถ้าบันทึกสำเร็จ False ถ้าล้มเหลว
    """
    # เตรียมข้อมูลสำหรับบันทึก
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    data_row = [timestamp_str, conductivity, unit, temperature]
    
    success = False
    filepath = None
    
    # พยายามใช้ไฟล์ในโฟลเดอร์โปรเจค
    try:
        # กำหนดพาธของไฟล์
        filepath = get_data_path()
        directory = os.path.dirname(filepath)
        
        # สร้างโฟลเดอร์หากไม่มี
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logging.info(f"สร้างโฟลเดอร์: {directory}")
        
        # ตรวจสอบว่าไฟล์มีอยู่แล้ว และต้องสร้างใหม่หรือไม่
        create_new_file = False
        if not os.path.exists(filepath):
            create_new_file = True
        elif os.path.getsize(filepath) == 0:
            create_new_file = True
        
        # สร้างไฟล์ใหม่ถ้าจำเป็น
        if create_new_file:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(HEADER_ROW)
            logging.info(f"สร้างไฟล์ใหม่: {filepath}")
        
        # บันทึกข้อมูล
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(data_row)
        
        logging.info(f"บันทึกข้อมูลสำเร็จ: {timestamp_str}")
        success = True
    
    except (PermissionError, OSError, IOError) as file_error:
        logging.error(f"ไม่สามารถเขียนไฟล์ {filepath}: {file_error}")
        success = False
    
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
        success = False
    
    # ถ้าไม่สามารถใช้ไฟล์หลักได้ ให้ใช้ไฟล์ชั่วคราว
    if not success:
        try:
            temp_filepath = os.path.join(tempfile.gettempdir(), f"condensate_data_{int(time.time())}.csv")
            
            with open(temp_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(HEADER_ROW)
                writer.writerow(data_row)  # บันทึกข้อมูลไปเลยพร้อมกับการสร้างไฟล์
            
            logging.warning(f"บันทึกข้อมูลในไฟล์ชั่วคราวแทน: {temp_filepath}")
            return True
            
        except Exception as temp_error:
            logging.error(f"ไม่สามารถบันทึกข้อมูลในไฟล์ชั่วคราว: {temp_error}")
            return False
    
    return success

def save_data(timestamp, conductivity, unit, temperature):
    """บันทึกข้อมูลลงฐานข้อมูลหรือไฟล์ CSV (ขึ้นอยู่กับการติดตั้ง)
    
    Args:
        timestamp: เวลาที่บันทึกข้อมูล (datetime object)
        conductivity: ค่าการนำไฟฟ้า
        unit: หน่วยของค่าการนำไฟฟ้า
        temperature: อุณหภูมิ
        
    Returns:
        bool: True ถ้าบันทึกสำเร็จ False ถ้าล้มเหลว
    """
    # ใช้ฐานข้อมูลถ้าเชื่อมต่อได้ ไม่เช่นนั้นใช้ไฟล์
    if DB_CONNECTION_AVAILABLE:
        return db_save_data(timestamp, conductivity, unit, temperature)
    else:
        return file_save_data(timestamp, conductivity, unit, temperature)

def init_storage():
    """เตรียมระบบเก็บข้อมูล (ฐานข้อมูลหรือไฟล์) ตามโหมดการทำงาน
    
    Returns:
        bool: True ถ้าเตรียมสำเร็จ
    """
    success = True
    
    print("กำลังตรวจสอบการเชื่อมต่อกับฐานข้อมูล MySQL...")
    # ทดสอบการเชื่อมต่อกับฐานข้อมูล
    db_success = test_db_connection()
    if db_success:
        print("เชื่อมต่อ MySQL สำเร็จ!")
    else:
        print("ไม่สามารถเชื่อมต่อกับ MySQL ได้ จะใช้ระบบไฟล์แทน")
    
    if DB_CONNECTION_AVAILABLE:
        print("ใช้ระบบฐานข้อมูล MySQL")
        
        # อ่านโหมดจากการตั้งค่า
        config = get_config()
        mock_mode = config.get('device', 'mock_data', fallback=True)
        
        # กำหนดชื่อตาราง
        mock_table = get_data_path(mock_mode=True)
        real_table = get_data_path(mock_mode=False)
        
        # สร้างการเชื่อมต่อกับฐานข้อมูล
        try:
            db_config = get_db_config()
            connection = pymysql.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            # สร้างตาราง
            with connection.cursor() as cursor:
                for table_name in [mock_table, real_table]:
                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        conductivity FLOAT NOT NULL,
                        unit VARCHAR(10) NOT NULL,
                        temperature FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                    cursor.execute(create_sql)
                connection.commit()
            
            # ถ้าเป็นโหมดจำลอง ตรวจสอบว่ามีข้อมูลในตารางหรือไม่
            if mock_mode:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {mock_table}")
                    count = cursor.fetchone()[0]
                    
                    # ถ้าไม่มีข้อมูล สร้างข้อมูลจำลอง
                    if count == 0:
                        connection.close()
                        generate_mock_data()
            
            else:
                connection.close()
        
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการเตรียมฐานข้อมูล: {e}")
            success = False
            
    else:
        print("ไม่พบ MySQL Server ที่ทำงานอยู่ ใช้ระบบไฟล์แทน")
        
        # อ่านโหมดจากการตั้งค่า
        config = get_config()
        mock_mode = config.get('device', 'mock_data', fallback=True)
        
        # กำหนดพาธของไฟล์
        mock_file = get_data_path(mock_mode=True)
        real_file = get_data_path(mock_mode=False)
        
        # แสดงข้อความโหมดการทำงาน
        mode_text = "จำลอง (MOCK)" if mock_mode else "จริง (REAL)"
        print(f"เริ่มต้นในโหมด: {mode_text}")
        
        # เตรียมไฟล์ตามโหมด
        if mock_mode:
            # โหมดจำลอง: เตรียมไฟล์จำลอง
            try:
                if not os.path.exists(mock_file) or os.path.getsize(mock_file) == 0:
                    # สร้างไฟล์จำลอง
                    directory = os.path.dirname(mock_file)
                    if not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                    
                    # สร้างไฟล์ใหม่พร้อมเฮดเดอร์
                    with open(mock_file, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(HEADER_ROW)
                    
                    # สร้างข้อมูลจำลอง
                    generate_mock_data()
                
                print(f"ใช้ไฟล์จำลอง: {mock_file}")
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการเตรียมโหมดจำลอง: {e}")
                success = False
        else:
            # โหมดจริง: เตรียมไฟล์จริง
            try:
                # เตรียมไฟล์จริง
                if not os.path.exists(real_file):
                    # สร้างไฟล์จริง
                    directory = os.path.dirname(real_file)
                    if not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                    
                    # สร้างไฟล์ใหม่พร้อมเฮดเดอร์
                    with open(real_file, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(HEADER_ROW)
                
                print(f"ใช้ไฟล์ข้อมูลจริง: {real_file}")
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการเตรียมโหมดจริง: {e}")
                success = False
    
    return success

def generate_mock_data(num_days=7):
    """สร้างข้อมูลจำลองย้อนหลัง
    
    Args:
        num_days: จำนวนวันที่ต้องการสร้างข้อมูลย้อนหลัง
        
    Returns:
        bool: True ถ้าสร้างสำเร็จ
    """
    # สร้างข้อมูลจำลอง
    data_rows = []
    
    # กำหนดช่วงเวลา
    end_time = datetime.now()
    start_time = end_time - timedelta(days=num_days)
    current_time = start_time
    
    # สร้างข้อมูลจำลองย้อนหลัง
    while current_time < end_time:
        # สุ่มค่าพื้นฐาน
        base_value = random.uniform(MIN_MOCK_VALUE, MAX_MOCK_VALUE * 0.6)
        temperature = random.uniform(MIN_MOCK_TEMP, MAX_MOCK_TEMP)
        
        # โอกาสที่จะมีค่าพีค
        if random.random() < SPIKE_PROBABILITY:
            base_value = random.uniform(MAX_MOCK_VALUE * 0.7, MAX_MOCK_VALUE)
        
        # สุ่มหน่วย
        unit = random.choice(["uS/cm", "mS/cm"])
        
        # สุ่มเวลาถัดไป
        current_time = current_time + timedelta(
            hours=2,
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        if DB_CONNECTION_AVAILABLE:
            # บันทึกข้อมูลลงฐานข้อมูลทันที
            save_data(current_time, base_value, unit, temperature)
        else:
            # เก็บข้อมูลในลิสต์เพื่อบันทึกทีเดียว
            data_rows.append([
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                base_value,
                unit,
                temperature
            ])
    
    # ถ้าใช้ระบบไฟล์ บันทึกข้อมูลลงไฟล์
    if not DB_CONNECTION_AVAILABLE and data_rows:
        try:
            # กำหนดพาธของไฟล์จำลอง
            filepath = get_data_path(mock_mode=True)
            
            # บันทึกข้อมูล
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                for row in data_rows:
                    writer.writerow(row)
                    
            logging.info(f"สร้างข้อมูลจำลองสำเร็จ {len(data_rows)} จุด")
            return True
        except Exception as e:
            logging.error(f"เกิดข้อผิดพลาดในการสร้างข้อมูลจำลอง: {e}")
            return False
    
    return True

def fetch_data_for_date(date_str, mock_mode=None):
    """ดึงข้อมูลสำหรับวันที่ระบุ
    
    Args:
        date_str: วันที่ต้องการดึงข้อมูลในรูปแบบ 'YYYY-MM-DD'
        mock_mode: โหมดการทำงาน (จำลอง/จริง) ถ้าไม่ระบุ ใช้ค่าจาก config
        
    Returns:
        list: รายการข้อมูลสำหรับวันที่ระบุ
    """
    # ตรวจสอบโหมดการทำงาน
    if mock_mode is None:
        config = get_config()
        mock_mode = config.get('device', 'mock_data', fallback=True)
    
    # ถ้าใช้ฐานข้อมูล
    if DB_CONNECTION_AVAILABLE:
        try:
            # เลือกตารางตามโหมด
            table_name = get_data_path(mock_mode)
            
            # เชื่อมต่อกับฐานข้อมูล
            db_config = get_db_config()
            connection = pymysql.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            # ดึงข้อมูล
            with connection.cursor() as cursor:
                sql = f"""
                SELECT timestamp, conductivity, unit, temperature
                FROM {table_name}
                WHERE DATE(timestamp) = %s
                ORDER BY timestamp ASC
                """
                cursor.execute(sql, (date_str,))
                rows = cursor.fetchall()
            
            # ปิดการเชื่อมต่อ
            connection.close()
            
            # แปลงข้อมูลเป็นรายการ dictionary
            result = []
            for row in rows:
                result.append({
                    "timestamp": row[0],
                    "conductivity": row[1],
                    "unit": row[2],
                    "temperature": row[3]
                })
            
            return result
        except Exception as e:
            logging.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลจากฐานข้อมูล: {e}")
            # ถ้าการดึงข้อมูลจากฐานข้อมูลล้มเหลว ลองดึงจากไฟล์
            return fetch_data_from_file(date_str, mock_mode)
    else:
        # ถ้าไม่ใช้ฐานข้อมูล ดึงข้อมูลจากไฟล์
        return fetch_data_from_file(date_str, mock_mode)

def fetch_data_from_file(date_str, mock_mode):
    """ดึงข้อมูลจากไฟล์ CSV สำหรับวันที่ระบุ
    
    Args:
        date_str: วันที่ต้องการดึงข้อมูลในรูปแบบ 'YYYY-MM-DD'
        mock_mode: โหมดการทำงาน (จำลอง/จริง)
        
    Returns:
        list: รายการข้อมูลสำหรับวันที่ระบุ
    """
    # กำหนดพาธของไฟล์
    filepath = get_data_path(mock_mode)
    
    # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
    if not os.path.exists(filepath):
        logging.error(f"ไม่พบไฟล์ข้อมูล: {filepath}")
        return []
    
    # อ่านข้อมูลจากไฟล์
    result = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # อ่านส่วนหัว
            
            # หาตำแหน่งคอลัมน์
            timestamp_idx = headers.index('Timestamp')
            conductivity_idx = headers.index('Conductivity')
            unit_idx = headers.index('Unit')
            
            # หาตำแหน่งคอลัมน์ Temperature (อาจไม่มี)
            temperature_idx = -1
            if 'Temperature' in headers:
                temperature_idx = headers.index('Temperature')
            
            # อ่านและกรองข้อมูลตามวันที่
            for row in reader:
                if len(row) > timestamp_idx:  # ตรวจสอบว่ามีข้อมูลในคอลัมน์ timestamp
                    timestamp_str = row[timestamp_idx]
                    row_date = timestamp_str.split(' ')[0]  # แยกเฉพาะส่วนวันที่
                    
                    if row_date == date_str:
                        # สร้าง dictionary สำหรับข้อมูลในแถวนี้
                        data_point = {
                            "timestamp": timestamp_str,
                            "conductivity": float(row[conductivity_idx]),
                            "unit": row[unit_idx]
                        }
                        
                        # เพิ่มข้อมูลอุณหภูมิถ้ามี
                        if temperature_idx >= 0 and temperature_idx < len(row):
                            try:
                                data_point["temperature"] = float(row[temperature_idx])
                            except:
                                data_point["temperature"] = None
                        
                        result.append(data_point)
        
        return result
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการอ่านข้อมูลจากไฟล์: {e}")
        return []

if __name__ == "__main__":
    # ตั้งค่า logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # ทดสอบการเชื่อมต่อกับฐานข้อมูล
    print("\n===== ทดสอบระบบการบันทึกข้อมูล =====")
    print("\nกำลังตรวจสอบระบบทั้งหมด...")
    
    # ทดสอบการเชื่อมต่อกับฐานข้อมูล
    db_result = test_db_connection()
    print(f"การเชื่อมต่อฐานข้อมูล: {'✅ สำเร็จ' if db_result else '❌ ล้มเหลว'}")
    
    # เตรียมระบบเก็บข้อมูล
    init_result = init_storage()
    print(f"การเตรียมระบบเก็บข้อมูล: {'✅ สำเร็จ' if init_result else '❌ ล้มเหลว'}")
    
    # ทดสอบบันทึกข้อมูล
    now = datetime.now()
    save_result = save_data(now, 123.45, "µS/cm", 25.0)
    print(f"การบันทึกข้อมูลทดสอบ: {'✅ สำเร็จ' if save_result else '❌ ล้มเหลว'}")
    
    # ดึงข้อมูลของวันนี้เพื่อตรวจสอบ
    today_str = now.strftime('%Y-%m-%d')
    mock_data = fetch_data_for_date(today_str, mock_mode=True)
    real_data = fetch_data_for_date(today_str, mock_mode=False)
    
    print(f"\nข้อมูลจำลองของวันนี้: {len(mock_data)} รายการ")
    print(f"ข้อมูลจริงของวันนี้: {len(real_data)} รายการ")
    
    # แสดงโหมดการทำงาน
    print(f"\nโหมดการเก็บข้อมูล: {'ฐานข้อมูล MySQL' if DB_CONNECTION_AVAILABLE else 'ไฟล์ CSV'}")
    
    print("\n===== การทดสอบเสร็จสิ้น =====")
