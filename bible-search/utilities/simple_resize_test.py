#!/usr/bin/env python3
"""
Very simple resize test - just test if the resize handle works.
"""

import tkinter as tk
from tkinter import ttk

def test_resize():
    root = tk.Tk()
    root.title("Simple Resize Test")
    root.geometry("400x300")
    
    # Create a frame
    frame = ttk.Frame(root, relief='solid', borderwidth=2)
    frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Add a label
    label = ttk.Label(frame, text="Test Frame - drag the handle below", font=('Arial', 12))
    label.pack(pady=20)
    
    # Create resize handle with visible styling
    resize_handle = ttk.Frame(frame, height=10, cursor='sb_v_double_arrow', relief='raised', borderwidth=2)
    resize_handle.pack(fill='x', side='bottom')
    
    # Status label
    status_label = ttk.Label(frame, text="Resize handle ready", foreground='blue')
    status_label.pack(pady=10)
    
    def on_click(event):
        status_label.config(text="Mouse clicked on resize handle!", foreground='red')
        print("CLICK: Mouse clicked on resize handle")
    
    def on_motion(event):
        status_label.config(text=f"Mouse moving: y={event.y_root}", foreground='green')
        print(f"MOTION: Mouse at y={event.y_root}")
    
    def on_release(event):
        status_label.config(text="Mouse released", foreground='blue')
        print("RELEASE: Mouse released")
    
    # Bind events
    resize_handle.bind('<Button-1>', on_click)
    resize_handle.bind('<B1-Motion>', on_motion)
    resize_handle.bind('<ButtonRelease-1>', on_release)
    
    print("Simple resize test started.")
    print("Try clicking and dragging the thick handle at the bottom of the frame.")
    print("You should see messages here and the status change in the window.")
    
    root.mainloop()

if __name__ == "__main__":
    test_resize()