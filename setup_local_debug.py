#!/usr/bin/env python3
"""
Setup script for local debugging
"""
import os
import platform
import subprocess
import sys

def check_chrome():
    """Check if Chrome is installed"""
    try:
        if platform.system() == "Windows":
            # Check for Chrome on Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    print(f"✅ Chrome found at: {path}")
                    return True
        else:
            # Check for Chrome on Mac/Linux
            result = subprocess.run(['which', 'google-chrome'], capture_output=True)
            if result.returncode == 0:
                print(f"✅ Chrome found at: {result.stdout.decode().strip()}")
                return True
            
            result = subprocess.run(['which', 'chromium-browser'], capture_output=True)
            if result.returncode == 0:
                print(f"✅ Chromium found at: {result.stdout.decode().strip()}")
                return True
                
        print("❌ Chrome/Chromium not found!")
        return False
    except Exception as e:
        print(f"❌ Error checking Chrome: {e}")
        return False

def check_chromedriver():
    """Check if chromedriver is available"""
    try:
        result = subprocess.run(['chromedriver', '--version'], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Chromedriver found: {result.stdout.decode().strip()}")
            return True
        else:
            print("❌ Chromedriver not found!")
            return False
    except FileNotFoundError:
        print("❌ Chromedriver not found!")
        return False
    except Exception as e:
        print(f"❌ Error checking chromedriver: {e}")
        return False

def install_chromedriver():
    """Try to install chromedriver using webdriver-manager"""
    try:
        print("🔧 Attempting to install chromedriver...")
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        print(f"✅ Chromedriver installed at: {driver_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to install chromedriver: {e}")
        return False

def main():
    print("🔍 Local Debug Setup Check")
    print("=" * 40)
    
    # Check Chrome
    chrome_ok = check_chrome()
    
    # Check chromedriver
    chromedriver_ok = check_chromedriver()
    
    if not chromedriver_ok:
        print("\n🔧 Trying to install chromedriver...")
        chromedriver_ok = install_chromedriver()
    
    print("\n" + "=" * 40)
    if chrome_ok and chromedriver_ok:
        print("✅ Setup complete! You can run: python test_local_debug.py")
    else:
        print("❌ Setup incomplete. Please install missing components:")
        if not chrome_ok:
            print("  • Install Google Chrome")
        if not chromedriver_ok:
            print("  • Install chromedriver or run: pip install webdriver-manager")

if __name__ == "__main__":
    main()
