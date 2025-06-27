"""
ไฟล์นี้ใช้สำหรับตรวจสอบปัญหา Bad file descriptor โดยเฉพาะ
"""

import os
import sys
import csv
import time
from datetime import datetime
import tempfile
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def test_file_access():
    # 1. ตรวจสอบโฟลเดอร์โปรเจค
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"โฟลเดอร์โปรเจค: {project_dir}")
    print(f"มีอยู่: {os.path.exists(project_dir)}")
    print(f"เขียนได้: {os.access(project_dir, os.W_OK)}")
    
    # 2. ทดลองสร้างไฟล์ CSV และเขียนข้อมูลจำนวนมาก
    csv_file = os.path.join(project_dir, "test_file_descr.csv")
    
    # สร้างไฟล์ CSV
    print("\nสร้างไฟล์ CSV...")
    header = ['Timestamp', 'Value1', 'Value2', 'Value3']
    
    try:
        # สร้างไฟล์พร้อมเขียน header
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
        print(f"✓ สร้างไฟล์สำเร็จ: {csv_file}")

        # เขียนข้อมูล 5 รอบเพื่อทดสอบ
        for i in range(5):
            now = datetime.now()
            row = [now.strftime('%Y-%m-%d %H:%M:%S'), i * 10, i * 20, i * 30]
            
            # เปิดไฟล์ในโหมดเพิ่มข้อมูล
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            print(f"✓ บันทึกข้อมูลรอบที่ {i+1} สำเร็จ")
            time.sleep(0.5)
            
        # อ่านไฟล์เพื่อตรวจสอบ
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            print(f"\nอ่านข้อมูล {len(rows)} แถว:")
            for row in rows:
                print(row)
                
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาด: {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"ประเภทข้อผิดพลาด: {exc_type.__name__}")
        print(f"บรรทัด: {exc_tb.tb_lineno}")
    
    # 3. ตรวจสอบโฟลเดอร์ชั่วคราว
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, f"test_descriptor_{int(time.time())}.csv")
    
    print(f"\nทดลองใช้ไฟล์ในโฟลเดอร์ชั่วคราว: {temp_file}")
    try:
        # สร้างไฟล์ชั่วคราว
        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 100, 200, 300])
        print(f"✓ สร้างไฟล์ชั่วคราวสำเร็จ")
        
        # อ่านไฟล์ชั่วคราว
        with open(temp_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            print(f"อ่านข้อมูลจากไฟล์ชั่วคราว {len(rows)} แถว:")
            for row in rows:
                print(row)
        
        # ลบไฟล์ชั่วคราว
        os.remove(temp_file)
        print(f"✓ ลบไฟล์ชั่วคราวสำเร็จ")
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาดกับไฟล์ชั่วคราว: {e}")

if __name__ == "__main__":
    test_file_access()
