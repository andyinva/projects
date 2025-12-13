#!/usr/bin/env python3
"""
Large File Manager
A GUI application to find, move, and manage large files with tracking capabilities.
"""

import os
import json
import shutil
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path
import threading
import string


class FileMove:
    """Represents a file move operation"""
    def __init__(self, source, destination, timestamp, size):
        self.source = source
        self.destination = destination
        self.timestamp = timestamp
        self.size = size

    def to_dict(self):
        return {
            'source': self.source,
            'destination': self.destination,
            'timestamp': self.timestamp,
            'size': self.size
        }

    @staticmethod
    def from_dict(data):
        return FileMove(
            data['source'],
            data['destination'],
            data['timestamp'],
            data['size']
        )


class LargeFileManager:
    def __init__(self, root):
        self.root = root

        # Detect platform
        self.platform = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)

        # Set window title with platform info
        self.root.title(f"Large File Manager - {self.platform}")
        self.root.geometry("1000x700")

        # Data storage
        self.found_files = []  # List of (path, size) tuples
        self.move_history = []  # List of FileMove objects
        self.history_file = "file_move_history.json"

        # Sort state
        self.sort_column = None
        self.sort_reverse = False

        # Define OS directories to skip
        self.windows_skip_dirs = {
            'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
            '$Recycle.Bin', 'System Volume Information', '$WINDOWS.~BT',
            'Recovery', 'Windows.old', 'WindowsApps', 'WinSxS'
        }
        self.linux_skip_dirs = {
            '/bin', '/boot', '/dev', '/etc', '/lib', '/lib64', '/proc',
            '/root', '/run', '/sbin', '/sys', '/usr', '/var', '/snap'
        }

        # Load existing history
        self.load_history()

        # Create GUI
        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets"""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Search and Move
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Search & Move")
        self.create_search_tab()

        # Tab 2: History and Restore
        self.history_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History & Restore")
        self.create_history_tab()

    def create_search_tab(self):
        """Create the search and move tab"""
        # Search parameters frame
        param_frame = ttk.LabelFrame(self.search_frame, text="Search Parameters", padding=10)
        param_frame.pack(fill='x', padx=5, pady=5)

        # Directory selection
        ttk.Label(param_frame, text="Search Directory:").grid(row=0, column=0, sticky='w', pady=5)
        self.search_dir_var = tk.StringVar(value=str(Path.home()))
        ttk.Entry(param_frame, textvariable=self.search_dir_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(param_frame, text="Browse", command=self.browse_search_dir).grid(row=0, column=2)

        # File size input
        ttk.Label(param_frame, text="Minimum Size (MB):").grid(row=1, column=0, sticky='w', pady=5)
        self.size_var = tk.StringVar(value="100")
        ttk.Entry(param_frame, textvariable=self.size_var, width=20).grid(row=1, column=1, sticky='w', padx=5)

        # Skip OS files checkbox
        self.skip_os_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(param_frame, text="Skip Operating System files and directories",
                       variable=self.skip_os_files_var).grid(row=2, column=0, columnspan=3, sticky='w', pady=5)

        # Search button
        ttk.Button(param_frame, text="Search Files", command=self.start_search).grid(row=3, column=0, columnspan=3, pady=10)

        # Progress label
        self.search_status_var = tk.StringVar(value="Ready")
        ttk.Label(param_frame, textvariable=self.search_status_var).grid(row=4, column=0, columnspan=3)

        # Results frame
        results_frame = ttk.LabelFrame(self.search_frame, text="Search Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create treeview with checkboxes
        tree_scroll = ttk.Scrollbar(results_frame)
        tree_scroll.pack(side='right', fill='y')

        self.file_tree = ttk.Treeview(results_frame, yscrollcommand=tree_scroll.set,
                                      columns=('Size', 'Path'), selectmode='extended')
        self.file_tree.pack(fill='both', expand=True)
        tree_scroll.config(command=self.file_tree.yview)

        # Configure columns
        self.file_tree.heading('#0', text='Select')
        self.file_tree.heading('Size', text='Size (MB)', command=lambda: self.sort_tree('Size', False))
        self.file_tree.heading('Path', text='File Path', command=lambda: self.sort_tree('Path', False))

        self.file_tree.column('#0', width=50)
        self.file_tree.column('Size', width=100)
        self.file_tree.column('Path', width=700)

        # Bind checkbox toggle
        self.file_tree.bind('<Button-1>', self.toggle_checkbox)

        # Buttons frame
        button_frame = ttk.Frame(results_frame)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(button_frame, text="Select All", command=self.select_all).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Move Selected Files", command=self.move_selected_files).pack(side='right', padx=5)

    def create_history_tab(self):
        """Create the history and restore tab"""
        # Info frame
        info_frame = ttk.LabelFrame(self.history_frame, text="Move History", padding=10)
        info_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create treeview for history
        tree_scroll = ttk.Scrollbar(info_frame)
        tree_scroll.pack(side='right', fill='y')

        self.history_tree = ttk.Treeview(info_frame, yscrollcommand=tree_scroll.set,
                                         columns=('Timestamp', 'Size', 'From', 'To'),
                                         selectmode='extended')
        self.history_tree.pack(fill='both', expand=True)
        tree_scroll.config(command=self.history_tree.yview)

        # Configure columns with sorting
        self.history_tree.heading('#0', text='Select')
        self.history_tree.heading('Timestamp', text='Date/Time', command=lambda: self.sort_history_tree('Timestamp'))
        self.history_tree.heading('Size', text='Size (MB)', command=lambda: self.sort_history_tree('Size'))
        self.history_tree.heading('From', text='Original Location', command=lambda: self.sort_history_tree('From'))
        self.history_tree.heading('To', text='Moved To', command=lambda: self.sort_history_tree('To'))

        self.history_tree.column('#0', width=50)
        self.history_tree.column('Timestamp', width=150)
        self.history_tree.column('Size', width=80)
        self.history_tree.column('From', width=350)
        self.history_tree.column('To', width=350)

        # Bind checkbox toggle
        self.history_tree.bind('<Button-1>', self.toggle_history_checkbox)

        # Refresh history display
        self.refresh_history_display()

        # Buttons frame
        button_frame = ttk.Frame(info_frame)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(button_frame, text="Select All", command=self.select_all_history).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_history).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Restore Selected Files", command=self.restore_selected_files).pack(side='right', padx=5)

    def browse_search_dir(self):
        """Open directory browser"""
        directory = filedialog.askdirectory(initialdir=self.search_dir_var.get())
        if directory:
            self.search_dir_var.set(directory)

    def start_search(self):
        """Start the file search in a separate thread"""
        try:
            min_size_mb = float(self.size_var.get())
            if min_size_mb <= 0:
                messagebox.showerror("Error", "Size must be greater than 0")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for file size")
            return

        search_dir = self.search_dir_var.get()
        if not os.path.isdir(search_dir):
            messagebox.showerror("Error", "Please select a valid directory")
            return

        # Clear previous results
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        self.found_files = []
        self.search_status_var.set("Searching...")

        # Run search in separate thread to keep GUI responsive
        search_thread = threading.Thread(target=self.search_files,
                                        args=(search_dir, min_size_mb))
        search_thread.daemon = True
        search_thread.start()

    def search_files(self, directory, min_size_mb):
        """Search for files larger than specified size"""
        min_size_bytes = min_size_mb * 1024 * 1024
        count = 0
        skip_os = self.skip_os_files_var.get()

        try:
            for root, dirs, files in os.walk(directory):
                # Skip OS directories if enabled
                if skip_os:
                    # Modify dirs in-place to skip OS directories
                    dirs[:] = [d for d in dirs if not self.should_skip_directory(os.path.join(root, d))]

                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(filepath)
                        if size >= min_size_bytes:
                            self.found_files.append((filepath, size))
                            count += 1
                            # Update status
                            self.root.after(0, self.search_status_var.set,
                                          f"Found {count} files...")
                            # Add to tree
                            self.root.after(0, self.add_file_to_tree, filepath, size)
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Search error: {str(e)}")

        self.root.after(0, self.search_status_var.set,
                       f"Search complete. Found {count} files.")

    def add_file_to_tree(self, filepath, size):
        """Add a file to the treeview"""
        size_mb = size / (1024 * 1024)
        self.file_tree.insert('', 'end', text='☐',
                             values=(f'{size_mb:.2f}', filepath),
                             tags=('unchecked',))

    def toggle_checkbox(self, event):
        """Toggle checkbox when clicked"""
        region = self.file_tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.file_tree.identify_row(event.y)
            if item:
                tags = self.file_tree.item(item, 'tags')
                if 'checked' in tags:
                    self.file_tree.item(item, text='☐', tags=('unchecked',))
                else:
                    self.file_tree.item(item, text='☑', tags=('checked',))

    def select_all(self):
        """Select all files in the tree"""
        for item in self.file_tree.get_children():
            self.file_tree.item(item, text='☑', tags=('checked',))

    def deselect_all(self):
        """Deselect all files in the tree"""
        for item in self.file_tree.get_children():
            self.file_tree.item(item, text='☐', tags=('unchecked',))

    def should_skip_directory(self, dirpath):
        """Check if a directory should be skipped based on OS"""
        if self.platform == "Windows":
            # For Windows, check if any part of the path matches skip directories
            path_parts = Path(dirpath).parts
            for part in path_parts:
                if part in self.windows_skip_dirs:
                    return True
            # Also skip hidden/system directories
            if any(part.startswith('$') for part in path_parts):
                return True
        elif self.platform == "Linux":
            # For Linux, check absolute paths
            if dirpath in self.linux_skip_dirs:
                return True
            # Also check if directory starts with any skip path
            for skip_dir in self.linux_skip_dirs:
                if dirpath.startswith(skip_dir + '/'):
                    return True
        return False

    def sort_tree(self, column, is_numeric):
        """Sort treeview by column"""
        # Toggle sort order if clicking the same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Get all items
        items = [(self.file_tree.item(item)['values'], item) for item in self.file_tree.get_children()]

        # Sort based on column
        if column == 'Size':
            # Sort by size (numeric)
            items.sort(key=lambda x: float(x[0][0]), reverse=self.sort_reverse)
        elif column == 'Path':
            # Sort by path (alphabetic)
            items.sort(key=lambda x: x[0][1].lower(), reverse=self.sort_reverse)

        # Rearrange items in sorted order
        for index, (values, item) in enumerate(items):
            self.file_tree.move(item, '', index)

        # Update column heading to show sort direction
        for col in ['Size', 'Path']:
            if col == column:
                arrow = ' ↓' if self.sort_reverse else ' ↑'
                self.file_tree.heading(col, text=f"{col} ({col == 'Size' and 'MB' or 'File Path'}){arrow}",
                                      command=lambda c=col: self.sort_tree(c, c == 'Size'))
            else:
                heading_text = 'Size (MB)' if col == 'Size' else 'File Path'
                self.file_tree.heading(col, text=heading_text,
                                      command=lambda c=col: self.sort_tree(c, c == 'Size'))

    def sort_history_tree(self, column):
        """Sort history treeview by column"""
        # Toggle sort order if clicking the same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Get all items
        items = [(self.history_tree.item(item)['values'], item) for item in self.history_tree.get_children()]

        # Sort based on column
        col_index = {'Timestamp': 0, 'Size': 1, 'From': 2, 'To': 3}[column]

        if column == 'Size':
            # Sort by size (numeric)
            items.sort(key=lambda x: float(x[0][col_index]), reverse=self.sort_reverse)
        else:
            # Sort alphabetically
            items.sort(key=lambda x: str(x[0][col_index]).lower(), reverse=self.sort_reverse)

        # Rearrange items in sorted order
        for index, (values, item) in enumerate(items):
            self.history_tree.move(item, '', index)

        # Update column heading to show sort direction
        arrow = ' ↓' if self.sort_reverse else ' ↑'
        heading_names = {
            'Timestamp': 'Date/Time',
            'Size': 'Size (MB)',
            'From': 'Original Location',
            'To': 'Moved To'
        }

        for col in ['Timestamp', 'Size', 'From', 'To']:
            if col == column:
                self.history_tree.heading(col, text=f"{heading_names[col]}{arrow}",
                                        command=lambda c=col: self.sort_history_tree(c))
            else:
                self.history_tree.heading(col, text=heading_names[col],
                                        command=lambda c=col: self.sort_history_tree(c))

    def move_selected_files(self):
        """Move selected files to USB drive"""
        # Get selected files
        selected_files = []
        for item in self.file_tree.get_children():
            tags = self.file_tree.item(item, 'tags')
            if 'checked' in tags:
                values = self.file_tree.item(item, 'values')
                filepath = values[1]
                size = float(values[0]) * 1024 * 1024  # Convert back to bytes
                selected_files.append((filepath, size))

        if not selected_files:
            messagebox.showwarning("No Selection", "Please select files to move")
            return

        # Ask user how they want to select destination
        dest_dir = self.select_destination()
        if not dest_dir:
            return

        # Confirm the move
        total_size_mb = sum(size for _, size in selected_files) / (1024 * 1024)
        if not messagebox.askyesno("Confirm Move",
                                   f"Move {len(selected_files)} files ({total_size_mb:.2f} MB) to\n{dest_dir}?"):
            return

        # Perform the move
        self.perform_move(selected_files, dest_dir)

    def select_destination(self):
        """Show dialog to select destination (USB drive or browse)"""
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Destination")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Choose destination for files:",
                 font=('', 10, 'bold')).pack(pady=20)

        destination = [None]

        def use_usb():
            dest = self.show_usb_drives()
            if dest:
                destination[0] = dest
                dialog.destroy()

        def browse():
            dest = filedialog.askdirectory(title="Select Destination Folder")
            if dest:
                destination[0] = dest
                dialog.destroy()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Detect USB Drives",
                  command=use_usb, width=20).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Browse...",
                  command=browse, width=20).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel",
                  command=cancel, width=20).pack(side='left', padx=5)

        dialog.wait_window()
        return destination[0]

    def perform_move(self, files, dest_dir):
        """Actually move the files"""
        success_count = 0
        error_count = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for filepath, size in files:
            try:
                filename = os.path.basename(filepath)
                dest_path = os.path.join(dest_dir, filename)

                # Handle duplicate filenames
                counter = 1
                base, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(dest_dir, filename)
                    counter += 1

                # Move the file
                shutil.move(filepath, dest_path)

                # Record the move
                file_move = FileMove(filepath, dest_path, timestamp, size)
                self.move_history.append(file_move)

                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error moving {filepath}: {str(e)}")

        # Save history
        self.save_history()

        # Refresh displays
        self.start_search()  # Refresh search results
        self.refresh_history_display()

        # Show result
        messagebox.showinfo("Move Complete",
                           f"Successfully moved {success_count} files.\n"
                           f"Errors: {error_count}")

    def refresh_history_display(self):
        """Refresh the history treeview"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Add history items
        for move in self.move_history:
            size_mb = move.size / (1024 * 1024)
            self.history_tree.insert('', 'end', text='☐',
                                    values=(move.timestamp, f'{size_mb:.2f}',
                                           move.source, move.destination),
                                    tags=('unchecked',))

    def toggle_history_checkbox(self, event):
        """Toggle checkbox in history tree"""
        region = self.history_tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.history_tree.identify_row(event.y)
            if item:
                tags = self.history_tree.item(item, 'tags')
                if 'checked' in tags:
                    self.history_tree.item(item, text='☐', tags=('unchecked',))
                else:
                    self.history_tree.item(item, text='☑', tags=('checked',))

    def select_all_history(self):
        """Select all items in history"""
        for item in self.history_tree.get_children():
            self.history_tree.item(item, text='☑', tags=('checked',))

    def deselect_all_history(self):
        """Deselect all items in history"""
        for item in self.history_tree.get_children():
            self.history_tree.item(item, text='☐', tags=('unchecked',))

    def restore_selected_files(self):
        """Restore selected files to their original locations"""
        # Get selected items
        selected_moves = []
        for item in self.history_tree.get_children():
            tags = self.history_tree.item(item, 'tags')
            if 'checked' in tags:
                values = self.history_tree.item(item, 'values')
                # Find the corresponding FileMove object
                for move in self.move_history:
                    if (move.timestamp == values[0] and
                        move.source == values[2] and
                        move.destination == values[3]):
                        selected_moves.append(move)
                        break

        if not selected_moves:
            messagebox.showwarning("No Selection", "Please select files to restore")
            return

        # Confirm restore
        if not messagebox.askyesno("Confirm Restore",
                                   f"Restore {len(selected_moves)} files to their original locations?"):
            return

        # Perform restore
        self.perform_restore(selected_moves)

    def perform_restore(self, moves):
        """Restore files to original locations"""
        success_count = 0
        error_count = 0
        errors = []

        for move in moves:
            try:
                # Check if destination file still exists
                if not os.path.exists(move.destination):
                    errors.append(f"File not found: {move.destination}")
                    error_count += 1
                    continue

                # Check if source location is available
                source_dir = os.path.dirname(move.source)
                if not os.path.exists(source_dir):
                    # Try to create the directory
                    try:
                        os.makedirs(source_dir)
                    except Exception as e:
                        errors.append(f"Cannot create directory {source_dir}: {str(e)}")
                        error_count += 1
                        continue

                # Check if source file already exists
                if os.path.exists(move.source):
                    errors.append(f"File already exists at original location: {move.source}")
                    error_count += 1
                    continue

                # Restore the file
                shutil.move(move.destination, move.source)

                # Remove from history
                self.move_history.remove(move)

                success_count += 1
            except Exception as e:
                errors.append(f"Error restoring {move.destination}: {str(e)}")
                error_count += 1

        # Save updated history
        self.save_history()

        # Refresh display
        self.refresh_history_display()

        # Show results
        message = f"Successfully restored {success_count} files.\nErrors: {error_count}"
        if errors:
            message += "\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                message += f"\n... and {len(errors) - 5} more errors"

        messagebox.showinfo("Restore Complete", message)

    def save_history(self):
        """Save move history to JSON file"""
        try:
            with open(self.history_file, 'w') as f:
                history_data = [move.to_dict() for move in self.move_history]
                json.dump(history_data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save history: {str(e)}")

    def load_history(self):
        """Load move history from JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    self.move_history = [FileMove.from_dict(data) for data in history_data]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load history: {str(e)}")
                self.move_history = []

    def get_usb_drives(self):
        """Detect available USB drives based on platform"""
        drives = []

        if self.platform == "Windows":
            # Windows: Check all drive letters
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        # Check if it's a removable drive
                        drive_type = self.get_drive_type_windows(drive)
                        if drive_type:
                            drives.append((drive, drive_type))
                    except:
                        pass

        elif self.platform == "Linux":
            # Linux: Check common mount points
            media_dirs = []
            username = os.getenv('USER') or os.getenv('USERNAME')

            # Check /media/username/
            if username:
                user_media = f"/media/{username}"
                if os.path.exists(user_media):
                    try:
                        for item in os.listdir(user_media):
                            path = os.path.join(user_media, item)
                            if os.path.ismount(path):
                                drives.append((path, f"USB - {item}"))
                    except:
                        pass

            # Check /mnt/
            if os.path.exists("/mnt"):
                try:
                    for item in os.listdir("/mnt"):
                        path = os.path.join("/mnt", item)
                        if os.path.isdir(path) and os.path.ismount(path):
                            drives.append((path, f"Mount - {item}"))
                except:
                    pass

            # Check /media/
            if os.path.exists("/media"):
                try:
                    for item in os.listdir("/media"):
                        path = os.path.join("/media", item)
                        if os.path.isdir(path) and item != username:
                            if os.path.ismount(path):
                                drives.append((path, f"Media - {item}"))
                except:
                    pass

        return drives

    def get_drive_type_windows(self, drive):
        """Get drive type on Windows (requires ctypes)"""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            drive_type = kernel32.GetDriveTypeW(drive)

            # Drive types: 0=Unknown, 1=No Root Dir, 2=Removable, 3=Fixed, 4=Remote, 5=CD-ROM, 6=RAM Disk
            drive_types = {
                0: "Unknown",
                1: "No Root Directory",
                2: "Removable (USB)",
                3: "Fixed (HDD/SSD)",
                4: "Network",
                5: "CD-ROM",
                6: "RAM Disk"
            }

            return drive_types.get(drive_type, "Unknown")
        except:
            return None

    def show_usb_drives(self):
        """Show available USB drives in a dialog"""
        drives = self.get_usb_drives()

        if not drives:
            messagebox.showinfo("USB Drives",
                              "No USB drives detected.\n\n" +
                              self.get_usb_help_text())
            return None

        # Create a simple dialog to select a drive
        dialog = tk.Toplevel(self.root)
        dialog.title("Select USB Drive")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Available Drives:", font=('', 10, 'bold')).pack(pady=10)

        # Create listbox
        frame = ttk.Frame(dialog)
        frame.pack(fill='both', expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side='right', fill='y')

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=('', 10))
        listbox.pack(fill='both', expand=True)
        scrollbar.config(command=listbox.yview)

        # Add drives to listbox
        for drive, drive_type in drives:
            listbox.insert('end', f"{drive} - {drive_type}")

        selected_drive = [None]

        def on_select():
            selection = listbox.curselection()
            if selection:
                selected_drive[0] = drives[selection[0]][0]
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Select", command=on_select).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)

        # Bind double-click
        listbox.bind('<Double-Button-1>', lambda e: on_select())

        dialog.wait_window()
        return selected_drive[0]

    def get_usb_help_text(self):
        """Get platform-specific help text for finding USB drives"""
        if self.platform == "Windows":
            return "On Windows, USB drives appear as drive letters (D:, E:, F:, etc.)\nMake sure your USB drive is plugged in and recognized by Windows."
        elif self.platform == "Linux":
            return "On Linux, USB drives are typically mounted in:\n- /media/username/\n- /mnt/\nMake sure your USB drive is plugged in and mounted."
        else:
            return "Make sure your USB drive is plugged in and mounted."


def main():
    root = tk.Tk()
    app = LargeFileManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
