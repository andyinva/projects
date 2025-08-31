#!/usr/bin/env python3
"""
Simple test interface to debug window sizing issues.
Just 4 windows that should start equal and resize together.
"""

import tkinter as tk
from tkinter import ttk

class SimpleResizableFrame(ttk.Frame):
    """Simple resizable frame for testing."""
    
    def __init__(self, parent, title: str, sync_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.parent = parent
        self.sync_callback = sync_callback
        
        # Create title label
        self.title_label = ttk.Label(self, text=title, font=('Arial', 9, 'bold'))
        self.title_label.pack(anchor='w', padx=5, pady=2)
        
        # Create content frame with some text
        self.content_frame = ttk.Frame(self, relief='sunken', borderwidth=1)
        self.content_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add some text content
        self.text_widget = tk.Text(self.content_frame, height=6, font=('Arial', 9))
        self.text_widget.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add sample text
        sample_text = f"Sample content for {title}\n" * 10
        self.text_widget.insert('1.0', sample_text)
        
        # Create resize handle
        self.resize_handle = ttk.Frame(self, height=3, cursor='sb_v_double_arrow', relief='raised')
        self.resize_handle.pack(fill='x', side='bottom')
        
        # Bind resize events
        self.resize_handle.bind('<Button-1>', self.start_resize)
        self.resize_handle.bind('<B1-Motion>', self.on_resize)
        
        self.start_y = 0
        self.start_height = 0
    
    def start_resize(self, event):
        """Start resize operation."""
        self.start_y = event.y_root
        self.start_height = self.winfo_height()
        print(f"Starting resize for {self.title}, current height: {self.start_height}")
    
    def on_resize(self, event):
        """Handle resize drag - synchronize with other windows."""
        delta_y = event.y_root - self.start_y
        new_height = max(80, self.start_height + delta_y)  # Min height 80px
        
        print(f"Resizing {self.title} to height: {new_height}")
        
        # Use callback to synchronize all windows
        if self.sync_callback:
            self.sync_callback(new_height)

class SimpleTestInterface:
    """Simple test interface with 4 resizable windows."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple Window Resize Test")
        self.root.geometry("800x600")
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create 4 windows with equal heights
        self.windows = {}
        window_configs = [
            ("Window 3 - Search", 0),
            ("Window 4 - Reading", 1),
            ("Window 5 - Subject", 2),
            ("Window 6 - Comments", 3)
        ]
        
        # Set equal starting height
        starting_height = 120  # Should show about 6 lines
        
        for title, row in window_configs:
            print(f"Creating {title} with height {starting_height}")
            
            frame = SimpleResizableFrame(self.main_frame, title, sync_callback=self.sync_all_heights)
            frame.configure(height=starting_height)
            frame.grid(row=row, column=0, sticky='nsew', padx=2, pady=2)
            frame.grid_propagate(False)  # Don't let content change the size
            
            # Give all windows equal weight for synchronized resizing
            self.main_frame.grid_rowconfigure(row, weight=1)
            
            self.windows[title] = frame
            
        # Print initial heights
        self.root.after(100, self.check_heights)
    
    def check_heights(self):
        """Check and print the actual heights of all windows."""
        print("\n--- Current Window Heights ---")
        for title, frame in self.windows.items():
            actual_height = frame.winfo_height()
            print(f"{title}: {actual_height}px")
        print("------------------------------\n")
    
    def sync_all_heights(self, new_height):
        """Synchronize all window heights."""
        print(f"Syncing all windows to height: {new_height}")
        for frame in self.windows.values():
            frame.configure(height=new_height)
        self.main_frame.update_idletasks()
    
    def run(self):
        """Start the test interface."""
        print("Starting simple test interface...")
        print("All 4 windows should start with equal heights of 120px")
        print("Dragging any resize handle should move all windows together")
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleTestInterface()
    app.run()