#!/usr/bin/env python3
"""
Debug test to understand window sizing without GUI.
"""

import tkinter as tk
from tkinter import ttk

def test_window_heights():
    """Test window heights without showing GUI."""
    print("Testing window height configuration...")
    
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create main frame
    main_frame = ttk.Frame(root)
    main_frame.grid(row=0, column=0, sticky='nsew')
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Create 4 test frames with same height
    test_height = 120
    frames = []
    
    for i in range(4):
        frame = ttk.Frame(main_frame, height=test_height)
        frame.grid(row=i, column=0, sticky='nsew', padx=2, pady=2)
        frame.grid_propagate(False)
        main_frame.grid_rowconfigure(i, weight=1)
        frames.append(frame)
        
        # Add text widget to see actual content size
        text = tk.Text(frame, height=6, font=('Arial', 9))
        text.pack(fill='both', expand=True)
        text.insert('1.0', f"Window {i+3} content\n" * 8)
    
    # Force geometry calculation
    root.update_idletasks()
    
    # Check actual heights
    print(f"\nConfigured height: {test_height}px")
    print("Actual heights after geometry calculation:")
    for i, frame in enumerate(frames):
        actual_height = frame.winfo_height()
        print(f"  Window {i+3}: {actual_height}px")
        
        # Check text widget
        for child in frame.winfo_children():
            if isinstance(child, tk.Text):
                text_height = child.winfo_height()
                print(f"    Text widget: {text_height}px")
    
    root.destroy()

if __name__ == "__main__":
    test_window_heights()