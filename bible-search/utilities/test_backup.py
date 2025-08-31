#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from bible_search_interface import BackupDialog, ConfigManager
import tempfile
import os

def test_backup_dialog():
    """Test the backup dialog functionality."""
    
    # Create a test root window
    root = tk.Tk()
    root.title("Backup Test")
    root.geometry("400x300")
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Create a test button to open backup dialog
    def open_backup_dialog():
        dialog = BackupDialog(root, config_manager)
        dialog.show()
    
    # Create UI
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    ttk.Label(main_frame, text="Backup Feature Test", 
              font=('Arial', 14, 'bold')).pack(pady=(0, 20))
    
    ttk.Label(main_frame, text="Click the button below to test the backup dialog:").pack(pady=(0, 10))
    
    ttk.Button(main_frame, text="Open Backup Dialog", 
               command=open_backup_dialog).pack(pady=10)
    
    ttk.Label(main_frame, text="This will open the backup/restore interface with:\n"
                               "• Create Backup tab with file navigation\n"
                               "• Restore Backup tab with backup selection\n"
                               "• Option to include/exclude config settings").pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    test_backup_dialog()