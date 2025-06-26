"""
Scrollable frame widgets for the application.
"""

import tkinter as tk
from tkinter import ttk

class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame widget that can contain other widgets.
    Can scroll vertically and optionally horizontally.
    """
    
    def __init__(self, container, horizontal_scroll=False, **kwargs):
        """
        Initialize a scrollable frame.
        
        Parameters:
        -----------
        container : tkinter widget
            Parent widget to contain the scrollable frame
        horizontal_scroll : bool
            Whether to include a horizontal scrollbar
        **kwargs : dict
            Additional keyword arguments to pass to Frame constructor
        """
        super().__init__(container, **kwargs)
        
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self)
        
        # Add vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        
        # Add horizontal scrollbar if needed
        if horizontal_scroll:
            self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.h_scrollbar.pack(side="bottom", fill="x")
            self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Frame to hold widgets
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame_id = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
            tags=("scrollable_frame",)
        )
        
        # Configure canvas scroll region when frame size changes
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        # Make sure canvas resizes properly
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self.scrollable_frame_id,
                width=e.width
            )
        )
        
        # Enable scrolling with mouse wheel
        self.bind_mouse_wheel()
    
    def bind_mouse_wheel(self):
        """Bind mouse wheel events for scrolling."""
        def _on_mousewheel(event):
            # Different handling for different platforms
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")
                
        # Bind for different platforms
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
        self.canvas.bind_all("<Button-4>", _on_mousewheel)  # Linux
        self.canvas.bind_all("<Button-5>", _on_mousewheel)  # Linux
    
    def unbind_mouse_wheel(self):
        """Unbind mouse wheel events."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def get_frame(self):
        """Get the scrollable frame to add widgets to."""
        return self.scrollable_frame
