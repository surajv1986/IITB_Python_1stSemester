#!/usr/bin/env python3
"""
Test script to verify ESPN Gallery Downloader setup
Run this to check if all dependencies are properly installed
"""

import sys

def test_python_version():
    """Check Python version"""
    print("Testing Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.7+)")
        return False

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    display_name = package_name or module_name
    print(f"Testing {display_name}...", end=" ")
    try:
        __import__(module_name)
        print("✓")
        return True
    except ImportError as e:
        print(f"✗ Not installed")
        return False

def test_selenium_driver():
    """Test if Selenium WebDriver can be initialized"""
    print("Testing Selenium WebDriver setup...", end=" ")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Try to setup ChromeDriver (but don't actually start browser)
        print("(Setting up ChromeDriver...)", end=" ")
        ChromeDriverManager().install()
        print("✓")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("ESPN Gallery Downloader - Setup Test")
    print("="*60)
    print()
    
    tests_passed = 0
    tests_total = 0
    
    # Test Python version
    tests_total += 1
    if test_python_version():
        tests_passed += 1
    
    print()
    print("Testing required dependencies...")
    print("-" * 60)
    
    # Test required packages
    required_packages = [
        ('selenium', 'Selenium'),
        ('requests', 'Requests'),
        ('webdriver_manager', 'WebDriver Manager'),
    ]
    
    for module, name in required_packages:
        tests_total += 1
        if test_import(module, name):
            tests_passed += 1
    
    print()
    print("Testing Selenium WebDriver...")
    print("-" * 60)
    
    # Test Selenium WebDriver setup
    tests_total += 1
    if test_selenium_driver():
        tests_passed += 1
    
    print()
    print("="*60)
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    print("="*60)
    
    if tests_passed == tests_total:
        print()
        print("✅ All tests passed! You're ready to run the downloader.")
        print()
        print("Quick start:")
        print("  python3 espn_gallery_downloader_auto.py -n 5")
        print()
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please install missing dependencies:")
        print()
        print("  pip3 install -r requirements.txt")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())

