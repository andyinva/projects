#!/usr/bin/env python3
"""
Test script to demonstrate database functionality
This script can be run independently to test the database module
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import TestDatabase


def main():
    """Test the database functionality"""
    print("=" * 60)
    print("Bridge Test Tool - Database Test")
    print("=" * 60)
    print()

    # Create database
    print("1. Creating/connecting to database...")
    db = TestDatabase("test_bridge.db")
    print("   ✓ Database connected")
    print()

    # Add some test results
    print("2. Adding test results...")
    test_data = [
        ("upload", 87.3, 125000000, 0.02, 3.2, 30.0, "client"),
        ("upload", 85.1, 122000000, 0.01, 3.1, 30.0, "client"),
        ("download", 89.5, 128000000, 0.03, 3.4, 30.0, "server"),
    ]

    for direction, speed, bytes_tx, loss, latency, duration, mode in test_data:
        result_id = db.add_test_result(
            direction=direction,
            speed_mbps=speed,
            bytes_transferred=bytes_tx,
            packet_loss=loss,
            latency_ms=latency,
            duration=duration,
            mode=mode
        )
        print(f"   ✓ Added {direction} test (ID: {result_id}, Speed: {speed} Mbps)")
    print()

    # Add connection events
    print("3. Adding connection events...")
    events = [
        ("server_started", "Listening on 0.0.0.0:5000", "server"),
        ("client_connected", "192.168.1.101:52341", "server"),
        ("connected_to_server", "192.168.1.100:5000", "client"),
    ]

    for event_type, details, mode in events:
        db.add_connection_event(event_type, details, mode)
        print(f"   ✓ Added event: {event_type}")
    print()

    # Retrieve all results
    print("4. Retrieving test results...")
    results = db.get_all_results()
    print(f"   ✓ Found {len(results)} test results")
    print()

    # Display results
    print("5. Test Results:")
    print("   " + "-" * 85)
    print(f"   {'ID':<4} {'Timestamp':<20} {'Dir':<8} {'Speed':<12} {'Bytes':<15} {'Duration':<10}")
    print("   " + "-" * 85)

    for result in results:
        print(f"   {result['id']:<4} "
              f"{result['timestamp']:<20} "
              f"{result['direction']:<8} "
              f"{result['speed_mbps']:>10.2f} "
              f"{result['bytes_transferred']:>14} "
              f"{result['test_duration']:>9.2f}s")
    print("   " + "-" * 85)
    print()

    # Get statistics
    print("6. Statistics:")
    stats = db.get_statistics()
    print(f"   Total tests: {stats['total_tests']}")
    print()
    print("   By direction:")
    for direction, data in stats['by_direction'].items():
        print(f"   - {direction}: {data['count']} tests, "
              f"avg speed: {data['avg_speed']:.2f} Mbps")
    print()

    # Get connection events
    print("7. Connection Events:")
    events = db.get_connection_events()
    print(f"   ✓ Found {len(events)} events")
    for event in events:
        print(f"   [{event['timestamp']}] {event['event_type']}: {event['details']}")
    print()

    # Clean up test
    print("8. Cleanup (optional):")
    response = input("   Delete test database? (y/N): ")
    if response.lower() == 'y':
        db.close()
        os.remove("test_bridge.db")
        print("   ✓ Test database deleted")
    else:
        print("   ✓ Test database kept (test_bridge.db)")
        db.close()

    print()
    print("=" * 60)
    print("Database test completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
