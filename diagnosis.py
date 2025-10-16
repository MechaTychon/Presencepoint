#!/usr/bin/env python3
"""
RFID Reader Diagnostic Tool
"""

import serial.tools.list_ports
import serial
import os
import subprocess
import time

def detect_serial_ports():
    print(" Scanning for serial devices...")
    print("=" * 50)

    # Method 1: List all serial ports using pyserial
    print("1. Serial ports found by pyserial:")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"    {port.device} - {port.description} - {port.hwid}")

    # Method 2: Check common serial device locations
    print("\n2. Checking common serial device locations:")
    common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyS0', '/dev/ttyS1']
    for port in common_ports:
        if os.path.exists(port):
            print(f"    Found: {port}")
        else:
            print(f"    Not found: {port}")

    # Method 3: List USB devices
    print("\n3. USB devices detected:")
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"    {line}")
    except:
        print("   Could not run lsusb")

    # Method 4: Check dmesg for recent USB connections
    print("\n4. Recent USB connections (dmesg):")
    try:
        result = subprocess.run(['dmesg | tail -20'], shell=True, capture_output=True, text=True)
        usb_lines = [line for line in result.stdout.split('\n') if 'usb' in line.lower() or 'tty' in line.lower()]
        for line in usb_lines[-10:]:  # Last 10 relevant lines
            print(f"   {line}")
    except:
        print("   Could not check dmesg")

def test_serial_connection(port_name, baudrate=9600):
    """Test connection to a specific serial port"""
    print(f"\n Testing connection to {port_name}...")
    try:
        with serial.Serial(port_name, baudrate, timeout=1) as ser:
            print(f"  Successfully opened {port_name}")

            # Try to read any available data
            print("    Listening for RFID data (scan a card now)...")
            for i in range(10):
                if ser.in_waiting > 0:
                    data = ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        print(f"    Received: {data}")
                time.sleep(0.5)

            return True
    except serial.SerialException as e:
        print(f"  Failed to open {port_name}: {e}")
        return False
    except PermissionError as e:
        print(f"   Permission denied for {port_name}: {e}")
        print("  Try: sudo chmod 666 {port_name} or add user to dialout group")
        return False

if __name__ == "__main__":
    detect_serial_ports()

    # Test all available ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        test_serial_connection(port.device)

    print("\n" + "=" * 50)
    print(" If no ports are found, make sure your RFID reader is:")
    print("   - Properly connected via USB")
    print("   - Powered on")
    print("   - Not being used by another program")
