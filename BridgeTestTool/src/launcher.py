"""
Main launcher for Bridge Test Tool
Allows user to choose between Server and Client mode
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check dependencies before importing GUI modules
from dependency_checker import check_dependencies

print("Checking dependencies...")
if not check_dependencies(verbose=True):
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)

print("\n✓ All dependencies satisfied - Starting application...\n")

import tkinter as tk
from tkinter import ttk
from server import BridgeTestServer
from client import BridgeTestClient


class LauncherWindow:
    """Main launcher window for choosing mode"""

    def __init__(self):
        """Initialize launcher"""
        self.root = tk.Tk()
        self.root.title("Bridge Test Tool - Launcher")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        self.setup_gui()

    def setup_gui(self):
        """Setup the launcher GUI"""
        # Title
        title_label = tk.Label(self.root,
                              text="Network Bridge Test Tool",
                              font=('Arial', 18, 'bold'),
                              pady=20)
        title_label.pack()

        # Description
        desc_label = tk.Label(self.root,
                             text="Test and diagnose network bridge performance\n"
                                  "between two Adalov CPE660 wireless bridge units",
                             font=('Arial', 10),
                             justify=tk.CENTER,
                             pady=10)
        desc_label.pack()

        # Mode Selection Frame
        mode_frame = ttk.LabelFrame(self.root, text="Select Mode", padding=20)
        mode_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Server Mode Button
        server_frame = ttk.Frame(mode_frame)
        server_frame.pack(pady=10, fill=tk.X)

        server_button = ttk.Button(server_frame,
                                   text="Server Mode",
                                   command=self.launch_server,
                                   width=20)
        server_button.pack(side=tk.LEFT, padx=10)

        server_desc = tk.Label(server_frame,
                              text="Run on Unit A (accepts connections)\n"
                                   "The server listens for incoming test connections",
                              justify=tk.LEFT,
                              font=('Arial', 9))
        server_desc.pack(side=tk.LEFT, padx=10)

        # Separator
        ttk.Separator(mode_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Client Mode Button
        client_frame = ttk.Frame(mode_frame)
        client_frame.pack(pady=10, fill=tk.X)

        client_button = ttk.Button(client_frame,
                                   text="Client Mode",
                                   command=self.launch_client,
                                   width=20)
        client_button.pack(side=tk.LEFT, padx=10)

        client_desc = tk.Label(client_frame,
                              text="Run on Unit B (initiates connection)\n"
                                   "The client connects to server and runs tests",
                              justify=tk.LEFT,
                              font=('Arial', 9))
        client_desc.pack(side=tk.LEFT, padx=10)

        # Instructions
        instructions_label = tk.Label(self.root,
                                     text="Run Server on one computer, Client on the other\n"
                                          "Both will share the same database file",
                                     font=('Arial', 8),
                                     foreground='gray',
                                     pady=10)
        instructions_label.pack()

    def launch_server(self):
        """Launch server mode"""
        self.root.destroy()
        server = BridgeTestServer()
        server.run()

    def launch_client(self):
        """Launch client mode"""
        self.root.destroy()
        client = BridgeTestClient()
        client.run()

    def run(self):
        """Run the launcher"""
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.root.mainloop()


def main():
    """Main entry point"""
    launcher = LauncherWindow()
    launcher.run()


if __name__ == '__main__':
    main()
