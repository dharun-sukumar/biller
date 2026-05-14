#!/bin/bash

# Exit on error
set -e

echo "Starting build process for BillerPy..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH."
    exit 1
fi

# Function to activate virtual environment
activate_venv() {
    if [ -d ".venv" ]; then
        if [ -f ".venv/Scripts/activate" ]; then
            source .venv/Scripts/activate
        elif [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            echo "Warning: .venv found but activation script missing."
        fi
    else
        echo "Creating virtual environment..."
        python -m venv .venv
        if [ -f ".venv/Scripts/activate" ]; then
            source .venv/Scripts/activate
        elif [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        fi
    fi
}

activate_venv

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Building executable with PyInstaller..."
pyinstaller BillerPy.spec --clean --noconfirm

if [ -f "dist/BillerPy.exe" ]; then
    echo "----------------------------------------"
    echo "Build successful!"
    echo "Executable: dist/BillerPy.exe"
    echo "----------------------------------------"
else
    echo "Error: Build failed. Executable not found."
    exit 1
fi
