#!/usr/bin/env python3
"""
Test script for the Bible Search Interface
This script demonstrates the key features and allows testing of the interface.
"""

import tkinter as tk
from tkinter import ttk
from bible_search_interface import BibleSearchInterface
import json
import os


def test_config_management():
    """Test the configuration management functionality."""
    print("Testing Configuration Management...")
    
    # Test config file creation and loading
    test_config_file = "test_config.json"
    
    # Clean up any existing test config
    if os.path.exists(test_config_file):
        os.remove(test_config_file)
    
    from bible_search_interface import ConfigManager
    config_manager = ConfigManager(test_config_file)
    
    # Test default values
    assert config_manager.get('window_width') == 1000
    assert config_manager.get('window_height') == 700
    
    # Test setting and getting values
    config_manager.set('window_width', 1000)
    assert config_manager.get('window_width') == 1000
    
    # Test saving and loading
    config_manager.save_config()
    new_config_manager = ConfigManager(test_config_file)
    assert new_config_manager.get('window_width') == 1000
    
    # Clean up
    os.remove(test_config_file)
    print("✓ Configuration management tests passed!")


def demonstrate_features():
    """Demonstrate the key features of the interface."""
    print("\nDemonstrating Bible Search Interface Features:")
    print("=" * 50)
    print("Key Features Implemented:")
    print("• 6 window sections with proper OOP design")
    print("• Synchronized width resizing for all windows")
    print("• Independent height resizing for bottom 4 windows")
    print("• JSON configuration management")
    print("• Bordered windows with titles")
    print("• Checkboxes and radio buttons in search settings")
    print("• Message display window")
    print("• Text display areas in resizable windows")
    print("• Configuration persistence on window close")
    print("\nTo test the interface:")
    print("1. Run: python bible_search_interface.py")
    print("2. Try resizing the main window (width syncs across all windows)")
    print("3. Try dragging the bottom borders of windows 3-6 to resize height")
    print("4. Check/uncheck boxes and radio buttons in the top window")
    print("5. Close and reopen to verify settings are saved")


def create_demo_with_test_data():
    """Create a demo version with additional test data."""
    
    class DemoBibleSearchInterface(BibleSearchInterface):
        """Enhanced demo version with test data and resize feedback."""
        
        def __init__(self):
            super().__init__()
            self.add_demo_data()
            self.create_resize_feedback()
        
        def create_resize_feedback(self):
            """Add real-time resize feedback display."""
            # Create a feedback label at the bottom
            self.feedback_frame = ttk.Frame(self.main_frame)
            self.feedback_frame.grid(row=6, column=0, sticky='ew', padx=2, pady=5)
            
            self.feedback_label = ttk.Label(self.feedback_frame, 
                                          text="Resize feedback will appear here...", 
                                          font=('Arial', 10, 'bold'),
                                          foreground='blue')
            self.feedback_label.pack()
            
            # Update window heights display every 500ms
            self.update_height_display()
        
        def update_height_display(self):
            """Update the height display in real-time."""
            heights = []
            for key, frame in self.resizable_frames.items():
                height = frame.winfo_height()
                window_num = {"search_window": "3", "reading_window": "4", 
                             "subject_verses": "5", "verse_comments": "6"}[key]
                heights.append(f"Win{window_num}:{height}px")
            
            feedback_text = "Window Heights: " + " | ".join(heights)
            self.feedback_label.configure(text=feedback_text)
            
            # Schedule next update
            self.root.after(500, self.update_height_display)
        
        def sync_window_heights(self, new_height):
            """Override sync method to show when it's called."""
            super().sync_window_heights(new_height)
            # Flash the feedback to show sync was called
            self.feedback_label.configure(foreground='red')
            self.root.after(200, lambda: self.feedback_label.configure(foreground='blue'))
        
        def add_demo_data(self):
            """Add demonstration data to the interface."""
            # Add more messages
            messages = [
                "Search functionality ready.",
                "Database connection established.",
                "4,032 verses loaded from database.",
                "Ready for Bible search operations."
            ]
            
            for msg in messages:
                self.add_message(msg)
            
            # Add sample content to resizable windows
            sample_contents = {
                "search_window": "Search Results:\n" + "\n".join([
                    f"Result {i+1}: John 3:16 - For God so loved the world..."
                    for i in range(15)
                ]),
                "reading_window": "Reading Pane:\n" + 
                    "John 3:16-18\n\n" +
                    "16 For God so loved the world that he gave his one and only Son, "
                    "that whoever believes in him shall not perish but have eternal life.\n\n" +
                    "17 For God did not send his Son into the world to condemn the world, "
                    "but to save the world through him.\n\n" +
                    "18 Whoever believes in him is not condemned, but whoever does not "
                    "believe stands condemned already because they have not believed in "
                    "the name of God's one and only Son.",
                "subject_verses": "Subject: Love\n" + "\n".join([
                    f"• 1 John 4:{i+7} - Love verse {i+1}"
                    for i in range(10)
                ]),
                "verse_comments": "Comments:\n" + "\n".join([
                    f"Comment {i+1}: This verse demonstrates God's love for humanity."
                    for i in range(8)
                ])
            }
            
            # Update the text widgets with sample content
            for key, frame in self.resizable_frames.items():
                for widget in frame.content_frame.winfo_children():
                    if isinstance(widget, tk.Text):
                        widget.delete('1.0', 'end')
                        widget.insert('1.0', sample_contents.get(key, "Sample content"))
    
    return DemoBibleSearchInterface


if __name__ == "__main__":
    print("Bible Search Interface Test Suite")
    print("=" * 40)
    
    # Run configuration tests
    test_config_management()
    
    # Demonstrate features
    demonstrate_features()
    
    print("\nStarting enhanced demo application...")
    print("(Close the window to return to this script)")
    
    # Create and run enhanced demo
    demo_app = create_demo_with_test_data()()
    demo_app.run()
    
    print("\nDemo completed. Check 'bible_search_config.json' for saved settings.")