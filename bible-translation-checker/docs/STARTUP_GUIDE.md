# Bible Correction System - Startup Guide

## 🚀 How to Launch the System

### **Option 1: Main System (Recommended)**
```bash
python3 bible_correction_system.py
```
This launches the complete system with GUI interface.

### **Option 2: Simple Launcher**
```bash
python3 launch_gui.py
```
Alternative launcher with error checking.

### **Option 3: Command Line Interface**
```bash
python3 bible_cli.py --help
```
For command-line operations without GUI.

## ❌ **Common Issues & Solutions**

### **"No GUI appears"**
- Make sure you're running from the correct directory
- Check that both `bible_correction_system.py` and `bible_correction_gui.py` are present
- Verify tkinter is installed: `python3 -c "import tkinter; print('✅ tkinter available')"`

### **"Import errors"**
```bash
# Check required files exist:
ls -la bible_correction_system.py bible_correction_gui.py bible_cli.py
```

### **"Database errors"**
- The system auto-creates `bible_correction.db` in the current directory
- If corrupted, delete the `.db` file and restart

## 🎯 **First Time Setup**

### **1. Launch System**
```bash
python3 bible_correction_system.py
```

### **2. Import Your Data**
- **GUI**: File → Import JSON Files...
- **CLI**: `python3 bible_cli.py import KJV.json`

### **3. Scan for Errors**
- **GUI**: Tools → Scan for Errors...
- **CLI**: `python3 bible_cli.py scan KJV`

### **4. View Results**
- **GUI**: Dashboard tab shows statistics
- **CLI**: `python3 bible_cli.py stats`

## 📱 **System Architecture**

```
bible_correction_system.py  ← Main application (run this)
bible_correction_gui.py     ← GUI components (imported by main)
bible_cli.py                ← Command line interface
bible_correction.db         ← SQLite database (auto-created)
```

## ✅ **Verification**

To verify everything is working:

```bash
# Test CLI
python3 bible_cli.py stats

# Test main system
python3 bible_correction_system.py
# (GUI should appear)
```

## 🔧 **Development Mode**

If you need to modify the code:

```bash
# Edit main system
nano bible_correction_system.py

# Edit GUI components
nano bible_correction_gui.py

# Test changes
python3 bible_correction_system.py
```

The system consists of:
- **📊 Dashboard**: Error statistics with color-coded buttons
- **✏️ Editor**: Text correction interface with verse navigation  
- **⚠️ Errors**: Error management and resolution tracking
- **📚 Translations**: Import/export and translation management

Your database is stored as `bible_correction.db` and contains all imported Bible texts, corrections, and error tracking data.