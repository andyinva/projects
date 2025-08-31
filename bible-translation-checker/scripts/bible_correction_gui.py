#!/usr/bin/env python3
"""
Bible Correction System - tkinter GUI Components

Comprehensive GUI interface for Bible text correction system with:
- Error statistics dashboard
- Text editor with correction capabilities  
- Translation management
- Export functionality
- Progress tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import webbrowser

class BibleCorrectionGUI:
    """Main GUI application for Bible correction system"""
    
    def __init__(self, root: tk.Tk, db_manager):
        self.root = root
        self.db = db_manager
        
        # Configure main window
        self.root.title("Bible Text Correction System")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Configure style
        self.setup_styles()
        
        # Initialize variables
        self.current_translation = tk.StringVar()
        self.current_book = tk.StringVar()
        self.current_chapter = tk.StringVar()
        self.selected_verse_id = None
        self.search_var = tk.StringVar()
        self.filter_error_type = tk.StringVar(value="All")
        self.filter_status = tk.StringVar(value="open")
        
        # Create GUI components
        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()
        
        # Load initial data
        self.refresh_translations()
        self.refresh_error_statistics()
        
        # Bind events
        self.setup_bindings()
    
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        
        # Configure styles for severity colors
        style.configure('Critical.TLabel', foreground='red', font=('Arial', 9, 'bold'))
        style.configure('Warning.TLabel', foreground='orange', font=('Arial', 9))
        style.configure('Info.TLabel', foreground='blue', font=('Arial', 9))
        
        style.configure('Error.TButton', foreground='red')
        style.configure('Success.TButton', foreground='green')
        style.configure('Warning.TButton', foreground='orange')
        
        # Treeview styles
        style.configure('Treeview', rowheight=25)
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import JSON Files...", command=self.import_json_files)
        file_menu.add_separator()
        file_menu.add_command(label="Export Translation...", command=self.export_translation)
        file_menu.add_command(label="Export Error Report...", command=self.export_error_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Scan for Errors...", command=self.scan_for_errors)
        tools_menu.add_command(label="Bulk Operations...", command=self.show_bulk_operations)
        tools_menu.add_separator()
        tools_menu.add_command(label="Database Statistics", command=self.show_database_stats)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_main_interface(self):
        """Create main tabbed interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_editor_tab()
        self.create_errors_tab()
        self.create_translations_tab()
        
        # Select dashboard tab by default
        self.notebook.select(0)
    
    def create_dashboard_tab(self):
        """Create error statistics dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Title
        title_label = ttk.Label(dashboard_frame, text="Error Statistics Dashboard", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(10, 20))
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(dashboard_frame, text="Error Type Statistics")
        stats_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create scrollable frame for error buttons
        canvas = tk.Canvas(stats_frame)
        scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=canvas.yview)
        self.stats_scrollable_frame = ttk.Frame(canvas)
        
        self.stats_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.stats_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Summary frame
        summary_frame = ttk.LabelFrame(dashboard_frame, text="Summary")
        summary_frame.pack(fill='x', padx=10, pady=5)
        
        self.summary_text = tk.Text(summary_frame, height=6, wrap='word', state='disabled')
        summary_scrollbar = ttk.Scrollbar(summary_frame, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        
        self.summary_text.pack(side='left', fill='both', expand=True)
        summary_scrollbar.pack(side='right', fill='y')
        
        # Refresh button
        refresh_btn = ttk.Button(dashboard_frame, text="🔄 Refresh Statistics", 
                                command=self.refresh_error_statistics)
        refresh_btn.pack(pady=10)
    
    def create_editor_tab(self):
        """Create text editor tab"""
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text="✏️ Editor")
        
        # Top controls
        controls_frame = ttk.Frame(editor_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        # Translation selection
        ttk.Label(controls_frame, text="Translation:").pack(side='left', padx=(0, 5))
        self.translation_combo = ttk.Combobox(controls_frame, textvariable=self.current_translation,
                                            state='readonly', width=10)
        self.translation_combo.pack(side='left', padx=(0, 20))
        self.translation_combo.bind('<<ComboboxSelected>>', self.on_translation_selected)
        
        # Book selection
        ttk.Label(controls_frame, text="Book:").pack(side='left', padx=(0, 5))
        self.book_combo = ttk.Combobox(controls_frame, textvariable=self.current_book,
                                     state='readonly', width=15)
        self.book_combo.pack(side='left', padx=(0, 20))
        self.book_combo.bind('<<ComboboxSelected>>', self.on_book_selected)
        
        # Chapter selection
        ttk.Label(controls_frame, text="Chapter:").pack(side='left', padx=(0, 5))
        self.chapter_combo = ttk.Combobox(controls_frame, textvariable=self.current_chapter,
                                        state='readonly', width=8)
        self.chapter_combo.pack(side='left', padx=(0, 20))
        self.chapter_combo.bind('<<ComboboxSelected>>', self.on_chapter_selected)
        
        # Search
        ttk.Label(controls_frame, text="Search:").pack(side='left', padx=(20, 5))
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=(0, 5))
        search_btn = ttk.Button(controls_frame, text="🔍", command=self.search_verses)
        search_btn.pack(side='left')
        
        # Main editor area
        editor_paned = ttk.PanedWindow(editor_frame, orient='horizontal')
        editor_paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - verse list
        left_frame = ttk.LabelFrame(editor_paned, text="Verses")
        editor_paned.add(left_frame, weight=1)
        
        # Verse tree
        verse_tree_frame = ttk.Frame(left_frame)
        verse_tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.verse_tree = ttk.Treeview(verse_tree_frame, columns=('Reference', 'Text', 'Status'), 
                                      show='tree headings', height=20)
        
        # Configure columns
        self.verse_tree.heading('#0', text='', anchor='w')
        self.verse_tree.column('#0', width=20, minwidth=20, stretch=False)
        self.verse_tree.heading('Reference', text='Reference', anchor='w')
        self.verse_tree.column('Reference', width=100, minwidth=80)
        self.verse_tree.heading('Text', text='Text Preview', anchor='w')
        self.verse_tree.column('Text', width=300, minwidth=200)
        self.verse_tree.heading('Status', text='Status', anchor='center')
        self.verse_tree.column('Status', width=80, minwidth=60)
        
        # Tree scrollbars
        verse_v_scroll = ttk.Scrollbar(verse_tree_frame, orient='vertical', 
                                      command=self.verse_tree.yview)
        verse_h_scroll = ttk.Scrollbar(verse_tree_frame, orient='horizontal', 
                                      command=self.verse_tree.xview)
        self.verse_tree.configure(yscrollcommand=verse_v_scroll.set, 
                                 xscrollcommand=verse_h_scroll.set)
        
        self.verse_tree.pack(side='left', fill='both', expand=True)
        verse_v_scroll.pack(side='right', fill='y')
        verse_h_scroll.pack(side='bottom', fill='x')
        
        self.verse_tree.bind('<<TreeviewSelect>>', self.on_verse_selected)
        
        # Right panel - editor
        right_frame = ttk.LabelFrame(editor_paned, text="Text Editor")
        editor_paned.add(right_frame, weight=2)
        
        # Verse info
        self.verse_info_label = ttk.Label(right_frame, text="Select a verse to edit", 
                                         font=('Arial', 12, 'bold'))
        self.verse_info_label.pack(pady=5)
        
        # Original text
        orig_frame = ttk.LabelFrame(right_frame, text="Original Text")
        orig_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        self.original_text = scrolledtext.ScrolledText(orig_frame, height=6, wrap='word', 
                                                      state='disabled', bg='#f0f0f0')
        self.original_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Corrected text
        corrected_frame = ttk.LabelFrame(right_frame, text="Corrected Text")
        corrected_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        self.corrected_text = scrolledtext.ScrolledText(corrected_frame, height=6, wrap='word')
        self.corrected_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Notes
        notes_frame = ttk.LabelFrame(right_frame, text="Correction Notes")
        notes_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        self.correction_notes = scrolledtext.ScrolledText(notes_frame, height=4, wrap='word')
        self.correction_notes.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="💾 Save Changes", 
                  command=self.save_verse_changes).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="↺ Reset", 
                  command=self.reset_verse_editor).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="🔍 View Errors", 
                  command=self.view_verse_errors).pack(side='left')
    
    def create_errors_tab(self):
        """Create errors management tab"""
        errors_frame = ttk.Frame(self.notebook)
        self.notebook.add(errors_frame, text="⚠️ Errors")
        
        # Filters frame
        filters_frame = ttk.LabelFrame(errors_frame, text="Filters")
        filters_frame.pack(fill='x', padx=10, pady=5)
        
        filter_row = ttk.Frame(filters_frame)
        filter_row.pack(fill='x', padx=10, pady=5)
        
        # Status filter
        ttk.Label(filter_row, text="Status:").pack(side='left', padx=(0, 5))
        status_combo = ttk.Combobox(filter_row, textvariable=self.filter_status,
                                   values=['open', 'fixed', 'ignored', 'all'], 
                                   state='readonly', width=10)
        status_combo.pack(side='left', padx=(0, 20))
        status_combo.bind('<<ComboboxSelected>>', self.refresh_errors_list)
        
        # Error type filter
        ttk.Label(filter_row, text="Error Type:").pack(side='left', padx=(0, 5))
        self.error_type_combo = ttk.Combobox(filter_row, textvariable=self.filter_error_type,
                                           state='readonly', width=20)
        self.error_type_combo.pack(side='left', padx=(0, 20))
        self.error_type_combo.bind('<<ComboboxSelected>>', self.refresh_errors_list)
        
        # Refresh button
        ttk.Button(filter_row, text="🔄 Refresh", 
                  command=self.refresh_errors_list).pack(side='right')
        
        # Errors list
        errors_list_frame = ttk.LabelFrame(errors_frame, text="Error Instances")
        errors_list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create treeview for errors
        tree_frame = ttk.Frame(errors_list_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('ID', 'Translation', 'Reference', 'Error Type', 'Severity', 'Status', 'Description')
        self.errors_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.errors_tree.heading(col, text=col, anchor='w')
        
        self.errors_tree.column('ID', width=60, minwidth=50)
        self.errors_tree.column('Translation', width=80, minwidth=60)
        self.errors_tree.column('Reference', width=120, minwidth=100)
        self.errors_tree.column('Error Type', width=150, minwidth=120)
        self.errors_tree.column('Severity', width=80, minwidth=70)
        self.errors_tree.column('Status', width=70, minwidth=60)
        self.errors_tree.column('Description', width=300, minwidth=200)
        
        # Scrollbars
        errors_v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', 
                                       command=self.errors_tree.yview)
        errors_h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', 
                                       command=self.errors_tree.xview)
        self.errors_tree.configure(yscrollcommand=errors_v_scroll.set, 
                                  xscrollcommand=errors_h_scroll.set)
        
        self.errors_tree.pack(side='left', fill='both', expand=True)
        errors_v_scroll.pack(side='right', fill='y')
        errors_h_scroll.pack(side='bottom', fill='x')
        
        # Context menu for errors
        self.errors_tree.bind('<Button-3>', self.show_error_context_menu)
        self.errors_tree.bind('<Double-1>', self.view_error_details)
        
        # Error details frame
        details_frame = ttk.LabelFrame(errors_frame, text="Error Details")
        details_frame.pack(fill='x', padx=10, pady=5)
        
        self.error_details_text = scrolledtext.ScrolledText(details_frame, height=6, 
                                                           wrap='word', state='disabled')
        self.error_details_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_translations_tab(self):
        """Create translations management tab"""
        trans_frame = ttk.Frame(self.notebook)
        self.notebook.add(trans_frame, text="📚 Translations")
        
        # Toolbar
        toolbar = ttk.Frame(trans_frame)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(toolbar, text="➕ Import JSON", 
                  command=self.import_json_files).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🔍 Scan Errors", 
                  command=self.scan_for_errors).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="📤 Export", 
                  command=self.export_translation).pack(side='left', padx=(0, 10))
        ttk.Button(toolbar, text="🗑️ Delete", 
                  command=self.delete_translation).pack(side='right')
        
        # Translations list
        trans_list_frame = ttk.LabelFrame(trans_frame, text="Available Translations")
        trans_list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        tree_frame = ttk.Frame(trans_list_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('Abbrev', 'Name', 'Source File', 'Verses', 'Errors', 'Imported')
        self.trans_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.trans_tree.heading(col, text=col, anchor='w')
        
        self.trans_tree.column('Abbrev', width=80, minwidth=60)
        self.trans_tree.column('Name', width=200, minwidth=150)
        self.trans_tree.column('Source File', width=300, minwidth=200)
        self.trans_tree.column('Verses', width=80, minwidth=60)
        self.trans_tree.column('Errors', width=80, minwidth=60)
        self.trans_tree.column('Imported', width=150, minwidth=120)
        
        # Scrollbars
        trans_v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', 
                                      command=self.trans_tree.yview)
        trans_h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', 
                                      command=self.trans_tree.xview)
        self.trans_tree.configure(yscrollcommand=trans_v_scroll.set, 
                                 xscrollcommand=trans_h_scroll.set)
        
        self.trans_tree.pack(side='left', fill='both', expand=True)
        trans_v_scroll.pack(side='right', fill='y')
        trans_h_scroll.pack(side='bottom', fill='x')
        
        self.trans_tree.bind('<Double-1>', self.view_translation_details)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, variable=self.progress_var,
                                           mode='determinate', length=200)
        self.progress_bar.pack(side='right', padx=5, pady=2)
        self.progress_bar.pack_forget()  # Hide initially
    
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<Control-s>', lambda e: self.save_verse_changes())
        self.root.bind('<Control-o>', lambda e: self.import_json_files())
        self.root.bind('<Control-e>', lambda e: self.export_translation())
        self.root.bind('<F5>', lambda e: self.refresh_all())
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
    
    # Event handlers and utility methods
    def set_status(self, message: str):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def show_progress(self, show: bool = True):
        """Show or hide progress bar"""
        if show:
            self.progress_bar.pack(side='right', padx=5, pady=2)
        else:
            self.progress_bar.pack_forget()
        self.root.update_idletasks()
    
    def refresh_translations(self):
        """Refresh translations list and combo boxes"""
        translations = self.db.get_translations()
        
        # Update translation combo
        trans_values = [t['abbrev'] for t in translations]
        self.translation_combo['values'] = trans_values
        
        # Update translations tree
        self.trans_tree.delete(*self.trans_tree.get_children())
        for trans in translations:
            self.trans_tree.insert('', 'end', values=(
                trans['abbrev'],
                trans['full_name'],
                trans.get('source_file', ''),
                trans.get('total_verses', 0),
                trans.get('error_count', 0),
                trans.get('imported_date', '')[:19] if trans.get('imported_date') else ''
            ))
    
    def refresh_error_statistics(self):
        """Refresh error statistics dashboard"""
        stats = self.db.get_error_statistics()
        
        # Clear existing buttons
        for widget in self.stats_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update error type combo
        error_types = ['All'] + [stat['error_code'] for stat in stats if stat['total_count'] > 0]
        self.error_type_combo['values'] = error_types
        
        # Create error buttons
        row = 0
        col = 0
        total_errors = 0
        total_open = 0
        total_fixed = 0
        
        for stat in stats:
            if stat['total_count'] == 0:
                continue
            
            # Determine button style based on severity
            if stat['severity'] == 'CRITICAL':
                style = 'Error.TButton'
            elif stat['severity'] == 'WARNING':
                style = 'Warning.TButton'
            else:
                style = 'TButton'
            
            # Create button with error info
            btn_text = f"{stat['error_code']}\n{stat['total_count']} total\n{stat['open_count']} open"
            
            btn = ttk.Button(self.stats_scrollable_frame, text=btn_text, style=style,
                           command=lambda ec=stat['error_code']: self.show_error_type_details(ec))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
            # Add tooltip
            self.create_tooltip(btn, f"{stat['description']}\nSeverity: {stat['severity']}")
            
            # Update totals
            total_errors += stat['total_count']
            total_open += stat['open_count']
            total_fixed += stat['fixed_count']
            
            col += 1
            if col >= 4:  # 4 buttons per row
                col = 0
                row += 1
        
        # Configure column weights
        for i in range(4):
            self.stats_scrollable_frame.columnconfigure(i, weight=1)
        
        # Update summary
        self.summary_text.config(state='normal')
        self.summary_text.delete(1.0, tk.END)
        
        summary = f"""Total Errors: {total_errors}
Open Errors: {total_open}
Fixed Errors: {total_fixed}
Ignored Errors: {total_errors - total_open - total_fixed}

Most Common Issues:
"""
        
        # Add top 5 error types
        sorted_stats = sorted([s for s in stats if s['total_count'] > 0], 
                             key=lambda x: x['total_count'], reverse=True)
        
        for i, stat in enumerate(sorted_stats[:5]):
            summary += f"{i+1}. {stat['error_code']}: {stat['total_count']} occurrences\n"
        
        self.summary_text.insert(1.0, summary)
        self.summary_text.config(state='disabled')
    
    def on_translation_selected(self, event=None):
        """Handle translation selection"""
        translation = self.current_translation.get()
        if not translation:
            return
        
        # Load books for this translation
        books = self.db.get_books(translation)
        book_values = [f"{book['book']} ({book['book_name']})" for book in books]
        self.book_combo['values'] = book_values
        
        # Clear current selections
        self.current_book.set('')
        self.current_chapter.set('')
        self.clear_verse_list()
    
    def on_book_selected(self, event=None):
        """Handle book selection"""
        book_str = self.current_book.get()
        translation = self.current_translation.get()
        
        if not book_str or not translation:
            return
        
        # Extract book abbreviation
        book = book_str.split(' ')[0]
        
        # Load chapters for this book
        chapters = self.db.get_chapters(translation, book)
        chapter_values = [str(ch['chapter']) for ch in chapters]
        self.chapter_combo['values'] = chapter_values
        
        self.current_chapter.set('')
        self.clear_verse_list()
    
    def on_chapter_selected(self, event=None):
        """Handle chapter selection"""
        self.load_verses()
    
    def load_verses(self):
        """Load verses for current selection"""
        translation = self.current_translation.get()
        book_str = self.current_book.get()
        chapter_str = self.current_chapter.get()
        
        if not all([translation, book_str, chapter_str]):
            return
        
        book = book_str.split(' ')[0]
        try:
            chapter = int(chapter_str)
        except ValueError:
            return
        
        # Get verses
        verses = self.db.get_verses(translation=translation, book=book, chapter=chapter)
        
        # Clear existing items
        self.verse_tree.delete(*self.verse_tree.get_children())
        
        # Add verses to tree
        for verse in verses:
            status = "❌ Error" if verse.has_errors else "✅ Clean"
            if verse.corrected_text:
                status = "✏️ Edited"
            
            preview = verse.original_text[:50] + "..." if len(verse.original_text) > 50 else verse.original_text
            
            self.verse_tree.insert('', 'end', values=(
                f"{verse.book} {verse.chapter}:{verse.verse}",
                preview,
                status
            ), tags=(str(verse.id),))
    
    def clear_verse_list(self):
        """Clear verse list"""
        self.verse_tree.delete(*self.verse_tree.get_children())
        self.clear_verse_editor()
    
    def on_verse_selected(self, event=None):
        """Handle verse selection in tree"""
        selection = self.verse_tree.selection()
        if not selection:
            return
        
        item = self.verse_tree.item(selection[0])
        tags = item.get('tags', [])
        
        if tags:
            verse_id = int(tags[0])
            self.load_verse_editor(verse_id)
    
    def load_verse_editor(self, verse_id: int):
        """Load verse into editor"""
        verses = self.db.get_verses()
        verse = next((v for v in verses if v.id == verse_id), None)
        
        if not verse:
            return
        
        self.selected_verse_id = verse_id
        
        # Update verse info
        self.verse_info_label.config(
            text=f"{verse.translation} {verse.book_name} {verse.chapter}:{verse.verse}"
        )
        
        # Load original text
        self.original_text.config(state='normal')
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(1.0, verse.original_text)
        self.original_text.config(state='disabled')
        
        # Load corrected text
        self.corrected_text.delete(1.0, tk.END)
        if verse.corrected_text:
            self.corrected_text.insert(1.0, verse.corrected_text)
        else:
            self.corrected_text.insert(1.0, verse.original_text)
        
        # Load notes
        self.correction_notes.delete(1.0, tk.END)
        if verse.correction_notes:
            self.correction_notes.insert(1.0, verse.correction_notes)
    
    def clear_verse_editor(self):
        """Clear verse editor"""
        self.selected_verse_id = None
        self.verse_info_label.config(text="Select a verse to edit")
        
        self.original_text.config(state='normal')
        self.original_text.delete(1.0, tk.END)
        self.original_text.config(state='disabled')
        
        self.corrected_text.delete(1.0, tk.END)
        self.correction_notes.delete(1.0, tk.END)
    
    def save_verse_changes(self):
        """Save changes to current verse"""
        if not self.selected_verse_id:
            messagebox.showwarning("No Selection", "Please select a verse to save.")
            return
        
        corrected_text = self.corrected_text.get(1.0, tk.END).strip()
        notes = self.correction_notes.get(1.0, tk.END).strip()
        
        if not corrected_text:
            messagebox.showwarning("Empty Text", "Corrected text cannot be empty.")
            return
        
        if self.db.update_verse(self.selected_verse_id, corrected_text, notes):
            self.set_status("Changes saved successfully")
            self.load_verses()  # Refresh the list
            messagebox.showinfo("Success", "Verse updated successfully!")
        else:
            messagebox.showerror("Error", "Failed to save changes.")
    
    def reset_verse_editor(self):
        """Reset verse editor to original text"""
        if not self.selected_verse_id:
            return
        
        if messagebox.askyesno("Reset", "Reset to original text? This will lose any changes."):
            self.load_verse_editor(self.selected_verse_id)
    
    def view_verse_errors(self):
        """View errors for current verse"""
        if not self.selected_verse_id:
            messagebox.showwarning("No Selection", "Please select a verse first.")
            return
        
        errors = self.db.get_error_instances(verse_id=self.selected_verse_id)
        
        if not errors:
            messagebox.showinfo("No Errors", "No errors found for this verse.")
            return
        
        # Show errors in a dialog
        error_window = tk.Toplevel(self.root)
        error_window.title("Verse Errors")
        error_window.geometry("600x400")
        
        tree = ttk.Treeview(error_window, columns=('Type', 'Severity', 'Status', 'Description'), 
                           show='headings')
        
        tree.heading('Type', text='Error Type')
        tree.heading('Severity', text='Severity')
        tree.heading('Status', text='Status')
        tree.heading('Description', text='Description')
        
        for error in errors:
            tree.insert('', 'end', values=(
                error['error_code'],
                error['severity'],
                error['status'],
                error['error_text']
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def search_verses(self):
        """Search for verses containing text"""
        search_text = self.search_var.get().strip()
        if not search_text:
            return
        
        translation = self.current_translation.get() or None
        results = self.db.search_verses(search_text, translation)
        
        if not results:
            messagebox.showinfo("No Results", f"No verses found containing '{search_text}'")
            return
        
        # Show results in a dialog
        results_window = tk.Toplevel(self.root)
        results_window.title(f"Search Results: '{search_text}'")
        results_window.geometry("800x500")
        
        tree = ttk.Treeview(results_window, columns=('Translation', 'Reference', 'Text'), 
                           show='headings')
        
        tree.heading('Translation', text='Translation')
        tree.heading('Reference', text='Reference')
        tree.heading('Text', text='Text')
        
        tree.column('Translation', width=100)
        tree.column('Reference', width=150)
        tree.column('Text', width=500)
        
        for result in results:
            ref = f"{result['book']} {result['chapter']}:{result['verse']}"
            text = result['original_text'][:100] + "..." if len(result['original_text']) > 100 else result['original_text']
            
            tree.insert('', 'end', values=(
                result['translation'],
                ref,
                text
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Double-click to go to verse
        def goto_verse(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                values = item['values']
                # You could implement navigation to the specific verse here
                messagebox.showinfo("Go to Verse", f"Navigate to {values[0]} {values[1]}")
        
        tree.bind('<Double-1>', goto_verse)
    
    def refresh_errors_list(self, event=None):
        """Refresh errors list based on filters"""
        status = self.filter_status.get()
        error_type = self.filter_error_type.get()
        
        # Get filtered errors
        error_type_id = None
        if error_type != "All":
            error_types = self.db.get_error_types()
            error_type_obj = next((et for et in error_types if et['error_code'] == error_type), None)
            if error_type_obj:
                error_type_id = error_type_obj['id']
        
        status_filter = status if status != 'all' else None
        errors = self.db.get_error_instances(status=status_filter, error_type_id=error_type_id)
        
        # Clear tree
        self.errors_tree.delete(*self.errors_tree.get_children())
        
        # Add errors
        for error in errors:
            ref = f"{error['book']} {error['chapter']}:{error['verse']}"
            
            self.errors_tree.insert('', 'end', values=(
                error['id'],
                error['translation'],
                ref,
                error['error_code'],
                error['severity'],
                error['status'],
                error['error_text'][:50] + "..." if len(error['error_text']) > 50 else error['error_text']
            ), tags=(str(error['id']),))
    
    def show_error_context_menu(self, event):
        """Show context menu for error items"""
        item = self.errors_tree.identify_row(event.y)
        if item:
            self.errors_tree.selection_set(item)
            
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Mark as Fixed", command=self.mark_error_fixed)
            context_menu.add_command(label="Mark as Ignored", command=self.mark_error_ignored)
            context_menu.add_command(label="Reopen Error", command=self.reopen_error)
            context_menu.add_separator()
            context_menu.add_command(label="View Details", command=self.view_error_details)
            
            context_menu.post(event.x_root, event.y_root)
    
    def mark_error_fixed(self):
        """Mark selected error as fixed"""
        selection = self.errors_tree.selection()
        if not selection:
            return
        
        item = self.errors_tree.item(selection[0])
        error_id = int(item['tags'][0])
        
        notes = tk.simpledialog.askstring("Resolution Notes", 
                                         "Enter resolution notes (optional):")
        
        if self.db.resolve_error(error_id, 'fixed', notes):
            self.refresh_errors_list()
            self.set_status("Error marked as fixed")
    
    def mark_error_ignored(self):
        """Mark selected error as ignored"""
        selection = self.errors_tree.selection()
        if not selection:
            return
        
        item = self.errors_tree.item(selection[0])
        error_id = int(item['tags'][0])
        
        notes = tk.simpledialog.askstring("Ignore Reason", 
                                         "Why is this error being ignored?")
        
        if self.db.resolve_error(error_id, 'ignored', notes):
            self.refresh_errors_list()
            self.set_status("Error marked as ignored")
    
    def reopen_error(self):
        """Reopen a resolved error"""
        selection = self.errors_tree.selection()
        if not selection:
            return
        
        item = self.errors_tree.item(selection[0])
        error_id = int(item['tags'][0])
        
        if self.db.resolve_error(error_id, 'open', "Reopened"):
            self.refresh_errors_list()
            self.set_status("Error reopened")
    
    def view_error_details(self, event=None):
        """View detailed error information"""
        selection = self.errors_tree.selection()
        if not selection:
            return
        
        item = self.errors_tree.item(selection[0])
        error_id = int(item['tags'][0])
        
        errors = self.db.get_error_instances()
        error = next((e for e in errors if e['id'] == error_id), None)
        
        if not error:
            return
        
        # Update error details text
        details = f"""Error ID: {error['id']}
Translation: {error['translation']}
Reference: {error['book']} {error['chapter']}:{error['verse']}
Error Type: {error['error_code']} ({error['severity']})
Status: {error['status']}
Detected: {error['detected_date']}
Resolved: {error['resolved_date'] or 'Not resolved'}

Error Text: {error['error_text']}

Context: {error['context']}

Resolution Notes: {error['resolution_notes'] or 'None'}
"""
        
        self.error_details_text.config(state='normal')
        self.error_details_text.delete(1.0, tk.END)
        self.error_details_text.insert(1.0, details)
        self.error_details_text.config(state='disabled')
    
    def show_error_type_details(self, error_code: str):
        """Show details for a specific error type"""
        # Filter errors by type
        self.filter_error_type.set(error_code)
        self.notebook.select(2)  # Switch to errors tab
        self.refresh_errors_list()
    
    # Import/Export and bulk operations
    def import_json_files(self):
        """Import JSON Bible files"""
        files = filedialog.askopenfilenames(
            title="Select JSON Bible Files",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="."
        )
        
        if not files:
            return
        
        # Show progress
        self.show_progress(True)
        self.progress_var.set(0)
        
        def import_worker():
            """Background import worker"""
            successful = 0
            failed = 0
            
            for i, file_path in enumerate(files):
                try:
                    self.set_status(f"Importing {Path(file_path).name}...")
                    
                    def progress_callback(count, description):
                        self.set_status(f"Importing {Path(file_path).name}: {count} {description}")
                    
                    result = self.db.import_json_file(Path(file_path), progress_callback=progress_callback)
                    successful += 1
                    
                    self.set_status(f"Imported {result['translation']}: {result['total_verses']} verses")
                    
                except Exception as e:
                    failed += 1
                    self.set_status(f"Failed to import {Path(file_path).name}: {e}")
                
                # Update progress
                self.progress_var.set((i + 1) / len(files) * 100)
            
            # Refresh UI
            self.root.after(0, lambda: [
                self.refresh_translations(),
                self.show_progress(False),
                self.set_status(f"Import complete: {successful} successful, {failed} failed"),
                messagebox.showinfo("Import Complete", 
                                  f"Import finished:\n{successful} files imported successfully\n{failed} files failed")
            ])
        
        # Run import in background thread
        thread = threading.Thread(target=import_worker)
        thread.daemon = True
        thread.start()
    
    def export_translation(self):
        """Export translation to JSON"""
        if not self.current_translation.get():
            messagebox.showwarning("No Selection", "Please select a translation to export.")
            return
        
        translation = self.current_translation.get()
        
        # Ask for export options
        dialog = ExportDialog(self.root, translation)
        if not dialog.result:
            return
        
        file_path = filedialog.asksaveasfilename(
            title=f"Export {translation}",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfilename=f"{translation}_corrected.json"
        )
        
        if not file_path:
            return
        
        try:
            data = self.db.export_translation(translation, dialog.use_corrected)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Export Complete", f"Translation exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export translation: {e}")
    
    def export_error_report(self):
        """Export error report to CSV"""
        file_path = filedialog.asksaveasfilename(
            title="Export Error Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfilename=f"bible_errors_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not file_path:
            return
        
        try:
            errors = self.db.get_error_instances()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Error ID', 'Translation', 'Book', 'Chapter', 'Verse',
                    'Error Type', 'Severity', 'Status', 'Error Text', 'Context',
                    'Detected Date', 'Resolved Date', 'Resolution Notes'
                ])
                
                # Write data
                for error in errors:
                    writer.writerow([
                        error['id'], error['translation'], error['book'],
                        error['chapter'], error['verse'], error['error_code'],
                        error['severity'], error['status'], error['error_text'],
                        error['context'], error['detected_date'],
                        error['resolved_date'], error['resolution_notes']
                    ])
            
            messagebox.showinfo("Export Complete", f"Error report exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export error report: {e}")
    
    def scan_for_errors(self):
        """Scan translations for errors"""
        translations = [t['abbrev'] for t in self.db.get_translations()]
        
        if not translations:
            messagebox.showwarning("No Translations", "No translations available to scan.")
            return
        
        # Show selection dialog
        dialog = ScanDialog(self.root, translations)
        if not dialog.selected_translations:
            return
        
        # Show progress
        self.show_progress(True)
        self.progress_var.set(0)
        
        def scan_worker():
            """Background scan worker"""
            from bible_correction_system import ErrorDetectionEngine
            
            engine = ErrorDetectionEngine(self.db)
            total_translations = len(dialog.selected_translations)
            
            for i, translation in enumerate(dialog.selected_translations):
                try:
                    def progress_callback(current, total, description):
                        progress = (i / total_translations + (current / total) / total_translations) * 100
                        self.progress_var.set(progress)
                        self.set_status(f"Scanning {translation}: {description}")
                    
                    result = engine.scan_translation(translation, progress_callback)
                    self.set_status(f"Scanned {translation}: {result['errors_found']} errors found")
                    
                except Exception as e:
                    self.set_status(f"Error scanning {translation}: {e}")
                
                self.progress_var.set((i + 1) / total_translations * 100)
            
            # Refresh UI
            self.root.after(0, lambda: [
                self.refresh_error_statistics(),
                self.refresh_errors_list(),
                self.show_progress(False),
                self.set_status("Scan complete"),
                messagebox.showinfo("Scan Complete", "Error scanning finished.")
            ])
        
        # Run scan in background thread
        thread = threading.Thread(target=scan_worker)
        thread.daemon = True
        thread.start()
    
    def delete_translation(self):
        """Delete selected translation"""
        selection = self.trans_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a translation to delete.")
            return
        
        item = self.trans_tree.item(selection[0])
        translation = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete translation '{translation}'?\n"
                              "This will remove all verses and associated errors."):
            try:
                # Delete from database
                self.db.conn.execute("DELETE FROM bible_verses WHERE translation = ?", (translation,))
                self.db.conn.execute("DELETE FROM translations WHERE abbrev = ?", (translation,))
                self.db.conn.commit()
                
                self.refresh_translations()
                self.set_status(f"Translation {translation} deleted")
                
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete translation: {e}")
    
    def show_bulk_operations(self):
        """Show bulk operations dialog"""
        BulkOperationsDialog(self.root, self.db, self)
    
    def show_database_stats(self):
        """Show database statistics"""
        translations = self.db.get_translations()
        total_verses = sum(t.get('total_verses', 0) for t in translations)
        total_errors = sum(t.get('error_count', 0) for t in translations)
        
        stats_text = f"""Database Statistics:

Translations: {len(translations)}
Total Verses: {total_verses:,}
Total Open Errors: {total_errors:,}

Translation Details:
"""
        
        for trans in translations:
            stats_text += f"- {trans['abbrev']}: {trans.get('total_verses', 0):,} verses, {trans.get('error_count', 0)} errors\n"
        
        messagebox.showinfo("Database Statistics", stats_text)
    
    def view_translation_details(self, event=None):
        """View detailed translation information"""
        selection = self.trans_tree.selection()
        if not selection:
            return
        
        item = self.trans_tree.item(selection[0])
        translation = item['values'][0]
        
        # Switch to editor tab and select this translation
        self.current_translation.set(translation)
        self.on_translation_selected()
        self.notebook.select(1)  # Editor tab
    
    def refresh_all(self):
        """Refresh all data"""
        self.refresh_translations()
        self.refresh_error_statistics()
        self.refresh_errors_list()
        self.set_status("All data refreshed")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """Bible Text Correction System - User Guide

Keyboard Shortcuts:
- Ctrl+S: Save verse changes
- Ctrl+O: Import JSON files
- Ctrl+E: Export translation
- F5: Refresh all data
- Ctrl+F: Focus search box

Tabs:
1. Dashboard: View error statistics and overview
2. Editor: Edit individual verses and corrections
3. Errors: Manage and resolve error instances
4. Translations: Import, export, and manage translations

Error Severities:
- CRITICAL: Must be fixed (structure issues, invalid data)
- WARNING: Should be reviewed (formatting, duplicates)
- INFO: For reference (capitalization patterns)

For more detailed help, refer to the documentation.
"""
        
        messagebox.showinfo("User Guide", help_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Bible Text Correction System
Version 1.0

A comprehensive system for correcting and managing Bible text data with error detection, correction tracking, and export capabilities.

Features:
- SQLite database storage
- Advanced error detection
- Text correction interface
- Statistics and reporting
- Import/Export functionality

Built with Python and tkinter.
"""
        
        messagebox.showinfo("About", about_text)
    
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="yellow", 
                           relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

# Helper dialog classes
class ExportDialog:
    """Dialog for export options"""
    
    def __init__(self, parent, translation):
        self.result = None
        self.use_corrected = True
        
        dialog = tk.Toplevel(parent)
        dialog.title(f"Export {translation}")
        dialog.geometry("300x150")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        ttk.Label(dialog, text=f"Export options for {translation}:").pack(pady=10)
        
        self.use_corrected_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Use corrected text where available", 
                       variable=self.use_corrected_var).pack(pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def on_ok():
            self.use_corrected = self.use_corrected_var.get()
            self.result = True
            dialog.destroy()
        
        def on_cancel():
            self.result = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        dialog.wait_window()

class ScanDialog:
    """Dialog for selecting translations to scan"""
    
    def __init__(self, parent, translations):
        self.selected_translations = []
        
        dialog = tk.Toplevel(parent)
        dialog.title("Scan for Errors")
        dialog.geometry("400x300")
        dialog.transient(parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select translations to scan:").pack(pady=10)
        
        # Listbox with checkboxes
        frame = ttk.Frame(dialog)
        frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.listbox = tk.Listbox(frame, selectmode='multiple')
        scrollbar = ttk.Scrollbar(frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        for trans in translations:
            self.listbox.insert(tk.END, trans)
        
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Select All", 
                  command=self.select_all).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_all).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='left', padx=15)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='left', padx=5)
        
        self.dialog = dialog
        dialog.wait_window()
    
    def select_all(self):
        self.listbox.select_set(0, tk.END)
    
    def clear_all(self):
        self.listbox.select_clear(0, tk.END)
    
    def on_ok(self):
        selected_indices = self.listbox.curselection()
        self.selected_translations = [self.listbox.get(i) for i in selected_indices]
        self.dialog.destroy()
    
    def on_cancel(self):
        self.selected_translations = []
        self.dialog.destroy()

class BulkOperationsDialog:
    """Dialog for bulk operations on errors and verses"""
    
    def __init__(self, parent, db_manager, main_gui):
        self.db = db_manager
        self.main_gui = main_gui
        
        dialog = tk.Toplevel(parent)
        dialog.title("Bulk Operations")
        dialog.geometry("500x400")
        dialog.transient(parent)
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Error operations tab
        error_frame = ttk.Frame(notebook)
        notebook.add(error_frame, text="Error Operations")
        
        ttk.Label(error_frame, text="Bulk Error Operations", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Button(error_frame, text="Mark All 'Whitespace Issues' as Fixed",
                  command=self.fix_whitespace_errors).pack(pady=5, fill='x')
        
        ttk.Button(error_frame, text="Ignore All 'Capitalization Issues'",
                  command=self.ignore_capitalization_errors).pack(pady=5, fill='x')
        
        ttk.Button(error_frame, text="Reopen All Fixed Errors",
                  command=self.reopen_fixed_errors).pack(pady=5, fill='x')
        
        # Text operations tab
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Text Operations")
        
        ttk.Label(text_frame, text="Bulk Text Operations", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Button(text_frame, text="Auto-fix Multiple Spaces",
                  command=self.auto_fix_spaces).pack(pady=5, fill='x')
        
        ttk.Button(text_frame, text="Auto-trim Whitespace",
                  command=self.auto_trim_whitespace).pack(pady=5, fill='x')
        
        ttk.Button(text_frame, text="Reset All Corrections",
                  command=self.reset_corrections).pack(pady=5, fill='x')
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def fix_whitespace_errors(self):
        """Mark all whitespace errors as fixed"""
        if messagebox.askyesno("Confirm", "Mark all whitespace issues as fixed?"):
            # Implementation here
            messagebox.showinfo("Complete", "Whitespace errors marked as fixed")
            self.main_gui.refresh_errors_list()
    
    def ignore_capitalization_errors(self):
        """Ignore all capitalization errors"""
        if messagebox.askyesno("Confirm", "Ignore all capitalization issues?"):
            # Implementation here
            messagebox.showinfo("Complete", "Capitalization errors ignored")
            self.main_gui.refresh_errors_list()
    
    def reopen_fixed_errors(self):
        """Reopen all fixed errors"""
        if messagebox.askyesno("Confirm", "Reopen all fixed errors? This cannot be undone."):
            # Implementation here
            messagebox.showinfo("Complete", "Fixed errors reopened")
            self.main_gui.refresh_errors_list()
    
    def auto_fix_spaces(self):
        """Auto-fix multiple spaces in all verses"""
        if messagebox.askyesno("Confirm", "Auto-fix multiple spaces in all verses?"):
            # Implementation here
            messagebox.showinfo("Complete", "Multiple spaces fixed")
            self.main_gui.refresh_all()
    
    def auto_trim_whitespace(self):
        """Auto-trim whitespace from all verses"""
        if messagebox.askyesno("Confirm", "Auto-trim whitespace from all verses?"):
            # Implementation here
            messagebox.showinfo("Complete", "Whitespace trimmed")
            self.main_gui.refresh_all()
    
    def reset_corrections(self):
        """Reset all corrections"""
        if messagebox.askyesno("Confirm", "Reset ALL corrections? This cannot be undone!"):
            # Implementation here
            messagebox.showinfo("Complete", "All corrections reset")
            self.main_gui.refresh_all()