# Bridge Test Tool - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK BRIDGE TEST TOOL                      │
└─────────────────────────────────────────────────────────────────┘

Computer A (Server Side)          Computer B (Client Side)
┌──────────────────────┐          ┌──────────────────────┐
│   run.py / run.bat   │          │   run.py / run.bat   │
│         ↓            │          │         ↓            │
│    launcher.py       │          │    launcher.py       │
│         ↓            │          │         ↓            │
│  ┌────────────────┐  │          │  ┌────────────────┐  │
│  │  Server Mode   │  │          │  │  Client Mode   │  │
│  │  (server.py)   │  │          │  │  (client.py)   │  │
│  │                │  │          │  │                │  │
│  │ ┌────────────┐ │  │          │  │ ┌────────────┐ │  │
│  │ │   GUI      │ │  │          │  │ │   GUI      │ │  │
│  │ │ Window     │ │  │          │  │ │ Window     │ │  │
│  │ └────────────┘ │  │          │  │ └────────────┘ │  │
│  │                │  │          │  │                │  │
│  │ • Start Server │  │          │  │ • Connect      │  │
│  │ • Activity Log │  │          │  │ • Start Test   │  │
│  │ • Statistics   │  │          │  │ • Statistics   │  │
│  │ • View DB      │  │◄────────►│  │ • View DB      │  │
│  │ • Clear DB     │  │   TCP    │  │ • Clear DB     │  │
│  └────────────────┘  │  Socket  │  └────────────────┘  │
│         ↓            │  Port    │         ↓            │
│    protocol.py       │  5000    │    protocol.py       │
│         ↓            │          │         ↓            │
│    database.py       │          │    database.py       │
│         ↓            │          │         ↓            │
│  bridge_test.db      │          │  bridge_test.db      │
└──────────────────────┘          └──────────────────────┘
         ▲                                  ▲
         └──────── Same Database File ──────┘
         (if on shared network drive)
```

## Component Flow

### 1. Launcher (launcher.py)

```
┌─────────────────────────────────┐
│    Bridge Test Tool Launcher    │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │   [Server Mode]           │  │
│  │   Run on Unit A           │  │
│  │   (accepts connections)   │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │   [Client Mode]           │  │
│  │   Run on Unit B           │  │
│  │   (initiates connection)  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### 2. Server Window

```
┌────────────────────────────────────────────────┐
│  Bridge Test Tool - Server               [×]  │
├────────────────────────────────────────────────┤
│ ┌─ Server Status ──────────────────────────┐  │
│ │ Server Address: 0.0.0.0:5000             │  │
│ │ Status: Running ●                        │  │
│ │ Client: 192.168.1.101:52341 ●           │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ [Start Server] [Stop Server]                  │
│ [View Database] [Clear Database]              │
│                                                │
│ ┌─ Live Statistics ────────────────────────┐  │
│ │ Received: 125.3 MB (87.3 Mbps)          │  │
│ │ Sent: 0 bytes (0 Mbps)                  │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ ┌─ Activity Log ───────────────────────────┐  │
│ │ [14:32:10] Server started               │  │
│ │ [14:32:15] Client connected             │  │
│ │ [14:32:20] Test started by client       │  │
│ │ [14:32:30] Received 10000 packets       │  │
│ │ [14:32:40] Upload test completed        │  │
│ │ ↓                                        │  │
│ └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### 3. Client Window

```
┌────────────────────────────────────────────────┐
│  Bridge Test Tool - Client               [×]  │
├────────────────────────────────────────────────┤
│ ┌─ Server Connection ──────────────────────┐  │
│ │ Server IP: [192.168.1.100▼]             │  │
│ │ Port: [5000] [Connect] [Disconnect]     │  │
│ │ Status: Connected ●                     │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ ┌─ Test Controls ──────────────────────────┐  │
│ │ Duration (sec): [10]  Packet Size: [8192] │ │
│ │                                           │  │
│ │ [Start Test]  [Stop Test]                │  │
│ │ [View Database] [Clear Database]         │  │
│ │                                           │  │
│ │ ████████████░░░░░░░░  Progress: 67%      │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ ┌─ Live Statistics ────────────────────────┐  │
│ │ Sent: 125.3 MB (87.3 Mbps)              │  │
│ │ Received: 0 bytes (0 Mbps)              │  │
│ │ Packets Sent: 15234                     │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ ┌─ Activity Log ───────────────────────────┐  │
│ │ [14:32:00] Client initialized           │  │
│ │ [14:32:15] Connected to server!         │  │
│ │ [14:32:20] Starting test: 10s           │  │
│ │ [14:32:25] Sent 5000 packets            │  │
│ │ [14:32:30] Test completed!              │  │
│ │ ↓                                        │  │
│ └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### 4. Database Viewer

```
┌───────────────────────────────────────────────────────────┐
│  Test Results Database                              [×]  │
├───────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┐ │
│ │ ID │ Timestamp         │ Direction │ Speed   │ ...   │ │
│ ├────┼──────────────────┼───────────┼─────────┼───────┤ │
│ │ 1  │ 2025-11-05 14:32 │ upload    │ 87.3    │ ...   │ │
│ │ 2  │ 2025-11-05 14:35 │ upload    │ 85.1    │ ...   │ │
│ │ 3  │ 2025-11-05 14:38 │ upload    │ 89.5    │ ...   │ │
│ │ 4  │ 2025-11-05 14:41 │ download  │ 8.9     │ ...   │ │
│ │ ↓                                                     │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                           │
│                    [Refresh]                              │
└───────────────────────────────────────────────────────────┘
```

## Data Flow During Test

```
CLIENT SIDE                    SERVER SIDE

1. Click "Start Test"
   │
   ├─► Send START_TEST ──────────► Receive START_TEST
   │                                │
   │                                ├─► Initialize counters
   │                                │
2. Start sending data               │
   │                                │
   ├─► Send TEST_DATA packet 1 ───► Receive & count
   ├─► Send TEST_DATA packet 2 ───► Receive & count
   ├─► Send TEST_DATA packet 3 ───► Receive & count
   │   ...                          │   ...
   │                                │
3. Update GUI                       Update GUI
   │ • Statistics                   │ • Statistics
   │ • Progress bar                 │ • Activity log
   │ • Activity log                 │
   │                                │
4. Test duration ends               │
   │                                │
   ├─► Send STOP_TEST ──────────────► Receive STOP_TEST
   │                                │
5. Calculate results                Calculate results
   │ • Speed (Mbps)                 │ • Speed (Mbps)
   │ • Bytes transferred            │ • Bytes received
   │                                │
6. Save to database                 Save to database
   │                                │
   └─► bridge_test.db ◄─────────────┘
```

## Database Schema

### test_results Table

```
┌──────────────────────────────────────────────────┐
│ Column                │ Type      │ Description  │
├───────────────────────┼───────────┼──────────────┤
│ id                    │ INTEGER   │ Primary key  │
│ timestamp             │ DATETIME  │ Date & time  │
│ direction             │ TEXT      │ upload/down  │
│ speed_mbps            │ REAL      │ Throughput   │
│ bytes_transferred     │ INTEGER   │ Data amount  │
│ packet_loss_percent   │ REAL      │ Loss %       │
│ latency_avg_ms        │ REAL      │ Avg latency  │
│ test_duration         │ REAL      │ Duration     │
│ mode                  │ TEXT      │ server/client│
└──────────────────────────────────────────────────┘
```

### connection_events Table

```
┌──────────────────────────────────────────────────┐
│ Column      │ Type      │ Description            │
├─────────────┼───────────┼────────────────────────┤
│ id          │ INTEGER   │ Primary key            │
│ timestamp   │ DATETIME  │ Date & time            │
│ event_type  │ TEXT      │ Event name             │
│ details     │ TEXT      │ Additional info        │
│ mode        │ TEXT      │ server/client          │
└──────────────────────────────────────────────────┘
```

## Message Protocol

### Message Format

```
┌─────────────────────────────────────┐
│ Header (8 bytes)                    │
├──────────────┬──────────────────────┤
│ Length (4)   │ Reserved (4)         │
├──────────────┴──────────────────────┤
│ JSON Payload                        │
│ {                                   │
│   "type": "TEST_DATA",              │
│   "timestamp": 1730825530.123,      │
│   "payload": {                      │
│     "sequence": 1234,               │
│     "size": 8192                    │
│   }                                 │
│ }                                   │
└─────────────────────────────────────┘
```

### Message Types

1. **HELLO** - Initial greeting
2. **HELLO_ACK** - Server acknowledges
3. **START_TEST** - Begin testing
4. **TEST_DATA** - Data packet
5. **TEST_RESULT** - Results report
6. **STOP_TEST** - End testing
7. **PING** - Latency check
8. **PONG** - Ping response
9. **ERROR** - Error message
10. **DISCONNECT** - Close connection

## Threading Model

### Server Threads

```
Main Thread (GUI)
    │
    ├─► Accept Thread
    │   └─► Waits for client connections
    │
    └─► Client Handler Thread
        └─► Processes client messages
```

### Client Threads

```
Main Thread (GUI)
    │
    ├─► Receive Thread
    │   └─► Receives server messages
    │
    └─► Test Thread
        └─► Sends test data
```

## File Locations

```
BridgeTestTool/
    │
    ├─ run.py              ← Start here
    ├─ bridge_test.db      ← Created on first run
    │
    └─ src/
        ├─ launcher.py     ← Entry point
        ├─ server.py       ← Server + GUI
        ├─ client.py       ← Client + GUI
        ├─ protocol.py     ← Network messages
        └─ database.py     ← SQLite operations
```

## Color Coding in Activity Log

- **Black** (info): General information
- **Green** (success): Successful operations
- **Orange** (warning): Warnings or disconnections
- **Red** (error): Errors and failures
- **Blue** (data): Data transfer events

---

**Architecture Version**: 1.0.0
**Last Updated**: November 5, 2025
