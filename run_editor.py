#!/usr/bin/env python3
"""
Simple launcher for the Fallout Shelter Save Editor
"""

import sys
import subprocess
import os

def check_requirements():
    """Check if required packages are installed."""
    required_packages = ['PyQt5', 'cryptography', 'pycryptodome']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_requirements():
    """Install missing requirements."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main launcher function."""
    print("Fallout Shelter Save Editor Launcher")
    print("=" * 40)
    
    # Check for missing packages
    missing = check_requirements()
    
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        
        if os.path.exists('requirements.txt'):
            response = input("Would you like to install them now? (y/n): ").lower().strip()
            if response == 'y':
                if install_requirements():
                    print("Packages installed successfully!")
                else:
                    print("Failed to install packages. Please install manually:")
                    print("pip install -r requirements.txt")
                    return
            else:
                print("Please install the required packages manually:")
                print("pip install -r requirements.txt")
                return
        else:
            print("requirements.txt not found. Please install manually:")
            print("pip install PyQt5 cryptography pycryptodome")
            return
    
    # Launch the editor
    print("Starting Fallout Shelter Save Editor...")
    try:
        from fallout_shelter_qt_editor import main as editor_main
        editor_main()
    except ImportError as e:
        print(f"Error importing editor: {e}")
        print("Make sure fallout_shelter_qt_editor.py is in the same directory.")
    except Exception as e:
        print(f"Error starting editor: {e}")

if __name__ == "__main__":
    main()