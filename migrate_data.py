"""
ไฟล์นี้ใช้สำหรับย้ายข้อมูลจากไฟล์ CSV เดิมไปยังฐานข้อมูล MySQL
"""

import os
import csv
import logging
from datetime import datetime
from db_manager import save_data, init_database, get_connection, get_data_table_name

logging.basicConfig(level=logging.INFO)

def migrate_csv_to_db(csv_filepath, mock_mode=False):
    """ย้ายข้อมูลจากไฟล์ CSV ไปยังฐานข้อมูล MySQL
    
    Args:
        csv_filepath: พาธของไฟล์ CSV ที่ต้องการย้าย
        mock_mode: โหมดการทำงาน True ถ้าเป็นข้อมูลจำลอง False ถ้าเป็นข้อมูลจริง
        
    Returns:
        tuple: (bool, str) - (ผลลัพธ์, ข้อความ)
    """
    # ตรวจสอบการมีอยู่ของไฟล์
    if not os.path.exists(csv_filepath):
        return False, f"ไม่พบไฟล์ {csv_filepath}"
    
    # เตรียมฐานข้อมูล
    init_database()
    
    # เชื่อมต่อกับฐานข้อมูล
    connection = get_connection()
    if not connection:
        return False, "ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้"
    
    # แสดงชื่อตาราง
    table_name = get_data_table_name(mock_mode=mock_mode)
    print(f"กำลังย้ายข้อมูลจาก {csv_filepath} ไปยังตาราง {table_name}...")
    
    try:
        # อ่านข้อมูลจาก CSV
        imported_count = 0
        with open(csv_filepath, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # อ่านส่วนหัว
            
            # ตรวจสอบรูปแบบของไฟล์
            if 'Timestamp' not in headers:
                return False, f"รูปแบบไฟล์ไม่ถูกต้อง ไม่พบคอลัมน์ Timestamp ใน {csv_filepath}"
            
            # ค้นหาตำแหน่งคอลัมน์
            timestamp_idx = headers.index('Timestamp')
            conductivity_idx = headers.index('Conductivity')
            unit_idx = headers.index('Unit')
            
            # หาตำแหน่งคอลัมน์ Temperature (อาจไม่มี)
            temperature_idx = -1
            if 'Temperature' in headers:
                temperature_idx = headers.index('Temperature')
            
            # ตรวจสอบถ้ามีข้อมูลอยู่ในตารางแล้ว
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                existing_count = cursor.fetchone()[0]
                
                if existing_count > 0:
                    print(f"ตาราง {table_name} มีข้อมูลอยู่แล้ว {existing_count} รายการ")
                    response = input("คุณต้องการลบข้อมูลเดิมก่อนนำเข้าหรือไม่? (y/n): ")
                    
                    if response.lower() == 'y':
                        cursor.execute(f"TRUNCATE TABLE {table_name}")
                        connection.commit()
                        print(f"ลบข้อมูลเดิมในตาราง {table_name} เรียบร้อยแล้ว")
            
            # เริ่มการนำเข้าข้อมูล
            with connection.cursor() as cursor:
                for row in reader:
                    if len(row) >= 3:  # ต้องมีอย่างน้อย 3 คอลัมน์
                        # แปลงข้อมูล
                        timestamp_str = row[timestamp_idx].strip()
                        conductivity_str = row[conductivity_idx].strip()
                        unit = row[unit_idx].strip()
                        
                        # ตรวจสอบค่าอุณหภูมิ
                        temperature = None
                        if temperature_idx >= 0 and temperature_idx < len(row):
                            try:
                                temperature = float(row[temperature_idx])
                            except:
                                pass
                        
                        try:
                            # แปลง timestamp เป็น datetime object
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            # แปลงค่าการนำไฟฟ้า
                            conductivity = float(conductivity_str)
                            
                            # บันทึกลงฐานข้อมูล
                            sql = f"""
                            INSERT INTO {table_name} (timestamp, conductivity, unit, temperature)
                            VALUES (%s, %s, %s, %s)
                            """
                            cursor.execute(sql, (timestamp_str, conductivity, unit, temperature))
                            imported_count += 1
                            
                            # แสดงความคืบหน้าทุกๆ 100 รายการ
                            if imported_count % 100 == 0:
                                print(f"นำเข้าข้อมูลแล้ว {imported_count} รายการ...")
                                connection.commit()
                        except Exception as e:
                            print(f"ข้ามแถวที่มีปัญหา: {row} - {e}")
                
                # บันทึกข้อมูลที่เหลือ
                connection.commit()
        
        # ปิดการเชื่อมต่อ
        connection.close()
        
        return True, f"นำเข้าข้อมูลสำเร็จ {imported_count} รายการ"
    
    except Exception as e:
        if connection:
            connection.close()
        return False, f"เกิดข้อผิดพลาดในการย้ายข้อมูล: {e}"

def migration_wizard():
    """ตัวช่วยย้ายข้อมูลแบบโต้ตอบ"""
    print("\n===== โปรแกรมช่วยย้ายข้อมูลจาก CSV ไป MySQL =====\n")
    
    # ตรวจสอบไฟล์ CSV ในโฟลเดอร์โปรเจค
    project_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(project_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("ไม่พบไฟล์ CSV ในโฟลเดอร์โปรเจค")
        csv_path = input("โปรดระบุพาธของไฟล์ CSV ที่ต้องการย้าย: ")
        if not os.path.exists(csv_path):
            print(f"ไม่พบไฟล์ {csv_path}")
            return
    else:
        print("พบไฟล์ CSV ในโฟลเดอร์โปรเจค:")
        for i, filename in enumerate(csv_files, 1):
            csv_path = os.path.join(project_dir, filename)
            size_kb = os.path.getsize(csv_path) / 1024
            print(f"{i}. {filename} ({size_kb:.1f} KB)")
        
        choice = input("\nเลือกไฟล์ที่ต้องการย้าย (1, 2, ...) หรือกด Enter เพื่อข้าม: ")
        if not choice:
            return
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(csv_files):
                csv_path = os.path.join(project_dir, csv_files[choice_idx])
            else:
                print("ตัวเลือกไม่ถูกต้อง")
                return
        except:
            print("กรุณาป้อนตัวเลข")
            return
    
    # เลือกโหมดการทำงาน
    mock_choice = input("\nเป็นข้อมูลจำลองใช่หรือไม่? (y/n): ")
    mock_mode = mock_choice.lower() == 'y'
    
    # ดำเนินการย้ายข้อมูล
    success, message = migrate_csv_to_db(csv_path, mock_mode)
    if success:
        print(f"\n✅ {message}")
        print("การย้ายข้อมูลเสร็จสิ้น คุณสามารถใช้โปรแกรมได้ตามปกติ")
    else:
        print(f"\n❌ {message}")

if __name__ == "__main__":
    migration_wizard()
