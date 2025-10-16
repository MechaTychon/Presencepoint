#!/usr/bin/env python3
"""
Improved RFID Student Presence System with Auto-Detection
"""

import serial.tools.list_ports
import serial
import datetime
import sqlite3
import logging
import sys
import os
import time
import threading
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('presence_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ImprovedRFIDReader:
    def __init__(self):
        self.serial_conn = None
        self.callback = None
        self.monitoring = False

    def auto_detect_port(self) -> Optional[str]:
        """Automatically detect RFID reader port"""
        logging.info("Auto-detecting RFID reader...")

        common_ports = [
            '/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3',
            '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2',
            '/dev/ttyS0', '/dev/ttyS1', '/dev/ttyAMA0'
        ]

        # First check pyserial listed ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        logging.info(f"Available serial ports: {available_ports}")

        # Test all available ports
        test_ports = available_ports + common_ports

        for port in test_ports:
            if not os.path.exists(port):
                continue

            logging.info(f"Testing port: {port}")
            try:
                # Try to open the port
                ser = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Wait for connection to stabilize

                # Try to read any data (scan an RFID card during this time)
                logging.info(f"Please scan an RFID card on {port}...")
                for i in range(5):
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8', errors='ignore').strip()
                        if data and len(data) > 3:  # Valid data received
                            logging.info(f"✅ RFID data received on {port}: {data}")
                            ser.close()
                            return port
                    time.sleep(1)

                ser.close()

            except (serial.SerialException, PermissionError) as e:
                logging.debug(f"Could not open {port}: {e}")
                continue

        logging.error("❌ No RFID reader detected automatically")
        return None

    def connect(self, port: str = None, baudrate: int = 9600) -> bool:
        """Connect to RFID reader"""
        if port is None:
            port = self.auto_detect_port()
            if port is None:
                return False

        try:
            self.serial_conn = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )

            # Wait for connection to stabilize
            time.sleep(2)
            logging.info(f"✅ Connected to RFID reader on {port}")
            return True

        except serial.SerialException as e:
            logging.error(f"❌ Failed to connect to {port}: {e}")
            return False
        except PermissionError as e:
            logging.error(f"❌ Permission denied for {port}: {e}")
            logging.info("💡 Try: sudo usermod -a -G dialout $USER")
            logging.info("💡 Then logout and login again, or run with sudo")
            return False

    def read_rfid(self) -> Optional[str]:
        """Read RFID data with improved error handling"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return None

        try:
            # Read available data
            if self.serial_conn.in_waiting > 0:
                data = self.serial_conn.readline()

                # Try different encodings
                for encoding in ['utf-8', 'ascii', 'latin-1']:
                    try:
                        decoded_data = data.decode(encoding).strip()
                        # Clean the data - remove non-printable characters
                        clean_data = ''.join(c for c in decoded_data if c.isprintable())

                        if clean_data and len(clean_data) >= 4:  # Reasonable minimum length
                            logging.debug(f"RFID raw data: {clean_data}")
                            return clean_data.upper()
                    except UnicodeDecodeError:
                        continue

                # If text decoding fails, return hex representation
                hex_data = data.hex().upper()
                if hex_data:
                    logging.debug(f"RFID hex data: {hex_data}")
                    return f"HEX:{hex_data}"

        except Exception as e:
            logging.error(f"Error reading RFID: {e}")

        return None

    def start_monitoring(self, callback):
        """Start monitoring for RFID tags"""
        self.callback = callback
        self.monitoring = True

        def monitor():
            while self.monitoring:
                rfid_data = self.read_rfid()
                if rfid_data:
                    self.callback(rfid_data)
                time.sleep(0.1)  # Small delay to prevent CPU overload

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logging.info("RFID monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False

    def close(self):
        """Close serial connection"""
        self.stop_monitoring()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logging.info("RFID reader connection closed")

class StudentDatabase:
    # ... (keep the same database class as before)
    def __init__(self, db_path="students.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                rfid_id TEXT PRIMARY KEY,
                student_id TEXT UNIQUE,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # Presence logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presence_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('IN', 'OUT')),
                FOREIGN KEY (rfid_id) REFERENCES students (rfid_id)
            )
        ''')

        conn.commit()
        conn.close()
        logging.info("Database initialized")

    def add_student(self, rfid_id: str, student_id: str, full_name: str, class_name: str):
        """Add a new student to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO students (rfid_id, student_id, full_name, class_name)
                VALUES (?, ?, ?, ?)
            ''', (rfid_id, student_id, full_name, class_name))
            conn.commit()
            logging.info(f"Student added: {full_name} ({student_id})")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error adding student: {e}")
            return False
        finally:
            conn.close()

    def get_student(self, rfid_id: str) -> Optional[Dict]:
        """Get student information by RFID ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT rfid_id, student_id, full_name, class_name
            FROM students
            WHERE rfid_id = ? AND is_active = 1
        ''', (rfid_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'rfid_id': result[0],
                'student_id': result[1],
                'full_name': result[2],
                'class_name': result[3]
            }
        return None

    def log_presence(self, rfid_id: str, action: str):
        """Log student presence (IN/OUT)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO presence_logs (rfid_id, timestamp, action)
                VALUES (?, ?, ?)
            ''', (rfid_id, timestamp, action))
            conn.commit()
            logging.info(f"Presence logged: {rfid_id} - {action} at {timestamp}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error logging presence: {e}")
            return False
        finally:
            conn.close()

    def get_last_action(self, rfid_id: str) -> Optional[str]:
        """Get the last action for a student"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT action FROM presence_logs
            WHERE rfid_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (rfid_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

class ImprovedPresenceSystem:
    def __init__(self):
        self.db = StudentDatabase()
        self.rfid_reader = ImprovedRFIDReader()

    def setup(self) -> bool:
        """Setup the presence system with auto-detection"""
        print(" Setting up RFID Presence System...")

        # Try to connect to RFID reader
        if not self.rfid_reader.connect():
            print("\n Could not auto-detect RFID reader.")
            print("\n Manual setup options:")
            print("1. Check if RFID reader is connected and powered")
            print("2. Try different USB port")
            print("3. Install required drivers")
            print("4. Check permissions (user in dialout group)")
            return False

        # Start monitoring
        self.rfid_reader.start_monitoring(self.handle_rfid_scan)
        print(" Presence system setup complete")
        return True

    def handle_rfid_scan(self, rfid_data: str):
        """Handle RFID scan event"""
        logging.info(f"RFID scanned: {rfid_data}")

        # Get student information
        student = self.db.get_student(rfid_data)

        if not student:
            print(f"\n Unknown RFID card: {rfid_data}")
            print("   Use manage_students.py to add this card to a student")
            return

        # Determine action (IN/OUT)
        last_action = self.db.get_last_action(rfid_data)
        new_action = 'OUT' if last_action == 'IN' else 'IN'

        # Log presence
        self.db.log_presence(rfid_data, new_action)

        # Display information
        self.display_presence(student, new_action)

    def display_presence(self, student: Dict, action: str):
        """Display presence information"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n" + "="*50)
        print(" STUDENT PRESENCE SYSTEM")
        print("="*50)
        print(f" Name: {student['full_name']}")
        print(f" Class: {student['class_name']}")
        print(f" Student ID: {student['student_id']}")
        print(f" Time: {current_time}")
        print(f" Status: {'CHECKED IN ' if action == 'IN' else 'CHECKED OUT '}")
        print("="*50)

def fix_permissions():
    """Fix common permission issues"""
    print(" Fixing permissions...")
    try:
        # Add user to dialout group
        os.system('sudo usermod -a -G dialout $USER')
        print(" Added user to dialout group")
        print(" Please logout and login again for changes to take effect")
    except:
        print(" Could not fix permissions automatically")

def main():
    """Main application entry point"""
    print(" Improved RFID Student Presence System")
    print("=" * 50)

    # Check if database exists, if not initialize sample data
    if not os.path.exists("students.db"):
        print("Initializing database with sample data...")
        db = StudentDatabase()
        # Add sample students
        sample_students = [
            ("A1B2C3D4", "S001", "John Smith", "Computer Science 101"),
            ("E5F6G7H8", "S002", "Emma Johnson", "Mathematics 202"),
        ]
        for student in sample_students:
            db.add_student(*student)

    # Create and setup presence system
    system = ImprovedPresenceSystem()

    if not system.setup():
        print("\n Troubleshooting tips:")
        print("1. Make sure RFID reader is connected via USB")
        print("2. Check if the reader has power (LED lights)")
        print("3. Try running: python3 rfid_diagnostic.py")
        print("4. Check if you need to install drivers")
        return

    print("\n System ready! Scan RFID cards to log presence.")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n System shutdown requested. Goodbye!")
        system.rfid_reader.close()

if __name__ == "__main__":
    main()
