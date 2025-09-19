#!/usr/bin/env python3
"""
Local debug script to test GPA calculator in non-headless mode
"""
import os
import sys
from utils.skyward import SkywardGPA

def progress_callback(message, progress):
    print(f"[{progress:3d}%] {message}")

def main():
    # Set environment variables for local debugging
    os.environ['HEADLESS'] = 'false'  # Run in non-headless mode
    os.environ['DISPLAY'] = ':0'     # Use local display (Linux/Mac)
    
    print("🔍 Running GPA Calculator in DEBUG MODE (non-headless)")
    print("=" * 60)
    
    # Get credentials from user
    username = input("Enter your Skyward username: ").strip()
    password = input("Enter your Skyward password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required!")
        return
    
    print(f"\n🚀 Starting calculation for user: {username}")
    print("📱 Chrome browser will open - you can watch the process!")
    print("⏳ This may take 30-60 seconds...")
    print("-" * 60)
    
    try:
        # Initialize calculator
        calculator = SkywardGPA(username, password, progress_callback)
        
        # Run calculation
        result = calculator.calculate()
        
        print("\n" + "=" * 60)
        print("✅ CALCULATION COMPLETE!")
        print("=" * 60)
        
        # Display results
        print(f"📊 Current Weighted GPA: {result['current_weighted_gpa']:.2f}")
        print(f"📊 Current Unweighted GPA: {result['current_unweighted_gpa']:.2f}")
        print(f"📈 Total Classes: {result['total_classes']}")
        print(f"📈 Classes with Grades: {result['classes_with_grades']}")
        
        print("\n📋 Class Details:")
        for class_name, grades in result['grades'].items():
            print(f"  • {class_name}: {grades}")
        
        print("\n📈 Period GPAs:")
        for period, gpa in result['weighted_gpas'].items():
            print(f"  • {period}: {gpa:.2f}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n🔍 Full error details:")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Debugging tips:")
        print("  • Check if Skyward website has changed")
        print("  • Verify your credentials are correct")
        print("  • Check if Chrome/chromedriver is working")
        print("  • Look at the browser window for visual clues")

if __name__ == "__main__":
    main()
