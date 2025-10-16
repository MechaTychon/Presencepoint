#!/bin/bash

echo "Installing RFID Student Presence System..."

# Update package list
sudo apt update

# Install Python3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies for serial communication
sudo apt install -y python3-serial

# Create virtual environment
python3 -m venv presence_env
source presence_env/bin/activate

# Install Python dependencies
pip install pyserial

# Make main script executable
chmod +x presence_system.py

echo "Installation complete!"
echo "To start the system:"
echo "  source presence_env/bin/activate"
echo "  python3 presence_system.py"
