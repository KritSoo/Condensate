"""
Database Manager Module - ระบบจัดการฐานข้อมูล MySQL
สำหรับบันทึกข้อมูลการวัดค่าการนำไฟฟ้า

ฟังก์ชันหลัก:
- save_data: บันทึกข้อมูลลงฐานข้อมูล
- init_database: ตรวจสอบและเตรียมฐานข้อมูลตามโหมดการทำงาน
- generate_mock_data: สร้างข้อมูลจำลอง
"""

import os
import time
import tempfile
from datetime import datetime, timedelta
import random
import logging
import pymysql
import configparser
from config_manager import get_config

# Constants
CONFIG_FILE = "database_config.ini"
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "conductivity_data"
}

# Tables
REAL_DATA_TABLE = "collect_data_sension"
MOCK_DATA_TABLE = "sension7_data"

# Mock data constants
MIN_MOCK_VALUE = 100.0
MAX_MOCK_VALUE = 500.0
MIN_MOCK_TEMP = 100.0 
MAX_MOCK_TEMP = 200.0
SPIKE_PROBABILITY = 0.05

def get_project_dir():
    """คืนค่าพาธของโฟลเดอร์โปรเจค"""
    return os.path.dirname(os.path.abspath(__file__))

def get_db_config():
    """อ่านค่า configuration สำหรับฐานข้อมูล
    
    Returns:
        dict: ข้อมูล configuration สำหรับการเชื่อมต่อฐานข้อมูล
    """
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

def get_connection():
    """สร้าง connection สำหรับฐานข้อมูล MySQL
    
    Returns:
        pymysql.Connection: Object การเชื่อมต่อกับฐานข้อมูล
    """
    db_config = get_db_config()
    try:
        print(f"กำลังเชื่อมต่อกับฐานข้อมูล: {db_config['host']}:{db_config['port']}, database: {db_config['database']}")
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            connect_timeout=5
        )
        return connection
    except pymysql.Error as e:
        logging.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับฐานข้อมูล: {e}")
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับฐานข้อมูล: {e}")
        
        # ในกรณีที่ฐานข้อมูลยังไม่ถูกสร้าง ให้พยายามสร้าง
        if e.args[0] == 1049:  # 1049 คือรหัสข้อผิดพลาด "Unknown database"
            try:
                # สร้าง connection ใหม่โดยไม่ระบุฐานข้อมูล
                temp_connection = pymysql.connect(
                    host=db_config['host'],
                    port=db_config['port'],
                    user=db_config['user'],
                    password=db_config['password']
                )
                
                # สร้างฐานข้อมูล
                with temp_connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE {db_config['database']}")
                temp_connection.close()
                
                # ลองเชื่อมต่ออีกครั้ง
                return pymysql.connect(
                    host=db_config['host'],
                    port=db_config['port'],
                    user=db_config['user'],
                    password=db_config['password'],
                    database=db_config['database']
                )
            except pymysql.Error as create_e:
                logging.error(f"ไม่สามารถสร้างฐานข้อมูลใหม่: {create_e}")
                return None
        return None

def get_data_table_name(mock_mode=None):
    """คืนค่าชื่อตารางตามโหมดการทำงาน
    
    Args:
        mock_mode: ถ้าระบุ ใช้ค่าที่ให้มา ถ้าไม่ระบุ ใช้ค่าจาก config
        
    Returns:
        str: ชื่อตาราง
    """
    # ตรวจสอบโหมดการทำงาน
    if mock_mode is None:
        config = get_config()
        mock_mode = config.get('device', 'mock_data', fallback=True)
    
    # เลือกชื่อตารางตามโหมด
    return MOCK_DATA_TABLE if mock_mode else REAL_DATA_TABLE

def create_table(connection, table_name):
    """สร้างตารางเก็บข้อมูลถ้ายังไม่มี
    
    Args:
        connection: pymysql.Connection object
        table_name: ชื่อตารางที่ต้องการสร้าง
        
    Returns:
        bool: True ถ้าสร้างสำเร็จหรือตารางมีอยู่แล้ว, False ถ้าล้มเหลว
    """
    try:
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
            logging.info(f"ตรวจสอบ/สร้างตาราง {table_name} สำเร็จ")
            return True
    except pymysql.Error as e:
        logging.error(f"ไม่สามารถสร้างตาราง {table_name}: {e}")
        return False

def save_data(timestamp, conductivity, unit, temperature):
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
    table_name = get_data_table_name()
    
    success = False
    
    try:
        # สร้างการเชื่อมต่อกับฐานข้อมูล
        connection = get_connection()
        if not connection:
            logging.error("ไม่สามารถเชื่อมต่อกับฐานข้อมูลเพื่อบันทึกข้อมูล")
            return False
        
        # ตรวจสอบว่าตารางมีอยู่หรือไม่ ถ้าไม่มีให้สร้าง
        create_table(connection, table_name)
            
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
    
    except pymysql.Error as e:
        logging.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลลงฐานข้อมูล: {e}")
        success = False
    
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
        success = False
    
    return success

def init_database():
    """เตรียมฐานข้อมูลตามโหมดการทำงาน
    
    Returns:
        bool: True ถ้าเตรียมสำเร็จ
    """
    success = True
    
    # อ่านโหมดจากการตั้งค่า
    config = get_config()
    mock_mode = config.get('device', 'mock_data', fallback=True)
    
    # กำหนดชื่อตาราง
    mock_table = get_data_table_name(mock_mode=True)
    real_table = get_data_table_name(mock_mode=False)
    
    # แสดงข้อความโหมดการทำงาน
    mode_text = "จำลอง (MOCK)" if mock_mode else "จริง (REAL)"
    logging.info(f"เริ่มต้นฐานข้อมูลในโหมด: {mode_text}")
    
    try:
        # สร้างการเชื่อมต่อกับฐานข้อมูล
        connection = get_connection()
        if not connection:
            logging.error("ไม่สามารถเชื่อมต่อกับฐานข้อมูล")
            return False
            
        # ตรวจสอบและสร้างตาราง
        if mock_mode:
            # โหมดจำลอง: เตรียมตารางข้อมูลจำลอง
            if create_table(connection, mock_table):
                # ตรวจสอบว่ามีข้อมูลในตารางหรือไม่
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {mock_table}")
                    count = cursor.fetchone()[0]
                    
                # ถ้าไม่มีข้อมูล ให้สร้างข้อมูลจำลอง
                if count == 0:
                    generate_mock_data()
                    logging.info(f"สร้างข้อมูลจำลองสำเร็จ")
            else:
                logging.error(f"ไม่สามารถสร้างตารางข้อมูลจำลอง")
                success = False
        else:
            # โหมดจริง: เตรียมตารางข้อมูลจริง
            if not create_table(connection, real_table):
                logging.error(f"ไม่สามารถสร้างตารางข้อมูลจริง")
                success = False
        
        # ปิดการเชื่อมต่อ
        connection.close()
        
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการเตรียมฐานข้อมูล: {e}")
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
        
        # เก็บข้อมูลในลิสต์
        data_rows.append({
            "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "conductivity": base_value,
            "unit": unit,
            "temperature": temperature
        })
    
    # พยายามบันทึกข้อมูลลงฐานข้อมูล
    try:
        connection = get_connection()
        if not connection:
            logging.error("ไม่สามารถเชื่อมต่อกับฐานข้อมูลเพื่อสร้างข้อมูลจำลอง")
            return False

        # เลือกตารางตามโหมด
        table_name = get_data_table_name(mock_mode=True)
        
        # ตรวจสอบว่าตารางมีอยู่หรือไม่ ถ้าไม่มีให้สร้าง
        create_table(connection, table_name)
                
        # บันทึกข้อมูล
        with connection.cursor() as cursor:
            sql = f"""
            INSERT INTO {table_name} (timestamp, conductivity, unit, temperature)
            VALUES (%s, %s, %s, %s)
            """
            for row in data_rows:
                cursor.execute(sql, (
                    row["timestamp"], 
                    row["conductivity"], 
                    row["unit"], 
                    row["temperature"]
                ))
            connection.commit()
                    
        logging.info(f"สร้างข้อมูลจำลองสำเร็จ {len(data_rows)} จุด")
        
        # ปิดการเชื่อมต่อ
        connection.close()
        return True
            
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการสร้างข้อมูลจำลอง: {e}")
        return False

def fetch_data_for_date(date_str, mock_mode=None):
    """ดึงข้อมูลสำหรับวันที่ระบุ
    
    Args:
        date_str: วันที่ต้องการดึงข้อมูลในรูปแบบ 'YYYY-MM-DD'
        mock_mode: โหมดการทำงาน (จำลอง/จริง) ถ้าไม่ระบุ ใช้ค่าจาก config
        
    Returns:
        list: รายการข้อมูลสำหรับวันที่ระบุ, None ถ้าเกิดข้อผิดพลาด
    """
    try:
        # เลือกตารางตามโหมด
        table_name = get_data_table_name(mock_mode)
        
        # เชื่อมต่อกับฐานข้อมูล
        connection = get_connection()
        if not connection:
            logging.error("ไม่สามารถเชื่อมต่อกับฐานข้อมูลเพื่อดึงข้อมูล")
            return None
        
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
        
        # แปลงข้อมูลเป็นรายการ dictionary
        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "conductivity": row[1],
                "unit": row[2],
                "temperature": row[3]
            })
        
        # ปิดการเชื่อมต่อ
        connection.close()
        
        return result
        
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return None

def fetch_data_range(start_date, end_date, mock_mode=None):
    """ดึงข้อมูลในช่วงวันที่ระบุ
    
    Args:
        start_date: วันที่เริ่มต้นในรูปแบบ 'YYYY-MM-DD'
        end_date: วันที่สิ้นสุดในรูปแบบ 'YYYY-MM-DD'
        mock_mode: โหมดการทำงาน (จำลอง/จริง) ถ้าไม่ระบุ ใช้ค่าจาก config
        
    Returns:
        list: รายการข้อมูลในช่วงวันที่ระบุ, None ถ้าเกิดข้อผิดพลาด
    """
    try:
        # เลือกตารางตามโหมด
        table_name = get_data_table_name(mock_mode)
        
        # เชื่อมต่อกับฐานข้อมูล
        connection = get_connection()
        if not connection:
            logging.error("ไม่สามารถเชื่อมต่อกับฐานข้อมูลเพื่อดึงข้อมูล")
            return None
        
        # ดึงข้อมูล
        with connection.cursor() as cursor:
            sql = f"""
            SELECT timestamp, conductivity, unit, temperature
            FROM {table_name}
            WHERE DATE(timestamp) BETWEEN %s AND %s
            ORDER BY timestamp ASC
            """
            cursor.execute(sql, (start_date, end_date))
            rows = cursor.fetchall()
        
        # แปลงข้อมูลเป็นรายการ dictionary
        result = []
        for row in rows:
            result.append({
                "timestamp": row[0],
                "conductivity": row[1],
                "unit": row[2],
                "temperature": row[3]
            })
        
        # ปิดการเชื่อมต่อ
        connection.close()
        
        return result
        
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return None

if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)
    init_database()
    now = datetime.now()
    save_data(now, 123.45, "µS/cm", 25.0)
    print("บันทึกข้อมูลทดสอบเสร็จสิ้น")
