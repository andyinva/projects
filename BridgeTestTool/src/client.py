"""
Client module with GUI for network bridge testing
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


class BridgeTestClient:
    """Client for bridge testing with GUI"""

    def __init__(self):
        """Initialize client"""
        self.server_host = ''
        self.server_port = 5000
        self.client_socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_testing = False

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
        self.root.title("Bridge Test Tool - Client")
        self.root.geometry("900x750")

        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Server Connection", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(conn_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.host_entry = ttk.Entry(conn_frame, width=20)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        self.host_entry.insert(0, "192.168.1.100")

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.port_entry = ttk.Entry(conn_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        self.port_entry.insert(0, "5000")

        self.connect_button = ttk.Button(conn_frame, text="Connect",
                                         command=self.connect_to_server)
        self.connect_button.grid(row=0, column=4, padx=5, pady=5)

        self.disconnect_button = ttk.Button(conn_frame, text="Disconnect",
                                            command=self.disconnect_from_server,
                                            state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=5, padx=5, pady=5)

        # Status
        ttk.Label(conn_frame, text="Status:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.status_label = ttk.Label(conn_frame, text="Not Connected",
                                      foreground="red", font=('Arial', 10, 'bold'))
        self.status_label.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5)

        # Test Control Frame
        test_frame = ttk.LabelFrame(self.root, text="Test Controls", padding=10)
        test_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(test_frame, text="Test Duration (seconds):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.duration_entry = ttk.Entry(test_frame, width=10)
        self.duration_entry.grid(row=0, column=1, padx=5, pady=5)
        self.duration_entry.insert(0, "10")

        ttk.Label(test_frame, text="Packet Size (bytes):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.packet_size_entry = ttk.Entry(test_frame, width=10)
        self.packet_size_entry.grid(row=0, column=3, padx=5, pady=5)
        self.packet_size_entry.insert(0, "8192")

        self.start_test_button = ttk.Button(test_frame, text="Start Test",
                                           command=self.start_test,
                                           state=tk.DISABLED)
        self.start_test_button.grid(row=1, column=0, columnspan=2, pady=10, padx=5)

        self.stop_test_button = ttk.Button(test_frame, text="Stop Test",
                                          command=self.stop_test,
                                          state=tk.DISABLED)
        self.stop_test_button.grid(row=1, column=2, columnspan=2, pady=10, padx=5)

        # Database Controls
        db_frame = ttk.Frame(test_frame)
        db_frame.grid(row=2, column=0, columnspan=4, pady=5)

        ttk.Button(db_frame, text="View Database",
                  command=self.show_database).pack(side=tk.LEFT, padx=5)

        ttk.Button(db_frame, text="Clear Database",
                  command=self.clear_database).pack(side=tk.LEFT, padx=5)

        # Statistics Frame
        stats_frame = ttk.LabelFrame(self.root, text="Live Statistics (Upload Test)", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(stats_frame, text="Uploaded to Server:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.sent_label = ttk.Label(stats_frame, text="0 bytes (0 Mbps)")
        self.sent_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(stats_frame, text="Downloaded from Server:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.received_label = ttk.Label(stats_frame, text="0 bytes (0 Mbps)", foreground="gray")
        self.received_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(stats_frame, text="Packets:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.packets_sent_label = ttk.Label(stats_frame, text="0")
        self.packets_sent_label.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(stats_frame, variable=self.progress_var,
                                       maximum=100, length=400)
        self.progress.grid(row=2, column=0, columnspan=4, pady=10, padx=5)

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

        self.log("Client initialized. Enter server IP and click 'Connect'.", 'info')

    def log(self, message: str, level: str = 'info'):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def connect_to_server(self):
        """Connect to the server"""
        try:
            self.server_host = self.host_entry.get()
            self.server_port = int(self.port_entry.get())

            self.log(f"Connecting to {self.server_host}:{self.server_port}...", 'info')

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0)

            # Disable Nagle's algorithm for immediate packet transmission
            self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self.client_socket.connect((self.server_host, self.server_port))

            self.is_connected = True
            self.log("Connected to server!", 'success')
            self.status_label.config(text="Connected", foreground="green")

            # Update button states
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.start_test_button.config(state=tk.NORMAL)
            self.host_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)

            # Send HELLO
            self.client_socket.send(Protocol.create_hello_message('client'))

            # Record event in database
            self.db.add_connection_event('connected_to_server',
                                        f'{self.server_host}:{self.server_port}',
                                        'client')

            # Start receiving messages
            threading.Thread(target=self.receive_messages, daemon=True).start()

        except Exception as e:
            self.log(f"Connection failed: {e}", 'error')
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def disconnect_from_server(self):
        """Disconnect from server"""
        if self.client_socket:
            try:
                self.client_socket.send(Protocol.create_disconnect_message())
                # Give server time to process disconnect message
                time.sleep(0.1)
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        self.is_connected = False
        self.log("Disconnected from server", 'warning')
        self.status_label.config(text="Not Connected", foreground="red")

        # Update button states
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.start_test_button.config(state=tk.DISABLED)
        self.stop_test_button.config(state=tk.DISABLED)
        self.host_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)

        # Record event in database
        self.db.add_connection_event('disconnected_from_server', '', 'client')

    def receive_messages(self):
        """Receive messages from server"""
        try:
            while self.is_connected:
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

                except socket.timeout:
                    continue
                except ConnectionError as e:
                    if self.is_connected:
                        self.log(f"Connection closed: {e}", 'warning')
                    break
                except Exception as e:
                    if self.is_connected:
                        self.log(f"Error receiving message: {e}", 'error')
                    break

        except Exception as e:
            self.log(f"Receive thread error: {e}", 'error')
        finally:
            if self.is_connected:
                self.disconnect_from_server()

    def process_message(self, message: dict):
        """Process received message"""
        msg_type = message.get('type')
        payload = message.get('payload', {})

        if msg_type == MessageType.HELLO_ACK:
            self.log(f"Server acknowledged connection (status: {payload.get('status')})", 'success')

        elif msg_type == MessageType.TEST_DATA:
            # Receiving data from server (download test)
            self.packets_received += 1
            self.bytes_received += payload.get('size', 0)

        elif msg_type == MessageType.PONG:
            # Received pong response
            rtt = (time.time() - payload.get('ping_timestamp', 0)) * 1000
            self.log(f"Ping: {rtt:.2f} ms", 'data')

        elif msg_type == MessageType.DISCONNECT:
            self.log("Server disconnecting", 'warning')
            self.disconnect_from_server()

    def start_test(self):
        """Start the throughput test"""
        try:
            duration = int(self.duration_entry.get())
            packet_size = int(self.packet_size_entry.get())

            if duration <= 0 or packet_size <= 0:
                messagebox.showerror("Invalid Input", "Duration and packet size must be positive")
                return

            self.is_testing = True
            self.bytes_sent = 0
            self.bytes_received = 0
            self.packets_sent = 0
            self.packets_received = 0
            self.test_start_time = time.time()

            # Update UI
            self.start_test_button.config(state=tk.DISABLED)
            self.stop_test_button.config(state=tk.NORMAL)
            self.progress_var.set(0)

            self.log(f"Starting test: {duration}s, {packet_size} byte packets", 'success')

            # Send START_TEST message
            self.client_socket.send(Protocol.create_start_test_message({
                'duration': duration,
                'packet_size': packet_size
            }))

            # Start test in separate thread
            threading.Thread(target=self.run_test,
                           args=(duration, packet_size),
                           daemon=True).start()

        except Exception as e:
            self.log(f"Error starting test: {e}", 'error')
            messagebox.showerror("Error", f"Failed to start test: {e}")

    def run_test(self, duration: int, packet_size: int):
        """Run the throughput test"""
        try:
            end_time = time.time() + duration
            sequence = 0

            while time.time() < end_time and self.is_testing:
                # Create and send test packet
                message = Protocol.create_test_data_message(sequence, packet_size)
                self.client_socket.send(message)

                self.packets_sent += 1
                self.bytes_sent += packet_size
                sequence += 1

                # Update progress
                elapsed = time.time() - self.test_start_time
                progress = (elapsed / duration) * 100
                self.progress_var.set(min(progress, 100))

                # Update statistics every 100 packets
                if self.packets_sent % 100 == 0:
                    self.update_statistics()

                # Log every 1000 packets
                if self.packets_sent % 1000 == 0:
                    self.log(f"Sent {self.packets_sent} packets ({format_bytes(self.bytes_sent)})", 'data')

                # Small delay to avoid overwhelming the network
                time.sleep(0.001)

            # Test completed
            self.stop_test()

        except Exception as e:
            self.log(f"Error during test: {e}", 'error')
            self.is_testing = False

    def stop_test(self):
        """Stop the current test"""
        if not self.is_testing:
            return

        self.is_testing = False

        # Send STOP_TEST message
        try:
            self.client_socket.send(Protocol.create_stop_test_message())
        except:
            pass

        # Calculate final results
        duration = time.time() - self.test_start_time

        if duration > 0 and self.bytes_sent > 0:
            upload_speed = calculate_throughput(self.bytes_sent, duration)
            self.log(f"Test completed!", 'success')
            self.log(f"Upload: {format_speed(upload_speed)} ({format_bytes(self.bytes_sent)} in {duration:.2f}s)", 'success')

            # Store in database
            self.db.add_test_result(
                direction='upload',
                speed_mbps=upload_speed,
                bytes_transferred=self.bytes_sent,
                packet_loss=0.0,
                latency_ms=0.0,
                duration=duration,
                mode='client'
            )

        # Update UI
        self.start_test_button.config(state=tk.NORMAL)
        self.stop_test_button.config(state=tk.DISABLED)
        self.progress_var.set(100)

    def update_statistics(self):
        """Update live statistics display"""
        duration = time.time() - self.test_start_time
        if duration > 0:
            sent_speed = calculate_throughput(self.bytes_sent, duration)
            recv_speed = calculate_throughput(self.bytes_received, duration)

            self.sent_label.config(text=f"{format_bytes(self.bytes_sent)} ({format_speed(sent_speed)})")
            self.received_label.config(text=f"{format_bytes(self.bytes_received)} ({format_speed(recv_speed)})")
            self.packets_sent_label.config(text=f"{self.packets_sent}")

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
        if self.is_connected:
            self.disconnect_from_server()
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

    print("\n✓ All dependencies satisfied - Starting client...\n")

    client = BridgeTestClient()
    client.run()


if __name__ == '__main__':
    main()
