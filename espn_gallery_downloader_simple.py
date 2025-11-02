#!/usr/bin/env python3
"""
ESPN Cricinfo Gallery Image Downloader (Simple version)
Downloads images from multiple gallery albums on ESPN Cricinfo
This version tries system ChromeDriver first (simpler and more reliable)
"""

import os
import time
import argparse
import requests
import subprocess
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse
import re


class ESPNGalleryDownloader:
    def __init__(self, num_albums=10, output_dir="espn_images"):
        """
        Initialize the downloader
        
        Args:
            num_albums (int): Number of albums to download
            output_dir (str): Directory to save downloaded images
        """
        self.num_albums = num_albums
        self.output_dir = output_dir
        self.gallery_url = "https://www.espncricinfo.com/gallery"
        self.driver = None
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
    
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        print("Setting up Chrome WebDriver...")
        
        options = webdriver.ChromeOptions()
        # Uncomment the next line if you want to run headless (no browser window)
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Try to find ChromeDriver in common locations
        chromedriver_path = None
        
        # Check if chromedriver is in PATH
        chromedriver_path = shutil.which('chromedriver')
        
        if chromedriver_path:
            print(f"Found ChromeDriver in PATH: {chromedriver_path}")
        else:
            # Try common homebrew locations for macOS
            possible_paths = [
                '/usr/local/bin/chromedriver',
                '/opt/homebrew/bin/chromedriver',
                '/usr/bin/chromedriver',
            ]
            
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    print(f"Found ChromeDriver at: {chromedriver_path}")
                    break
        
        if chromedriver_path:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            # Fall back to letting Selenium find it automatically
            print("ChromeDriver not found in common locations, trying default...")
            print("If this fails, install ChromeDriver with: brew install chromedriver")
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.maximize_window()
        print("WebDriver setup complete!")
    
    def get_album_links(self):
        """
        Navigate to gallery page and extract album links
        
        Returns:
            list: List of tuples containing (album_url, album_title)
        """
        print(f"\nNavigating to {self.gallery_url}...")
        self.driver.get(self.gallery_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Try to handle any cookie consent or popups
        try:
            # Common selectors for cookie/consent buttons
            consent_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Accept') or contains(text(), 'agree') or contains(text(), 'OK')]")
            if consent_buttons:
                consent_buttons[0].click()
                time.sleep(1)
        except:
            pass
        
        # Scroll to load more content
        self.scroll_page()
        
        album_links = []
        
        # Try multiple selectors to find album links
        selectors = [
            "//a[contains(@href, '/gallery/')]",
            "//article//a",
            "//div[contains(@class, 'gallery')]//a",
            "//div[contains(@class, 'card')]//a",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found {len(elements)} potential album links using selector: {selector[:50]}...")
                    break
            except:
                continue
        
        seen_urls = set()
        
        for element in elements:
            try:
                url = element.get_attribute('href')
                if url and '/gallery/' in url and url not in seen_urls:
                    # Get album title
                    try:
                        title = element.get_attribute('title') or element.text or f"album_{len(album_links)+1}"
                        # Clean title for use as folder name
                        title = self.sanitize_filename(title)
                    except:
                        title = f"album_{len(album_links)+1}"
                    
                    album_links.append((url, title))
                    seen_urls.add(url)
                    
                    if len(album_links) >= self.num_albums:
                        break
            except:
                continue
        
        print(f"\nFound {len(album_links)} album links")
        return album_links[:self.num_albums]
    
    def scroll_page(self):
        """Scroll the page to load dynamic content"""
        print("Scrolling to load content...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def get_images_from_album(self, album_url, album_title):
        """
        Navigate to an album and extract all image URLs
        
        Args:
            album_url (str): URL of the album
            album_title (str): Title of the album
            
        Returns:
            list: List of image URLs
        """
        print(f"\n{'='*60}")
        print(f"Processing album: {album_title}")
        print(f"URL: {album_url}")
        print(f"{'='*60}")
        
        self.driver.get(album_url)
        time.sleep(3)
        
        # Scroll to load all images
        self.scroll_page()
        
        # Find all img tags
        img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
        print(f"Found {len(img_elements)} img tags in the album")
        
        image_urls = []
        seen_urls = set()
        
        for img in img_elements:
            try:
                # Try different attributes where image URL might be stored
                img_url = None
                for attr in ['src', 'data-src', 'data-lazy-src', 'srcset']:
                    img_url = img.get_attribute(attr)
                    if img_url:
                        # If srcset, take the first URL
                        if 'http' in img_url:
                            img_url = img_url.split(',')[0].split(' ')[0]
                            break
                
                if img_url and img_url.startswith('http'):
                    # Filter out small images (like icons, logos)
                    # ESPN images typically have certain patterns
                    if any(keyword in img_url.lower() for keyword in ['espn', 'static', 'img']):
                        # Avoid duplicates
                        if img_url not in seen_urls:
                            image_urls.append(img_url)
                            seen_urls.add(img_url)
            except Exception as e:
                continue
        
        print(f"Extracted {len(image_urls)} unique image URLs")
        return image_urls
    
    def download_image(self, img_url, save_path):
        """
        Download a single image
        
        Args:
            img_url (str): URL of the image
            save_path (str): Path to save the image
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(img_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"  Failed to download (status {response.status_code}): {img_url}")
                return False
        except Exception as e:
            print(f"  Error downloading {img_url}: {str(e)}")
            return False
    
    def download_album_images(self, album_url, album_title):
        """
        Download all images from an album
        
        Args:
            album_url (str): URL of the album
            album_title (str): Title of the album
            
        Returns:
            int: Number of successfully downloaded images
        """
        # Get image URLs
        image_urls = self.get_images_from_album(album_url, album_title)
        
        if not image_urls:
            print(f"No images found in album: {album_title}")
            return 0
        
        # Create album directory
        album_dir = os.path.join(self.output_dir, album_title)
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        
        # Download images
        print(f"\nDownloading {len(image_urls)} images to {album_dir}...")
        successful_downloads = 0
        
        for idx, img_url in enumerate(image_urls, 1):
            # Get file extension from URL
            parsed_url = urlparse(img_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            filename = f"image_{idx:03d}{ext}"
            save_path = os.path.join(album_dir, filename)
            
            print(f"  [{idx}/{len(image_urls)}] Downloading {filename}...", end=' ')
            
            if self.download_image(img_url, save_path):
                print("✓")
                successful_downloads += 1
            else:
                print("✗")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        print(f"\nSuccessfully downloaded {successful_downloads}/{len(image_urls)} images")
        return successful_downloads
    
    def sanitize_filename(self, filename):
        """
        Clean filename to be filesystem-safe
        
        Args:
            filename (str): Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces and special chars with underscores
        filename = re.sub(r'[\s]+', '_', filename)
        # Limit length
        filename = filename[:100]
        # Remove leading/trailing underscores and dots
        filename = filename.strip('._')
        
        return filename if filename else "unnamed_album"
    
    def run(self):
        """Main execution method"""
        try:
            # Setup driver
            self.setup_driver()
            
            # Get album links
            album_links = self.get_album_links()
            
            if not album_links:
                print("No albums found! Please check the website structure.")
                return
            
            # Download images from each album
            total_images = 0
            print(f"\n\nStarting download of {len(album_links)} albums...\n")
            
            for idx, (album_url, album_title) in enumerate(album_links, 1):
                print(f"\n\n[Album {idx}/{len(album_links)}]")
                try:
                    num_images = self.download_album_images(album_url, album_title)
                    total_images += num_images
                except Exception as e:
                    print(f"Error processing album {album_title}: {str(e)}")
                    continue
            
            print(f"\n\n{'='*60}")
            print(f"Download complete!")
            print(f"Total albums processed: {len(album_links)}")
            print(f"Total images downloaded: {total_images}")
            print(f"Images saved to: {os.path.abspath(self.output_dir)}")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                print("\nClosing browser...")
                self.driver.quit()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Download images from ESPN Cricinfo gallery albums',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Download from first 10 albums (default)
  %(prog)s -n 5                     # Download from first 5 albums
  %(prog)s -n 20 -o my_images       # Download from first 20 albums to 'my_images' folder

Note: This version requires ChromeDriver to be installed.
  macOS: brew install chromedriver
  Linux: sudo apt-get install chromium-chromedriver
  Windows: Download from https://chromedriver.chromium.org/
        """
    )
    
    parser.add_argument(
        '-n', '--num-albums',
        type=int,
        default=10,
        help='Number of albums to download (default: 10)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='espn_images',
        help='Output directory for downloaded images (default: espn_images)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("ESPN Cricinfo Gallery Image Downloader")
    print("="*60)
    print(f"Configuration:")
    print(f"  - Number of albums: {args.num_albums}")
    print(f"  - Output directory: {args.output_dir}")
    print("="*60)
    
    downloader = ESPNGalleryDownloader(
        num_albums=args.num_albums,
        output_dir=args.output_dir
    )
    
    downloader.run()


if __name__ == "__main__":
    main()

