# ESPN Gallery Downloader - Complete Usage Guide

## Quick Start (Recommended)

### Step 1: Install Dependencies
```bash
pip3 install -r requirements.txt
```

### Step 2: Run the Downloader
```bash
# Use the auto version (automatically manages ChromeDriver)
python3 espn_gallery_downloader_auto.py -n 10
```

Or use the quick start script:
```bash
./quick_start.sh
```

## Script Versions

### 1. `espn_gallery_downloader_auto.py` (Recommended)
- **Automatically installs and manages ChromeDriver**
- No manual ChromeDriver setup needed
- Best for first-time users

```bash
python3 espn_gallery_downloader_auto.py -n 10
```

### 2. `espn_gallery_downloader.py` (Standard)
- Requires ChromeDriver to be installed manually
- More control over ChromeDriver version
- Use if you already have ChromeDriver set up

```bash
python3 espn_gallery_downloader.py -n 10
```

## Command-Line Options

### `-n, --num-albums` (Number of Albums)
Specify how many albums to download from the gallery.

```bash
# Download first 5 albums
python3 espn_gallery_downloader_auto.py -n 5

# Download first 20 albums
python3 espn_gallery_downloader_auto.py -n 20

# Download first 50 albums
python3 espn_gallery_downloader_auto.py -n 50
```

### `-o, --output-dir` (Output Directory)
Specify where to save the downloaded images.

```bash
# Save to custom folder
python3 espn_gallery_downloader_auto.py -n 10 -o cricket_gallery

# Save to nested folder
python3 espn_gallery_downloader_auto.py -n 10 -o downloads/espn_images

# Save to absolute path
python3 espn_gallery_downloader_auto.py -n 10 -o /Users/username/Pictures/cricket
```

## Examples

### Example 1: Basic Download (Default Settings)
```bash
python3 espn_gallery_downloader_auto.py
```
- Downloads: First 10 albums
- Output: `espn_images/` folder in current directory

### Example 2: Download 5 Albums to Custom Folder
```bash
python3 espn_gallery_downloader_auto.py -n 5 -o my_cricket_pics
```
- Downloads: First 5 albums
- Output: `my_cricket_pics/` folder

### Example 3: Large Download
```bash
python3 espn_gallery_downloader_auto.py -n 30 -o cricket_archive_2024
```
- Downloads: First 30 albums
- Output: `cricket_archive_2024/` folder

### Example 4: Get Help
```bash
python3 espn_gallery_downloader_auto.py --help
```

## Understanding the Output

### Folder Structure
```
espn_images/
├── album_1_title/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   ├── image_003.jpg
│   └── ...
├── album_2_title/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
└── album_3_title/
    ├── image_001.jpg
    └── ...
```

### Console Output Explained
```
=============================================================
ESPN Cricinfo Gallery Image Downloader
=============================================================
Configuration:
  - Number of albums: 10          # How many albums you requested
  - Output directory: espn_images # Where images will be saved
=============================================================
Setting up Chrome WebDriver...
(This may download ChromeDriver on first run)  # First run only
WebDriver setup complete!

Navigating to https://www.espncricinfo.com/gallery...
Scrolling to load content...
Found 50 potential album links...  # Total links found on page
Found 10 album links               # Filtered to your requested amount

[Album 1/10]                       # Current album being processed
=============================================================
Processing album: IPL_2024_Finals
URL: https://www.espncricinfo.com/gallery/...
=============================================================
Found 25 img tags in the album     # Total <img> tags found
Extracted 15 unique image URLs     # After filtering duplicates

Downloading 15 images to espn_images/IPL_2024_Finals...
  [1/15] Downloading image_001.jpg... ✓   # ✓ = success
  [2/15] Downloading image_002.jpg... ✓   # ✗ = failed
  ...

Successfully downloaded 15/15 images

[Album 2/10]
...

=============================================================
Download complete!
Total albums processed: 10
Total images downloaded: 156        # Total across all albums
Images saved to: /full/path/to/espn_images
=============================================================
```

## Advanced Usage

### Running in Headless Mode (No Browser Window)
Edit the script and uncomment this line in the `setup_driver()` method:
```python
options.add_argument('--headless')
```

### Adjusting Download Delays
If you're experiencing rate limiting, increase the delay in the `download_album_images()` method:
```python
time.sleep(1.0)  # Change from 0.5 to 1.0 seconds
```

### Filtering Images
Modify the `get_images_from_album()` method to add custom filters:
```python
# Example: Only download large images
if 'w=1200' in img_url or 'large' in img_url:
    image_urls.append(img_url)
```

## Troubleshooting

### Problem: "No albums found!"
**Solutions:**
1. Check your internet connection
2. Verify the gallery URL is accessible: https://www.espncricinfo.com/gallery
3. The website structure may have changed - inspect the page source
4. Try running without headless mode to see what's happening

### Problem: "ChromeDriver not found"
**Solutions:**
1. Use `espn_gallery_downloader_auto.py` instead (auto-manages ChromeDriver)
2. Or manually install ChromeDriver:
   ```bash
   brew install chromedriver  # macOS
   # or download from: https://chromedriver.chromium.org/
   ```

### Problem: Images failing to download
**Solutions:**
1. Check internet connection stability
2. Increase delays between downloads (edit the script)
3. Some images may be protected - this is expected
4. Try downloading fewer albums at a time

### Problem: "Chrome is being controlled by automated test software"
This is normal and expected. The script is working correctly.

### Problem: Rate limiting or blocked requests
**Solutions:**
1. Reduce the number of albums: `-n 5` instead of `-n 20`
2. Increase delays in the script
3. Run downloads at different times
4. Use a VPN if blocked by region

## Performance Tips

### For Faster Downloads
- Use a stable, fast internet connection
- Download during off-peak hours
- Close other bandwidth-intensive applications

### For Large Downloads
- Use smaller batches: Download 10 albums at a time
- Monitor disk space
- Consider using external storage for large archives

### To Minimize Resource Usage
- Enable headless mode (no browser window)
- Close other applications
- Download sequentially rather than all at once

## File Management

### Finding Downloaded Images
```bash
# List all downloaded albums
ls -la espn_images/

# Count total images
find espn_images/ -name "*.jpg" | wc -l

# Check folder sizes
du -sh espn_images/*
```

### Organizing Downloads
```bash
# Rename output folder
mv espn_images cricket_gallery_nov_2024

# Archive downloads
tar -czf cricket_images.tar.gz espn_images/

# Copy to backup location
cp -r espn_images ~/Backups/
```

## Best Practices

1. **Start Small**: Test with `-n 2` or `-n 3` first
2. **Monitor Progress**: Watch the console output
3. **Check Results**: Verify images after download
4. **Respect the Server**: Don't download excessively
5. **Backup**: Keep copies of important downloads
6. **Clean Up**: Remove unnecessary files periodically

## Legal & Ethical Considerations

- **Respect Terms of Service**: Use in accordance with ESPN's ToS
- **Personal Use**: Intended for personal, educational use
- **Attribution**: Credit ESPN Cricinfo when sharing images
- **Rate Limiting**: Script includes delays to be respectful
- **No Redistribution**: Don't republish copyrighted content

## Getting Help

### View All Options
```bash
python3 espn_gallery_downloader_auto.py --help
```

### Check Python Version
```bash
python3 --version  # Should be 3.7 or higher
```

### Verify Dependencies
```bash
pip3 list | grep selenium
pip3 list | grep requests
pip3 list | grep webdriver-manager
```

### Test Installation
```bash
# Quick test with just 1 album
python3 espn_gallery_downloader_auto.py -n 1 -o test_download
```

## Customization Ideas

### 1. Filter by Date
Modify the script to only download albums from specific time periods.

### 2. Image Quality Selection
Choose between different image qualities if available.

### 3. Metadata Storage
Save album titles, dates, and descriptions in a JSON file.

### 4. Progress Bar
Add tqdm library for fancy progress bars.

### 5. Resume Capability
Implement checkpoint system to resume interrupted downloads.

## Additional Resources

- **Selenium Documentation**: https://selenium-python.readthedocs.io/
- **ChromeDriver Downloads**: https://chromedriver.chromium.org/
- **Python Requests**: https://requests.readthedocs.io/

## Support

For issues or questions:
1. Check this guide first
2. Review the README.md
3. Check the script's help: `--help`
4. Verify your Python and dependencies are up to date

---

**Happy downloading! 🏏📸**

