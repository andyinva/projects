"""
Database module for storing and retrieving test results
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class TestDatabase:
    """Manages SQLite database for test results"""

    def __init__(self, db_path: str = "bridge_test.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Create database tables if they don't exist"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                direction TEXT NOT NULL,
                speed_mbps REAL NOT NULL,
                bytes_transferred INTEGER NOT NULL,
                packet_loss_percent REAL DEFAULT 0.0,
                latency_avg_ms REAL DEFAULT 0.0,
                test_duration REAL NOT NULL,
                mode TEXT DEFAULT 'unknown'
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS connection_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                mode TEXT DEFAULT 'unknown'
            )
        ''')

        self.conn.commit()

    def add_test_result(self, direction: str, speed_mbps: float,
                       bytes_transferred: int, packet_loss: float = 0.0,
                       latency_ms: float = 0.0, duration: float = 0.0,
                       mode: str = 'unknown') -> int:
        """
        Add a test result to the database

        Args:
            direction: 'upload', 'download', or 'bidirectional'
            speed_mbps: Speed in megabits per second
            bytes_transferred: Total bytes transferred
            packet_loss: Packet loss percentage
            latency_ms: Average latency in milliseconds
            duration: Test duration in seconds
            mode: 'server' or 'client'

        Returns:
            ID of inserted record
        """
        timestamp = datetime.now()

        self.cursor.execute('''
            INSERT INTO test_results
            (timestamp, direction, speed_mbps, bytes_transferred,
             packet_loss_percent, latency_avg_ms, test_duration, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, direction, speed_mbps, bytes_transferred,
              packet_loss, latency_ms, duration, mode))

        self.conn.commit()
        return self.cursor.lastrowid

    def add_connection_event(self, event_type: str, details: str = '',
                            mode: str = 'unknown'):
        """
        Add a connection event to the database

        Args:
            event_type: Type of event (connected, disconnected, error, etc.)
            details: Additional details about the event
            mode: 'server' or 'client'
        """
        timestamp = datetime.now()

        self.cursor.execute('''
            INSERT INTO connection_events (timestamp, event_type, details, mode)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, event_type, details, mode))

        self.conn.commit()

    def get_all_results(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all test results from database

        Args:
            limit: Maximum number of results to return (None for all)

        Returns:
            List of test result dictionaries
        """
        query = '''
            SELECT id, timestamp, direction, speed_mbps, bytes_transferred,
                   packet_loss_percent, latency_avg_ms, test_duration, mode
            FROM test_results
            ORDER BY timestamp DESC
        '''

        if limit:
            query += f' LIMIT {limit}'

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'direction': row[2],
                'speed_mbps': row[3],
                'bytes_transferred': row[4],
                'packet_loss_percent': row[5],
                'latency_avg_ms': row[6],
                'test_duration': row[7],
                'mode': row[8]
            })

        return results

    def get_connection_events(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get connection events from database

        Args:
            limit: Maximum number of events to return (None for all)

        Returns:
            List of event dictionaries
        """
        query = '''
            SELECT id, timestamp, event_type, details, mode
            FROM connection_events
            ORDER BY timestamp DESC
        '''

        if limit:
            query += f' LIMIT {limit}'

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        events = []
        for row in rows:
            events.append({
                'id': row[0],
                'timestamp': row[1],
                'event_type': row[2],
                'details': row[3],
                'mode': row[4]
            })

        return events

    def clear_all_data(self):
        """Clear all data from database"""
        self.cursor.execute('DELETE FROM test_results')
        self.cursor.execute('DELETE FROM connection_events')
        self.conn.commit()

    def get_statistics(self) -> Dict:
        """Get summary statistics from database"""
        stats = {}

        # Total tests
        self.cursor.execute('SELECT COUNT(*) FROM test_results')
        stats['total_tests'] = self.cursor.fetchone()[0]

        # Average speeds by direction
        self.cursor.execute('''
            SELECT direction, AVG(speed_mbps), COUNT(*)
            FROM test_results
            GROUP BY direction
        ''')

        stats['by_direction'] = {}
        for row in self.cursor.fetchall():
            stats['by_direction'][row[0]] = {
                'avg_speed': row[1],
                'count': row[2]
            }

        return stats

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
