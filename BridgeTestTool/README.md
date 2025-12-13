# Network Bridge Test Tool

A Python-based diagnostic tool with Windows GUI for testing and analyzing network performance between two wireless bridge units (e.g., Adalov CPE660).

## Features

- **Simple Windows GUI** - Easy-to-use interface for both server and client
- **Real-time Monitoring** - Live data display in scrolling log window
- **Connection Status** - Visual indicators showing connection state
- **Throughput Testing** - Measure upload/download speeds
- **SQLite Database** - Persistent storage of all test results
- **Database Viewer** - Built-in viewer to examine historical data
- **Timestamp Tracking** - All data includes date and time
- **Bidirectional Testing** - Test both sides of the bridge

## System Requirements

- Python 3.7 or higher
- Windows, Linux, or macOS
- Two computers (one on each side of the wireless bridge)
- Network connectivity between the computers

## Installation

1. **Clone or download this repository**

2. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

3. **Check dependencies** (recommended)
   ```bash
   cd BridgeTestTool
   python check_dependencies.py
   ```
   This will verify that your system has everything needed to run the tool.

4. **No additional packages required!**
   - The tool uses only Python standard library (tkinter, socket, sqlite3)
   - Automatic dependency checking on startup
   - Clear warnings if anything is missing

## Quick Start Guide

### Step 1: Setup on Both Computers

1. Copy the entire `BridgeTestTool` folder to both computers
2. Make sure both computers are connected to the network bridge

### Step 2: Start the Server (Computer A)

On the first computer:

```bash
cd BridgeTestTool
python src/launcher.py
```

1. Click **"Server Mode"** button
2. Click **"Start Server"** in the server window
3. Note the server's IP address (shown in the window)

### Step 3: Start the Client (Computer B)

On the second computer:

```bash
cd BridgeTestTool
python src/launcher.py
```

1. Click **"Client Mode"** button
2. Enter the server's IP address
3. Click **"Connect"**
4. Once connected, click **"Start Test"**

### Step 4: View Results

- Live data appears in the Activity Log
- Statistics update in real-time
- Click "View Database" to see all historical test results
- Click "Clear Database" to remove all stored data

## Running Modes

### Launcher Mode (Recommended)

```bash
python src/launcher.py
```

Choose between Server or Client mode from the launcher window.

### Direct Server Mode

```bash
python src/server.py
```

Runs directly in server mode.

### Direct Client Mode

```bash
python src/client.py
```

Runs directly in client mode.

## GUI Features

### Server Window

- **Server Status** - Shows if server is running
- **Client Status** - Shows if a client is connected
- **Start/Stop Server** - Control server operation
- **Activity Log** - Real-time log of all events
- **Live Statistics** - Shows data received/sent with speeds
- **View Database** - Opens database viewer
- **Clear Database** - Removes all test data

### Client Window

- **Server Connection** - Enter IP and port to connect
- **Connection Status** - Shows if connected to server
- **Test Controls** - Configure test duration and packet size
- **Start Test** - Begin throughput test
- **Progress Bar** - Visual progress during test
- **Activity Log** - Real-time log of all events
- **Live Statistics** - Shows data sent/received with speeds
- **View Database** - Opens database viewer
- **Clear Database** - Removes all test data

### Database Viewer

- Displays all test results in a sortable table
- Shows timestamp, direction, speed, bytes transferred, etc.
- Refresh button to update the view
- Can be opened from both server and client

## Understanding the Results

### Test Metrics

- **Speed (Mbps)** - Throughput in megabits per second
- **Bytes Transferred** - Total data sent/received
- **Direction** - Upload, download, or bidirectional
- **Duration** - How long the test ran
- **Mode** - Whether recorded by server or client

### Interpreting Results

**Good Performance:**
- Upload and download speeds are similar
- Speed close to the bridge's rated capacity
- Consistent results across multiple tests

**Problems to Watch For:**
- Large difference between upload and download speeds (asymmetry)
- Speeds much lower than expected
- High variation between tests
- Connection drops during testing

## Database

### Database File

- **Filename**: `bridge_test.db`
- **Location**: Same directory as the program
- **Format**: SQLite database

### Tables

**test_results** - Stores test result data:
- ID
- Timestamp (date and time)
- Direction (upload/download)
- Speed in Mbps
- Bytes transferred
- Packet loss percentage
- Average latency
- Test duration
- Mode (server/client)

**connection_events** - Stores connection events:
- ID
- Timestamp
- Event type (connected, disconnected, etc.)
- Details
- Mode (server/client)

### Accessing Database

The database can be accessed programmatically or using any SQLite viewer:

```python
from src.database import TestDatabase

db = TestDatabase()
results = db.get_all_results()
for result in results:
    print(result)
```

## Configuration

Edit `config.yaml` to customize:

- Default server IP and port
- Test parameters (duration, packet size)
- Buffer sizes and timeouts
- Database settings
- Logging options

## Troubleshooting

### Missing Dependencies

If you get errors about missing modules when starting the tool:

1. **Run the dependency checker**
   ```bash
   python check_dependencies.py
   ```
   This will show exactly what's missing and how to install it.

2. **Missing tkinter** (most common on Linux)
   ```bash
   # Debian/Ubuntu
   sudo apt-get install python3-tk

   # RedHat/CentOS/Fedora
   sudo yum install python3-tkinter

   # Arch Linux
   sudo pacman -S tk
   ```

3. **Python version too old**
   - You need Python 3.7 or higher
   - Download the latest version from https://www.python.org/downloads/

4. **Import errors**
   - Make sure you're running from the correct directory
   - Try: `python3 check_dependencies.py` to diagnose

### Cannot Connect to Server

1. **Check IP Address** - Make sure you're using the correct server IP
2. **Check Firewall** - Ensure port 5000 is not blocked
3. **Check Network** - Verify both computers can ping each other
4. **Check Server** - Make sure server is running and shows "Running" status

### Test Fails or Errors

1. **Network Issues** - Check wireless bridge connection
2. **Timeout** - Try increasing test duration
3. **Firewall** - Disable firewall temporarily to test

### Slow Performance

1. **Bridge Configuration** - Check CPE660 settings
2. **Interference** - Look for sources of wireless interference
3. **Alignment** - Ensure bridge antennas are properly aligned
4. **Obstructions** - Check for physical obstructions in signal path

### Database Issues

1. **Permission Denied** - Run from a directory where you have write permissions
2. **Database Locked** - Close all other instances of the program
3. **Corrupt Database** - Delete `bridge_test.db` and restart

## Tips for Best Results

1. **Close Other Programs** - Minimize network usage during testing
2. **Run Multiple Tests** - Test several times for consistency
3. **Try Different Times** - Test at different times of day
4. **Vary Test Duration** - Short tests for quick checks, long tests for stability
5. **Keep Records** - Use the database to track performance over time

## Project Structure

```
BridgeTestTool/
├── src/
│   ├── __init__.py         # Package initialization
│   ├── launcher.py         # Main launcher (choose mode)
│   ├── server.py           # Server with GUI
│   ├── client.py           # Client with GUI
│   ├── protocol.py         # Network protocol/messages
│   └── database.py         # SQLite database management
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

### Network Protocol

- Uses TCP sockets for reliable communication
- Custom message protocol with JSON payloads
- Message types: HELLO, START_TEST, TEST_DATA, STOP_TEST, etc.
- Automatic message size handling

### Threading

- Server: Separate thread for accepting connections and handling clients
- Client: Separate threads for receiving messages and running tests
- All GUI operations run on the main thread

### Database

- SQLite3 for zero-configuration database
- Automatic table creation on first run
- Thread-safe operations
- Persistent storage across sessions

## Future Enhancements

Potential features for future versions:

- Latency and ping tests
- Packet loss measurement
- Graphical charts and visualizations
- Export to CSV/Excel
- Email reports
- Scheduled automated testing
- Web-based interface
- Support for multiple simultaneous clients

## License

This project is provided as-is for network diagnostic purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the log messages in the Activity Log
3. Check the database for historical patterns
4. Consult the wireless bridge documentation

## Credits

Created for testing Adalov CPE660 wireless bridge units and diagnosing network performance issues.

## Version

Version 1.0.0 - Initial Release

---

**Happy Testing!**
