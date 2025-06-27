"""
Data Manager Module - ระบบจัดการไฟล์ข้อมูลแบบเรียบง่าย
สำหรับบันทึกข้อมูลการวัดค่าการนำไฟฟ้า โดยเก็บข้อมูลในโฟลเดอร์โปรเจคเท่านั้น

ฟังก์ชันหลัก:
- save_data: บันทึกข้อมูลลงไฟล์ CSV
- init_data_files: ตรวจสอบและเตรียมไฟล์ข้อมูลตามโหมดการทำงาน
- generate_mock_data: สร้างข้อมูลจำลอง
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

# Constants
HEADER_ROW = ['Timestamp', 'Conductivity', 'Unit', 'Temperature']
REAL_DATA_FILE = "collect_data_sension.csv"
MOCK_DATA_FILE = "sension7_data.csv"

# Mock data constants
MIN_MOCK_VALUE = 100.0
MAX_MOCK_VALUE = 500.0
MIN_MOCK_TEMP = 100.0 
MAX_MOCK_TEMP = 200.0
SPIKE_PROBABILITY = 0.05

def get_project_dir():
    """คืนค่าพาธของโฟลเดอร์โปรเจค"""
    return os.path.dirname(os.path.abspath(__file__))

def get_data_file_path(mock_mode=None):
    """คืนค่าพาธของไฟล์ CSV ตามโหมดการทำงาน
    
    Args:
        mock_mode: ถ้าระบุ ใช้ค่าที่ให้มา ถ้าไม่ระบุ ใช้ค่าจาก config
        
    Returns:
        str: พาธเต็มของไฟล์ CSV
    """
    # ตรวจสอบโหมดการทำงาน
    if mock_mode is None:
        config = get_config()
        mock_mode = config.get('device', 'mock_data', fallback=True)
    
    # เลือกชื่อไฟล์ตามโหมด
    filename = MOCK_DATA_FILE if mock_mode else REAL_DATA_FILE
    
    # สร้างพาธเต็ม
    return os.path.join(get_project_dir(), filename)

def save_data(timestamp, conductivity, unit, temperature):
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
        filepath = get_data_file_path()
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
            
            # พยายามบันทึกลงในไฟล์ฉุกเฉินอื่น
            try:
                emergency_filepath = os.path.join(os.path.expanduser("~"), f"condensate_emergency_{int(time.time())}.csv")
                
                with open(emergency_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(HEADER_ROW)
                    writer.writerow(data_row)
                
                logging.warning(f"บันทึกข้อมูลในไฟล์ฉุกเฉิน: {emergency_filepath}")
                return True
            except:
                return False
    
    return success

def create_new_data_file(filepath):
    """สร้างไฟล์ข้อมูลใหม่พร้อมเฮดเดอร์
    
    Args:
        filepath: พาธไฟล์ที่ต้องการสร้าง
        
    Returns:
        bool: True ถ้าสร้างสำเร็จ, filepath ที่ใช้จริง
    """
    original_filepath = filepath
    
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"สร้างโฟลเดอร์: {directory}")
        except Exception as e:
            logging.error(f"ไม่สามารถสร้างโฟลเดอร์: {e}")
            # ใช้โฟลเดอร์ชั่วคราวแทน
            filepath = os.path.join(tempfile.gettempdir(), os.path.basename(filepath))
            logging.warning(f"ใช้ไฟล์ในโฟลเดอร์ชั่วคราวแทน: {filepath}")
    
    # พยายามสำรองข้อมูลเดิม (ถ้ามี)
    if os.path.exists(filepath):
        try:
            backup_file = f"{filepath}.bak"
            shutil.copy2(filepath, backup_file)
            logging.info(f"สำรองข้อมูลเดิมไว้ที่: {backup_file}")
        except Exception as e:
            logging.warning(f"ไม่สามารถสำรองข้อมูลเดิม: {e}")
        
        # ลบไฟล์เดิมถ้ามี
        try:
            os.remove(filepath)
            logging.info(f"ลบไฟล์เดิม: {filepath}")
        except (PermissionError, OSError) as e:
            logging.warning(f"ไม่สามารถลบไฟล์เดิม {filepath}: {e}")
            # ถ้าลบไม่ได้ ให้ใช้ชื่อไฟล์ใหม่
            filename = f"{os.path.splitext(os.path.basename(filepath))[0]}_{int(time.time())}.csv"
            filepath = os.path.join(os.path.dirname(filepath), filename)
            logging.warning(f"ใช้ชื่อไฟล์ใหม่แทน: {filepath}")
    
    # สร้างไฟล์ใหม่พร้อมเฮดเดอร์
    try:
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(HEADER_ROW)
        logging.info(f"สร้างไฟล์ข้อมูลใหม่: {filepath}")
        return True
    except (PermissionError, OSError, IOError) as e:
        logging.error(f"ไม่สามารถสร้างไฟล์ข้อมูลใหม่ {filepath}: {e}")
        
        # ลองสร้างในโฟลเดอร์ชั่วคราว
        try:
            temp_filepath = os.path.join(tempfile.gettempdir(), 
                                        f"condensate_data_{int(time.time())}.csv")
            with open(temp_filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(HEADER_ROW)
            logging.warning(f"สร้างไฟล์ข้อมูลในโฟลเดอร์ชั่วคราว: {temp_filepath}")
            
            # ถ้าสามารถสร้างในโฟลเดอร์ชั่วคราวได้ ให้ใช้ไฟล์นั้นแทน
            if original_filepath != filepath:
                # ตรวจสอบว่าเราได้เปลี่ยนไฟล์ไปแล้ว
                return True
            return True
        except Exception as temp_e:
            logging.error(f"ไม่สามารถสร้างไฟล์ในโฟลเดอร์ชั่วคราว: {temp_e}")
            return False

def init_data_files():
    """เตรียมไฟล์ข้อมูลตามโหมดการทำงาน
    
    Returns:
        bool: True ถ้าเตรียมสำเร็จ
    """
    success = True
    
    # สร้างโฟลเดอร์โปรเจค
    project_dir = get_project_dir()
    try:
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)
            logging.info(f"สร้างโฟลเดอร์โปรเจค: {project_dir}")
    except Exception as e:
        logging.error(f"ไม่สามารถสร้างโฟลเดอร์โปรเจค: {e}")
        # เราจะดำเนินการต่อและใช้ไฟล์ชั่วคราวแทน

    # อ่านโหมดจากการตั้งค่า
    config = get_config()
    mock_mode = config.get('device', 'mock_data', fallback=True)
    
    # กำหนดพาธของไฟล์
    mock_file = get_data_file_path(mock_mode=True)
    real_file = get_data_file_path(mock_mode=False)
    
    # แสดงข้อความโหมดการทำงาน
    mode_text = "จำลอง (MOCK)" if mock_mode else "จริง (REAL)"
    logging.info(f"เริ่มต้นในโหมด: {mode_text}")
    
    # เตรียมไฟล์ตามโหมด
    if mock_mode:
        # โหมดจำลอง: เตรียมไฟล์จำลอง
        try:
            if not os.path.exists(mock_file) or os.path.getsize(mock_file) == 0:
                create_success = create_new_data_file(mock_file)
                if create_success:
                    generate_mock_data()
                    logging.info(f"สร้างไฟล์จำลองและข้อมูลสำเร็จ")
                else:
                    logging.warning(f"ไม่สามารถสร้างไฟล์จำลอง จะใช้ไฟล์ชั่วคราวแทน")
                    success = False
            logging.info(f"ใช้ไฟล์จำลอง: {mock_file}")
            
            # ไม่ลบไฟล์จริง เพื่อเก็บข้อมูล
            if os.path.exists(real_file):
                logging.info(f"พบไฟล์ข้อมูลจริง (จะไม่ถูกลบ): {real_file}")
        except Exception as mock_e:
            logging.error(f"เกิดข้อผิดพลาดในการเตรียมโหมดจำลอง: {mock_e}")
            success = False
    else:
        # โหมดจริง: ลบไฟล์จำลองและเตรียมไฟล์จริง
        try:
            if os.path.exists(mock_file):
                try:
                    os.remove(mock_file)
                    logging.info(f"ลบไฟล์จำลอง: {mock_file}")
                except (PermissionError, OSError) as e:
                    logging.warning(f"ไม่สามารถลบไฟล์จำลอง: {e}")
                    # ไม่ถือว่าเป็นข้อผิดพลาดร้ายแรง ดำเนินการต่อ
            
            # เตรียมไฟล์จริง
            if not os.path.exists(real_file):
                create_success = create_new_data_file(real_file)
                if not create_success:
                    logging.warning(f"ไม่สามารถสร้างไฟล์ข้อมูลจริง จะใช้ไฟล์ชั่วคราวแทน")
                    success = False
            logging.info(f"ใช้ไฟล์ข้อมูลจริง: {real_file}")
        except Exception as real_e:
            logging.error(f"เกิดข้อผิดพลาดในการเตรียมโหมดจริง: {real_e}")
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
        data_rows.append([
            current_time.strftime('%Y-%m-%d %H:%M:%S'),
            base_value,
            unit,
            temperature
        ])
    
    # พยายามบันทึกข้อมูลลงไฟล์
    try:
        # กำหนดพาธของไฟล์จำลอง
        filepath = get_data_file_path(mock_mode=True)
        
        # ตรวจสอบและสร้างไฟล์หากยังไม่มี
        prepare_file_success = False
        
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            try:
                # พยายามสร้างไฟล์ใหม่พร้อมเฮดเดอร์
                directory = os.path.dirname(filepath)
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(HEADER_ROW)
                prepare_file_success = True
                logging.info(f"สร้างไฟล์ข้อมูลจำลองใหม่: {filepath}")
            except (PermissionError, OSError, IOError) as e:
                logging.error(f"ไม่สามารถสร้างไฟล์ข้อมูลจำลอง {filepath}: {e}")
                # ใช้ไฟล์ชั่วคราวแทน
                filepath = os.path.join(tempfile.gettempdir(), f"mock_data_{int(time.time())}.csv")
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(HEADER_ROW)
                prepare_file_success = True
                logging.warning(f"ใช้ไฟล์ชั่วคราวแทน: {filepath}")
        else:
            prepare_file_success = True
        
        if prepare_file_success:
            # บันทึกข้อมูล
            with open(filepath, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for row in data_rows:
                    writer.writerow(row)
                    
            logging.info(f"สร้างข้อมูลจำลองสำเร็จ {len(data_rows)} จุด")
            return True
        else:
            logging.error("ไม่สามารถเตรียมไฟล์สำหรับบันทึกข้อมูลจำลอง")
            return False
            
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการสร้างข้อมูลจำลอง: {e}")
        
        # พยายามใช้ไฟล์ชั่วคราว
        try:
            temp_filepath = os.path.join(tempfile.gettempdir(), f"emergency_mock_data_{int(time.time())}.csv")
            with open(temp_filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(HEADER_ROW)
                for row in data_rows:
                    writer.writerow(row)
            logging.warning(f"บันทึกข้อมูลจำลองฉุกเฉิน: {temp_filepath}")
            return True
        except Exception as temp_e:
            logging.error(f"ไม่สามารถบันทึกข้อมูลจำลองฉุกเฉิน: {temp_e}")
            return False

def clean_backup_files():
    """ลบไฟล์สำรองที่ไม่จำเป็น"""
    project_dir = get_project_dir()
    backup_extensions = ['.bak', '.old', '.tmp', '.backup']
    
    try:
        for filename in os.listdir(project_dir):
            for ext in backup_extensions:
                if filename.endswith(ext):
                    filepath = os.path.join(project_dir, filename)
                    try:
                        os.remove(filepath)
                        logging.info(f"ลบไฟล์สำรอง: {filepath}")
                    except Exception as e:
                        logging.error(f"ไม่สามารถลบไฟล์สำรอง {filepath}: {e}")
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดในการทำความสะอาดไฟล์สำรอง: {e}")

def verify_data_file(filepath):
    """ตรวจสอบความถูกต้องของไฟล์ข้อมูล
    
    Args:
        filepath: พาธของไฟล์ที่ต้องการตรวจสอบ
        
    Returns:
        bool: True ถ้าไฟล์ถูกต้อง False ถ้าไม่ถูกต้องหรือไม่มีไฟล์
    """
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', newline='') as csvfile:
            # ตรวจสอบเฮดเดอร์
            reader = csv.reader(csvfile)
            header = next(reader, None)
            
            if not header or 'Timestamp' not in header:
                return False
                
            # ตรวจสอบว่ามีข้อมูลหรือไม่
            try:
                row = next(reader, None)
                if not row:  # ไม่มีข้อมูล (มีแต่เฮดเดอร์)
                    return True  # ถือว่าถูกต้อง แค่ยังไม่มีข้อมูล
            except:
                pass  # อาจจะมีแค่เฮดเดอร์ ถือว่าใช้ได้
            
            return True
    except:
        return False

if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)
    init_data_files()
    now = datetime.now()
    save_data(now, 123.45, "µS/cm", 25.0)
    print("บันทึกข้อมูลทดสอบเสร็จสิ้น")
