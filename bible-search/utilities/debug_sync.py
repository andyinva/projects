#!/usr/bin/env python3
"""
Debug the sync callback issue.
"""

import tkinter as tk
from tkinter import ttk

class DebugResizableFrame(ttk.Frame):
    """Debug version of resizable frame."""
    
    def __init__(self, parent, title: str, sync_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.parent = parent
        self.sync_callback = sync_callback
        
        # Create title label
        self.title_label = ttk.Label(self, text=title, font=('Arial', 9, 'bold'))
        self.title_label.pack(anchor='w', padx=5, pady=2)
        
        # Create content frame
        self.content_frame = ttk.Frame(self, relief='sunken', borderwidth=1)
        self.content_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add text widget
        self.text_widget = tk.Text(self.content_frame, height=4, font=('Arial', 9))
        self.text_widget.pack(fill='both', expand=True, padx=2, pady=2)
        self.text_widget.insert('1.0', f"Content for {title}\n" * 5)
        
        # Create resize handle - make it much more visible
        self.resize_handle = ttk.Frame(self, height=8, cursor='sb_v_double_arrow', relief='raised', borderwidth=2)
        self.resize_handle.pack(fill='x', side='bottom')
        
        # Add a label to the resize handle to make it obvious
        handle_label = ttk.Label(self.resize_handle, text="═══ DRAG HERE ═══", font=('Arial', 8), anchor='center', cursor='sb_v_double_arrow')
        handle_label.pack(fill='x')
        
        # Bind resize events to BOTH the handle frame AND the label
        self.resize_handle.bind('<Button-1>', self.start_resize)
        self.resize_handle.bind('<B1-Motion>', self.on_resize)
        handle_label.bind('<Button-1>', self.start_resize)
        handle_label.bind('<B1-Motion>', self.on_resize)
        
        print(f"DEBUG: Bindings created for {self.title}")
        
        self.start_y = 0
        self.start_height = 0
    
    def start_resize(self, event):
        """Start resize operation."""
        self.start_y = event.y_root
        self.start_height = self.winfo_height()
        print(f"DEBUG: Starting resize for {self.title}, height: {self.start_height}")
        print(f"DEBUG: Callback is: {self.sync_callback}")
    
    def on_resize(self, event):
        """Handle resize drag."""
        delta_y = event.y_root - self.start_y
        new_height = max(50, self.start_height + delta_y)
        
        print(f"DEBUG: {self.title} resizing to {new_height}px")
        
        # Test if callback exists and call it
        if self.sync_callback:
            print(f"DEBUG: Calling sync_callback with height {new_height}")
            self.sync_callback(new_height)
        else:
            print(f"DEBUG: No callback, just resizing {self.title}")
            self.configure(height=new_height)

class DebugInterface:
    """Debug interface to test sync callbacks."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Debug Sync Callback")
        self.root.geometry("800x600")
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create 4 windows
        self.frames = {}
        titles = ["Window 3", "Window 4", "Window 5", "Window 6"]
        
        for i, title in enumerate(titles):
            print(f"Creating {title} with sync_callback")
            frame = DebugResizableFrame(self.main_frame, title, sync_callback=self.sync_all_heights)
            frame.configure(height=120)
            frame.grid(row=i, column=0, sticky='nsew', padx=2, pady=2)
            frame.grid_propagate(False)
            self.main_frame.grid_rowconfigure(i, weight=1)
            self.frames[title] = frame
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="Drag any resize handle and watch console output", 
                                     font=('Arial', 10, 'bold'))
        self.status_label.grid(row=4, column=0, pady=10)
        
    def sync_all_heights(self, new_height):
        """Sync all window heights."""
        print(f"SYNC: Setting all windows to {new_height}px")
        for frame in self.frames.values():
            # Force the height by configuring the frame AND ensuring grid_propagate is False
            frame.configure(height=new_height)
            frame.grid_propagate(False)  # Make sure content doesn't override height
            
            # Also force update the grid row height
            for row in range(4):
                self.main_frame.grid_rowconfigure(row, minsize=new_height)
        
        # Calculate total height needed and resize main window
        total_height = (new_height * 4) + 100 + 50  # 4 windows + status label + padding
        current_width = self.root.winfo_width()
        
        print(f"SYNC: Resizing main window to {current_width}x{total_height}")
        self.root.geometry(f"{current_width}x{total_height}")
        
        self.main_frame.update()
        print("SYNC: Complete")
    
    def run(self):
        """Start the debug interface."""
        print("Debug interface started. Watch console for callback messages.")
        self.root.mainloop()

if __name__ == "__main__":
    app = DebugInterface()
    app.run()