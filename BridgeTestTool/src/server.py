"""
Server module with GUI for network bridge testing
"""

import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from typing import Optional

from protocol import (Protocol, MessageType, calculate_throughput,
                     format_bytes, format_speed, recv_exact)
from database import TestDatabase


class BridgeTestServer:
    """Server for bridge testing with GUI"""

    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        """Initialize server"""
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.client_address: Optional[tuple] = None
        self.is_running = False
        self.is_connected = False

        # Database
        self.db = TestDatabase()

        # GUI
        self.root = None
        self.setup_gui()

        # Statistics
        self.bytes_received = 0
        self.bytes_sent = 0
        self.test_start_time = 0
        self.packets_received = 0
        self.packets_sent = 0

    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("Bridge Test Tool - Server")
        self.root.geometry("900x700")

        # Status Frame
        status_frame = ttk.LabelFrame(self.root, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(status_frame, text="Server Address:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.server_address_label = ttk.Label(status_frame, text=f"{self.host}:{self.port}",
                                               font=('Courier', 10, 'bold'))
        self.server_address_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Status:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.status_label = ttk.Label(status_frame, text="Stopped",
                                      foreground="red", font=('Arial', 10, 'bold'))
        self.status_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Client:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.client_label = ttk.Label(status_frame, text="Not Connected",
                                      foreground="gray")
        self.client_label.grid(row=2, column=1, sticky=tk.W, padx=5)

        # Control Frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = ttk.Button(control_frame, text="Start Server",
                                       command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop Server",
                                      command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="View Database",
                  command=self.show_database).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Clear Database",
                  command=self.clear_database).pack(side=tk.LEFT, padx=5)

        # Statistics Frame
        stats_frame = ttk.LabelFrame(self.root, text="Live Statistics (Upload Test)", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(stats_frame, text="Received from Client:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.received_label = ttk.Label(stats_frame, text="0 bytes (0 Mbps)")
        self.received_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(stats_frame, text="Sent to Client:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.sent_label = ttk.Label(stats_frame, text="0 bytes (0 Mbps)", foreground="gray")
        self.sent_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80,
                                                   font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colored output
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('data', foreground='blue')

        self.log("Server initialized. Click 'Start Server' to begin.", 'info')

    def log(self, message: str, level: str = 'info'):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_server(self):
        """Start the server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.is_running = True

            self.log(f"Server started on {self.host}:{self.port}", 'success')
            self.status_label.config(text="Running", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            # Record event in database
            self.db.add_connection_event('server_started',
                                        f'Listening on {self.host}:{self.port}',
                                        'server')

            # Start accepting connections in a separate thread
            threading.Thread(target=self.accept_connections, daemon=True).start()

        except Exception as e:
            self.log(f"Error starting server: {e}", 'error')
            messagebox.showerror("Error", f"Failed to start server: {e}")

    def stop_server(self):
        """Stop the server"""
        self.is_running = False

        if self.client_socket:
            try:
                # Send disconnect message
                self.client_socket.send(Protocol.create_disconnect_message())
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        self.is_connected = False
        self.log("Server stopped", 'warning')
        self.status_label.config(text="Stopped", foreground="red")
        self.client_label.config(text="Not Connected", foreground="gray")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # Record event in database
        self.db.add_connection_event('server_stopped', '', 'server')

    def accept_connections(self):
        """Accept incoming connections"""
        while self.is_running:
            try:
                self.log("Waiting for client connection...", 'info')
                self.server_socket.settimeout(1.0)

                try:
                    client_socket, client_address = self.server_socket.accept()
                except socket.timeout:
                    continue

                self.client_socket = client_socket
                self.client_address = client_address

                # Disable Nagle's algorithm for immediate packet transmission
                self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                self.is_connected = True

                self.log(f"Client connected from {client_address[0]}:{client_address[1]}", 'success')
                self.client_label.config(text=f"{client_address[0]}:{client_address[1]}",
                                        foreground="green")

                # Record event in database
                self.db.add_connection_event('client_connected',
                                            f'{client_address[0]}:{client_address[1]}',
                                            'server')

                # Handle client communication
                self.handle_client()

            except Exception as e:
                if self.is_running:
                    self.log(f"Error accepting connection: {e}", 'error')

    def handle_client(self):
        """Handle communication with connected client"""
        try:
            # Send HELLO_ACK
            self.client_socket.send(Protocol.create_hello_ack_message('server'))

            # Set socket timeout to make the loop responsive
            self.client_socket.settimeout(1.0)

            self.log("Ready to receive messages from client", 'info')

            while self.is_running and self.is_connected:
                try:
                    # Receive header (exact bytes)
                    header = recv_exact(self.client_socket, Protocol.HEADER_SIZE)

                    # Get message length
                    import struct
                    length, _ = struct.unpack('!II', header)

                    # Receive full message body (exact bytes)
                    body = recv_exact(self.client_socket, length)
                    data = header + body
                    message = Protocol.decode_message(data)

                    if message:
                        self.process_message(message)
                    else:
                        self.log(f"Failed to decode message (length={length})", 'error')

                except socket.timeout:
                    continue
                except ConnectionError as e:
                    self.log(f"Connection closed: {e}", 'warning')
                    break
                except Exception as e:
                    self.log(f"Error receiving data: {e}", 'error')
                    break

        except Exception as e:
            self.log(f"Error handling client: {e}", 'error')
        finally:
            self.disconnect_client()

    def process_message(self, message: dict):
        """Process received message"""
        msg_type = message.get('type')
        payload = message.get('payload', {})

        # Debug: log message types (except TEST_DATA to avoid spam)
        if msg_type != MessageType.TEST_DATA:
            self.log(f"Processing message type: {msg_type}", 'info')

        if msg_type == MessageType.HELLO:
            self.log(f"Received HELLO from client (mode: {payload.get('mode')})", 'info')

        elif msg_type == MessageType.START_TEST:
            self.log("Test started by client", 'success')
            self.bytes_received = 0
            self.bytes_sent = 0
            self.test_start_time = time.time()
            self.packets_received = 0
            self.packets_sent = 0

        elif msg_type == MessageType.TEST_DATA:
            # Receiving data from client (upload test)
            self.packets_received += 1
            data_size = payload.get('size', 0)
            self.bytes_received += data_size

            # Log first packet for debugging
            if self.packets_received == 1:
                self.log(f"Receiving TEST_DATA packets (size={data_size} bytes each)", 'info')

            # Update statistics every 100 packets
            if self.packets_received % 100 == 0:
                self.update_statistics()

            # Log every 1000 packets
            if self.packets_received % 1000 == 0:
                self.log(f"Received {self.packets_received} packets ({format_bytes(self.bytes_received)})", 'data')

        elif msg_type == MessageType.TEST_RESULT:
            # Client is sending test results
            self.log(f"Client test results: {payload}", 'success')

        elif msg_type == MessageType.STOP_TEST:
            self.handle_test_stop()

        elif msg_type == MessageType.PING:
            # Respond to ping
            pong = Protocol.create_pong_message(message.get('timestamp'))
            self.client_socket.send(pong)

        elif msg_type == MessageType.DISCONNECT:
            self.log("Client disconnecting", 'warning')
            self.disconnect_client()

    def handle_test_stop(self):
        """Handle test stop"""
        duration = time.time() - self.test_start_time

        if duration > 0 and self.bytes_received > 0:
            speed = calculate_throughput(self.bytes_received, duration)
            self.log(f"Upload test completed: {format_speed(speed)} ({format_bytes(self.bytes_received)} in {duration:.2f}s)", 'success')

            # Store in database
            self.db.add_test_result(
                direction='upload',
                speed_mbps=speed,
                bytes_transferred=self.bytes_received,
                packet_loss=0.0,
                latency_ms=0.0,
                duration=duration,
                mode='server'
            )

    def update_statistics(self):
        """Update live statistics display"""
        duration = time.time() - self.test_start_time
        if duration > 0:
            recv_speed = calculate_throughput(self.bytes_received, duration)
            sent_speed = calculate_throughput(self.bytes_sent, duration)

            self.received_label.config(text=f"{format_bytes(self.bytes_received)} ({format_speed(recv_speed)})")
            self.sent_label.config(text=f"{format_bytes(self.bytes_sent)} ({format_speed(sent_speed)})")

    def disconnect_client(self):
        """Disconnect the current client"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        self.is_connected = False
        self.client_label.config(text="Not Connected", foreground="gray")
        self.log("Client disconnected", 'warning')

        # Record event in database
        self.db.add_connection_event('client_disconnected', '', 'server')

    def show_database(self):
        """Show database viewer window"""
        db_window = tk.Toplevel(self.root)
        db_window.title("Test Results Database")
        db_window.geometry("1000x600")

        # Create treeview
        tree_frame = ttk.Frame(db_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview
        tree = ttk.Treeview(tree_frame,
                           columns=("ID", "Timestamp", "Direction", "Speed", "Bytes", "Loss", "Latency", "Duration", "Mode"),
                           show="headings",
                           yscrollcommand=vsb.set,
                           xscrollcommand=hsb.set)

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Configure columns
        tree.heading("ID", text="ID")
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Direction", text="Direction")
        tree.heading("Speed", text="Speed (Mbps)")
        tree.heading("Bytes", text="Bytes")
        tree.heading("Loss", text="Loss %")
        tree.heading("Latency", text="Latency (ms)")
        tree.heading("Duration", text="Duration (s)")
        tree.heading("Mode", text="Mode")

        tree.column("ID", width=50)
        tree.column("Timestamp", width=150)
        tree.column("Direction", width=100)
        tree.column("Speed", width=100)
        tree.column("Bytes", width=120)
        tree.column("Loss", width=70)
        tree.column("Latency", width=100)
        tree.column("Duration", width=100)
        tree.column("Mode", width=80)

        # Load data
        results = self.db.get_all_results()
        for result in results:
            tree.insert("", tk.END, values=(
                result['id'],
                result['timestamp'],
                result['direction'],
                f"{result['speed_mbps']:.2f}",
                format_bytes(result['bytes_transferred']),
                f"{result['packet_loss_percent']:.2f}",
                f"{result['latency_avg_ms']:.2f}",
                f"{result['test_duration']:.2f}",
                result['mode']
            ))

        # Pack
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Refresh button
        ttk.Button(db_window, text="Refresh",
                  command=lambda: self.refresh_database_view(tree)).pack(pady=5)

    def refresh_database_view(self, tree):
        """Refresh the database view"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)

        # Reload data
        results = self.db.get_all_results()
        for result in results:
            tree.insert("", tk.END, values=(
                result['id'],
                result['timestamp'],
                result['direction'],
                f"{result['speed_mbps']:.2f}",
                format_bytes(result['bytes_transferred']),
                f"{result['packet_loss_percent']:.2f}",
                f"{result['latency_avg_ms']:.2f}",
                f"{result['test_duration']:.2f}",
                result['mode']
            ))

    def clear_database(self):
        """Clear all database records"""
        result = messagebox.askyesno("Confirm",
                                     "Are you sure you want to clear all test data?")
        if result:
            self.db.clear_all_data()
            self.log("Database cleared", 'warning')
            messagebox.showinfo("Success", "Database has been cleared")

    def run(self):
        """Run the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_server()
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point"""
    # Check dependencies when running directly
    import sys
    from dependency_checker import check_dependencies

    print("Checking dependencies...")
    if not check_dependencies(verbose=True):
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

    print("\n✓ All dependencies satisfied - Starting server...\n")

    server = BridgeTestServer()
    server.run()


if __name__ == '__main__':
    main()
