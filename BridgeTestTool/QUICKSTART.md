# Quick Start Guide - Bridge Test Tool

## 5-Minute Setup

### Prerequisites
- Python 3.7+ installed on both computers
- Both computers connected to the network bridge
- Know the IP address of one computer (will be the server)

### First Time Setup (Optional but Recommended)

Before starting, verify your system is ready:

```bash
cd BridgeTestTool
python check_dependencies.py
```

This checks that all required modules are installed. If anything is missing, you'll get clear instructions on how to install it.

**The tool also checks dependencies automatically when you start it**, so you'll always know if something is missing!

---

## Step-by-Step Instructions

### On Computer A (Server Side)

1. **Open the tool:**
   - Windows: Double-click `run.bat`
   - Linux/Mac: Run `./run.sh` or `python3 run.py`

2. **Choose Server Mode:**
   - Click the "Server Mode" button

3. **Start the server:**
   - Click "Start Server"
   - Note the IP address shown (e.g., 192.168.1.100)

4. **Wait for connection:**
   - The log will show "Waiting for client connection..."
   - Status will show "Running" in green

---

### On Computer B (Client Side)

1. **Open the tool:**
   - Windows: Double-click `run.bat`
   - Linux/Mac: Run `./run.sh` or `python3 run.py`

2. **Choose Client Mode:**
   - Click the "Client Mode" button

3. **Connect to server:**
   - Enter the server's IP address (from Step 3 above)
   - Enter port: 5000
   - Click "Connect"
   - Status should show "Connected" in green

4. **Run a test:**
   - Keep default settings (10 seconds, 8192 bytes)
   - Click "Start Test"
   - Watch the progress bar and live statistics
   - Test completes automatically

---

## Understanding Results

### During Test
- **Activity Log**: Shows real-time events
- **Live Statistics**: Shows current speed in Mbps
- **Progress Bar**: Shows test completion percentage
- **Packets Sent**: Number of data packets transmitted

### After Test
- Results are automatically saved to the database
- Click "View Database" to see all test results
- Check the "Speed (Mbps)" column for throughput

### What to Look For

**Good Results:**
- Speed: Close to your bridge's rated speed (e.g., 80-100 Mbps)
- Consistent: Similar speeds across multiple tests
- Both directions: Upload and download speeds are similar

**Problem Indicators:**
- Very low speed (< 10 Mbps on 100 Mbps hardware)
- Large difference between upload/download (10x difference)
- Connection drops or errors in the log

---

## Common Settings

### Quick Test (10 seconds)
- Duration: 10
- Packet Size: 8192
- Use for: Fast diagnosis

### Standard Test (30 seconds)
- Duration: 30
- Packet Size: 8192
- Use for: Accurate measurement

### Extended Test (5 minutes)
- Duration: 300
- Packet Size: 8192
- Use for: Stability analysis

---

## Troubleshooting

### "Connection failed" error
1. Check server IP address
2. Make sure server is running
3. Check firewall settings (allow port 5000)
4. Try pinging the server computer

### Very slow speeds
1. Check wireless bridge alignment
2. Look for physical obstructions
3. Check for interference sources
4. Verify bridge configuration

### Cannot start server
1. Check if another program is using port 5000
2. Try running as administrator (Windows)
3. Check firewall settings

---

## Finding Your IP Address

### Windows
```
Open Command Prompt
Type: ipconfig
Look for "IPv4 Address"
```

### Linux/Mac
```
Open Terminal
Type: ifconfig (or ip addr)
Look for "inet" address
```

---

## Next Steps

1. **Run Multiple Tests**: Test several times for consistency
2. **View Database**: Check historical results and trends
3. **Try Different Settings**: Experiment with duration and packet size
4. **Compare Results**: Test at different times of day
5. **Keep Records**: Use the database to track performance over time

---

## Support

- Full documentation: See README.md
- Configuration: Edit config.yaml
- Database: Located at bridge_test.db

**Ready? Start with the Server on Computer A!**
