#!/usr/bin/env python3
"""
Local debugging script - separate from main production code
"""
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def test_skyward_ui():
    """Test Skyward UI changes with local Chrome"""
    print("🔍 Testing Skyward UI in non-headless mode")
    print("=" * 50)
    
    # Set up Chrome options for local debugging
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    # Don't run headless - we want to see the browser
    
    try:
        # Use webdriver-manager for local testing
        print("🔧 Setting up Chrome driver...")
        chromedriver_path = ChromeDriverManager().install()
        print(f"✅ Chromedriver ready: {chromedriver_path}")
        
        service = ChromeService(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🌐 Opening Skyward login page...")
        driver.get("https://skyward.aisd.net/")
        
        print("✅ Browser opened! Check the window to see Skyward UI changes.")
        print("🔍 Look for:")
        print("  • Login form layout changes")
        print("  • Navigation menu changes") 
        print("  • Gradebook button location")
        print("  • Any new elements or removed elements")
        
        input("\n⏸️  Press Enter when you're done inspecting the UI...")
        
        driver.quit()
        print("✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try running: pip install webdriver-manager")

if __name__ == "__main__":
    test_skyward_ui()
