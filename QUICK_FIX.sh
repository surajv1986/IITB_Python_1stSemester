#!/bin/bash
# Quick fix script for ChromeDriver issue on macOS

echo "=============================================="
echo "ChromeDriver Quick Fix for macOS"
echo "=============================================="
echo ""

# Check if homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed."
    echo ""
    echo "Please install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    exit 1
fi

echo "✓ Homebrew found"
echo ""

# Install chromedriver
echo "📦 Installing ChromeDriver via Homebrew..."
brew install chromedriver

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  ChromeDriver installation had issues."
    echo "    Trying to continue anyway..."
fi

echo ""
echo "🔓 Removing macOS quarantine from ChromeDriver..."

# Find chromedriver location
CHROMEDRIVER_PATH=$(which chromedriver)

if [ -z "$CHROMEDRIVER_PATH" ]; then
    echo "⚠️  Could not find chromedriver in PATH"
    echo "   Checking common locations..."
    
    if [ -f "/opt/homebrew/bin/chromedriver" ]; then
        CHROMEDRIVER_PATH="/opt/homebrew/bin/chromedriver"
    elif [ -f "/usr/local/bin/chromedriver" ]; then
        CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
    fi
fi

if [ -n "$CHROMEDRIVER_PATH" ]; then
    echo "Found ChromeDriver at: $CHROMEDRIVER_PATH"
    xattr -d com.apple.quarantine "$CHROMEDRIVER_PATH" 2>/dev/null
    echo "✓ Quarantine removed"
else
    echo "⚠️  ChromeDriver not found"
fi

echo ""
echo "🧹 Cleaning up old webdriver-manager cache..."
rm -rf ~/.wdm/drivers/chromedriver
echo "✓ Cache cleaned"

echo ""
echo "✅ Fix complete!"
echo ""
echo "=============================================="
echo "Test ChromeDriver:"
echo "  chromedriver --version"
echo ""
echo "Run the downloader:"
echo "  python3 espn_gallery_downloader_simple.py -n 5"
echo "=============================================="
echo ""

# Test chromedriver
if command -v chromedriver &> /dev/null; then
    echo "ChromeDriver version:"
    chromedriver --version
    echo ""
    echo "✅ All set! You can now run the script."
else
    echo "⚠️  ChromeDriver still not accessible in PATH"
    echo ""
    echo "Try adding to your PATH:"
    echo "  export PATH=\"/opt/homebrew/bin:\$PATH\""
fi

