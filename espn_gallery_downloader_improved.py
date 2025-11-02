#!/usr/bin/env python3
"""
ESPN Cricinfo Gallery Image Downloader (Improved version)
Downloads actual gallery images (not just header images) from ESPN Cricinfo albums
"""

import os
import time
import argparse
import requests
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
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
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--window-size=1920,1080')
        
        # Try to find ChromeDriver in common locations
        chromedriver_path = shutil.which('chromedriver')
        
        if chromedriver_path:
            print(f"Found ChromeDriver in PATH: {chromedriver_path}")
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            print("ChromeDriver not found in common locations, trying default...")
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
                    print(f"Found {len(elements)} potential album links...")
                    break
            except:
                continue
        
        seen_urls = set()
        
        for element in elements:
            try:
                url = element.get_attribute('href')
                if url and '/gallery/' in url and url not in seen_urls and url != self.gallery_url:
                    # Get album title
                    try:
                        title = element.get_attribute('title') or element.text or f"album_{len(album_links)+1}"
                        title = self.sanitize_filename(title)
                    except:
                        title = f"album_{len(album_links)+1}"
                    
                    album_links.append((url, title))
                    seen_urls.add(url)
                    
                    if len(album_links) >= self.num_albums:
                        break
            except:
                continue
        
        print(f"Found {len(album_links)} album links\n")
        return album_links[:self.num_albums]
    
    def scroll_page(self, times=5):
        """Scroll the page to load dynamic content"""
        print("Scrolling to load content...")
        for i in range(times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
    
    def get_images_from_album(self, album_url, album_title):
        """
        Navigate to an album and extract all gallery image URLs
        
        Args:
            album_url (str): URL of the album
            album_title (str): Title of the album
            
        Returns:
            list: List of image URLs
        """
        print(f"\n{'='*70}")
        print(f"Processing album: {album_title}")
        print(f"URL: {album_url}")
        print(f"{'='*70}")
        
        self.driver.get(album_url)
        time.sleep(4)
        
        # Scroll aggressively to load all images
        print("Loading all images...")
        self.scroll_page(times=10)
        
        image_urls = []
        seen_urls = set()
        
        # Strategy 1: Look for high-resolution images in picture/source tags
        print("Strategy 1: Looking for <picture> and <source> tags...")
        try:
            picture_elements = self.driver.find_elements(By.TAG_NAME, 'picture')
            for pic in picture_elements:
                try:
                    sources = pic.find_elements(By.TAG_NAME, 'source')
                    for source in sources:
                        srcset = source.get_attribute('srcset')
                        if srcset:
                            # Parse srcset and get the highest resolution
                            urls = self.parse_srcset(srcset)
                            for url in urls:
                                if self.is_gallery_image(url) and url not in seen_urls:
                                    image_urls.append(url)
                                    seen_urls.add(url)
                except:
                    continue
        except Exception as e:
            print(f"  Picture tag search: {e}")
        
        # Strategy 2: Look for img tags with specific patterns
        print("Strategy 2: Looking for <img> tags with gallery patterns...")
        try:
            img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
            print(f"  Found {len(img_elements)} total img tags")
            
            for img in img_elements:
                try:
                    # Try different attributes
                    for attr in ['src', 'data-src', 'data-lazy-src', 'srcset', 'data-srcset']:
                        img_url = img.get_attribute(attr)
                        if img_url:
                            if attr in ['srcset', 'data-srcset']:
                                urls = self.parse_srcset(img_url)
                            else:
                                urls = [img_url]
                            
                            for url in urls:
                                if self.is_gallery_image(url) and url not in seen_urls:
                                    image_urls.append(url)
                                    seen_urls.add(url)
                except:
                    continue
        except Exception as e:
            print(f"  Img tag search: {e}")
        
        # Strategy 3: Look for background images in style attributes
        print("Strategy 3: Looking for background images...")
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[@style]")
            for elem in all_elements:
                try:
                    style = elem.get_attribute('style')
                    if style and 'background-image' in style:
                        # Extract URL from background-image: url(...)
                        matches = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
                        for url in matches:
                            if self.is_gallery_image(url) and url not in seen_urls:
                                image_urls.append(url)
                                seen_urls.add(url)
                except:
                    continue
        except Exception as e:
            print(f"  Background image search: {e}")
        
        # Strategy 4: Try clicking through slideshow if present
        print("Strategy 4: Checking for slideshow navigation...")
        try:
            next_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(@class, 'next') or contains(@aria-label, 'next') or contains(@class, 'arrow')]")
            
            if next_buttons:
                print(f"  Found slideshow with navigation button")
                clicks = 0
                max_clicks = 50  # Prevent infinite loops
                
                while clicks < max_clicks:
                    try:
                        # Get current image
                        current_imgs = self.driver.find_elements(By.TAG_NAME, 'img')
                        for img in current_imgs:
                            for attr in ['src', 'srcset']:
                                img_url = img.get_attribute(attr)
                                if img_url:
                                    urls = self.parse_srcset(img_url) if attr == 'srcset' else [img_url]
                                    for url in urls:
                                        if self.is_gallery_image(url) and url not in seen_urls:
                                            image_urls.append(url)
                                            seen_urls.add(url)
                        
                        # Try to click next
                        next_button = self.driver.find_element(By.XPATH, 
                            "//button[contains(@class, 'next') or contains(@aria-label, 'next')]")
                        
                        if not next_button.is_enabled():
                            break
                        
                        next_button.click()
                        time.sleep(2)
                        clicks += 1
                        
                    except (NoSuchElementException, StaleElementReferenceException):
                        break
                    except Exception as e:
                        break
                
                print(f"  Clicked through {clicks} slides")
        except Exception as e:
            print(f"  Slideshow navigation: {e}")
        
        print(f"\n✓ Extracted {len(image_urls)} unique gallery images")
        return image_urls
    
    def parse_srcset(self, srcset):
        """Parse srcset attribute and return list of URLs"""
        urls = []
        if not srcset:
            return urls
        
        # Split by comma and extract URLs
        parts = srcset.split(',')
        for part in parts:
            # Extract URL (before any size descriptor like 1x, 2x, 100w, etc.)
            url = part.strip().split()[0]
            if url.startswith('http'):
                urls.append(url)
        
        return urls
    
    def is_gallery_image(self, url):
        """
        Check if URL is likely a gallery image (not logo/icon)
        
        Args:
            url (str): Image URL
            
        Returns:
            bool: True if likely a gallery image
        """
        if not url or not url.startswith('http'):
            return False
        
        # Exclude common non-gallery patterns
        exclude_patterns = [
            'logo',
            'icon',
            'favicon',
            'sprite',
            'placeholder',
            'avatar',
            'profile',
            'badge',
            '/ads/',
            '/ad/',
            'advertisement',
            'banner',
            'widget',
            'button',
            '/ui/',
            '/static/media',
            'f_auto',  # ESPN's auto-format placeholder that fails
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Include patterns that suggest gallery images
        include_patterns = [
            'img1.hscicdn.com',
            'p.imgci.com',
            'cricket',
            'image/upload',
            '/gallery/',
        ]
        
        # Must match at least one include pattern
        has_include = any(pattern in url_lower for pattern in include_patterns)
        
        # Check if URL has proper image extension or format
        has_image_format = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
        
        return has_include and (has_image_format or 'image/upload' in url_lower)
    
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
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.espncricinfo.com/'
            }
            response = requests.get(img_url, headers=headers, timeout=15, stream=True)
            
            if response.status_code == 200:
                # Check if it's actually an image (not HTML error page)
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Check file size - skip if too small (likely placeholder)
                    file_size = os.path.getsize(save_path)
                    if file_size < 5000:  # Less than 5KB
                        os.remove(save_path)
                        return False
                    
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
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
            print(f"⚠️  No gallery images found in album: {album_title}")
            return 0
        
        # Create album directory
        album_dir = os.path.join(self.output_dir, album_title)
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        
        # Download images
        print(f"\nDownloading {len(image_urls)} images...")
        print(f"Saving to: {album_dir}")
        print("-" * 70)
        
        successful_downloads = 0
        
        for idx, img_url in enumerate(image_urls, 1):
            # Get file extension from URL
            parsed_url = urlparse(img_url)
            path = parsed_url.path
            
            # Try to get extension from URL
            ext = os.path.splitext(path)[1]
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                # Default to jpg if no valid extension
                ext = '.jpg'
            
            filename = f"image_{idx:03d}{ext}"
            save_path = os.path.join(album_dir, filename)
            
            print(f"  [{idx}/{len(image_urls)}] {filename}...", end=' ')
            
            if self.download_image(img_url, save_path):
                file_size = os.path.getsize(save_path) / 1024  # KB
                print(f"✓ ({file_size:.1f} KB)")
                successful_downloads += 1
            else:
                print("✗")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.3)
        
        print("-" * 70)
        print(f"✓ Successfully downloaded {successful_downloads}/{len(image_urls)} images\n")
        return successful_downloads
    
    def sanitize_filename(self, filename):
        """Clean filename to be filesystem-safe"""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        filename = filename[:100]
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
                print("⚠️  No albums found! Please check the website structure.")
                return
            
            # Download images from each album
            total_images = 0
            print(f"\n{'='*70}")
            print(f"Starting download of {len(album_links)} albums")
            print(f"{'='*70}\n")
            
            for idx, (album_url, album_title) in enumerate(album_links, 1):
                print(f"\n[Album {idx}/{len(album_links)}]")
                try:
                    num_images = self.download_album_images(album_url, album_title)
                    total_images += num_images
                except Exception as e:
                    print(f"❌ Error processing album {album_title}: {str(e)}")
                    continue
            
            print(f"\n\n{'='*70}")
            print(f"✅ DOWNLOAD COMPLETE!")
            print(f"{'='*70}")
            print(f"Total albums processed: {len(album_links)}")
            print(f"Total images downloaded: {total_images}")
            print(f"Images saved to: {os.path.abspath(self.output_dir)}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Download gallery images from ESPN Cricinfo albums',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -n 5                     # Download from first 5 albums
  %(prog)s -n 10 -o my_images       # Download from 10 albums to custom folder
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
    
    print("="*70)
    print("ESPN Cricinfo Gallery Image Downloader (Improved)")
    print("="*70)
    print(f"Configuration:")
    print(f"  - Number of albums: {args.num_albums}")
    print(f"  - Output directory: {args.output_dir}")
    print("="*70)
    
    downloader = ESPNGalleryDownloader(
        num_albums=args.num_albums,
        output_dir=args.output_dir
    )
    
    downloader.run()


if __name__ == "__main__":
    main()

