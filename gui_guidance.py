"""
Guidance dialogs for the application.
Provides help and instruction dialogs for users.
"""

import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk

class RealDeviceGuidanceDialog:
    """Dialog for guiding users on how to use real device mode."""
    
    def __init__(self, parent):
        """Initialize guidance dialog."""
        self.parent = parent
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("คำแนะนำการใช้งานเครื่อง Sension7 จริง")
        self.window.geometry("700x550")
        self.window.minsize(600, 400)
        self.window.resizable(True, True)
        self.window.transient(parent)  # Set as transient to parent
        self.window.grab_set()  # Modal dialog
        
        # Create UI
        self.create_widgets()
        
        # Center the dialog window relative to parent
        self.center_window()
    
    def create_widgets(self):
        """Create UI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(header_frame, 
                               text="คำแนะนำการใช้งานเครื่องวัดค่าการนำไฟฟ้า HACH Sension7",
                               font=("Helvetica", 14, "bold"))
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(header_frame, 
                                 text="ขั้นตอนการเชื่อมต่อและทำงานกับเครื่องจริง",
                                 font=("Helvetica", 12))
        subtitle_label.pack(pady=5)
        
        # Content in scrollable area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(content_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Canvas for scrolling
        canvas = tk.Canvas(content_frame)
        canvas.pack(side="left", fill="both", expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=canvas.yview)
        canvas.config(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Frame inside canvas for steps
        steps_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=steps_frame, anchor="nw", width=canvas.winfo_reqwidth())
        
        # Steps content
        self.add_steps(steps_frame)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Close button
        ttk.Button(button_frame, text="เข้าใจแล้ว", 
                  command=self.window.destroy, width=15).pack(side="right", padx=5)
        
        # Don't show again checkbox
        self.dont_show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(button_frame, text="ไม่ต้องแสดงอีก", 
                       variable=self.dont_show_var).pack(side="left", padx=5)
    
    def add_steps(self, parent):
        """Add step by step instructions."""
        steps = [
            {
                "title": "1. เตรียมการเชื่อมต่อ",
                "content": "ตรวจสอบให้แน่ใจว่าได้เชื่อมต่อเครื่อง HACH Sension7 กับคอมพิวเตอร์โดยใช้สายเชื่อมต่อ RS-232 หรืออะแดปเตอร์ USB-to-Serial แล้ว"
            },
            {
                "title": "2. เปิดเครื่อง HACH Sension7",
                "content": "เปิดเครื่องวัดค่าการนำไฟฟ้าและรอให้เครื่องพร้อมใช้งาน ควรเห็นหน้าจอแสดงค่าการนำไฟฟ้าและอุณหภูมิ"
            },
            {
                "title": "3. ตรวจสอบพอร์ตที่เชื่อมต่อ",
                "content": "เลือกพอร์ต COM ที่ถูกต้อง หากไม่แน่ใจว่าใช้พอร์ตไหน ให้ลองตรวจสอบใน Device Manager (กรณี Windows) หรือใช้ปุ่ม 'ทดสอบการเชื่อมต่อ' ในหน้าตั้งค่า"
            },
            {
                "title": "4. ตรวจสอบอัตราบอด (Baud Rate)",
                "content": "เครื่อง HACH Sension7 โดยทั่วไปใช้อัตราบอดที่ 9600 bps ตรวจสอบให้แน่ใจว่าได้ตั้งค่าถูกต้องในหน้าการตั้งค่าการเชื่อมต่อ"
            },
            {
                "title": "5. ยืนยันการเชื่อมต่อ",
                "content": "กดปุ่ม 'ทดสอบการเชื่อมต่อ' ในหน้าตั้งค่าเพื่อทดสอบการสื่อสารกับเครื่องวัด หากเชื่อมต่อสำเร็จ จะแสดงข้อความยืนยัน"
            },
            {
                "title": "6. เริ่มการวัด",
                "content": "เมื่อเชื่อมต่อสำเร็จ ให้กลับมาที่หน้าหลักของโปรแกรม ค่าการวัดจากเครื่องจริงจะเริ่มปรากฏ ให้นำหัววัดจุ่มลงในสารละลายที่ต้องการวัด"
            },
            {
                "title": "7. การบันทึกข้อมูล",
                "content": "ข้อมูลจะถูกบันทึกอัตโนมัติตามที่ตั้งค่าไว้ในแท็บ 'การบันทึกข้อมูล' โดยบันทึกลงในไฟล์ CSV ตามที่ระบุ"
            },
            {
                "title": "8. หากเกิดปัญหาการเชื่อมต่อ",
                "content": "• ตรวจสอบว่าเลือกพอร์ต COM ถูกต้อง\n• ตรวจสอบสายเชื่อมต่อว่าเสียบแน่นดีหรือไม่\n• รีสตาร์ทเครื่องวัดและโปรแกรม\n• ตรวจสอบว่าไม่มีโปรแกรมอื่นที่ใช้พอร์ต COM เดียวกัน"
            },
            {
                "title": "9. สิ่งที่ควรระวัง",
                "content": "• ระวังไม่ให้เกิดการกระชากของสายขณะกำลังวัด\n• ถ้าต้องการเปลี่ยนพอร์ตหรือการตั้งค่าอื่นๆ ให้หยุดการวัดก่อน\n• หากเครื่องแสดงค่าผิดปกติ ลองปรับเทียบ (Calibrate) เครื่องตามคู่มือเครื่องวัด"
            }
        ]
        
        for i, step in enumerate(steps):
            step_frame = ttk.LabelFrame(parent, text=step["title"], padding="10")
            step_frame.pack(fill="x", pady=5, padx=5)
            
            ttk.Label(step_frame, text=step["content"], 
                     wraplength=600, justify="left").pack(pady=5)
    
    def center_window(self):
        """Center the dialog window on screen."""
        self.window.update_idletasks()
        
        # Get screen and window dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"+{x}+{y}")
    
    def get_dont_show_again(self):
        """Return whether the 'don't show again' option is checked."""
        return self.dont_show_var.get()


def show_real_device_guidance(parent):
    """Show the real device guidance dialog and return whether 'don't show again' was selected."""
    dialog = RealDeviceGuidanceDialog(parent)
    parent.wait_window(dialog.window)
    return dialog.get_dont_show_again()

if __name__ == "__main__":
    # Test the dialog
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    show_real_device_guidance(root)
    
    root.destroy()
