"""
Network protocol for bridge testing communication
"""

import json
import time
import struct
from typing import Dict, Any, Optional


class MessageType:
    """Message type constants"""
    HELLO = "HELLO"
    HELLO_ACK = "HELLO_ACK"
    START_TEST = "START_TEST"
    TEST_DATA = "TEST_DATA"
    TEST_RESULT = "TEST_RESULT"
    STOP_TEST = "STOP_TEST"
    PING = "PING"
    PONG = "PONG"
    ERROR = "ERROR"
    DISCONNECT = "DISCONNECT"


class Protocol:
    """Handles message encoding and decoding"""

    HEADER_SIZE = 8  # 4 bytes for length + 4 bytes reserved
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1 MB

    @staticmethod
    def encode_message(msg_type: str, payload: Dict[str, Any] = None) -> bytes:
        """
        Encode a message for transmission

        Args:
            msg_type: Type of message (from MessageType)
            payload: Optional payload dictionary

        Returns:
            Encoded message as bytes
        """
        if payload is None:
            payload = {}

        message = {
            'type': msg_type,
            'timestamp': time.time(),
            'payload': payload
        }

        json_data = json.dumps(message).encode('utf-8')
        length = len(json_data)

        # Create header: 4 bytes for length, 4 bytes reserved
        header = struct.pack('!II', length, 0)

        return header + json_data

    @staticmethod
    def decode_message(data: bytes) -> Optional[Dict[str, Any]]:
        """
        Decode a received message

        Args:
            data: Raw bytes received

        Returns:
            Decoded message dictionary or None if invalid
        """
        try:
            if len(data) < Protocol.HEADER_SIZE:
                return None

            # Parse header
            length, _ = struct.unpack('!II', data[:Protocol.HEADER_SIZE])

            if length > Protocol.MAX_MESSAGE_SIZE:
                return None

            # Parse JSON
            json_data = data[Protocol.HEADER_SIZE:Protocol.HEADER_SIZE + length]
            message = json.loads(json_data.decode('utf-8'))

            return message

        except Exception as e:
            print(f"Error decoding message: {e}")
            return None

    @staticmethod
    def create_hello_message(mode: str) -> bytes:
        """Create a HELLO message"""
        return Protocol.encode_message(MessageType.HELLO, {
            'mode': mode,
            'version': '1.0.0'
        })

    @staticmethod
    def create_hello_ack_message(mode: str) -> bytes:
        """Create a HELLO_ACK message"""
        return Protocol.encode_message(MessageType.HELLO_ACK, {
            'mode': mode,
            'version': '1.0.0',
            'status': 'ready'
        })

    @staticmethod
    def create_start_test_message(test_config: Dict[str, Any]) -> bytes:
        """Create a START_TEST message"""
        return Protocol.encode_message(MessageType.START_TEST, test_config)

    @staticmethod
    def create_test_data_message(sequence: int, data_size: int) -> bytes:
        """Create a TEST_DATA message"""
        # Create a payload with specified size
        data = b'X' * data_size

        return Protocol.encode_message(MessageType.TEST_DATA, {
            'sequence': sequence,
            'size': data_size,
            'data': list(data[:100])  # Only send first 100 bytes in JSON
        })

    @staticmethod
    def create_test_result_message(results: Dict[str, Any]) -> bytes:
        """Create a TEST_RESULT message"""
        return Protocol.encode_message(MessageType.TEST_RESULT, results)

    @staticmethod
    def create_stop_test_message() -> bytes:
        """Create a STOP_TEST message"""
        return Protocol.encode_message(MessageType.STOP_TEST, {})

    @staticmethod
    def create_ping_message() -> bytes:
        """Create a PING message"""
        return Protocol.encode_message(MessageType.PING, {})

    @staticmethod
    def create_pong_message(ping_timestamp: float) -> bytes:
        """Create a PONG message"""
        return Protocol.encode_message(MessageType.PONG, {
            'ping_timestamp': ping_timestamp
        })

    @staticmethod
    def create_error_message(error_msg: str) -> bytes:
        """Create an ERROR message"""
        return Protocol.encode_message(MessageType.ERROR, {
            'error': error_msg
        })

    @staticmethod
    def create_disconnect_message() -> bytes:
        """Create a DISCONNECT message"""
        return Protocol.encode_message(MessageType.DISCONNECT, {})


def calculate_throughput(bytes_transferred: int, duration_seconds: float) -> float:
    """
    Calculate throughput in Mbps

    Args:
        bytes_transferred: Total bytes transferred
        duration_seconds: Duration in seconds

    Returns:
        Throughput in Mbps
    """
    if duration_seconds <= 0:
        return 0.0

    bits = bytes_transferred * 8
    megabits = bits / 1_000_000
    throughput_mbps = megabits / duration_seconds

    return throughput_mbps


def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"


def format_speed(mbps: float) -> str:
    """Format speed into human-readable string"""
    if mbps < 1.0:
        return f"{mbps * 1000:.2f} Kbps"
    else:
        return f"{mbps:.2f} Mbps"


def recv_exact(sock, num_bytes: int) -> bytes:
    """
    Receive exactly num_bytes from socket

    This ensures we get all requested bytes, even if recv()
    returns partial data. Essential for reliable message framing.

    Args:
        sock: Socket to receive from
        num_bytes: Exact number of bytes to receive

    Returns:
        Bytes received

    Raises:
        ConnectionError: If connection closes before receiving all bytes
        socket.timeout: If socket times out (will be caught by caller)
    """
    import socket
    data = b''
    while len(data) < num_bytes:
        try:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data")
            data += chunk
        except socket.timeout:
            # Socket timeout - this is normal, just retry
            # The caller's loop will handle whether to continue or break
            if len(data) == 0:
                # No data received at all, re-raise to let caller handle
                raise
            # Otherwise continue trying to receive the rest
            continue
    return data
