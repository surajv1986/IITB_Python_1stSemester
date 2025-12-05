import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
# Config
BASE_URL = "https://www.espncricinfo.com/gallery"
MAX_LINKS = 150
MAX_DOWNLOADS = 400
SCROLL_PAUSE = 2

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# By default, use a 'data/raw' directory next to this script
base_data_dir = os.getenv('DATA_DIR', os.path.join(script_dir, 'data', 'raw'))
save_folder = base_data_dir
os.makedirs(save_folder, exist_ok=True)

# Utility function for error recovery (defined early so it's available when used)
def already_downloaded(filename):
    """Check if the image file already exists in save_folder."""
    return os.path.exists(filename)

print("[INFO] Starting Selenium...")
# Use webdriver-manager to simplify getting a matching chromedriver. This is a
# low-risk improvement: environments that already have chromedriver on PATH will
# keep working because webdriver-manager will install and return a path.
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
except Exception as e:
    print(f"[INFO] webdriver-manager failed or is unavailable: {e}")
    print("[INFO] Falling back to webdriver.Chrome() which requires chromedriver on PATH.")
    driver = webdriver.Chrome()
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
driver.get(BASE_URL)

# Handle pop-up
try:
    time.sleep(3)
    not_now_button = driver.find_element(By.XPATH, "//button[contains(text(),'Not Now')]")
    not_now_button.click()
    print("[INFO] Pop-up dismissed successfully.")
except Exception:
    print("[INFO] No pop-up found.")

gallery_links = set()
last_height = driver.execute_script("return document.body.scrollHeight")

# Scroll until we collect enough gallery links
scroll_attempts = 0
max_scroll_attempts = 20
while len(gallery_links) < MAX_LINKS and scroll_attempts < max_scroll_attempts:
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        new_links = [a['href'] for a in soup.find_all('a', href=True) if '/gallery/' in a['href']]
        gallery_links.update(new_links)

        print(f"[INFO] Collected {len(gallery_links)} gallery links so far...")

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("[INFO] No new content loaded. Stopping scroll.")
            break
        last_height = new_height
        scroll_attempts += 1
    except Exception as e:
        print(f"[ERROR] Error during scroll (attempt {scroll_attempts + 1}): {e}")
        scroll_attempts += 1
        time.sleep(5)
        continue

print(f"[INFO] Final collected gallery links: {len(gallery_links)}")

# Phase 1: collect candidate image URLs (single-threaded, using Selenium)
img_urls = []
img_urls_set = set()
for link in list(gallery_links):
    gallery_url = "https://www.espncricinfo.com" + link
    print(f"[INFO] Scanning gallery page for image URLs: {gallery_url}")
    try:
        driver.get(gallery_url)
        time.sleep(2)  # Wait for images to load
        gallery_soup = BeautifulSoup(driver.page_source, 'html.parser')

        img_tags = gallery_soup.find_all('img')
        print(f"[INFO] Found {len(img_tags)} <img> tags on page.")

        for img_tag in img_tags:
            # Extract high-res image from srcset if available
            srcset = img_tag.get('srcset')
            if srcset:
                urls = [u.split(' ')[0] for u in srcset.split(',') if u.strip()]
                img_url = urls[-1] if urls else img_tag.get('src')
            else:
                img_url = img_tag.get('src')

            if not img_url:
                continue
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            if img_url.startswith('http') and img_url not in img_urls_set:
                img_urls_set.add(img_url)
                img_urls.append(img_url)

        # Stop early if we already have plenty of candidates
        if len(img_urls) >= MAX_DOWNLOADS * 3:
            print(f"[INFO] Collected {len(img_urls)} candidate image URLs; stopping collection early.")
            break
    except Exception as e:
        print(f"[ERROR] Error scanning gallery page: {e}")
        time.sleep(5)
        continue

driver.quit()
print(f"[INFO] Total candidate image URLs collected: {len(img_urls)}")

# Phase 2: download images concurrently (IO-bound work)
download_count = 0
download_count_lock = threading.Lock()

def process_and_save(img_url):
    """Download an image, process it, and save to disk if it meets the size requirements."""
    global download_count
    # Quick check to avoid unnecessary work
    with download_count_lock:
        if download_count >= MAX_DOWNLOADS:
            return False

    print(f"[INFO] Attempting download: {img_url}")
    try:
        resp = requests.get(img_url, timeout=15)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch image. Status: {resp.status_code} - {img_url}")
            return False

        img_data = resp.content
        try:
            img = Image.open(BytesIO(img_data))
            width, height = img.size
            print(f"[INFO] Image size: {width}x{height} - {img_url}")
            if width >= 800 and height >= 600:
                filename = os.path.join(save_folder, os.path.basename(img_url.split('?')[0]))
                # Avoid race conditions when two threads try to write same filename
                tmp_filename = filename + ".part"
                with open(tmp_filename, 'wb') as f:
                    f.write(img_data)
                os.replace(tmp_filename, filename)
                with download_count_lock:
                    if download_count >= MAX_DOWNLOADS:
                        return False
                    download_count += 1
                    current = download_count
                print(f"[SUCCESS] Downloaded ({current}/{MAX_DOWNLOADS}): {filename}")
                return True
            else:
                print(f"[INFO] Skipped (size too small): {img_url}")
        except Exception as e:
            print(f"[ERROR] Pillow failed to identify image: {e} - {img_url}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch image: {e} - {img_url}")
    return False


max_workers = min(16, (os.cpu_count() or 4) * 2)
print(f"[INFO] Starting concurrent downloads with {max_workers} workers...")
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {executor.submit(process_and_save, url): url for url in img_urls}
    try:
        for future in as_completed(futures):
            # If we've reached the target, break out early.
            with download_count_lock:
                if download_count >= MAX_DOWNLOADS:
                    break
            # Trigger exception if any
            _ = future.result()
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user. Shutting down executor...")

print(f"[INFO] Total downloaded: {download_count}")