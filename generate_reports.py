#!/usr/bin/env python3
"""
Generate presence reports from the database
"""

import sqlite3
import datetime
from student_presence_system import StudentDatabase

def generate_daily_report(date=None):
    """Generate daily presence report"""
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")

    db = StudentDatabase()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    # Get presence data for the specified date
    cursor.execute('''
        SELECT s.full_name, s.class_name, p.timestamp, p.action
        FROM presence_logs p
        JOIN students s ON p.rfid_id = s.rfid_id
        WHERE DATE(p.timestamp) = ?
        ORDER BY p.timestamp
    ''', (date,))

    records = cursor.fetchall()

    print(f"\n Daily Presence Report - {date}")
    print("=" * 60)

    if not records:
        print("No records found for this date.")
        return

    current_student = None
    for record in records:
        name, class_name, timestamp, action = record

        if name != current_student:
            print(f"\n {name} ({class_name})")
            current_student = name

        time_only = timestamp.split()[1]
        print(f"   {time_only} - {action}")

    conn.close()

def main():
    """Main report generation interface"""
    print(" Presence Report Generator")

    date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
    if not date:
        date = None

    generate_daily_report(date)

if __name__ == "__main__":
    main()
