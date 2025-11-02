#!/bin/bash
# Quick start script for ESPN Gallery Downloader

echo "================================================"
echo "ESPN Cricinfo Gallery Downloader - Quick Start"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "✓ Python3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "================================================"
echo "You can now run the downloader:"
echo ""
echo "  Default (10 albums):"
echo "    python3 espn_gallery_downloader_auto.py"
echo ""
echo "  Custom number of albums:"
echo "    python3 espn_gallery_downloader_auto.py -n 5"
echo ""
echo "  Custom output folder:"
echo "    python3 espn_gallery_downloader_auto.py -n 10 -o my_images"
echo ""
echo "================================================"
echo ""
echo "Run now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting downloader with default settings (10 albums)..."
    python3 espn_gallery_downloader_auto.py
fi

