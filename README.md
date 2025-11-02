# ESPN Cricinfo Gallery Image Downloader

A Python script that automates downloading images from ESPN Cricinfo gallery albums using Selenium WebDriver.

## Features

- 🖼️ Downloads images from multiple gallery albums
- 📁 Organizes images into separate folders by album
- 🔢 Customizable number of albums to download
- 🚀 Automatic scrolling to load dynamic content
- 🛡️ Error handling and retry logic
- 📊 Progress tracking and statistics

## Prerequisites

- Python 3.7 or higher
- Google Chrome browser installed
- ChromeDriver (will be automatically managed by webdriver-manager)

## Installation

1. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

2. **Verify Chrome is installed:**
   - The script uses Chrome WebDriver, so ensure Google Chrome is installed on your system.

## Usage

### Basic Usage

Download images from the first 10 albums (default):

```bash
python espn_gallery_downloader.py
```

### Custom Number of Albums

Download images from the first 5 albums:

```bash
python espn_gallery_downloader.py -n 5
```

Download images from the first 20 albums:

```bash
python espn_gallery_downloader.py -n 20
```

### Custom Output Directory

Download images to a custom folder:

```bash
python espn_gallery_downloader.py -n 10 -o my_cricket_images
```

### Combined Options

```bash
python espn_gallery_downloader.py -n 15 -o downloads/cricket_gallery
```

## Command-Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--num-albums` | `-n` | Number of albums to download | 10 |
| `--output-dir` | `-o` | Output directory for images | espn_images |

## How It Works

1. **Navigation**: The script navigates to `https://www.espncricinfo.com/gallery`
2. **Album Discovery**: Finds album links on the gallery page
3. **Image Extraction**: For each album, it:
   - Opens the album page
   - Scrolls to load all images
   - Extracts all `<img>` tag URLs
4. **Download**: Downloads each image to a folder named after the album
5. **Organization**: Creates a clean folder structure:
   ```
   espn_images/
   ├── album_1/
   │   ├── image_001.jpg
   │   ├── image_002.jpg
   │   └── ...
   ├── album_2/
   │   ├── image_001.jpg
   │   └── ...
   └── ...
   ```

## Output

The script will display:
- Progress for each album being processed
- Number of images found and downloaded
- Success/failure status for each image
- Final statistics (total albums, total images)

Example output:
```
=============================================================
ESPN Cricinfo Gallery Image Downloader
=============================================================
Configuration:
  - Number of albums: 10
  - Output directory: espn_images
=============================================================
Setting up Chrome WebDriver...
WebDriver setup complete!

Navigating to https://www.espncricinfo.com/gallery...
Found 50 potential album links
Found 10 album links

[Album 1/10]
=============================================================
Processing album: IPL_2024_Finals
URL: https://www.espncricinfo.com/gallery/...
=============================================================
Found 25 img tags in the album
Extracted 15 unique image URLs

Downloading 15 images to espn_images/IPL_2024_Finals...
  [1/15] Downloading image_001.jpg... ✓
  ...
```

## Troubleshooting

### ChromeDriver Issues

If you encounter ChromeDriver errors:

```bash
# Install webdriver-manager to auto-manage ChromeDriver
pip install webdriver-manager
```

Or manually download ChromeDriver from: https://chromedriver.chromium.org/

### No Albums Found

If the script doesn't find any albums:
1. The website structure may have changed
2. Check your internet connection
3. Try running without headless mode to see what's happening

### Rate Limiting

If downloads are failing:
- The script includes delays between downloads
- You can increase delays in the code if needed
- Consider running in smaller batches

## Customization

You can modify the script to:
- Run in headless mode (uncomment the headless option in `setup_driver()`)
- Adjust scroll behavior
- Change image filtering logic
- Add more sophisticated error handling

## Notes

- The script respects the website's structure and includes delays to avoid overwhelming the server
- Images are downloaded in their original quality
- Album titles are sanitized to create valid folder names
- Duplicate images are automatically filtered out

## License

This script is provided for educational purposes. Please respect ESPN Cricinfo's terms of service and use responsibly.

