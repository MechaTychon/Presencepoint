#!/usr/bin/env python3
"""
Student Management Utility
Add, remove, or list students in the database
"""

import sqlite3
import sys
from student_presence_system import StudentDatabase

def add_student_interactive():
    """Interactive function to add a student"""
    print("\nAdd New Student")
    print("=" * 20)

    rfid_id = input("RFID ID: ").strip()
    student_id = input("Student ID: ").strip()
    full_name = input("Full Name: ").strip()
    class_name = input("Class: ").strip()

    db = StudentDatabase()
    if db.add_student(rfid_id, student_id, full_name, class_name):
        print("Student added successfully!")
    else:
        print("Failed to add student.")

def list_students():
    """List all students in the database"""
    db = StudentDatabase()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT rfid_id, student_id, full_name, class_name FROM students WHERE is_active = 1')
    students = cursor.fetchall()

    print("\nRegistered Students")
    print("=" * 60)
    print(f"{'RFID':<12} {'Student ID':<10} {'Name':<20} {'Class':<15}")
    print("-" * 60)

    for student in students:
        print(f"{student[0]:<12} {student[1]:<10} {student[2]:<20} {student[3]:<15}")

    conn.close()

def main():
    """Main management interface"""
    while True:
        print("\n Student Management System")
        print("1. Add Student")
        print("2. List Students")
        print("3. Exit")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            add_student_interactive()
        elif choice == "2":
            list_students()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
