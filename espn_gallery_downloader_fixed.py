#!/usr/bin/env python3
"""
ESPN Cricinfo Gallery Image Downloader (Fixed version)
Downloads actual gallery images from ESPN Cricinfo albums
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse, urljoin
import re


class ESPNGalleryDownloader:
    def __init__(self, num_albums=10, output_dir="espn_images"):
        self.num_albums = num_albums
        self.output_dir = output_dir
        self.gallery_url = "https://www.espncricinfo.com/gallery"
        self.driver = None
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
    
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        print("Setting up Chrome WebDriver...")
        
        options = webdriver.ChromeOptions()
        # Uncomment for headless mode
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--window-size=1920,1080')
        
        chromedriver_path = shutil.which('chromedriver')
        
        if chromedriver_path:
            print(f"Found ChromeDriver: {chromedriver_path}")
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.maximize_window()
        print("WebDriver setup complete!\n")
    
    def get_album_links(self):
        """Navigate to gallery page and extract album links"""
        print(f"Navigating to {self.gallery_url}...")
        self.driver.get(self.gallery_url)
        time.sleep(3)
        
        # Handle cookie consent
        try:
            consent_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Accept') or contains(text(), 'agree')]")
            if consent_buttons:
                consent_buttons[0].click()
                time.sleep(1)
        except:
            pass
        
        # Scroll to load more albums
        self.scroll_page(times=3)
        
        album_links = []
        selectors = [
            "//a[contains(@href, '/gallery/') and not(contains(@href, '/gallery?'))]",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found {len(elements)} potential album links")
                    break
            except:
                continue
        
        seen_urls = set()
        
        for element in elements:
            try:
                url = element.get_attribute('href')
                if url and '/gallery/' in url and url not in seen_urls and url != self.gallery_url:
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
        
        print(f"Selected {len(album_links)} albums for download\n")
        return album_links[:self.num_albums]
    
    def scroll_page(self, times=5):
        """Scroll the page to load dynamic content"""
        for i in range(times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
    
    def get_images_from_album(self, album_url, album_title):
        """
        Navigate to an album and extract all gallery image URLs
        Uses multiple strategies to find actual gallery photos
        """
        print(f"\n{'='*70}")
        print(f"Album: {album_title}")
        print(f"URL: {album_url}")
        print(f"{'='*70}")
        
        self.driver.get(album_url)
        time.sleep(4)
        
        # Scroll extensively to ensure all images load
        print("Loading page content...")
        self.scroll_page(times=8)
        time.sleep(2)
        
        image_urls = []
        seen_urls = set()
        
        # Debug: Print page title and URL to confirm we're on the right page
        page_title = self.driver.title
        print(f"Page title: {page_title}")
        
        # Strategy 1: Get all img tags and analyze them
        print("\nAnalyzing all <img> tags...")
        img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
        print(f"Found {len(img_elements)} total <img> tags")
        
        # Collect ALL possible image URLs for debugging
        all_urls = []
        
        for img in img_elements:
            try:
                # Check multiple attributes
                for attr in ['src', 'data-src', 'srcset', 'data-srcset']:
                    value = img.get_attribute(attr)
                    if value:
                        if 'srcset' in attr:
                            # Parse srcset
                            parts = value.split(',')
                            for part in parts:
                                url = part.strip().split()[0]
                                if url.startswith('http'):
                                    all_urls.append((url, attr))
                        elif value.startswith('http'):
                            all_urls.append((value, attr))
            except:
                continue
        
        print(f"Found {len(all_urls)} total image URLs")
        
        # Filter for actual gallery images
        for url, source in all_urls:
            if self.is_gallery_image(url) and url not in seen_urls:
                image_urls.append(url)
                seen_urls.add(url)
        
        print(f"After filtering: {len(image_urls)} gallery images")
        
        # If we still don't have images, be less strict
        if len(image_urls) < 5:
            print("\nTrying less strict filtering...")
            for url, source in all_urls:
                if self.is_likely_photo(url) and url not in seen_urls:
                    image_urls.append(url)
                    seen_urls.add(url)
            print(f"After relaxed filtering: {len(image_urls)} images")
        
        # Debug: Print first few URLs
        if image_urls:
            print("\nSample URLs found:")
            for i, url in enumerate(image_urls[:3], 1):
                print(f"  {i}. {url[:100]}...")
        else:
            print("\n⚠️  No images passed the filter. Sample raw URLs:")
            for i, (url, source) in enumerate(all_urls[:5], 1):
                print(f"  {i}. [{source}] {url[:100]}...")
        
        return image_urls
    
    def is_gallery_image(self, url):
        """Check if URL is likely a gallery image - LESS STRICT"""
        if not url or not url.startswith('http'):
            return False
        
        url_lower = url.lower()
        
        # Exclude obvious non-photos
        exclude = ['logo', 'icon', 'favicon', 'sprite', 'badge', '/ads/', 'banner']
        if any(ex in url_lower for ex in exclude):
            return False
        
        # Look for cricket image hosting domains
        good_domains = [
            'img1.hscicdn.com',
            'p.imgci.com',
            'a.espncdn.com',
            'img.espncdn.com',
        ]
        
        # Check domain
        has_good_domain = any(domain in url_lower for domain in good_domains)
        
        # Check for image indicators
        has_image_path = any(x in url_lower for x in ['/image/', '/upload/', '/cricket/', 'gallery'])
        has_image_ext = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp'])
        
        return has_good_domain and (has_image_path or has_image_ext)
    
    def is_likely_photo(self, url):
        """Even less strict - just check if it looks like a photo"""
        if not url or not url.startswith('http'):
            return False
        
        url_lower = url.lower()
        
        # Definitely exclude
        bad = ['logo', 'icon', 'favicon', 'sprite', 'badge', 'f_auto,']
        if any(b in url_lower for b in bad):
            return False
        
        # Include anything from these domains with image extensions
        domains = ['hscicdn', 'imgci', 'espncdn']
        has_domain = any(d in url_lower for d in domains)
        
        has_ext = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', 'image/upload'])
        
        return has_domain and has_ext
    
    def download_image(self, img_url, save_path):
        """Download a single image"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.espncricinfo.com/',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            }
            
            response = requests.get(img_url, headers=headers, timeout=15, stream=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'image' in content_type or 'octet-stream' in content_type:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Check file size
                    file_size = os.path.getsize(save_path)
                    if file_size < 2000:  # Less than 2KB - likely placeholder
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
        """Download all images from an album"""
        image_urls = self.get_images_from_album(album_url, album_title)
        
        if not image_urls:
            print(f"\n⚠️  No images found in this album\n")
            return 0
        
        # Create album directory
        album_dir = os.path.join(self.output_dir, album_title)
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        
        print(f"\nDownloading {len(image_urls)} images...")
        print(f"Saving to: {album_dir}")
        print("-" * 70)
        
        successful_downloads = 0
        
        for idx, img_url in enumerate(image_urls, 1):
            parsed_url = urlparse(img_url)
            path = parsed_url.path
            
            ext = os.path.splitext(path)[1]
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                ext = '.jpg'
            
            filename = f"image_{idx:03d}{ext}"
            save_path = os.path.join(album_dir, filename)
            
            print(f"  [{idx}/{len(image_urls)}] {filename}...", end=' ', flush=True)
            
            if self.download_image(img_url, save_path):
                file_size = os.path.getsize(save_path) / 1024
                print(f"✓ ({file_size:.1f} KB)")
                successful_downloads += 1
            else:
                print("✗ (failed)")
            
            time.sleep(0.3)
        
        print("-" * 70)
        print(f"✓ Downloaded {successful_downloads}/{len(image_urls)} images\n")
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
            self.setup_driver()
            album_links = self.get_album_links()
            
            if not album_links:
                print("⚠️  No albums found!")
                return
            
            total_images = 0
            print(f"\n{'='*70}")
            print(f"Starting download of {len(album_links)} albums")
            print(f"{'='*70}")
            
            for idx, (album_url, album_title) in enumerate(album_links, 1):
                print(f"\n[Album {idx}/{len(album_links)}]")
                try:
                    num_images = self.download_album_images(album_url, album_title)
                    total_images += num_images
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"\n{'='*70}")
            print(f"✅ DOWNLOAD COMPLETE!")
            print(f"{'='*70}")
            print(f"Albums processed: {len(album_links)}")
            print(f"Total images downloaded: {total_images}")
            print(f"Saved to: {os.path.abspath(self.output_dir)}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description='Download gallery images from ESPN Cricinfo albums'
    )
    
    parser.add_argument('-n', '--num-albums', type=int, default=10,
                        help='Number of albums to download (default: 10)')
    parser.add_argument('-o', '--output-dir', type=str, default='espn_images',
                        help='Output directory (default: espn_images)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("ESPN Cricinfo Gallery Downloader (Fixed)")
    print("="*70)
    print(f"Albums: {args.num_albums}")
    print(f"Output: {args.output_dir}")
    print("="*70)
    
    downloader = ESPNGalleryDownloader(
        num_albums=args.num_albums,
        output_dir=args.output_dir
    )
    
    downloader.run()


if __name__ == "__main__":
    main()

