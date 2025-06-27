"""
ไฟล์สำหรับเตรียมฐานข้อมูล MySQL ให้พร้อมใช้งาน
"""

import logging
from db_manager import init_database, get_connection, get_data_table_name, generate_mock_data

logging.basicConfig(level=logging.INFO)

def setup_database():
    """เตรียมฐานข้อมูล MySQL ให้พร้อมใช้งาน"""
    print("\n===== เตรียมฐานข้อมูล MySQL =====")
    
    # 1. ทดสอบการเชื่อมต่อกับฐานข้อมูล
    print("ทดสอบการเชื่อมต่อกับฐานข้อมูล...")
    
    # แสดง error ทั้งหมด
    import traceback
    try:
        connection = get_connection()
        if not connection:
            print("❌ ไม่สามารถเชื่อมต่อกับฐานข้อมูลได้")
            print("โปรดตรวจสอบการตั้งค่าฐานข้อมูลใน database_config.ini")
            return False
    except Exception as e:
        print(f"❌ เกิด error ในการเชื่อมต่อกับฐานข้อมูล: {e}")
        print("รายละเอียด error:")
        traceback.print_exc()
        return False
    
    print("✅ เชื่อมต่อกับฐานข้อมูลสำเร็จ!")
    
    # 2. เตรียมฐานข้อมูลและตาราง
    print("\nเตรียมฐานข้อมูลและตาราง...")
    init_result = init_database()
    if not init_result:
        print("❌ เกิดข้อผิดพลาดในการเตรียมฐานข้อมูล")
        return False
    
    print("✅ เตรียมฐานข้อมูลและตารางสำเร็จ!")
    
    # 3. สร้างข้อมูลจำลอง
    print("\nสร้างข้อมูลจำลองเพื่อทดสอบ...")
    mock_result = generate_mock_data(num_days=1)
    if not mock_result:
        print("⚠️ ไม่สามารถสร้างข้อมูลจำลองได้")
    else:
        print("✅ สร้างข้อมูลจำลองสำเร็จ!")
    
    # 4. แสดงข้อมูลในตาราง
    mock_table = get_data_table_name(mock_mode=True)
    real_table = get_data_table_name(mock_mode=False)
    
    try:
        # ตรวจสอบจำนวนข้อมูลในตาราง
        cursor = connection.cursor()
        
        # ตรวจสอบตารางข้อมูลจำลอง
        cursor.execute(f"SELECT COUNT(*) FROM {mock_table}")
        mock_count = cursor.fetchone()[0]
        
        # ตรวจสอบตารางข้อมูลจริง
        cursor.execute(f"SELECT COUNT(*) FROM {real_table}")
        real_count = cursor.fetchone()[0]
        
        print(f"\nตารางข้อมูลจำลอง ({mock_table}): {mock_count} รายการ")
        print(f"ตารางข้อมูลจริง ({real_table}): {real_count} รายการ")
        
        # ตรวจสอบข้อมูลล่าสุดในแต่ละตาราง
        if mock_count > 0:
            cursor.execute(f"SELECT timestamp, conductivity, unit, temperature FROM {mock_table} ORDER BY timestamp DESC LIMIT 5")
            rows = cursor.fetchall()
            print(f"\nข้อมูลล่าสุดในตารางจำลอง ({mock_table}):")
            for row in rows:
                print(f"  {row[0]} - {row[1]} {row[2]}, {row[3]}°C")
        
        if real_count > 0:
            cursor.execute(f"SELECT timestamp, conductivity, unit, temperature FROM {real_table} ORDER BY timestamp DESC LIMIT 5")
            rows = cursor.fetchall()
            print(f"\nข้อมูลล่าสุดในตารางจริง ({real_table}):")
            for row in rows:
                print(f"  {row[0]} - {row[1]} {row[2]}, {row[3]}°C")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการแสดงข้อมูล: {e}")
    finally:
        if connection:
            connection.close()
    
    print("\n✅ การเตรียมฐานข้อมูลเสร็จสิ้น")
    print("คุณสามารถเริ่มโปรแกรมได้โดยใช้คำสั่ง 'python main.py'\n")
    return True

if __name__ == "__main__":
    setup_database()
