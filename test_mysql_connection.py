"""
ไฟล์ทดสอบการเชื่อมต่อ MySQL อย่างง่าย
"""
import pymysql
import traceback
import sys

print("Python version:", sys.version)
print("PyMySQL version:", pymysql.__version__)
print("\nกำลังทดสอบการเชื่อมต่อ MySQL...")
    connection = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="conductivity_data",
        connect_timeout=5
    )
    print("การเชื่อมต่อสำเร็จ!")
    connection.close()
except Exception as e:
    print(f"ไม่สามารถเชื่อมต่อกับ MySQL ได้: {e}")
    print("\nรายละเอียด error:")
    traceback.print_exc()
    
    print("\nข้อมูลการเชื่อมต่อที่ใช้:")
    print("- Host: localhost")
    print("- Port: 3306")
    print("- User: root")
    print("- Password: (ไม่แสดง)")
    print("- Database: conductivity_data")
    
    print("\nสาเหตุและวิธีแก้ไขที่เป็นไปได้:")
    print("1. MySQL Server ไม่ได้ติดตั้งบนเครื่องคอมพิวเตอร์นี้")
    print("   - ติดตั้ง MySQL Server หรือ MariaDB")
    print("2. MySQL Server ไม่ได้ทำงานอยู่")
    print("   - เริ่มการทำงานของ MySQL Service")
    print("3. ข้อมูลการเชื่อมต่อไม่ถูกต้อง")
    print("   - ตรวจสอบและแก้ไขไฟล์ database_config.ini")
    print("4. Firewall บล็อคการเชื่อมต่อ")
    print("   - อนุญาตการเชื่อมต่อที่พอร์ต 3306")
