import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sqlite3
import shutil
import zipfile
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from bible_search import BibleSearch, SearchResult, Translation

def find_database(filename: str = "bibles.db") -> str:
    """Find database file, searching current directory first, then subdirectories."""
    # Check current directory first
    if os.path.exists(filename):
        return filename
    
    # Search in common subdirectories
    common_dirs = ['database', 'db', 'data', 'databases']
    for dir_name in common_dirs:
        db_path = os.path.join(dir_name, filename)
        if os.path.exists(db_path):
            return db_path
    
    # Search recursively in all subdirectories (up to 2 levels deep)
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        # Limit search depth to avoid performance issues
        level = root.replace(current_dir, '').count(os.sep)
        if level < 3:  # Allow up to 2 subdirectory levels
            if filename in files:
                return os.path.join(root, filename)
    
    # If not found, return default name (will cause error later if file doesn't exist)
    return filename

class ConfigManager:
    """Manages configuration settings for the Bible search interface."""
    
    def __init__(self, config_file: str = "bible_search_config.json"):
        self.config_file = config_file
        self.default_config = {
            "window_width": 1000,
            "window_height": 700,
            "window_heights": {
                "search_window": 120,
                "reading_window": 120,
                "subject_verses": 120,
                "verse_comments": 120
            },
            "static_heights": {
                "search_settings": 120,
                "message_window": 80
            },
            "search_settings": {
                "case_sensitive": False,
                "unique_verses": False,
                "abbreviate_results": False
            },
            "translations": [],
            "font_size": 10
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            except (json.JSONDecodeError, IOError):
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError:
            pass
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value

class ResizableFrame(ttk.Frame):
    """A frame that can be resized by dragging its bottom border."""
    
    def __init__(self, parent, title: str, min_height: int = 50, sync_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.min_height = min_height
        self.parent = parent
        self.sync_callback = sync_callback
        
        # Create title label
        self.title_label = ttk.Label(self, text=title, font=('Arial', 9, 'bold'))
        self.title_label.pack(anchor='w', padx=5, pady=2)
        
        # Create resize handle FIRST - make it much more visible
        self.resize_handle = ttk.Frame(self, height=10, cursor='sb_v_double_arrow', relief='raised', borderwidth=2)
        self.resize_handle.pack(fill='x', side='bottom')
        
        # Add a label to the resize handle to make it obvious
        handle_label = ttk.Label(self.resize_handle, text="═══ DRAG HERE ═══", font=('Arial', 8, 'bold'), anchor='center', cursor='sb_v_double_arrow')
        handle_label.pack(fill='x')
        
        # Create content frame AFTER resize handle so it doesn't cover it
        self.content_frame = ttk.Frame(self, relief='sunken', borderwidth=1)
        self.content_frame.pack(fill='both', expand=True, padx=2, pady=(2, 0))
        
        # Bind resize events to BOTH the handle frame AND the label
        self.resize_handle.bind('<Button-1>', self.start_resize)
        self.resize_handle.bind('<B1-Motion>', self.on_resize)
        self.resize_handle.bind('<ButtonRelease-1>', self.end_resize)
        handle_label.bind('<Button-1>', self.start_resize)
        handle_label.bind('<B1-Motion>', self.on_resize)
        handle_label.bind('<ButtonRelease-1>', self.end_resize)
        
        self.start_y = 0
        self.start_height = 0
        self.last_update_y = 0  # For throttling updates
    
    def start_resize(self, event):
        """Start resize operation."""
        self.start_y = event.y_root
        self.start_height = self.winfo_height()
        self.last_update_y = event.y_root
# print(f"DEBUG: Starting resize for {self.title}, height: {self.start_height}, callback: {self.sync_callback}")
    
    def on_resize(self, event):
        """Handle resize drag - synchronize with other resizable windows."""
        # Throttle updates - only update every 5 pixels of movement
        if abs(event.y_root - self.last_update_y) < 5:
            return
        
        self.last_update_y = event.y_root
        delta_y = event.y_root - self.start_y
        new_height = max(self.min_height, self.start_height + delta_y)
        
        # Use callback to synchronize all resizable windows
        if self.sync_callback:
            # Ensure minimum height for content (don't go below 80px)
            safe_height = max(80, new_height)
            # print(f"DEBUG: {self.title} calling sync_callback with height {safe_height}")
            self.sync_callback(safe_height)
        else:
            # print(f"DEBUG: {self.title} no callback, resizing individually to {new_height}")
            safe_height = max(80, new_height)
            self.configure(height=safe_height)
            self.parent.update()
    
    def end_resize(self, event):
        """End resize operation - final update to ensure perfect sync."""
        # Final update without throttling - ensure all windows end up exactly the same
        delta_y = event.y_root - self.start_y
        new_height = max(self.min_height, self.start_height + delta_y)
        
        if self.sync_callback:
            # Do a final sync to make sure all windows are exactly the same height
            safe_height = max(80, new_height)
            self.sync_callback(safe_height)
            # Force one more sync with a reasonable height to ensure precision
            actual_height = max(80, self.winfo_height())
            self.sync_callback(actual_height)
        else:
            safe_height = max(80, new_height)
            self.configure(height=safe_height)
            self.parent.update()

class TranslationDialog:
    """Dialog for managing translation settings."""
    
    def __init__(self, parent, bible_search: BibleSearch, config_manager: ConfigManager):
        self.parent = parent
        self.bible_search = bible_search
        self.config_manager = config_manager
        self.window = None
        self.translation_vars = {}
        self.sort_order_vars = {}
    
    def show(self):
        """Show the translation settings dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Translation Settings")
        self.window.geometry("600x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Headers
        ttk.Label(scrollable_frame, text="Enabled", font=('Arial', 9, 'bold')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Abbreviation", font=('Arial', 9, 'bold')).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(scrollable_frame, text="Translation Name", font=('Arial', 9, 'bold')).grid(row=0, column=2, padx=5, pady=5, sticky='w')
        ttk.Label(scrollable_frame, text="Sort Order", font=('Arial', 9, 'bold')).grid(row=0, column=3, padx=5, pady=5)
        
        # Load saved settings
        saved_translations = self.config_manager.get('translations', [])
        saved_settings = {t.get('abbreviation', ''): t for t in saved_translations}
        
        # Create controls for each translation
        for i, translation in enumerate(self.bible_search.translations):
            row = i + 1
            
            # Get saved settings or use defaults
            saved_setting = saved_settings.get(translation.abbreviation, {})
            enabled = saved_setting.get('enabled', True)
            sort_order = saved_setting.get('sort_order', i + 1)
            
            # Checkbox for enabled
            var = tk.BooleanVar(value=enabled)
            self.translation_vars[translation.abbreviation] = var
            cb = ttk.Checkbutton(scrollable_frame, variable=var)
            cb.grid(row=row, column=0, padx=5, pady=2)
            
            # Abbreviation label
            ttk.Label(scrollable_frame, text=translation.abbreviation).grid(row=row, column=1, padx=5, pady=2)
            
            # Full name label
            ttk.Label(scrollable_frame, text=translation.full_name).grid(row=row, column=2, padx=5, pady=2, sticky='w')
            
            # Sort order entry
            sort_var = tk.StringVar(value=str(sort_order))
            self.sort_order_vars[translation.abbreviation] = sort_var
            sort_entry = ttk.Entry(scrollable_frame, textvariable=sort_var, width=8)
            sort_entry.grid(row=row, column=3, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Select/Deselect buttons frame
        select_frame = ttk.Frame(self.window)
        select_frame.pack(fill='x', padx=10, pady=(5, 0))
        
        ttk.Button(select_frame, text="Select All", command=self.select_all).pack(side='left', padx=(0, 5))
        ttk.Button(select_frame, text="Deselect All", command=self.deselect_all).pack(side='left')
        
        # Button frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side='right')
    
    def select_all(self):
        """Select all translations."""
        for var in self.translation_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Deselect all translations."""
        for var in self.translation_vars.values():
            var.set(False)
    
    def save_settings(self):
        """Save translation settings."""
        translation_settings = []
        
        for translation in self.bible_search.translations:
            abbrev = translation.abbreviation
            enabled = self.translation_vars[abbrev].get()
            
            try:
                sort_order = int(self.sort_order_vars[abbrev].get())
            except ValueError:
                sort_order = 1
            
            # Update the translation object
            translation.enabled = enabled
            translation.sort_order = sort_order
            
            translation_settings.append({
                'abbreviation': abbrev,
                'enabled': enabled,
                'sort_order': sort_order
            })
        
        # Sort translations by sort order
        self.bible_search.translations.sort(key=lambda x: x.sort_order)
        
        # Save to config
        self.config_manager.set('translations', translation_settings)
        self.config_manager.save_config()
        
        messagebox.showinfo("Settings", "Translation settings saved successfully!")
        self.window.destroy()

class FontDialog:
    """Dialog for managing font size settings."""
    
    def __init__(self, parent, config_manager: ConfigManager, interface_callback):
        self.parent = parent
        self.config_manager = config_manager
        self.interface_callback = interface_callback
        self.window = None
        self.font_size_var = tk.IntVar(value=config_manager.get('font_size', 10))
    
    def show(self):
        """Show the font settings dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Font Settings")
        self.window.geometry("400x350")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Font Size for Bible and Comments", 
                               font=('Arial', 11, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(main_frame, text="This affects Windows 3, 4, 5 (Bible display) and Window 6 (Comments)", 
                              font=('Arial', 9), wraplength=250)
        desc_label.pack(pady=(0, 20))
        
        # Radio buttons frame
        radio_frame = ttk.Frame(main_frame)
        radio_frame.pack(pady=(0, 30))
        
        # Radio buttons for font sizes with more spacing
        font_sizes = [8, 9, 10, 11]
        for size in font_sizes:
            radio = ttk.Radiobutton(radio_frame, text=f"Size {size}", 
                                   variable=self.font_size_var, value=size)
            radio.pack(anchor='w', pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Apply", command=self.apply_font_settings).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side='right')
    
    def apply_font_settings(self):
        """Apply font settings."""
        new_font_size = self.font_size_var.get()
        
        # Save to config
        self.config_manager.set('font_size', new_font_size)
        self.config_manager.save_config()
        
        # Apply to interface
        if self.interface_callback:
            self.interface_callback(new_font_size)
        
        messagebox.showinfo("Font Settings", f"Font size changed to {new_font_size}")
        self.window.destroy()

class BackupDialog:
    """Dialog for managing backup and restore operations."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.window = None
        self.include_config_var = tk.BooleanVar(value=True)
        
        # Default backup directory
        self.default_backup_dir = os.path.join(os.path.expanduser("~"), "BibleSearchBackups")
        if not os.path.exists(self.default_backup_dir):
            os.makedirs(self.default_backup_dir)
    
    def show(self):
        """Show the backup/restore dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Backup & Restore")
        self.window.geometry("700x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Backup tab
        backup_frame = ttk.Frame(notebook)
        notebook.add(backup_frame, text="Create Backup")
        self.create_backup_tab(backup_frame)
        
        # Restore tab
        restore_frame = ttk.Frame(notebook)
        notebook.add(restore_frame, text="Restore Backup")
        self.create_restore_tab(restore_frame)
    
    def create_backup_tab(self, parent):
        """Create the backup creation tab."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Create New Backup", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Backup location section
        location_frame = ttk.LabelFrame(main_frame, text="Backup Location")
        location_frame.pack(fill='x', pady=(0, 15))
        
        # Current backup directory
        self.backup_dir_var = tk.StringVar(value=self.default_backup_dir)
        dir_entry = ttk.Entry(location_frame, textvariable=self.backup_dir_var, width=50)
        dir_entry.pack(side='left', padx=(10, 5), pady=10)
        
        browse_button = ttk.Button(location_frame, text="Browse...", 
                                  command=self.browse_backup_location)
        browse_button.pack(side='left', padx=(0, 10), pady=10)
        
        # What to backup section
        content_frame = ttk.LabelFrame(main_frame, text="Backup Contents")
        content_frame.pack(fill='x', pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(content_frame, 
                              text="The following will be included in your backup:",
                              font=('Arial', 9))
        desc_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        # Backup items list
        items_frame = ttk.Frame(content_frame)
        items_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        backup_items = [
            "✓ All subjects and their associated verses",
            "✓ All verse comments with formatting",
            "✓ Subject organization and order"
        ]
        
        for item in backup_items:
            item_label = ttk.Label(items_frame, text=item, font=('Arial', 9))
            item_label.pack(anchor='w', pady=1)
        
        # Config option
        config_check = ttk.Checkbutton(content_frame, 
                                      text="Include configuration settings (window sizes, font settings, translation settings)",
                                      variable=self.include_config_var)
        config_check.pack(anchor='w', padx=10, pady=(5, 10))
        
        # Backup name section
        name_frame = ttk.LabelFrame(main_frame, text="Backup Name")
        name_frame.pack(fill='x', pady=(0, 15))
        
        name_desc = ttk.Label(name_frame, 
                             text="Leave empty to use automatic name with date/time",
                             font=('Arial', 9), foreground='gray')
        name_desc.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.backup_name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.backup_name_var, width=40)
        name_entry.pack(anchor='w', padx=10, pady=(0, 10))
        
        # Progress section (initially hidden)
        self.progress_frame = ttk.Frame(main_frame)
        
        self.progress_var = tk.StringVar(value="")
        self.progress_label = ttk.Label(self.progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # Create backup button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        create_button = ttk.Button(button_frame, text="Create Backup", 
                                  command=self.create_backup)
        create_button.pack(side='right', padx=(5, 0))
    
    def create_restore_tab(self, parent):
        """Create the restore tab."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Restore from Backup", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Backup location section
        location_frame = ttk.LabelFrame(main_frame, text="Backup Location")
        location_frame.pack(fill='x', pady=(0, 15))
        
        self.restore_dir_var = tk.StringVar(value=self.default_backup_dir)
        restore_dir_entry = ttk.Entry(location_frame, textvariable=self.restore_dir_var, width=50)
        restore_dir_entry.pack(side='left', padx=(10, 5), pady=10)
        
        browse_restore_button = ttk.Button(location_frame, text="Browse...", 
                                          command=self.browse_restore_location)
        browse_restore_button.pack(side='left', padx=(0, 5), pady=10)
        
        refresh_button = ttk.Button(location_frame, text="Refresh", 
                                   command=self.refresh_backup_list)
        refresh_button.pack(side='left', padx=(5, 10), pady=10)
        
        # Available backups section
        backups_frame = ttk.LabelFrame(main_frame, text="Available Backups")
        backups_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Create Treeview for backup list
        columns = ('Name', 'Date', 'Size', 'Config')
        self.backup_tree = ttk.Treeview(backups_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.backup_tree.heading('Name', text='Backup Name')
        self.backup_tree.heading('Date', text='Created Date')
        self.backup_tree.heading('Size', text='Size')
        self.backup_tree.heading('Config', text='Includes Config')
        
        self.backup_tree.column('Name', width=250)
        self.backup_tree.column('Date', width=150)
        self.backup_tree.column('Size', width=80)
        self.backup_tree.column('Config', width=100)
        
        # Scrollbars for treeview
        tree_scrollbar_v = ttk.Scrollbar(backups_frame, orient='vertical', command=self.backup_tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(backups_frame, orient='horizontal', command=self.backup_tree.xview)
        self.backup_tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)
        
        self.backup_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        tree_scrollbar_v.pack(side='right', fill='y', pady=10)
        tree_scrollbar_h.pack(side='bottom', fill='x', padx=10)
        
        # Warning section
        warning_frame = ttk.LabelFrame(main_frame, text="⚠ Warning")
        warning_frame.pack(fill='x', pady=(0, 15))
        
        warning_text = ("Restoring will replace all current subjects, verses, and comments.\n"
                       "Consider creating a backup of your current data first.")
        warning_label = ttk.Label(warning_frame, text=warning_text, 
                                 font=('Arial', 9), foreground='red')
        warning_label.pack(padx=10, pady=10)
        
        # Progress section for restore (initially hidden)
        self.restore_progress_frame = ttk.Frame(main_frame)
        
        self.restore_progress_var = tk.StringVar(value="")
        self.restore_progress_label = ttk.Label(self.restore_progress_frame, textvariable=self.restore_progress_var)
        self.restore_progress_label.pack(pady=10)
        
        self.restore_progress_bar = ttk.Progressbar(self.restore_progress_frame, mode='indeterminate')
        self.restore_progress_bar.pack(fill='x', pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        restore_button = ttk.Button(button_frame, text="Restore Selected", 
                                   command=self.restore_backup)
        restore_button.pack(side='right', padx=(5, 0))
        
        delete_button = ttk.Button(button_frame, text="Delete Selected", 
                                  command=self.delete_backup)
        delete_button.pack(side='right', padx=(5, 0))
        
        # Load initial backup list
        self.refresh_backup_list()
    
    def browse_backup_location(self):
        """Browse for backup location."""
        directory = filedialog.askdirectory(
            title="Select Backup Location",
            initialdir=self.backup_dir_var.get()
        )
        if directory:
            self.backup_dir_var.set(directory)
    
    def browse_restore_location(self):
        """Browse for restore location."""
        directory = filedialog.askdirectory(
            title="Select Backup Location", 
            initialdir=self.restore_dir_var.get()
        )
        if directory:
            self.restore_dir_var.set(directory)
            self.refresh_backup_list()
    
    def create_backup(self):
        """Create a new backup."""
        backup_dir = self.backup_dir_var.get()
        if not backup_dir:
            messagebox.showerror("Error", "Please select a backup location.")
            return
        
        # Create backup directory if it doesn't exist
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create backup directory: {str(e)}")
            return
        
        # Generate backup filename
        backup_name = self.backup_name_var.get().strip()
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"BibleSearch_Backup_{timestamp}"
        
        backup_filename = f"{backup_name}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Check if file already exists
        if os.path.exists(backup_path):
            if not messagebox.askyesno("File Exists", 
                                      f"Backup file '{backup_filename}' already exists. Overwrite?"):
                return
        
        # Show progress
        self.progress_frame.pack(fill='x', pady=(10, 0))
        self.progress_var.set("Creating backup...")
        self.progress_bar.start(10)
        self.window.update()
        
        try:
            self._create_backup_file(backup_path)
            
            self.progress_bar.stop()
            self.progress_frame.pack_forget()
            
            messagebox.showinfo("Success", 
                               f"Backup created successfully:\n{backup_path}")
            
            # Clear the backup name for next use
            self.backup_name_var.set("")
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_frame.pack_forget()
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")
    
    def _create_backup_file(self, backup_path):
        """Create the actual backup file."""
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            
            # Backup database (subjects, verses, comments)
            db_path = find_database()
            if os.path.exists(db_path):
                backup_zip.write(db_path, "bibles.db")
            
            # Backup configuration if requested
            if self.include_config_var.get():
                if os.path.exists(self.config_manager.config_file):
                    backup_zip.write(self.config_manager.config_file, 
                                    os.path.basename(self.config_manager.config_file))
            
            # Create backup manifest
            manifest = {
                "created_date": datetime.now().isoformat(),
                "includes_config": self.include_config_var.get(),
                "database_file": "bibles.db",
                "config_file": os.path.basename(self.config_manager.config_file) if self.include_config_var.get() else None,
                "version": "1.0"
            }
            
            manifest_json = json.dumps(manifest, indent=2)
            backup_zip.writestr("backup_manifest.json", manifest_json)
    
    def refresh_backup_list(self):
        """Refresh the list of available backups."""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        backup_dir = self.restore_dir_var.get()
        if not os.path.exists(backup_dir):
            return
        
        # Find all .zip files in backup directory
        try:
            for filename in os.listdir(backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(backup_dir, filename)
                    try:
                        # Get file info
                        stat = os.stat(file_path)
                        size = self._format_file_size(stat.st_size)
                        date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        
                        # Check if it includes config by examining manifest
                        includes_config = "Unknown"
                        try:
                            with zipfile.ZipFile(file_path, 'r') as zf:
                                if 'backup_manifest.json' in zf.namelist():
                                    manifest_data = zf.read('backup_manifest.json')
                                    manifest = json.loads(manifest_data.decode())
                                    includes_config = "Yes" if manifest.get('includes_config', False) else "No"
                        except:
                            pass
                        
                        # Insert into tree
                        self.backup_tree.insert('', 'end', values=(filename, date, size, includes_config))
                    except:
                        continue
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read backup directory: {str(e)}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def restore_backup(self):
        """Restore from selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a backup to restore.")
            return
        
        # Get selected backup info
        item_values = self.backup_tree.item(selection[0])['values']
        backup_filename = item_values[0]
        backup_path = os.path.join(self.restore_dir_var.get(), backup_filename)
        
        # Confirm restoration
        if not messagebox.askyesno("Confirm Restore", 
                                  f"Are you sure you want to restore from '{backup_filename}'?\n\n"
                                  "This will replace all current subjects, verses, and comments.\n"
                                  "This action cannot be undone."):
            return
        
        # Show progress
        self.restore_progress_frame.pack(fill='x', pady=(10, 0))
        self.restore_progress_var.set("Restoring backup...")
        self.restore_progress_bar.start(10)
        self.window.update()
        
        try:
            self._restore_backup_file(backup_path)
            
            self.restore_progress_bar.stop()
            self.restore_progress_frame.pack_forget()
            
            messagebox.showinfo("Success", 
                               "Backup restored successfully!\n\n"
                               "Please restart the application to see the restored data.")
            
        except Exception as e:
            self.restore_progress_bar.stop()
            self.restore_progress_frame.pack_forget()
            messagebox.showerror("Error", f"Failed to restore backup: {str(e)}")
    
    def _restore_backup_file(self, backup_path):
        """Restore from backup file."""
        with zipfile.ZipFile(backup_path, 'r') as backup_zip:
            
            # Read manifest to understand backup contents
            manifest = {}
            if 'backup_manifest.json' in backup_zip.namelist():
                manifest_data = backup_zip.read('backup_manifest.json')
                manifest = json.loads(manifest_data.decode())
            
            # Restore database
            if 'bibles.db' in backup_zip.namelist():
                # Create backup of current database
                current_db_path = find_database()
                if os.path.exists(current_db_path):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_current = f"bibles_backup_{timestamp}.db"
                    shutil.copy2(current_db_path, backup_current)
                
                # Extract and replace database (extract to current directory)
                backup_zip.extract("bibles.db", ".")
            
            # Restore configuration if it exists in backup
            config_file = manifest.get('config_file')
            if config_file and config_file in backup_zip.namelist():
                # Ask user if they want to restore config
                restore_config = messagebox.askyesno("Restore Configuration",
                                                    "This backup includes configuration settings.\n"
                                                    "Do you want to restore them as well?")
                if restore_config:
                    # Backup current config
                    if os.path.exists(self.config_manager.config_file):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        config_backup = f"config_backup_{timestamp}.json"
                        shutil.copy2(self.config_manager.config_file, config_backup)
                    
                    # Extract and replace config
                    backup_zip.extract(config_file, ".")
                    if config_file != self.config_manager.config_file:
                        shutil.move(config_file, self.config_manager.config_file)
    
    def delete_backup(self):
        """Delete selected backup file."""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a backup to delete.")
            return
        
        item_values = self.backup_tree.item(selection[0])['values']
        backup_filename = item_values[0]
        backup_path = os.path.join(self.restore_dir_var.get(), backup_filename)
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete '{backup_filename}'?\n\n"
                              "This action cannot be undone."):
            try:
                os.remove(backup_path)
                messagebox.showinfo("Success", f"Backup '{backup_filename}' deleted successfully.")
                self.refresh_backup_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete backup: {str(e)}")

class BibleSearchInterface:
    """Main interface class for the Bible search program."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.bible_search = BibleSearch()
        self.selected_verses = []  # For subject verse management
        self.current_subject = None
        self.current_subject_id = None
        # Initialize synchronized height - force all windows to exactly the same height
        window_heights = self.config_manager.get('window_heights', {})
        # Use 120 as default for all windows, or the largest existing height if config exists
        if window_heights:
            max_height = max(window_heights.values())
            # Force all windows to the same height in config
            uniform_heights = {
                "search_window": max_height,
                "reading_window": max_height,
                "subject_verses": max_height,
                "verse_comments": max_height
            }
            self.config_manager.set('window_heights', uniform_heights)
            self.current_sync_height = max_height
        else:
            self.current_sync_height = 120
        
        self.root = tk.Tk()
        self.root.title("Bible Search Program")
        self.root.geometry(f"{self.config_manager.get('window_width')}x{self.config_manager.get('window_height')}")
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.main_frame = ttk.Frame(self.root, relief='solid', borderwidth=2)
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # Configure main frame grid
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize search settings variables
        self.case_sensitive_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('case_sensitive', False))
        self.unique_verses_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('unique_verses', False))
        self.abbreviate_results_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('abbreviate_results', False))
        
        # Advanced search settings variables
        self.synonyms_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('synonyms', False))
        self.fuzzy_match_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('fuzzy_match', False))
        self.word_stems_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('word_stems', False))
        self.within_words_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('within_words', False))
        self.wildcards_var = tk.BooleanVar(value=self.config_manager.get('search_settings', {}).get('wildcards', False))
        
        # Initialize font size
        self.current_font_size = self.config_manager.get('font_size', 10)
        
        # Create window sections
        self.create_window_sections()
        
        # Load translation settings from config
        self.load_translation_settings()
        
        # Load subjects from database
        self.load_subjects()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind resize events for width synchronization
        self.root.bind('<Configure>', self.on_window_resize)
    
    def load_translation_settings(self):
        """Load translation settings from config."""
        saved_translations = self.config_manager.get('translations', [])
        if saved_translations:
            saved_settings = {t.get('abbreviation', ''): t for t in saved_translations}
            
            for translation in self.bible_search.translations:
                saved_setting = saved_settings.get(translation.abbreviation, {})
                translation.enabled = saved_setting.get('enabled', True)
                translation.sort_order = saved_setting.get('sort_order', translation.sort_order)
            
            # Sort by sort order
            self.bible_search.translations.sort(key=lambda x: x.sort_order)
    
    def create_window_sections(self):
        """Create all six window sections."""
        
        # 1. Search Settings Window (static height)
        self.search_settings_frame = ttk.Frame(
            self.main_frame, 
            relief='solid', 
            borderwidth=1,
            height=self.config_manager.get('static_heights')['search_settings']
        )
        self.search_settings_frame.grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        self.search_settings_frame.grid_propagate(False)
        self.search_settings_frame.grid_columnconfigure(0, weight=1)
        self.create_search_settings()
        
        # 2. Message Window (static height)
        self.message_frame = ttk.Frame(
            self.main_frame, 
            relief='solid', 
            borderwidth=1,
            height=self.config_manager.get('static_heights')['message_window']
        )
        self.message_frame.grid(row=1, column=0, sticky='ew', padx=2, pady=2)
        self.message_frame.grid_propagate(False)
        self.message_frame.grid_columnconfigure(0, weight=1)
        self.create_message_window()
        
        # 3-6. Resizable Windows (all resize together with equal weight)
        self.resizable_frames = {}
        window_configs = [
            ("3. Search Results", "search_window", 2),
            ("4. Reading Window", "reading_window", 3),
            ("5. Subject Verses", "subject_verses", 4),
            ("6. Verse Comments", "verse_comments", 5)
        ]
        
        for title, key, row in window_configs:
            # Force equal starting height instead of using config
            height = 120  # Always start with equal heights
            frame = ResizableFrame(self.main_frame, title, sync_callback=self.sync_window_heights)
            frame.configure(height=height)
            frame.grid(row=row, column=0, sticky='nsew', padx=2, pady=2)
            frame.grid_propagate(False)
            # All resizable windows get the same weight for synchronized resizing
            self.main_frame.grid_rowconfigure(row, weight=1)
            self.resizable_frames[key] = frame
        
        # Create content for each window
        self.create_search_window()
        self.create_reading_window()
        self.create_subject_verses_window()
        self.create_comments_window()
        
        # Create height display at bottom
        self.create_height_display()
        
        # Force synchronization after everything is created
        self.root.after(100, self.force_initial_sync)
    
    def force_initial_sync(self):
        """Force all windows to the correct synchronized height after startup."""
        print(f"FORCE SYNC: Setting all windows to {self.current_sync_height}px")
        self.sync_window_heights(self.current_sync_height)
    
    def create_height_display(self):
        """Create a display showing current window heights in real-time."""
        # Height display frame at the very bottom
        self.height_display_frame = ttk.Frame(self.main_frame)
        self.height_display_frame.grid(row=6, column=0, sticky='ew', padx=2, pady=5)
        
        # Title
        ttk.Label(self.height_display_frame, text="Window Heights:", 
                 font=('Arial', 9, 'bold')).pack(side='left', padx=(5, 10))
        
        # Height display label
        self.height_display_label = ttk.Label(self.height_display_frame, 
                                            text="Loading...", 
                                            font=('Arial', 9),
                                            foreground='blue')
        self.height_display_label.pack(side='left')
        
        # Sync height display
        self.sync_height_label = ttk.Label(self.height_display_frame, 
                                          text=f"Sync: {self.current_sync_height}px", 
                                          font=('Arial', 9, 'bold'),
                                          foreground='red')
        self.sync_height_label.pack(side='right', padx=(10, 5))
        
        # Start updating heights
        self.update_height_display()
    
    def update_height_display(self):
        """Update the height display in real-time."""
        heights = []
        for key, frame in self.resizable_frames.items():
            height = frame.winfo_height()
            window_num = {"search_window": "3", "reading_window": "4", 
                         "subject_verses": "5", "verse_comments": "6"}[key]
            heights.append(f"Win{window_num}:{height}px")
        
        height_text = " | ".join(heights)
        self.height_display_label.configure(text=height_text)
        self.sync_height_label.configure(text=f"Sync: {self.current_sync_height}px")
        
        # Schedule next update
        self.root.after(500, self.update_height_display)
    
    def sync_window_heights(self, new_height):
        """Synchronize all resizable window heights using an ultra-aggressive approach."""
        # Ensure minimum height
        if new_height < 80:
            new_height = 80
            
        # Track the current synchronized height
        self.current_sync_height = new_height
        
        # Ultra-aggressive approach: completely override all height constraints
        for attempt in range(10):  # Try even more times
            for frame in self.resizable_frames.values():
                # Force height on the main frame
                frame.configure(height=new_height)
                frame.grid_propagate(False)
                frame.pack_propagate(False)
                
                # Also force height on the content frame inside
                if hasattr(frame, 'content_frame'):
                    content_height = new_height - 25  # Account for title label
                    frame.content_frame.configure(height=content_height)
                    frame.content_frame.grid_propagate(False)
                    frame.content_frame.pack_propagate(False)
                
            # Force grid constraints more aggressively
            for row in [2, 3, 4, 5]:  # Rows for windows 3, 4, 5, 6
                self.main_frame.grid_rowconfigure(row, minsize=new_height, weight=0)
                
            # Multiple forced updates
            self.main_frame.update_idletasks()
            self.main_frame.update()
            self.root.update_idletasks()
            
            # Force another round of height setting after updates
            for frame in self.resizable_frames.values():
                frame.configure(height=new_height)
                
        # Re-enable automatic main window resizing with correct calculation
        static_heights = self.config_manager.get('static_heights')
        total_static = static_heights['search_settings'] + static_heights['message_window']
        total_resizable = new_height * 4  # 4 resizable windows
        height_display = 30  # Height of our debug display
        total_height = total_static + total_resizable + height_display + 60  # Add padding
        current_width = self.root.winfo_width()
        
        # Resize main window to fit content
        self.root.geometry(f"{current_width}x{total_height}")
        
        # Force one final update to ensure everything is properly sized
        self.root.update_idletasks()
    
    def create_search_settings(self):
        """Create the search settings window."""
        # Title with gear button
        header_frame = ttk.Frame(self.search_settings_frame)
        header_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=2)
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ttk.Label(header_frame, text="1. Search Settings", 
                               font=('Arial', 9, 'bold'))
        title_label.grid(row=0, column=0, sticky='w')
        
        # Gear button
        self.gear_button = ttk.Button(header_frame, text="⚙", width=3)
        self.gear_button.grid(row=0, column=1, sticky='e', padx=(5, 0))
        
        # Bind mouse events to show menu on press
        self.gear_button.bind('<Button-1>', self.on_gear_button_press)
        
        self.gear_menu = None  # Store menu reference
        
        # Content frame
        content_frame = ttk.Frame(self.search_settings_frame, relief='sunken', borderwidth=1)
        content_frame.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)
        self.search_settings_frame.grid_rowconfigure(1, weight=1)
        
        # Settings checkboxes - arranged in two rows
        settings_frame = ttk.Frame(content_frame)
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        # Top row - basic settings
        basic_frame = ttk.Frame(settings_frame)
        basic_frame.pack(fill='x', pady=(0, 3))
        
        ttk.Checkbutton(basic_frame, text="Case Sensitive", 
                       variable=self.case_sensitive_var).pack(side='left', padx=(0, 15))
        ttk.Checkbutton(basic_frame, text="Unique Verse", 
                       variable=self.unique_verses_var).pack(side='left', padx=(0, 15))
        ttk.Checkbutton(basic_frame, text="Abbreviate Results", 
                       variable=self.abbreviate_results_var).pack(side='left')
        
        # Bottom row - advanced search features
        advanced_frame = ttk.Frame(settings_frame)
        advanced_frame.pack(fill='x')
        
        ttk.Checkbutton(advanced_frame, text="Synonyms", 
                       variable=self.synonyms_var).pack(side='left', padx=(0, 15))
        ttk.Checkbutton(advanced_frame, text="Fuzzy Match", 
                       variable=self.fuzzy_match_var).pack(side='left', padx=(0, 15))
        ttk.Checkbutton(advanced_frame, text="Word Stems", 
                       variable=self.word_stems_var).pack(side='left', padx=(0, 15))
        ttk.Checkbutton(advanced_frame, text="Within 5 Words", 
                       variable=self.within_words_var).pack(side='left', padx=(0, 15))
        # Note: Wildcards (*,?,!,AND,OR) are always available - see Tips for help
        wildcards_cb = ttk.Checkbutton(advanced_frame, text="(See Tips for wildcards)", 
                                      variable=self.wildcards_var, state='disabled')
        wildcards_cb.pack(side='left')
    
    def on_gear_button_press(self, event):
        """Handle gear button press - show menu."""
        # Hide any existing menu first
        if self.gear_menu:
            try:
                self.gear_menu.unpost()
                self.gear_menu.destroy()
            except:
                pass
            self.gear_menu = None
        
        # Create and show menu
        self.gear_menu = tk.Menu(self.root, tearoff=0)
        self.gear_menu.add_command(label="Translations", command=self.hide_gear_menu_and_show_translations)
        self.gear_menu.add_command(label="Font", command=self.hide_gear_menu_and_show_font)
        self.gear_menu.add_command(label="Backup", command=self.hide_gear_menu_and_show_backup)
        
        # Show menu at button location
        try:
            # Get the gear button's position
            button_x = self.gear_button.winfo_rootx()
            button_y = self.gear_button.winfo_rooty() + self.gear_button.winfo_height()
            
            # Show the menu and let tkinter handle the rest
            self.gear_menu.tk_popup(button_x, button_y)
            
            # Bind events to detect when menu should be hidden
            self.root.bind_all('<Button-1>', self.check_hide_gear_menu)
            self.root.bind_all('<Escape>', self.force_hide_gear_menu)
            
        except Exception as e:
            pass
    
    def check_hide_gear_menu(self, event):
        """Check if click is outside menu and hide if so."""
        if self.gear_menu:
            # Get the widget that was clicked
            clicked_widget = event.widget
            
            # If the click was not on the menu or gear button, hide the menu
            if clicked_widget != self.gear_menu and clicked_widget != self.gear_button:
                self.hide_gear_menu()
    
    def force_hide_gear_menu(self, event=None):
        """Force hide the gear menu (e.g., on Escape key)."""
        self.hide_gear_menu()
    
    def hide_gear_menu(self):
        """Hide the gear menu and clean up bindings."""
        if self.gear_menu:
            try:
                self.gear_menu.unpost()
                self.gear_menu.destroy()
            except:
                pass
            self.gear_menu = None
            
            # Remove global bindings
            try:
                self.root.unbind_all('<Button-1>')
                self.root.unbind_all('<Escape>')
            except:
                pass
    
    def hide_gear_menu_and_show_translations(self):
        """Hide gear menu and show translations dialog."""
        self.hide_gear_menu()
        self.show_translation_dialog()
    
    def hide_gear_menu_and_show_font(self):
        """Hide gear menu and show font dialog."""
        self.hide_gear_menu()
        self.show_font_dialog()
    
    def hide_gear_menu_and_show_backup(self):
        """Hide gear menu and show backup dialog."""
        self.hide_gear_menu()
        self.show_backup_dialog()
    
    def show_translation_dialog(self):
        """Show translation settings dialog."""
        dialog = TranslationDialog(self.root, self.bible_search, self.config_manager)
        dialog.show()
    
    def show_font_dialog(self):
        """Show font settings dialog."""
        dialog = FontDialog(self.root, self.config_manager, self.update_font_sizes)
        dialog.show()
    
    def show_backup_dialog(self):
        """Show backup/restore dialog."""
        dialog = BackupDialog(self.root, self.config_manager)
        dialog.show()
    
    def show_subject_tips(self):
        """Show subject tips dialog."""
        tips_window = tk.Toplevel(self.root)
        tips_window.title("Subject Tips")
        tips_window.geometry("650x500")
        tips_window.transient(self.root)
        tips_window.grab_set()
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(tips_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Subject Verses (Window 5) - Tips", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Content
        tips_content = """
WHAT ARE SUBJECTS?
Subjects are topical collections of Bible verses that you can create to study specific themes, topics, or concepts. This feature helps you organize verses by topic for easy reference and study.

HOW TO USE SUBJECTS:

1. CREATING A SUBJECT:
   • Type a subject name in the "Subject:" field (e.g., "Faith", "Love", "Prayer")
   • Click "Create Subject" to create a new subject or select an existing one
   • Subject names should be descriptive of the topic you want to study

2. ACQUIRING VERSES FOR SUBJECTS:
   • First, search for verses using the search function (Window 3)
   • Click on a search result to select it (it will be highlighted in blue)
   • Make sure you have a subject selected or created
   • Click "Acquire Verses" to add the selected verse to your subject
   • You can acquire multiple verses for the same subject

3. VIEWING SUBJECT VERSES:
   • Select a subject from the dropdown to see all verses associated with it
   • Verses are displayed with their translation, reference, and text
   • Click on any verse in the list to view/edit comments for that verse
   • Verses maintain their order as you add them

4. MANAGING SUBJECTS:
   • Use the dropdown to switch between different subjects
   • Click "Delete Subject" to remove a subject and all its verses (with confirmation)
   • Deleted subjects cannot be recovered unless you have a backup

EXAMPLES OF USEFUL SUBJECTS:
• "Salvation" - verses about being saved
• "God's Love" - verses showing God's love for humanity  
• "Prayer Examples" - verses showing how biblical figures prayed
• "Prophecies about Jesus" - Old Testament verses about the Messiah
• "Comfort in Trials" - verses for encouragement during difficult times
• "Christian Living" - verses about how to live as a believer

WORKFLOW TIPS:
1. Plan your subject names before starting (be specific but not too long)
2. Use the search function to find relevant verses
3. Build your subjects gradually over time
4. Review and study your collected verses regularly
5. Use the comments feature to add your own insights to verses
6. Create backups regularly to preserve your work

WHY USE SUBJECTS?
• Organize verses by topic for systematic study
• Quick access to relevant verses for specific situations
• Build comprehensive collections on important themes
• Create personalized study materials
• Prepare for teaching or sharing with others
        """
        
        text_widget = tk.Text(scrollable_frame, wrap='word', font=('Arial', 10),
                             height=25, width=75)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', tips_content)
        text_widget.configure(state='disabled')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        button_frame = ttk.Frame(tips_window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", 
                  command=tips_window.destroy).pack(side='right')
    
    def show_comment_tips(self):
        """Show comment tips dialog."""
        tips_window = tk.Toplevel(self.root)
        tips_window.title("Comment Tips")
        tips_window.geometry("650x500")
        tips_window.transient(self.root)
        tips_window.grab_set()
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(tips_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Verse Comments (Window 6) - Tips", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Content
        tips_content = """
WHAT ARE VERSE COMMENTS?
Comments are your personal notes, insights, and observations that you can attach to any verse in your subjects. This feature helps you record your thoughts and study notes for future reference.

HOW TO USE COMMENTS:

1. SELECTING A VERSE:
   • First, select a subject that contains verses
   • Click on any verse in the Subject Verses list (Window 5)
   • The verse will be highlighted, and comment buttons will become active
   • Window 6 will show any existing comment for that verse

2. ADDING COMMENTS:
   • Click "Add Comment" to start writing a new comment
   • A text editor will appear with formatting tools
   • Type your thoughts, insights, or study notes
   • Click "Save" to store your comment

3. EDITING EXISTING COMMENTS:
   • Select a verse that already has a comment
   • Click "Edit" to modify the existing comment
   • Make your changes using the full editor
   • Click "Save" to update the comment

4. FORMATTING YOUR COMMENTS:
   • Use the formatting toolbar that appears when editing
   • Bold (B): Make important points stand out
   • Italic (I): Emphasize words or add personal reflections
   • Underline (U): Highlight key concepts
   • Font Size: Adjust text size for headers or emphasis
   • Color: Use different colors for different types of notes
   • Clear Format: Remove all formatting from selected text

5. MANAGING COMMENTS:
   • Click "Delete" to remove a comment (with confirmation)
   • Comments are automatically saved when you click "Save"
   • Formatting is preserved and will display when viewing

WHAT TO INCLUDE IN COMMENTS:
• Personal insights and revelations from studying the verse
• Cross-references to other related Bible verses
• Historical or cultural context you've learned
• Application to your personal life or current situations
• Questions for further study or meditation
• Teaching points if you plan to share with others
• Prayer requests or spiritual goals related to the verse

FORMATTING EXAMPLES:
• Use BOLD for main points or key words from the verse
• Use italic for your personal thoughts and reflections
• Use different colors to categorize:
  - Blue for cross-references
  - Red for important warnings or commands
  - Green for promises and encouragements
  - Purple for prophecies or future events

STUDY WORKFLOW:
1. Select a verse from your subject collection
2. Read the verse in context (use Window 4 for surrounding verses)
3. Add your initial thoughts and questions
4. Research cross-references and add them to your comment
5. Apply the verse to your life situation
6. Update comments as you gain new insights over time

WHY USE COMMENTS?
• Remember important insights months or years later
• Build a personal commentary on Bible passages
• Track your spiritual growth and changing perspectives
• Prepare notes for teaching or sharing with others
• Create a searchable database of your study notes
• Preserve revelations and "aha moments" from your Bible study

TIPS FOR EFFECTIVE COMMENTS:
• Be specific - vague notes are less helpful later
• Date significant insights (manually in your comment)
• Ask questions that lead to deeper study
• Connect verses to current life situations
• Review and update comments periodically
• Use formatting to organize different types of information
        """
        
        text_widget = tk.Text(scrollable_frame, wrap='word', font=('Arial', 10),
                             height=25, width=75)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', tips_content)
        text_widget.configure(state='disabled')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        button_frame = ttk.Frame(tips_window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", 
                  command=tips_window.destroy).pack(side='right')
    
    def update_font_sizes(self, font_size):
        """Update font sizes for windows 3, 4, 5, and 6."""
        # Store current font size
        self.current_font_size = font_size
        
        # Window 3 - Search Results
        if hasattr(self, 'search_results_text'):
            self.search_results_text.configure(font=('DejaVu Sans Mono', font_size))
            # Update search results text tags
            self.search_results_text.tag_configure("bold", font=('DejaVu Sans Mono', font_size, 'bold'))
            # Recalculate verse tag indentation for new font size
            char_width = 7 * font_size // 10  # Adjust for font size
            indent_pixels = 16 * char_width  # Align wrapped text at position 16
            self.search_results_text.tag_configure("verse", lmargin2=f"{indent_pixels}p")
        
        # Window 4 - Reading Window  
        if hasattr(self, 'reading_text'):
            self.reading_text.configure(font=('DejaVu Sans Mono', font_size))
            # Recalculate verse tag indentation for new font size
            char_width = 7 * font_size // 10  # Adjust for font size
            indent_pixels = 16 * char_width  # Align wrapped text at position 16
            self.reading_text.tag_configure("verse", lmargin2=f"{indent_pixels}p")
        
        # Window 5 - Subject Verses
        if hasattr(self, 'subject_verses_listbox'):
            self.subject_verses_listbox.configure(font=('DejaVu Sans Mono', font_size))
        
        # Window 6 - Comments
        if hasattr(self, 'comments_text'):
            self.comments_text.configure(font=('DejaVu Sans Mono', font_size))
            # Update formatting tags with new font size
            self.setup_text_formatting_tags_with_size(font_size)
    
    def clear_search(self):
        """Clear search entry and results."""
        self.search_var.set("")
        self.search_results_text.configure(state='normal')
        self.search_results_text.delete('1.0', tk.END)
        self.search_results_text.configure(state='disabled')
        self.search_results = []
        self.selected_search_result_index = None
        self.reading_text.delete('1.0', tk.END)
        
        # Disable Clear, Clip and Export buttons when no results
        self.clear_button.configure(state='disabled')
        self.clip_button.configure(state='disabled')
        self.export_button.configure(state='disabled')
        
        self.add_message("Search cleared.")
    
    def show_search_tips(self):
        """Show search tips dialog."""
        tips_window = tk.Toplevel(self.root)
        tips_window.title("Search Tips")
        tips_window.geometry("600x500")
        tips_window.transient(self.root)
        tips_window.grab_set()
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(tips_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Bible Search Tips", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Content
        tips_content = """
WORD SEARCH:
• Basic search: love, faith, hope
• Multiple words (AND): love AND faith
• Either word (OR): love OR faith  
• Exclude words: !sin (excludes verses with "sin")
• Exact phrases: "in the beginning"

WILDCARD PATTERNS:
• * = any characters: love* (finds love, loved, loving)
• ? = single character: lo?e (finds love, lose)
• Examples: 
  - Jerusalem* (finds Jerusalem, Jerusalemites)
  - *tion (finds words ending in "tion")

VERSE REFERENCES:
• Book and verse: Gen 1:1, Genesis 1:1
• Numbered books: 1 Samuel 1:1, 2 Kings 3:4
• Verse ranges: Gen 1:1-5
• Common abbreviations: Gen, Ex, Lev, Num, etc.

SEARCH OPTIONS:
• Case Sensitive: Matches exact capitalization
• Unique Verse: Shows only one translation per verse
• Abbreviate Results: Replaces common words with dots

ADVANCED SEARCH FEATURES:
• Synonyms: Finds words with similar meanings
  - love → also searches: affection, care, devotion, adore, cherish
  - god → also searches: lord, almighty, creator, father, divine
  - faith → also searches: belief, trust, confidence, hope
• Fuzzy Match: Handles similar spellings and common typos
  - automatically finds word variations (loves, loving, loved)
• Word Stems: Finds different forms of the same word
  - love → love, loves, loving, loved, lover, etc.
• Within 5 Words: Finds terms appearing close to each other
  - "faith hope" finds verses where these words appear within 5 words

EXAMPLES:
Word Search Examples:
• "beginning" - finds all verses with "beginning"
• "God created" - finds verses with both words
• love OR charity - finds verses with either word
• faith* - finds faith, faithful, faithfulness
• !war - excludes verses containing "war"

Advanced Search Examples:
• "love" with Synonyms → finds love, affection, care, devotion
• "lov*" with Word Stems → finds love, loved, loving, lovely, lover
• "faith hope" with Within 5 Words → finds these words near each other
• Combine features: "god" with Synonyms + Stems for comprehensive results

Verse Reference Examples:
• Gen 1:1 - Genesis chapter 1, verse 1
• John 3:16 - John chapter 3, verse 16
• 1 Cor 13:4-8 - 1 Corinthians chapter 13, verses 4-8
• Ps 23 - All verses in Psalm 23

TIPS:
• Use quotes for exact phrases: "love thy neighbor"
• Combine wildcards: "Jesus*" AND "heal*"
• Try different book abbreviations if not found
• Use Translation Settings (⚙) to enable/disable versions
• Enable advanced features with checkboxes in Search Settings (row 2)
• Combine multiple advanced features for broader search results
• Synonyms work best with theological/biblical terms
• Use "Within 5 Words" for concept searches across multiple terms
        """
        
        text_widget = tk.Text(scrollable_frame, wrap='word', font=('Arial', 10),
                             height=25, width=70)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', tips_content)
        text_widget.configure(state='disabled')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        button_frame = ttk.Frame(tips_window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", 
                  command=tips_window.destroy).pack(side='right')
    
    def load_search_history(self):
        """Load search history from config."""
        self.search_history = self.config_manager.get('search_history', [])
        self.update_search_combobox()
    
    def save_search_history(self):
        """Save search history to config."""
        self.config_manager.set('search_history', self.search_history)
        self.config_manager.save_config()
    
    def add_to_search_history(self, query):
        """Add a search query to history, maintaining last 10 unique searches."""
        query = query.strip()
        if not query:
            return
        
        # Remove if already exists to move it to front
        if query in self.search_history:
            self.search_history.remove(query)
        
        # Add to front of list
        self.search_history.insert(0, query)
        
        # Keep only last 10 searches
        self.search_history = self.search_history[:10]
        
        # Update combobox and save
        self.update_search_combobox()
        self.save_search_history()
    
    def update_search_combobox(self):
        """Update the combobox with current search history."""
        self.search_entry['values'] = self.search_history
    
    def create_message_window(self):
        """Create the message display window."""
        title_label = ttk.Label(self.message_frame, text="2. Message Window", 
                               font=('Arial', 9, 'bold'))
        title_label.grid(row=0, column=0, sticky='w', padx=5, pady=2)
        
        content_frame = ttk.Frame(self.message_frame, relief='sunken', borderwidth=1)
        content_frame.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)
        self.message_frame.grid_rowconfigure(1, weight=1)
        
        # Create message display
        self.message_text = tk.Text(content_frame, height=2, wrap='word', 
                                   font=('Arial', 9), padx=3, pady=3)
        scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.message_text.yview)
        self.message_text.configure(yscrollcommand=scrollbar.set)
        
        self.message_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Add initial message
        self.add_message("Bible Search Program initialized successfully.")
    
    def create_search_window(self):
        """Create Window 3 - Search interface and results."""
        search_frame = self.resizable_frames["search_window"]
        
        # Search interface at top
        search_interface_frame = ttk.Frame(search_frame.content_frame)
        search_interface_frame.pack(fill='x', padx=5, pady=5)
        
        # Search combobox with history (left justified)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Combobox(search_interface_frame, textvariable=self.search_var,
                                        width=37, font=('Arial', 10))
        self.search_entry.pack(side='left', padx=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        
        # Initialize search history
        self.search_history = []
        self.load_search_history()
        
        # Search button (next to entry)
        search_button = ttk.Button(search_interface_frame, text="Search", 
                                  command=self.perform_search)
        search_button.pack(side='left', padx=(0, 5))
        
        # Clear button (next to search button)
        self.clear_button = ttk.Button(search_interface_frame, text="Clear", 
                                      command=self.clear_search, state='disabled')
        self.clear_button.pack(side='left', padx=(0, 5))
        
        # Export, Clip, and Tips buttons (right justified)
        self.export_button = ttk.Button(search_interface_frame, text="Export", 
                                       command=self.export_results, state='disabled')
        self.export_button.pack(side='right')
        
        self.clip_button = ttk.Button(search_interface_frame, text="Clip", 
                                     command=self.clip_search_results, state='disabled')
        self.clip_button.pack(side='right', padx=(0, 5))
        
        tips_button = ttk.Button(search_interface_frame, text="Tips", 
                                command=self.show_search_tips)
        tips_button.pack(side='right', padx=(0, 5))
        
        # Search results area
        self.search_results_frame = ttk.Frame(search_frame.content_frame)
        self.search_results_frame.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        
        # Create search results text widget with scrollbar for better formatting
        self.search_results_text = tk.Text(self.search_results_frame, 
                                          font=('DejaVu Sans Mono', self.current_font_size),
                                          state='disabled',
                                          cursor='hand2',
                                          wrap='word')
        search_scrollbar = ttk.Scrollbar(self.search_results_frame, orient='vertical',
                                        command=self.search_results_text.yview)
        self.search_results_text.configure(yscrollcommand=search_scrollbar.set)
        
        # Configure text tags for formatting
        self.search_results_text.tag_configure("bold", font=('DejaVu Sans Mono', self.current_font_size, 'bold'))
        self.search_results_text.tag_configure("highlight", background="lightblue")
        # Configure verse text tag with hanging indent to keep wrapped lines aligned near reference side
        # Using pixels - approximately 7 pixels per character in DejaVu Sans Mono
        char_width = 7 * self.current_font_size // 10  # Adjust for font size
        indent_pixels = 16 * char_width  # Align wrapped text at position 16
        self.search_results_text.tag_configure("verse", lmargin2=f"{indent_pixels}p")
        
        self.search_results_text.pack(side='left', fill='both', expand=True)
        search_scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.search_results_text.bind('<Button-1>', self.on_search_result_click)
        
        # Track current selection
        self.selected_search_result_index = None
        
        self.search_results = []  # Store actual SearchResult objects
    
    def create_reading_window(self):
        """Create Window 4 - Continuous reading display."""
        reading_frame = self.resizable_frames["reading_window"]
        
        # Create reading area with checkboxes
        self.reading_frame = ttk.Frame(reading_frame.content_frame)
        self.reading_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Create scrollable text widget for reading
        self.reading_text = tk.Text(self.reading_frame, wrap='word', font=('DejaVu Sans Mono', self.current_font_size))
        reading_scrollbar = ttk.Scrollbar(self.reading_frame, orient='vertical',
                                         command=self.reading_text.yview)
        self.reading_text.configure(yscrollcommand=reading_scrollbar.set)
        
        # Configure verse text tag with hanging indent for wrapped lines
        char_width = 7 * self.current_font_size // 10  # Adjust for font size
        indent_pixels = 16 * char_width  # Align wrapped text at position 16
        self.reading_text.tag_configure("verse", lmargin2=f"{indent_pixels}p")
        
        self.reading_text.pack(side='left', fill='both', expand=True)
        reading_scrollbar.pack(side='right', fill='y')
        
        self.reading_verses = []  # Store verses for checkbox management
    
    def create_subject_verses_window(self):
        """Create Window 5 - Subject verse management."""
        subject_frame = self.resizable_frames["subject_verses"]
        
        # Subject management interface
        subject_interface_frame = ttk.Frame(subject_frame.content_frame)
        subject_interface_frame.pack(fill='x', padx=5, pady=5)
        
        # Subject title entry and dropdown
        ttk.Label(subject_interface_frame, text="Subject:").pack(side='left', padx=(0, 5))
        
        self.subject_var = tk.StringVar()
        self.subject_combobox = ttk.Combobox(subject_interface_frame, textvariable=self.subject_var, width=30)
        self.subject_combobox.pack(side='left', padx=(0, 5))
        self.subject_combobox.bind('<<ComboboxSelected>>', self.on_subject_selected)
        
        # Create Subject button
        self.create_subject_button = ttk.Button(subject_interface_frame, text="Create",
                                               command=self.create_subject)
        self.create_subject_button.pack(side='left', padx=(0, 5))
        
        # Acquire Verse button
        self.acquire_verse_button = ttk.Button(subject_interface_frame, text="Acquire",
                                              command=self.acquire_verses, state='disabled')
        self.acquire_verse_button.pack(side='left', padx=(0, 5))
        
        # Delete Subject button
        self.delete_subject_button = ttk.Button(subject_interface_frame, text="Delete",
                                               command=self.delete_subject, state='disabled')
        self.delete_subject_button.pack(side='left', padx=(0, 5))
        
        # Clear Subject button
        self.clear_subject_button = ttk.Button(subject_interface_frame, text="Clear",
                                              command=self.clear_subject, state='disabled')
        self.clear_subject_button.pack(side='left', padx=(0, 5))
        
        # Export, Clip, and Tips buttons on the right side
        self.export_subject_button = ttk.Button(subject_interface_frame, text="Export",
                                               command=self.export_subject, state='disabled')
        self.export_subject_button.pack(side='right')
        
        self.clip_subject_button = ttk.Button(subject_interface_frame, text="Clip",
                                             command=self.clip_subject_verses, state='disabled')
        self.clip_subject_button.pack(side='right', padx=(0, 5))
        
        subject_tips_button = ttk.Button(subject_interface_frame, text="Tips",
                                        command=self.show_subject_tips)
        subject_tips_button.pack(side='right', padx=(0, 5))
        
        # Subject verses display
        self.subject_verses_frame_display = ttk.Frame(subject_frame.content_frame)
        self.subject_verses_frame_display.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        
        # Create subject verses listbox
        self.subject_verses_listbox = tk.Listbox(self.subject_verses_frame_display, 
                                                font=('DejaVu Sans Mono', self.current_font_size))
        subject_scrollbar = ttk.Scrollbar(self.subject_verses_frame_display, orient='vertical',
                                         command=self.subject_verses_listbox.yview)
        self.subject_verses_listbox.configure(yscrollcommand=subject_scrollbar.set)
        
        self.subject_verses_listbox.pack(side='left', fill='both', expand=True)
        subject_scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.subject_verses_listbox.bind('<<ListboxSelect>>', self.on_subject_verse_select)
    
    def create_comments_window(self):
        """Create Window 6 - Comments editor."""
        comments_frame = self.resizable_frames["verse_comments"]
        
        # Comment management interface
        comment_interface_frame = ttk.Frame(comments_frame.content_frame)
        comment_interface_frame.pack(fill='x', padx=5, pady=5)
        
        # Comment buttons
        self.add_comment_button = ttk.Button(comment_interface_frame, text="Add Comment",
                                            command=self.add_comment, state='disabled')
        self.add_comment_button.pack(side='left', padx=(0, 5))
        
        self.edit_comment_button = ttk.Button(comment_interface_frame, text="Edit",
                                             command=self.edit_comment, state='disabled')
        self.edit_comment_button.pack(side='left', padx=(0, 5))
        
        self.save_comment_button = ttk.Button(comment_interface_frame, text="Save",
                                             command=self.save_comment, state='disabled')
        self.save_comment_button.pack(side='left', padx=(0, 5))
        
        self.delete_comment_button = ttk.Button(comment_interface_frame, text="Delete",
                                               command=self.delete_comment, state='disabled')
        self.delete_comment_button.pack(side='left', padx=(0, 5))
        
        # Close button (for exiting edit mode without saving)
        self.close_comment_button = ttk.Button(comment_interface_frame, text="Close",
                                             command=self.close_comment_edit, state='disabled')
        self.close_comment_button.pack(side='left', padx=(0, 5))
        
        # Export, Clip, and Tips buttons (right justified)
        self.export_comment_button = ttk.Button(comment_interface_frame, text="Export",
                                               command=self.export_comment, state='disabled')
        self.export_comment_button.pack(side='right')
        
        self.clip_comment_button = ttk.Button(comment_interface_frame, text="Clip",
                                             command=self.clip_comment, state='disabled')
        self.clip_comment_button.pack(side='right', padx=(0, 5))
        
        comment_tips_button = ttk.Button(comment_interface_frame, text="Tips",
                                        command=self.show_comment_tips)
        comment_tips_button.pack(side='right', padx=(0, 5))
        
        # Formatting toolbar (initially hidden)
        self.formatting_toolbar = ttk.Frame(comments_frame.content_frame)
        
        # Text formatting buttons
        ttk.Button(self.formatting_toolbar, text="B", width=3,
                  command=self.toggle_bold).pack(side='left', padx=2)
        ttk.Button(self.formatting_toolbar, text="I", width=3,
                  command=self.toggle_italic).pack(side='left', padx=2)
        ttk.Button(self.formatting_toolbar, text="U", width=3,
                  command=self.toggle_underline).pack(side='left', padx=2)
        
        # Font size
        ttk.Label(self.formatting_toolbar, text="Size:").pack(side='left', padx=(10, 2))
        self.font_size_var = tk.StringVar(value="10")
        font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20"]
        self.font_size_combo = ttk.Combobox(self.formatting_toolbar, textvariable=self.font_size_var,
                                           values=font_sizes, width=5, state='readonly')
        self.font_size_combo.pack(side='left', padx=2)
        self.font_size_combo.bind('<<ComboboxSelected>>', self.change_font_size)
        
        # Text color
        ttk.Label(self.formatting_toolbar, text="Color:").pack(side='left', padx=(10, 2))
        ttk.Button(self.formatting_toolbar, text="Color", width=6,
                  command=self.choose_text_color).pack(side='left', padx=2)
        
        # Clear formatting
        ttk.Button(self.formatting_toolbar, text="Clear Format", width=12,
                  command=self.clear_formatting).pack(side='left', padx=(10, 2))
        
        # Comments text area
        self.comments_frame_display = ttk.Frame(comments_frame.content_frame)
        self.comments_frame_display.pack(fill='both', expand=True, padx=2, pady=(0, 2))
        
        # Create comments text widget with RTF capabilities
        self.comments_text = tk.Text(self.comments_frame_display, wrap='word', 
                                    font=('DejaVu Sans Mono', self.current_font_size), state='disabled')
        comments_scrollbar = ttk.Scrollbar(self.comments_frame_display, orient='vertical',
                                          command=self.comments_text.yview)
        self.comments_text.configure(yscrollcommand=comments_scrollbar.set)
        
        # Configure text tags for RTF formatting
        self.setup_text_formatting_tags()
        
        # Bind events to handle placeholder text and formatting
        self.comments_text.bind('<Button-1>', self.on_comment_click)
        self.comments_text.bind('<KeyPress>', self.on_comment_keypress)
        self.comments_text.bind('<ButtonRelease-1>', self.update_formatting_buttons)
        self.comments_text.bind('<KeyRelease>', self.update_formatting_buttons)
        
        self.comments_text.pack(side='left', fill='both', expand=True)
        comments_scrollbar.pack(side='right', fill='y')
        
        self.comment_placeholder_active = False
        self.current_formatting = {'bold': False, 'italic': False, 'underline': False, 
                                  'font_size': 10, 'text_color': 'black'}
    
    def add_message(self, message: str):
        """Add a message to the message window."""
        self.message_text.insert('end', f"{message}\n")
        # Scroll to show the most recent messages properly
        # Since we have a 2-line display, position so the latest message is visible
        total_lines = int(self.message_text.index('end-1c').split('.')[0])
        if total_lines > 2:
            # Show the last 2 lines by scrolling to the line that puts them in view
            target_line = max(1, total_lines - 1)
            self.message_text.see(f'{target_line}.0')
        else:
            # If we have 2 or fewer lines, just show from the beginning
            self.message_text.see('1.0')
    
    def perform_search(self):
        """Perform search based on current settings."""
        query = self.search_var.get().strip()
        if not query:
            self.add_message("Please enter a search term.")
            return
        
        # Add to search history
        self.add_to_search_history(query)
        
        # Get enabled translations
        enabled_translations = [t.abbreviation for t in self.bible_search.translations if t.enabled]
        if not enabled_translations:
            self.add_message("No translations enabled. Please check translation settings.")
            return
        
        # Get search settings
        case_sensitive = self.case_sensitive_var.get()
        unique_verses = self.unique_verses_var.get()
        abbreviate_results = self.abbreviate_results_var.get()
        
        # Get advanced search settings
        use_synonyms = self.synonyms_var.get()
        use_fuzzy = self.fuzzy_match_var.get()
        use_stems = self.word_stems_var.get()
        use_within_words = self.within_words_var.get()
        use_wildcards = self.wildcards_var.get()
        
        # Expand query based on advanced search options
        expanded_queries = self.expand_search_query(query, use_synonyms, use_fuzzy, use_stems, use_within_words, use_wildcards)
        
        # Show active advanced features
        active_features = []
        if use_synonyms: active_features.append("Synonyms")
        if use_fuzzy: active_features.append("Fuzzy")
        if use_stems: active_features.append("Stems") 
        if use_within_words: active_features.append("Within 5")
        # Note: Wildcards are always available, no need to show as feature
        
        if active_features:
            self.add_message(f"Searching for: '{query}' (with {', '.join(active_features)})")
        else:
            self.add_message(f"Searching for: '{query}'...")
        
        # Start timing the search
        search_start_time = time.time()
        
        try:
            # Perform search with expanded queries
            all_results = []
            
            for search_query in expanded_queries:
                try:
                    results = self.bible_search.search_verses(
                        query=search_query,
                        enabled_translations=enabled_translations,
                        case_sensitive=case_sensitive,
                        unique_verses=False,  # Handle uniqueness after combining
                        abbreviate_results=abbreviate_results
                    )
                    all_results.extend(results)
                except Exception as e:
                    # If one query fails, continue with others
                    self.add_message(f"Query '{search_query}' failed: {str(e)}")
            
            # Remove duplicates if unique_verses is enabled
            if unique_verses and all_results:
                seen_verses = set()
                unique_results = []
                for result in all_results:
                    verse_key = f"{result.book} {result.chapter}:{result.verse}"
                    if verse_key not in seen_verses:
                        seen_verses.add(verse_key)
                        unique_results.append(result)
                self.search_results = unique_results
            else:
                self.search_results = all_results
            
            # Calculate search time
            search_time = time.time() - search_start_time
            
            # Clear previous results
            self.search_results_text.configure(state='normal')
            self.search_results_text.delete('1.0', tk.END)
            
            # Display results with formatting
            for i, result in enumerate(self.search_results):
                # Format: "KJV Gen 1:1 In the beginning God created..."
                reference = f"{result.translation} {result.book} {result.chapter}:{result.verse}"
                verse_text = result.highlighted_text
                
                # Calculate padding to align verse text at position 17
                # Reference + padding should equal 16 characters (position 16 is the separating space)
                padding_needed = 16 - len(reference)
                prefix_text = reference + " " * padding_needed
                
                # Mark the start position for applying verse tag
                line_start = self.search_results_text.index(tk.INSERT)
                
                # Insert prefix without formatting
                self.search_results_text.insert(tk.END, prefix_text)
                
                # Process verse text for bold bracketed terms
                self.insert_formatted_text(verse_text, i)
                
                # Mark the end position and apply verse tag to entire line
                line_end = self.search_results_text.index(tk.INSERT)
                self.search_results_text.tag_add("verse", line_start, line_end)
                
                # Add newline for next result
                if i < len(self.search_results) - 1:
                    self.search_results_text.insert(tk.END, "\n")
            
            self.search_results_text.configure(state='disabled')
            
            # Enable/disable Clear, Clip and Export buttons based on results
            if self.search_results:
                self.clear_button.configure(state='normal')
                self.clip_button.configure(state='normal')
                self.export_button.configure(state='normal')
            else:
                self.clear_button.configure(state='disabled')
                self.clip_button.configure(state='disabled')
                self.export_button.configure(state='disabled')
            
            # Update message with total count, unique count, and timing
            result_count = len(self.search_results)
            
            # Calculate unique verses (by book, chapter, verse combination)
            unique_verses = set()
            for result in self.search_results:
                verse_key = f"{result.book} {result.chapter}:{result.verse}"
                unique_verses.add(verse_key)
            unique_count = len(unique_verses)
            
            # Format timing (always show in seconds)
            time_str = f"{search_time:.3f}s"
            
            self.add_message(f"Search completed. Found {result_count} results ({unique_count} unique) in {time_str}.")
            
            # Enable export button if results exist
            if result_count > 0:
                # Find export button and enable it
                search_frame = self.resizable_frames["search_window"]
                for child in search_frame.content_frame.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for button in child.winfo_children():
                            if isinstance(button, ttk.Button) and button.cget('text') == 'Export':
                                button.configure(state='normal')
                                break
        
        except Exception as e:
            self.add_message(f"Search error: {str(e)}")
    
    def insert_formatted_text(self, text, line_index):
        """Insert text with bold formatting for bracketed terms."""
        import re
        
        # Find all bracketed terms and their positions
        pattern = r'\[([^\]]+)\]'
        last_end = 0
        
        for match in re.finditer(pattern, text):
            # Insert text before the bracket
            if match.start() > last_end:
                self.search_results_text.insert(tk.END, text[last_end:match.start()])
            
            # Insert the bracketed term with bold formatting
            start_pos = self.search_results_text.index(tk.INSERT)
            self.search_results_text.insert(tk.END, match.group(1))  # Insert without brackets
            end_pos = self.search_results_text.index(tk.INSERT)
            
            # Apply bold formatting to the inserted term
            self.search_results_text.tag_add("bold", start_pos, end_pos)
            
            last_end = match.end()
        
        # Insert any remaining text after the last bracket
        if last_end < len(text):
            self.search_results_text.insert(tk.END, text[last_end:])
    
    def on_search_result_click(self, event):
        """Handle click in search results text widget."""
        # Get the line number that was clicked
        click_index = self.search_results_text.index(f"@{event.x},{event.y}")
        line_num = int(click_index.split('.')[0]) - 1
        
        if 0 <= line_num < len(self.search_results):
            # Clear previous highlight
            self.search_results_text.tag_remove("highlight", "1.0", tk.END)
            
            # Highlight the clicked line
            line_start = f"{line_num + 1}.0"
            line_end = f"{line_num + 2}.0"
            self.search_results_text.tag_add("highlight", line_start, line_end)
            
            # Update selection
            self.selected_search_result_index = line_num
            selected_result = self.search_results[line_num]
            
            # Update reading window with continuous verses
            self.update_reading_window(selected_result)
    
    def clip_search_results(self):
        """Copy all search results to clipboard."""
        if not self.search_results:
            self.add_message("No search results to copy.")
            return
        
        try:
            # Format results for clipboard
            clipboard_text = "Bible Search Results\n"
            clipboard_text += "=" * 20 + "\n\n"
            
            for result in self.search_results:
                reference = f"{result.translation} {result.book} {result.chapter}:{result.verse}"
                padding_needed = 16 - len(reference)
                prefix_text = reference + " " * padding_needed
                # Remove highlighting brackets for clean text
                clean_text = result.highlighted_text.replace('[', '').replace(']', '')
                clipboard_text += f"{prefix_text}{clean_text}\n"
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            self.add_message(f"Copied {len(self.search_results)} verses to clipboard.")
            
        except Exception as e:
            self.add_message(f"Error copying to clipboard: {str(e)}")

    def export_results(self):
        """Export search results to text file."""
        if not self.search_results:
            self.add_message("No search results to export.")
            return
        
        # Ask user for file location
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~"),
            title="Export Search Results"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Bible Search Results\n")
                    f.write(f"Query: {self.search_var.get()}\n")
                    f.write(f"Results: {len(self.search_results)}\n")
                    f.write("="*50 + "\n\n")
                    
                    for result in self.search_results:
                        f.write(f"{result.translation} {result.book} {result.chapter}:{result.verse} {result.text}\n")
                
                self.add_message(f"Results exported to: {filename}")
            except Exception as e:
                self.add_message(f"Export error: {str(e)}")
    
    
    def update_reading_window(self, selected_result: SearchResult):
        """Update reading window with continuous verses."""
        # Update title
        translation_obj = next((t for t in self.bible_search.translations 
                               if t.abbreviation == selected_result.translation), None)
        if translation_obj:
            title = f"4. Reading Window: {translation_obj.full_name}"
            self.resizable_frames["reading_window"].title_label.configure(text=title)
        
        # Get continuous reading verses
        continuous_verses = self.bible_search.get_continuous_reading(
            translation=selected_result.translation,
            book=selected_result.book,
            chapter=selected_result.chapter,
            start_verse=selected_result.verse,
            num_verses=20  # Adjust based on window size
        )
        
        # Clear and update reading text
        self.reading_text.delete('1.0', tk.END)
        self.reading_verses = continuous_verses
        
        for i, verse in enumerate(continuous_verses):
            # Format with proper spacing like search results
            reference = f"{verse.translation} {verse.book} {verse.chapter}:{verse.verse}"
            padding_needed = 16 - len(reference)
            prefix_text = reference + " " * padding_needed
            verse_text = verse.text
            
            # Mark the start position for applying verse tag
            line_start = self.reading_text.index(tk.INSERT)
            
            # Insert the formatted verse
            self.reading_text.insert(tk.END, f"{prefix_text}{verse_text}")
            
            # Mark the end position and apply verse tag to entire line
            line_end = self.reading_text.index(tk.INSERT)
            self.reading_text.tag_add("verse", line_start, line_end)
            
            # Add newline for next verse (except for the last one)
            if i < len(continuous_verses) - 1:
                self.reading_text.insert(tk.END, "\n")
    
    def sync_reading_window_to_verse(self, verse_data):
        """Sync reading window to show the selected subject verse."""
        try:
            # Parse the verse reference to get book, chapter, verse
            reference = verse_data['reference']  # e.g., "Gen 1:1"
            translation = verse_data['translation']
            
            # Parse reference - handle different formats
            if ':' in reference:
                book_chapter, verse_num = reference.rsplit(':', 1)
                if ' ' in book_chapter:
                    book = ' '.join(book_chapter.split()[:-1])
                    chapter = int(book_chapter.split()[-1])
                else:
                    # Handle single word books like "Revelation"
                    book = book_chapter
                    chapter = 1
                verse = int(verse_num)
            else:
                # Handle references without verse (shouldn't happen but just in case)
                parts = reference.split()
                book = ' '.join(parts[:-1]) if len(parts) > 1 else parts[0]
                chapter = int(parts[-1]) if len(parts) > 1 else 1
                verse = 1
            
            # Create a SearchResult-like object to pass to update_reading_window
            class VerseRef:
                def __init__(self, translation, book, chapter, verse):
                    self.translation = translation
                    self.book = book
                    self.chapter = chapter
                    self.verse = verse
            
            verse_ref = VerseRef(translation, book, chapter, verse)
            
            # Update the reading window
            self.update_reading_window(verse_ref)
            
        except Exception as e:
            # If parsing fails, show an error message but don't crash
            self.add_message(f"Could not sync reading window: {str(e)}")
    
    def expand_search_query(self, query, use_synonyms, use_fuzzy, use_stems, use_within_words, use_wildcards):
        """Expand search query based on advanced search options."""
        expanded_terms = set([query])  # Start with original query
        
        words = query.split()
        
        for word in words:
            word_lower = word.lower()
            
            # Synonyms expansion
            if use_synonyms:
                synonyms = self.get_synonyms(word_lower)
                expanded_terms.update(synonyms)
            
            # Fuzzy matching (similar spellings)
            if use_fuzzy:
                fuzzy_matches = self.get_fuzzy_matches(word_lower)
                expanded_terms.update(fuzzy_matches)
            
            # Word stems (different forms of the same word)
            if use_stems:
                stem_variants = self.get_stem_variants(word_lower)
                expanded_terms.update(stem_variants)
            
            # Note: Wildcards are already supported natively by the search engine
        
        # Within N words handling (modify query structure)
        if use_within_words and len(words) > 1:
            within_query = f"NEAR({' '.join(words)}, 5)"
            expanded_terms.add(within_query)
        
        return list(expanded_terms)
    
    def get_synonyms(self, word):
        """Get synonyms for a word. Basic implementation - can be enhanced."""
        synonym_dict = {
            'love': ['affection', 'care', 'devotion', 'adore', 'cherish'],
            'god': ['lord', 'almighty', 'creator', 'father', 'divine'],
            'good': ['righteous', 'virtuous', 'holy', 'pure', 'blessed'],
            'evil': ['wicked', 'sin', 'darkness', 'iniquity', 'corruption'],
            'peace': ['tranquility', 'harmony', 'calm', 'serenity'],
            'joy': ['happiness', 'delight', 'gladness', 'rejoice'],
            'fear': ['afraid', 'terror', 'dread', 'anxiety'],
            'faith': ['belief', 'trust', 'confidence', 'hope'],
            'light': ['illumination', 'brightness', 'radiance'],
            'dark': ['darkness', 'shadow', 'night', 'gloom'],
            'heart': ['soul', 'spirit', 'mind', 'conscience'],
            'kingdom': ['reign', 'dominion', 'rule', 'throne'],
            'praise': ['worship', 'glorify', 'honor', 'exalt'],
            'prayer': ['supplication', 'petition', 'intercession'],
            'wisdom': ['knowledge', 'understanding', 'insight', 'prudence']
        }
        return synonym_dict.get(word, [])
    
    def get_fuzzy_matches(self, word):
        """Get fuzzy matches for a word (similar spellings)."""
        # Simple fuzzy matching - can be enhanced with algorithms like Levenshtein
        fuzzy_variants = []
        if len(word) > 3:
            # Common variations
            if word.endswith('s'):
                fuzzy_variants.append(word[:-1])  # Remove plural 's'
            if word.endswith('ed'):
                fuzzy_variants.append(word[:-2])  # Remove past tense 'ed'
            if word.endswith('ing'):
                fuzzy_variants.append(word[:-3])  # Remove 'ing'
        return fuzzy_variants
    
    def get_stem_variants(self, word):
        """Get stem variants of a word (different forms)."""
        stem_variants = []
        
        # Basic stemming rules
        if len(word) > 3:
            # Add common endings
            base_word = word
            if word.endswith('s'):
                base_word = word[:-1]
            elif word.endswith('ed'):
                base_word = word[:-2]
            elif word.endswith('ing'):
                base_word = word[:-3]
            
            # Generate variants from base
            variants = [
                base_word,
                base_word + 's',
                base_word + 'ed',
                base_word + 'ing',
                base_word + 'er',
                base_word + 'est'
            ]
            stem_variants.extend([v for v in variants if v != word and len(v) > 2])
        
        return stem_variants
    
    def create_subject(self):
        """Create a new subject."""
        subject_name = self.subject_var.get().strip()
        if not subject_name:
            self.add_message("Please enter a subject name.")
            return
        
        try:
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            
            # Check if subject already exists
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
            existing = cursor.fetchone()
            
            if existing:
                self.current_subject_id = existing[0]
                self.add_message(f"Subject '{subject_name}' selected.")
            else:
                # Create new subject
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
                self.current_subject_id = cursor.lastrowid
                conn.commit()
                self.add_message(f"Subject '{subject_name}' created.")
            
            conn.close()
            
            # Update combobox values
            self.load_subjects()
            self.current_subject = subject_name
            
            # Update button states for created/selected subject
            self.create_subject_button.configure(state='disabled')  # Can't create when subject is selected
            self.acquire_verse_button.configure(state='normal')
            self.delete_subject_button.configure(state='normal')
            self.clear_subject_button.configure(state='normal')
            self.clip_subject_button.configure(state='normal')  # Can clip subject verses
            self.export_subject_button.configure(state='normal')
            
            # Load verses for this subject
            self.load_subject_verses()
            
        except Exception as e:
            self.add_message(f"Error creating subject: {str(e)}")
    
    def load_subjects(self):
        """Load subjects from database into combobox."""
        try:
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM subjects ORDER BY name")
            subjects = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self.subject_combobox['values'] = subjects
        except Exception as e:
            self.add_message(f"Error loading subjects: {str(e)}")
    
    def on_subject_selected(self, event):
        """Handle subject selection from combobox."""
        subject_name = self.subject_var.get().strip()
        if subject_name:
            try:
                conn = sqlite3.connect(find_database())
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    self.current_subject_id = result[0]
                    self.current_subject = subject_name
                    
                    # Update button states for selected subject
                    self.create_subject_button.configure(state='disabled')  # Can't create when subject is selected
                    self.acquire_verse_button.configure(state='normal')
                    self.delete_subject_button.configure(state='normal')
                    self.clear_subject_button.configure(state='normal')
                    self.clip_subject_button.configure(state='normal')  # Can clip subject verses
                    self.export_subject_button.configure(state='normal')
                    
                    self.load_subject_verses()
                    self.add_message(f"Selected subject: '{subject_name}'")
                    
            except Exception as e:
                self.add_message(f"Error selecting subject: {str(e)}")
    
    def load_subject_verses(self):
        """Load verses for current subject."""
        if not self.current_subject_id:
            return
            
        try:
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT verse_reference, translation, verse_text, comments, id 
                FROM subject_verses 
                WHERE subject_id = ? 
                ORDER BY order_index
            """, (self.current_subject_id,))
            
            verses = cursor.fetchall()
            conn.close()
            
            # Clear and populate listbox
            self.subject_verses_listbox.delete(0, tk.END)
            self.subject_verse_data = []
            
            for verse_ref, translation, verse_text, comments, verse_id in verses:
                # Format with proper spacing like search results
                reference = f"{translation} {verse_ref}"
                padding_needed = 16 - len(reference)
                prefix_text = reference + " " * padding_needed
                display_text = f"{prefix_text}{verse_text}"
                self.subject_verses_listbox.insert(tk.END, display_text)
                self.subject_verse_data.append({
                    'id': verse_id,
                    'reference': verse_ref,
                    'translation': translation,
                    'text': verse_text,
                    'comments': comments or ""
                })
                
        except Exception as e:
            self.add_message(f"Error loading subject verses: {str(e)}")
    
    def acquire_verses(self):
        """Acquire selected verses for current subject."""
        if not self.current_subject_id:
            self.add_message("Please create or select a subject first.")
            return
        
        # Get selected verse from search results
        acquired_count = 0
        
        if self.selected_search_result_index is not None and self.selected_search_result_index < len(self.search_results):
            try:
                conn = sqlite3.connect(find_database())
                cursor = conn.cursor()
                
                # Add selected search result
                result = self.search_results[self.selected_search_result_index]
                verse_reference = f"{result.book} {result.chapter}:{result.verse}"
                
                # Check if verse already exists for this subject
                cursor.execute("""
                    SELECT id FROM subject_verses 
                    WHERE subject_id = ? AND verse_reference = ? AND translation = ?
                """, (self.current_subject_id, verse_reference, result.translation))
                
                if not cursor.fetchone():
                    # Get next order index
                    cursor.execute("""
                        SELECT COALESCE(MAX(order_index), 0) + 1 
                        FROM subject_verses 
                        WHERE subject_id = ?
                    """, (self.current_subject_id,))
                    next_order = cursor.fetchone()[0]
                    
                    # Insert verse
                    cursor.execute("""
                        INSERT INTO subject_verses 
                        (subject_id, verse_reference, translation, verse_text, order_index)
                        VALUES (?, ?, ?, ?, ?)
                    """, (self.current_subject_id, verse_reference, result.translation, result.text, next_order))
                    acquired_count = 1
                
                conn.commit()
                conn.close()
                
                # Reload verses to show new additions
                self.load_subject_verses()
                
                if acquired_count > 0:
                    self.add_message(f"Acquired {acquired_count} verse for subject '{self.current_subject}'.")
                else:
                    self.add_message("Verse already exists for this subject.")
                    
            except Exception as e:
                self.add_message(f"Error acquiring verses: {str(e)}")
        else:
            self.add_message("Please select a verse from the search results first.")
    
    def delete_subject(self):
        """Delete the current subject and all its verses."""
        if not self.current_subject_id or not self.current_subject:
            self.add_message("Please select a subject first.")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Delete Subject", 
                                  f"Are you sure you want to delete subject '{self.current_subject}' and all its verses?\n\nThis action cannot be undone."):
            return
        
        try:
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            
            # Delete all verses for this subject first
            cursor.execute("DELETE FROM subject_verses WHERE subject_id = ?", (self.current_subject_id,))
            
            # Delete the subject
            cursor.execute("DELETE FROM subjects WHERE id = ?", (self.current_subject_id,))
            
            conn.commit()
            conn.close()
            
            # Save subject name for message before clearing
            deleted_subject_name = self.current_subject
            
            # Clear UI and reset state
            self.current_subject_id = None
            self.current_subject = None
            self.subject_var.set("")
            
            # Clear subject verses listbox
            self.subject_verses_listbox.delete(0, tk.END)
            if hasattr(self, 'subject_verse_data'):
                self.subject_verse_data = []
            
            # Clear comments
            self.comments_text.configure(state='normal')
            self.comments_text.delete('1.0', tk.END)
            self.comments_text.configure(state='disabled')
            
            # Update button states for no subject selected
            self.create_subject_button.configure(state='normal')  # Can create new subject
            self.acquire_verse_button.configure(state='disabled')
            self.delete_subject_button.configure(state='disabled')
            self.clear_subject_button.configure(state='disabled')
            self.clip_subject_button.configure(state='disabled')
            self.export_subject_button.configure(state='disabled')
            self.add_comment_button.configure(state='disabled')
            self.edit_comment_button.configure(state='disabled')
            self.save_comment_button.configure(state='disabled')
            self.delete_comment_button.configure(state='disabled')
            self.clip_comment_button.configure(state='disabled')
            self.export_comment_button.configure(state='disabled')
            
            # Reset selected verse data
            if hasattr(self, 'selected_verse_data'):
                self.selected_verse_data = None
            
            # Reload subjects combobox
            self.load_subjects()
            
            self.add_message(f"Subject '{deleted_subject_name}' deleted successfully.")
            
        except Exception as e:
            self.add_message(f"Error deleting subject: {str(e)}")
    
    def on_subject_verse_select(self, event):
        """Handle subject verse selection."""
        selection = self.subject_verses_listbox.curselection()
        if selection and hasattr(self, 'subject_verse_data'):
            index = selection[0]
            if index < len(self.subject_verse_data):
                self.selected_verse_data = self.subject_verse_data[index]
                
                # Load existing comment first to determine button states
                self.comments_text.configure(state='normal')
                self.comments_text.delete('1.0', tk.END)
                
                # Set button states based on whether verse already has a comment
                if self.selected_verse_data['comments']:
                    # Verse has existing comment - disable Add Comment, enable Edit and Delete
                    self.add_comment_button.configure(state='disabled')  # Can't add to existing comment
                    self.edit_comment_button.configure(state='normal')
                    self.delete_comment_button.configure(state='normal')
                    self.clip_comment_button.configure(state='normal')  # Can copy existing comment
                    self.export_comment_button.configure(state='normal')  # Can export existing comment
                    
                    # Load the existing comment
                    self.load_formatted_comment(self.selected_verse_data['comments'])
                    self.comment_placeholder_active = False
                    self.comments_text.configure(fg='black')
                else:
                    # Verse has no comment - enable Add Comment, disable Edit and Delete
                    self.add_comment_button.configure(state='normal')  # Can add new comment
                    self.edit_comment_button.configure(state='disabled')  # Nothing to edit
                    self.delete_comment_button.configure(state='disabled')  # Nothing to delete
                    self.clip_comment_button.configure(state='disabled')  # Nothing to copy
                    self.export_comment_button.configure(state='disabled')  # Nothing to export
                    
                    # Show empty comment area
                    self.comments_text.insert('1.0', "")
                    self.comment_placeholder_active = False
                    self.comments_text.configure(fg='black')
                
                # Save button always starts disabled until entering edit mode
                self.save_comment_button.configure(state='disabled')
                
                # Close button enabled if there's an existing comment to view, disabled if no comment
                if self.selected_verse_data['comments']:
                    self.close_comment_button.configure(state='normal')  # User can close viewing mode
                else:
                    self.close_comment_button.configure(state='disabled')  # Nothing to close
                self.comments_text.configure(state='disabled')
                
                # Hide formatting toolbar when just viewing
                self.hide_formatting_toolbar()
                
                # Sync reading window to show this verse
                self.sync_reading_window_to_verse(self.selected_verse_data)
        else:
            # Disable comment buttons
            self.add_comment_button.configure(state='disabled')
            self.edit_comment_button.configure(state='disabled')
            self.save_comment_button.configure(state='disabled')
            self.delete_comment_button.configure(state='disabled')
            self.close_comment_button.configure(state='disabled')
            self.clip_comment_button.configure(state='disabled')
            self.export_comment_button.configure(state='disabled')
            self.selected_verse_data = None
    
    def add_comment(self):
        """Add a comment to selected verse."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            self.add_message("Please select a verse first.")
            return
            
        self.comments_text.configure(state='normal')
        self.comments_text.delete('1.0', tk.END)
        
        # Show formatting toolbar
        self.show_formatting_toolbar()
        
        if not self.selected_verse_data['comments']:
            self.comments_text.insert('1.0', "Enter your comment here...")
            self.comment_placeholder_active = True
            # Set placeholder text color to gray
            self.comments_text.configure(fg='gray')
        else:
            # Load formatted text (assume it's already formatted if it exists)
            self.load_formatted_comment(self.selected_verse_data['comments'])
            self.comment_placeholder_active = False
            self.comments_text.configure(fg='black')
        
        # Enable Save and Close buttons when entering edit mode
        self.save_comment_button.configure(state='normal')
        self.close_comment_button.configure(state='normal')
        self.add_message("Comment editor opened. Edit and save your comment.")
    
    def edit_comment(self):
        """Edit existing comment."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            self.add_message("Please select a verse first.")
            return
            
        self.comments_text.configure(state='normal')
        
        # Show formatting toolbar
        self.show_formatting_toolbar()
        
        # If there's existing comment text, load it; otherwise show placeholder
        if self.selected_verse_data['comments']:
            self.comments_text.delete('1.0', tk.END)
            self.load_formatted_comment(self.selected_verse_data['comments'])
            self.comment_placeholder_active = False
            self.comments_text.configure(fg='black')
        else:
            self.comments_text.delete('1.0', tk.END)
            self.comments_text.insert('1.0', "Enter your comment here...")
            self.comment_placeholder_active = True
            self.comments_text.configure(fg='gray')
        
        # Enable Save and Close buttons when entering edit mode
        self.save_comment_button.configure(state='normal')
        self.close_comment_button.configure(state='normal')
        self.add_message("Comment editor enabled. Make your changes and save.")
    
    def save_comment(self):
        """Save comment for selected verse."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            self.add_message("Please select a verse first.")
            return
            
        comment_text = self.comments_text.get('1.0', 'end-1c')
        
        # Don't save if it's just the placeholder text
        if self.comment_placeholder_active and comment_text == "Enter your comment here...":
            comment_text = ""
        
        # Save formatted text as RTF-like format
        formatted_comment = self.save_formatted_comment()
        
        try:
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            
            # Update comment in database with formatting
            cursor.execute("""
                UPDATE subject_verses 
                SET comments = ? 
                WHERE id = ?
            """, (formatted_comment, self.selected_verse_data['id']))
            
            conn.commit()
            conn.close()
            
            # Update local data
            self.selected_verse_data['comments'] = formatted_comment
            self.comment_placeholder_active = False
            
            # Hide formatting toolbar and disable text
            self.hide_formatting_toolbar()
            self.comments_text.configure(state='disabled', fg='black')
            
            # Update button states after saving - now there's an existing comment
            self.add_comment_button.configure(state='disabled')  # Can't add to existing comment
            self.edit_comment_button.configure(state='normal')  # Can edit existing comment
            self.delete_comment_button.configure(state='normal')  # Can delete existing comment
            self.clip_comment_button.configure(state='normal')  # Can copy existing comment
            self.export_comment_button.configure(state='normal')  # Can export existing comment
            self.save_comment_button.configure(state='disabled')  # Not in edit mode
            self.close_comment_button.configure(state='normal')  # User can close/exit viewing mode
            
            self.add_message("Comment saved successfully.")
            
        except Exception as e:
            self.add_message(f"Error saving comment: {str(e)}")
    
    def delete_comment(self):
        """Delete comment for selected verse."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            self.add_message("Please select a verse first.")
            return
            
        if messagebox.askyesno("Delete Comment", "Are you sure you want to delete this comment?"):
            try:
                conn = sqlite3.connect(find_database())
                cursor = conn.cursor()
                
                # Clear comment in database
                cursor.execute("""
                    UPDATE subject_verses 
                    SET comments = NULL 
                    WHERE id = ?
                """, (self.selected_verse_data['id'],))
                
                conn.commit()
                conn.close()
                
                # Update local data and display
                self.selected_verse_data['comments'] = ""
                self.comments_text.configure(state='normal')
                self.comments_text.delete('1.0', tk.END)
                self.comments_text.configure(state='disabled')
                
                # Update button states - now that comment is deleted, enable Add Comment, disable Edit/Delete
                self.add_comment_button.configure(state='normal')  # Can now add comment
                self.edit_comment_button.configure(state='disabled')  # Nothing to edit
                self.delete_comment_button.configure(state='disabled')  # Nothing to delete
                self.clip_comment_button.configure(state='disabled')  # Nothing to copy
                self.export_comment_button.configure(state='disabled')  # Nothing to export
                self.save_comment_button.configure(state='disabled')  # Not in edit mode
                self.close_comment_button.configure(state='disabled')  # Not in edit mode
                
                self.add_message("Comment deleted.")
                
            except Exception as e:
                self.add_message(f"Error deleting comment: {str(e)}")
    
    def close_comment_edit(self):
        """Close comment editing without saving changes, or exit comment viewing mode."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            return
        
        # Check if we're in edit mode (text widget is enabled) or viewing mode (disabled)
        is_editing = str(self.comments_text.cget('state')) == 'normal'
        
        if is_editing:
            # In edit mode - cancel editing and restore original content
            self.comments_text.delete('1.0', tk.END)
            
            # Reload the original comment if it exists
            if self.selected_verse_data['comments']:
                self.load_formatted_comment(self.selected_verse_data['comments'])
                self.comment_placeholder_active = False
                self.comments_text.configure(fg='black')
            else:
                self.comments_text.insert('1.0', "")
                self.comment_placeholder_active = False
                self.comments_text.configure(fg='black')
            
            # Disable the text widget and hide formatting toolbar
            self.comments_text.configure(state='disabled')
            self.hide_formatting_toolbar()
            
            # Reset button states based on whether the verse has a comment
            if self.selected_verse_data['comments']:
                # Verse has comment - disable Add Comment, enable Edit and Delete, enable Close for viewing
                self.add_comment_button.configure(state='disabled')
                self.edit_comment_button.configure(state='normal')
                self.delete_comment_button.configure(state='normal')
                self.clip_comment_button.configure(state='normal')  # Can copy existing comment
                self.export_comment_button.configure(state='normal')  # Can export existing comment
                self.close_comment_button.configure(state='normal')  # Can still close viewing mode
            else:
                # Verse has no comment - enable Add Comment, disable Edit and Delete and Close
                self.add_comment_button.configure(state='normal')
                self.edit_comment_button.configure(state='disabled')
                self.delete_comment_button.configure(state='disabled')
                self.clip_comment_button.configure(state='disabled')  # Nothing to copy
                self.export_comment_button.configure(state='disabled')  # Nothing to export
                self.close_comment_button.configure(state='disabled')
            
            # Save button always disabled when not in edit mode
            self.save_comment_button.configure(state='disabled')
            
            self.add_message("Comment editing cancelled.")
        else:
            # In viewing mode - clear comment display and deselect verse
            self.comments_text.configure(state='normal')
            self.comments_text.delete('1.0', tk.END)
            self.comments_text.configure(state='disabled')
            
            # Clear verse selection in the listbox
            self.subject_verses_listbox.selection_clear(0, tk.END)
            
            # Disable all comment buttons
            self.add_comment_button.configure(state='disabled')
            self.edit_comment_button.configure(state='disabled')
            self.save_comment_button.configure(state='disabled')
            self.delete_comment_button.configure(state='disabled')
            self.close_comment_button.configure(state='disabled')
            self.clip_comment_button.configure(state='disabled')
            self.export_comment_button.configure(state='disabled')
            
            # Clear selected verse data
            self.selected_verse_data = None
            
            self.add_message("Comment viewing closed.")
    
    def clear_subject(self):
        """Clear the selected subject and reset the interface."""
        # Clear the combobox selection
        self.subject_var.set("")
        
        # Clear the subject verses listbox
        self.subject_verses_listbox.delete(0, tk.END)
        
        # Clear subject verse data
        if hasattr(self, 'subject_verse_data'):
            self.subject_verse_data = []
        
        # Clear comments display
        self.comments_text.configure(state='normal')
        self.comments_text.delete('1.0', tk.END)
        self.comments_text.configure(state='disabled')
        
        # Update button states for no subject selected
        self.create_subject_button.configure(state='normal')  # Can create new subject
        self.acquire_verse_button.configure(state='disabled')
        self.delete_subject_button.configure(state='disabled')
        self.clear_subject_button.configure(state='disabled')
        self.clip_subject_button.configure(state='disabled')
        self.export_subject_button.configure(state='disabled')
        
        # Disable all comment buttons
        self.add_comment_button.configure(state='disabled')
        self.edit_comment_button.configure(state='disabled')
        self.save_comment_button.configure(state='disabled')
        self.delete_comment_button.configure(state='disabled')
        self.close_comment_button.configure(state='disabled')
        self.clip_comment_button.configure(state='disabled')
        self.export_comment_button.configure(state='disabled')
        
        # Clear selected verse data
        if hasattr(self, 'selected_verse_data'):
            self.selected_verse_data = None
        
        self.add_message("Subject selection cleared.")
    
    def clip_comment(self):
        """Copy the current comment to clipboard."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            self.add_message("Please select a verse first.")
            return
            
        comment_text = self.comments_text.get('1.0', 'end-1c')
        
        if not comment_text.strip():
            self.add_message("No comment to copy.")
            return
        
        try:
            # Format comment for clipboard
            reference = f"{self.selected_verse_data['translation']} {self.selected_verse_data['reference']}"
            clipboard_text = f"Comment for {reference}:\n"
            clipboard_text += "=" * (len(reference) + 12) + "\n\n"
            clipboard_text += comment_text
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            self.add_message(f"Copied comment for {reference} to clipboard.")
            
        except Exception as e:
            self.add_message(f"Error copying comment to clipboard: {str(e)}")
    
    def export_comment(self):
        """Export the current comment to a text file."""
        if not hasattr(self, 'selected_verse_data') or not self.selected_verse_data:
            self.add_message("Please select a verse first.")
            return
            
        comment_text = self.comments_text.get('1.0', 'end-1c')
        
        if not comment_text.strip():
            self.add_message("No comment to export.")
            return
        
        try:
            # Get file location
            reference = f"{self.selected_verse_data['translation']} {self.selected_verse_data['reference']}"
            initial_filename = f"{reference.replace(' ', '_').replace(':', '-')}_comment.txt"
            export_path = filedialog.asksaveasfilename(
                title="Export Comment",
                initialdir=os.getcwd(),
                initialfile=initial_filename,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                defaultextension=".txt"
            )
            
            if not export_path:
                return
            
            # Format and write comment
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(f"Comment for {reference}\n")
                f.write("=" * (len(reference) + 12) + "\n\n")
                f.write(comment_text)
            
            self.add_message(f"Comment exported to {export_path}")
            
        except Exception as e:
            self.add_message(f"Error exporting comment: {str(e)}")
    
    def clip_subject_verses(self):
        """Copy all verses in the current subject to clipboard."""
        if not self.subject_var.get():
            self.add_message("Please select a subject first.")
            return
            
        if not hasattr(self, 'subject_verse_data') or not self.subject_verse_data:
            self.add_message("No verses in current subject to copy.")
            return
        
        try:
            # Format subject verses for clipboard
            clipboard_text = f"Subject: {self.subject_var.get()}\n"
            clipboard_text += "=" * (len(self.subject_var.get()) + 9) + "\n\n"
            
            for verse_data in self.subject_verse_data:
                reference = f"{verse_data['translation']} {verse_data['reference']}"
                padding_needed = 16 - len(reference)
                prefix_text = reference + " " * padding_needed
                clipboard_text += f"{prefix_text}{verse_data['text']}\n"
                
                # Include comments if they exist
                if verse_data['comments']:
                    clipboard_text += f"    Comment: {verse_data['comments']}\n"
                clipboard_text += "\n"
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            self.add_message(f"Copied {len(self.subject_verse_data)} verses from '{self.subject_var.get()}' to clipboard.")
            
        except Exception as e:
            self.add_message(f"Error copying to clipboard: {str(e)}")
    
    def export_subject(self):
        """Export a selected subject with its verses and comments."""
        try:
            # Get all subjects from database
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM subjects ORDER BY name")
            subjects = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not subjects:
                messagebox.showinfo("No Subjects", "No subjects found to export.")
                return
            
            # Create subject selection dialog
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Select Subject to Export")
            selection_window.geometry("400x300")
            selection_window.transient(self.root)
            selection_window.grab_set()
            
            # Center the dialog
            selection_window.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
            
            # Subject selection listbox
            tk.Label(selection_window, text="Select a subject to export:", font=('DejaVu Sans Mono', 12)).pack(pady=10)
            
            listbox_frame = tk.Frame(selection_window)
            listbox_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            subject_listbox = tk.Listbox(listbox_frame, font=('DejaVu Sans Mono', 10))
            scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=subject_listbox.yview)
            subject_listbox.configure(yscrollcommand=scrollbar.set)
            
            for subject in subjects:
                subject_listbox.insert(tk.END, subject)
            
            subject_listbox.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Button frame
            button_frame = tk.Frame(selection_window)
            button_frame.pack(fill='x', padx=20, pady=10)
            
            selected_subject = [None]  # Use list to allow modification in nested function
            
            def on_export():
                selection = subject_listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a subject to export.")
                    return
                
                selected_subject[0] = subjects[selection[0]]
                selection_window.destroy()
            
            def on_cancel():
                selection_window.destroy()
            
            ttk.Button(button_frame, text="Export", command=on_export).pack(side='right', padx=(5, 0))
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='right')
            
            # Wait for selection
            selection_window.wait_window()
            
            if not selected_subject[0]:
                return
            
            # Get file location with default to root folder
            initial_filename = f"{selected_subject[0].replace(' ', '_')}_export.txt"
            export_path = filedialog.asksaveasfilename(
                title="Save Subject Export",
                initialdir=os.getcwd(),  # Default to root folder
                initialfile=initial_filename,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                defaultextension=".txt"
            )
            
            if not export_path:
                return
            
            # Get subject data
            conn = sqlite3.connect(find_database())
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (selected_subject[0],))
            subject_id = cursor.fetchone()[0]
            
            # Get verses for this subject, sorted by order_index (same as reading window display)
            cursor.execute("""
                SELECT verse_reference, translation, verse_text, comments 
                FROM subject_verses 
                WHERE subject_id = ? 
                ORDER BY order_index
            """, (subject_id,))
            
            verses = cursor.fetchall()
            conn.close()
            
            if not verses:
                messagebox.showinfo("No Verses", f"No verses found for subject '{selected_subject[0]}'.")
                return
            
            # Format and write export
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {selected_subject[0]}\n")
                f.write("=" * (len(selected_subject[0]) + 9) + "\n\n")
                
                for verse_ref, translation, verse_text, comments in verses:
                    # Write verse (left-justified)
                    f.write(f"{translation} {verse_ref}\n")
                    f.write(f"{verse_text}\n")
                    
                    # Write associated comments if they exist (left-justified)
                    if comments and comments.strip():
                        f.write("\nComments:\n")
                        # Simple formatting - remove any RTF-like tags for plain text export
                        clean_comments = comments.replace('<bold>', '').replace('</bold>', '')
                        clean_comments = clean_comments.replace('<italic>', '').replace('</italic>', '')
                        clean_comments = clean_comments.replace('<underline>', '').replace('</underline>', '')
                        f.write(f"{clean_comments}\n")
                    
                    f.write("\n" + "-" * 50 + "\n\n")
            
            messagebox.showinfo("Export Complete", f"Subject '{selected_subject[0]}' exported successfully to:\n{export_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export:\n{str(e)}")
    
    def setup_text_formatting_tags(self):
        """Setup text formatting tags for RTF capabilities."""
        self.setup_text_formatting_tags_with_size(self.current_font_size)
    
    def setup_text_formatting_tags_with_size(self, base_font_size):
        """Setup text formatting tags with specified base font size."""
        # Basic formatting tags using base font size
        self.comments_text.tag_configure("bold", font=('DejaVu Sans Mono', base_font_size, 'bold'))
        self.comments_text.tag_configure("italic", font=('DejaVu Sans Mono', base_font_size, 'italic'))
        self.comments_text.tag_configure("underline", underline=True)
        
        # Font sizes
        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20]:
            self.comments_text.tag_configure(f"size_{size}", font=('DejaVu Sans Mono', size))
            self.comments_text.tag_configure(f"bold_size_{size}", font=('DejaVu Sans Mono', size, 'bold'))
            self.comments_text.tag_configure(f"italic_size_{size}", font=('DejaVu Sans Mono', size, 'italic'))
            self.comments_text.tag_configure(f"bold_italic_size_{size}", font=('DejaVu Sans Mono', size, 'bold italic'))
        
        # Colors
        colors = ['black', 'red', 'blue', 'green', 'purple', 'orange', 'brown', 'gray']
        for color in colors:
            self.comments_text.tag_configure(f"color_{color}", foreground=color)
    
    def show_formatting_toolbar(self):
        """Show the formatting toolbar."""
        self.formatting_toolbar.pack(fill='x', padx=5, pady=(0, 5), after=self.add_comment_button.master)
    
    def hide_formatting_toolbar(self):
        """Hide the formatting toolbar."""
        self.formatting_toolbar.pack_forget()
    
    def toggle_bold(self):
        """Toggle bold formatting for selected text or insertion point."""
        if self.comments_text.cget('state') == 'disabled':
            return
            
        try:
            # Get current selection or insertion point
            if self.comments_text.tag_ranges('sel'):
                start, end = self.comments_text.index('sel.first'), self.comments_text.index('sel.last')
                current_tags = self.comments_text.tag_names(start)
                
                if 'bold' in current_tags:
                    self.comments_text.tag_remove('bold', start, end)
                else:
                    self.comments_text.tag_add('bold', start, end)
            else:
                # Toggle for future typing
                self.current_formatting['bold'] = not self.current_formatting['bold']
        except tk.TclError:
            pass
    
    def toggle_italic(self):
        """Toggle italic formatting for selected text or insertion point."""
        if self.comments_text.cget('state') == 'disabled':
            return
            
        try:
            if self.comments_text.tag_ranges('sel'):
                start, end = self.comments_text.index('sel.first'), self.comments_text.index('sel.last')
                current_tags = self.comments_text.tag_names(start)
                
                if 'italic' in current_tags:
                    self.comments_text.tag_remove('italic', start, end)
                else:
                    self.comments_text.tag_add('italic', start, end)
            else:
                self.current_formatting['italic'] = not self.current_formatting['italic']
        except tk.TclError:
            pass
    
    def toggle_underline(self):
        """Toggle underline formatting for selected text or insertion point."""
        if self.comments_text.cget('state') == 'disabled':
            return
            
        try:
            if self.comments_text.tag_ranges('sel'):
                start, end = self.comments_text.index('sel.first'), self.comments_text.index('sel.last')
                current_tags = self.comments_text.tag_names(start)
                
                if 'underline' in current_tags:
                    self.comments_text.tag_remove('underline', start, end)
                else:
                    self.comments_text.tag_add('underline', start, end)
            else:
                self.current_formatting['underline'] = not self.current_formatting['underline']
        except tk.TclError:
            pass
    
    def change_font_size(self, event=None):
        """Change font size for selected text or insertion point."""
        if self.comments_text.cget('state') == 'disabled':
            return
            
        size = int(self.font_size_var.get())
        
        try:
            if self.comments_text.tag_ranges('sel'):
                start, end = self.comments_text.index('sel.first'), self.comments_text.index('sel.last')
                
                # Remove existing size tags
                for s in [8, 9, 10, 11, 12, 14, 16, 18, 20]:
                    self.comments_text.tag_remove(f"size_{s}", start, end)
                
                # Apply new size
                self.comments_text.tag_add(f"size_{size}", start, end)
            else:
                self.current_formatting['font_size'] = size
        except tk.TclError:
            pass
    
    def choose_text_color(self):
        """Choose text color for selected text or insertion point."""
        if self.comments_text.cget('state') == 'disabled':
            return
            
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Choose Text Color")[1]
        
        if color:
            try:
                if self.comments_text.tag_ranges('sel'):
                    start, end = self.comments_text.index('sel.first'), self.comments_text.index('sel.last')
                    
                    # Create unique color tag
                    color_tag = f"color_{color.replace('#', '')}"
                    self.comments_text.tag_configure(color_tag, foreground=color)
                    self.comments_text.tag_add(color_tag, start, end)
                else:
                    self.current_formatting['text_color'] = color
            except tk.TclError:
                pass
    
    def clear_formatting(self):
        """Clear all formatting from selected text."""
        if self.comments_text.cget('state') == 'disabled':
            return
            
        try:
            if self.comments_text.tag_ranges('sel'):
                start, end = self.comments_text.index('sel.first'), self.comments_text.index('sel.last')
                
                # Remove all formatting tags
                for tag in self.comments_text.tag_names(start):
                    if tag not in ['sel']:
                        self.comments_text.tag_remove(tag, start, end)
        except tk.TclError:
            pass
    
    def update_formatting_buttons(self, event=None):
        """Update formatting button states based on current selection."""
        # This would update button states to show current formatting
        # Implementation can be added later for visual feedback
        pass
    
    def save_formatted_comment(self):
        """Save comment with formatting information as JSON."""
        import json
        
        if self.comment_placeholder_active:
            return ""
        
        # Get plain text
        text = self.comments_text.get('1.0', 'end-1c')
        
        if not text.strip():
            return ""
        
        # Create format data structure
        format_data = {
            'text': text,
            'formatting': []
        }
        
        # Collect all formatting tags and their ranges
        for tag in self.comments_text.tag_names():
            if tag not in ['sel', 'current']:
                ranges = self.comments_text.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    start_idx = str(ranges[i])
                    end_idx = str(ranges[i+1])
                    
                    # Convert tkinter indices to character positions
                    start_pos = self.tk_index_to_pos(start_idx)
                    end_pos = self.tk_index_to_pos(end_idx)
                    
                    format_data['formatting'].append({
                        'tag': tag,
                        'start': start_pos,
                        'end': end_pos
                    })
        
        return json.dumps(format_data)
    
    def load_formatted_comment(self, formatted_text):
        """Load comment with formatting from JSON data."""
        import json
        
        if not formatted_text or formatted_text.strip() == "":
            return
        
        try:
            # Try to parse as JSON (formatted text)
            format_data = json.loads(formatted_text)
            
            # Insert plain text
            self.comments_text.insert('1.0', format_data['text'])
            
            # Apply formatting
            for fmt in format_data['formatting']:
                tag = fmt['tag']
                start_pos = self.pos_to_tk_index(fmt['start'])
                end_pos = self.pos_to_tk_index(fmt['end'])
                
                # Ensure tag is configured
                if tag.startswith('color_'):
                    color = '#' + tag.replace('color_', '')
                    self.comments_text.tag_configure(tag, foreground=color)
                
                self.comments_text.tag_add(tag, start_pos, end_pos)
                
        except (json.JSONDecodeError, KeyError):
            # Fall back to plain text if parsing fails
            self.comments_text.insert('1.0', formatted_text)
    
    def tk_index_to_pos(self, tk_index):
        """Convert tkinter text index to character position."""
        line, col = map(int, tk_index.split('.'))
        pos = 0
        for i in range(1, line):
            line_text = self.comments_text.get(f"{i}.0", f"{i}.end")
            pos += len(line_text) + 1  # +1 for newline
        pos += col
        return pos
    
    def pos_to_tk_index(self, pos):
        """Convert character position to tkinter text index."""
        text = self.comments_text.get('1.0', 'end-1c')
        if pos >= len(text):
            return f"end"
        
        line = 1
        current_pos = 0
        
        for char in text:
            if current_pos == pos:
                break
            if char == '\n':
                line += 1
                current_pos += 1
                col = 0
            else:
                current_pos += 1
                col = current_pos - sum(1 for c in text[:current_pos] if c == '\n')
        
        col = pos - sum(1 for c in text[:pos] if c == '\n')
        return f"{line}.{col}"
    
    def on_comment_click(self, event):
        """Handle click in comment text area."""
        if self.comment_placeholder_active:
            self.comments_text.delete('1.0', tk.END)
            self.comment_placeholder_active = False
            self.comments_text.configure(fg='black')
    
    def on_comment_keypress(self, event):
        """Handle keypress in comment text area."""
        if self.comment_placeholder_active:
            self.comments_text.delete('1.0', tk.END)
            self.comment_placeholder_active = False
            self.comments_text.configure(fg='black')
    
    def on_window_resize(self, event):
        """Handle window resize to maintain width synchronization."""
        if event.widget == self.root:
            new_width = self.root.winfo_width()
            self.config_manager.set('window_width', new_width)
    
    def on_closing(self):
        """Handle application closing - save configuration."""
        # Save current window dimensions
        self.config_manager.set('window_width', self.root.winfo_width())
        self.config_manager.set('window_height', self.root.winfo_height())
        
        # Save search settings
        search_settings = {
            'case_sensitive': self.case_sensitive_var.get(),
            'unique_verses': self.unique_verses_var.get(),
            'abbreviate_results': self.abbreviate_results_var.get(),
            'synonyms': self.synonyms_var.get(),
            'fuzzy_match': self.fuzzy_match_var.get(),
            'word_stems': self.word_stems_var.get(),
            'within_words': self.within_words_var.get(),
            'wildcards': self.wildcards_var.get()
        }
        self.config_manager.set('search_settings', search_settings)
        
        # Save resizable window heights using the synchronized height
        height_config = {}
        for key in self.resizable_frames.keys():
            height_config[key] = self.current_sync_height  # Use synchronized height, not individual heights
        
        self.config_manager.config['window_heights'] = height_config
        self.config_manager.save_config()
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = BibleSearchInterface()
    app.run()