"""
ไฟล์ทดสอบการเชื่อมต่อกับฐานข้อมูล MySQL
"""

import os
import tempfile
import logging
import time
from datetime import datetime

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)

# นำเข้าโมดูลที่เกี่ยวข้อง
from db_manager import (
    save_data, init_database, generate_mock_data, 
    get_connection, get_project_dir, get_data_table_name
)

def test_database_operations():
    """ทดสอบการทำงานกับฐานข้อมูลทั้งหมด"""
    print("\n===== ทดสอบการทำงานกับฐานข้อมูล MySQL =====")
    
    # 1. แสดงโฟลเดอร์โปรเจค (ยังคงต้องการสำหรับไฟล์ config)
    project_dir = get_project_dir()
    print(f"โฟลเดอร์โปรเจค: {project_dir}")
    print(f"มีอยู่: {'✓' if os.path.exists(project_dir) else '✗'}")
    
    # 2. ทดสอบการเชื่อมต่อกับฐานข้อมูล
    print("\nทดสอบการเชื่อมต่อกับฐานข้อมูล...")
    connection = get_connection()
    print(f"เชื่อมต่อสำเร็จ: {'✓' if connection else '✗'}")
    
    if not connection:
        print("ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้ โปรดตรวจสอบการตั้งค่า")
        print("โปรแกรมจะยุติการทำงานที่นี่...")
        return
    
    # ปิดการเชื่อมต่อ (เราจะสร้างใหม่ในแต่ละขั้นตอน)
    connection.close()
    
    # 3. เตรียมฐานข้อมูล (สร้างตาราง)
    print("\nเตรียมฐานข้อมูล...")
    init_result = init_database()
    print(f"ผลลัพธ์: {'✓ สำเร็จ' if init_result else '✗ ล้มเหลว'}")
    
    # 4. แสดงชื่อตารางข้อมูล
    mock_table = get_data_table_name(mock_mode=True)
    real_table = get_data_table_name(mock_mode=False)
    print(f"\nตารางข้อมูลจำลอง: {mock_table}")
    print(f"ตารางข้อมูลจริง: {real_table}")
    
    # ตรวจสอบว่าตารางมีอยู่จริงหรือไม่
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            # ตรวจสอบตารางข้อมูลจำลอง
            cursor.execute(f"SHOW TABLES LIKE '{mock_table}'")
            mock_exists = cursor.fetchone() is not None
            
            # ตรวจสอบตารางข้อมูลจริง
            cursor.execute(f"SHOW TABLES LIKE '{real_table}'")
            real_exists = cursor.fetchone() is not None
            
        connection.close()
        
        print(f"ตารางข้อมูลจำลองมีอยู่: {'✓' if mock_exists else '✗'}")
        print(f"ตารางข้อมูลจริงมีอยู่: {'✓' if real_exists else '✗'}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการตรวจสอบตาราง: {e}")
    
    # 5. ทดสอบบันทึกข้อมูล
    print("\nทดสอบบันทึกข้อมูลจริง...")
    now = datetime.now()
    save_result = save_data(now, 123.45, "µS/cm", 25.0)
    print(f"ผลลัพธ์: {'✓ สำเร็จ' if save_result else '✗ ล้มเหลว'}")
    
    # 6. ทดสอบสร้างข้อมูลจำลอง
    print("\nทดสอบสร้างข้อมูลจำลอง...")
    mock_result = generate_mock_data(num_days=1)
    print(f"ผลลัพธ์: {'✓ สำเร็จ' if mock_result else '✗ ล้มเหลว'}")
    
    # 7. ตรวจสอบข้อมูลในฐานข้อมูล
    print("\nตรวจสอบข้อมูลในฐานข้อมูล...")
    connection = get_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # ตรวจสอบจำนวนข้อมูลในตารางจริง
                cursor.execute(f"SELECT COUNT(*) FROM {real_table}")
                real_count = cursor.fetchone()[0]
                
                # ตรวจสอบจำนวนข้อมูลในตารางจำลอง
                cursor.execute(f"SELECT COUNT(*) FROM {mock_table}")
                mock_count = cursor.fetchone()[0]
                
            print(f"จำนวนข้อมูลจริง: {real_count} รายการ")
            print(f"จำนวนข้อมูลจำลอง: {mock_count} รายการ")
            
            connection.close()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการตรวจสอบข้อมูล: {e}")
            connection.close()
    
    print("\n===== การทดสอบเสร็จสิ้น =====")

if __name__ == "__main__":
    test_database_operations()
