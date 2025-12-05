import os
import sys
from tqdm import tqdm
import subprocess
import time
import logging

# --- Utility Functions ---
def ensure_dirs(base_dir):
    """Ensure raw/ and size_processed/ subfolders exist under base_dir."""
    raw_dir = os.path.join(base_dir, 'raw')
    processed_dir = os.path.join(base_dir, 'size_processed')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    return raw_dir, processed_dir

def setup_logging(log_path):
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"Logging to {log_path}")

def run_with_progress(command, desc, log_path):
    """Run a Python script and show a progress bar. Progress is updated on [SUCCESS] log lines."""
    # Open subprocess in text mode with explicit UTF-8 encoding and replacement for
    # undecodable bytes. On Windows the default locale/encoding (cp1252) can raise
    # UnicodeDecodeError when child output contains bytes outside that code page.
    process = subprocess.Popen(
        [sys.executable, command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    pbar = tqdm(desc=desc, unit='files')
    success_count = 0
    error_count = 0
    def sanitize_output(s: str) -> str:
        # Replace control / non-printable characters (except newline/tab) with U+FFFD
        if not s:
            return s
        out_chars = []
        for ch in s:
            code = ord(ch)
            if ch in ('\n', '\r', '\t'):
                out_chars.append(ch)
            elif 32 <= code <= 0x10FFFF:
                out_chars.append(ch)
            else:
                out_chars.append('\ufffd')
        return ''.join(out_chars)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            safe = sanitize_output(output).strip()
            logging.info(safe)
            if '[SUCCESS]' in output:
                pbar.update(1)
                success_count += 1
            if '[ERROR]' in output:
                error_count += 1
            if any(tag in output for tag in ['[ERROR]', '[INFO] Total']):
                tqdm.write(safe)
    pbar.close()
    return process.poll(), success_count, error_count

def summarize(raw_dir, processed_dir, download_stats, process_stats):
    """Print a summary report of the pipeline run."""
    raw_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    processed_files = [f for f in os.listdir(processed_dir) if f.endswith('_processed.jpg')]
    print("\n--- Pipeline Summary Report ---")
    print(f"Downloaded images: {download_stats[1]} (errors: {download_stats[2]})")
    print(f"Processed images: {process_stats[1]} (errors: {process_stats[2]})")
    print(f"Total images in raw/: {len(raw_files)}")
    print(f"Total images in processed/: {len(processed_files)}")
    print(f"Log file: pipeline.log")
    print("------------------------------\n")

# --- Main Pipeline ---
def main():
    """Main pipeline: download and process images with error recovery, subfolder structure, logging, and summary report."""
    print("[INFO] Starting image download and processing pipeline...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.getenv('DATA_DIR', os.path.join(script_dir, 'data'))
    raw_dir, processed_dir = ensure_dirs(data_dir)
    log_path = os.path.join(script_dir, 'pipeline.log')
    setup_logging(log_path)

    # Step 1: Download images to raw/
    print("\n[PHASE 1] Downloading images from ESPNCricinfo to raw/...")
    os.environ['DATA_DIR'] = raw_dir
    download_stats = run_with_progress('img_downloader_self.py', 'Downloading', log_path)
    if download_stats[0] != 0:
        print("[ERROR] Download phase failed!")
        return
    time.sleep(1)

    # Step 2: Process images to size_processed/
    print("\n[PHASE 2] Processing images to 800x600 (cropped, no black bars) in size_processed/...")
    os.environ['DATA_DIR'] = raw_dir
    os.environ['PROCESSED_DIR'] = processed_dir
    process_stats = run_with_progress('process_images.py', 'Processing', log_path)
    if process_stats[0] != 0:
        print("[ERROR] Processing phase failed!")
        return

    summarize(raw_dir, processed_dir, download_stats, process_stats)
    print("[SUCCESS] Pipeline complete! Check the 'data/raw' and 'data/size_processed' folders for results.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Pipeline interrupted by user")
        sys.exit(1)