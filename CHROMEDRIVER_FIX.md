# ChromeDriver Fix for macOS ARM64

## The Problem

The `webdriver-manager` library sometimes picks the wrong file on macOS ARM64 systems, trying to execute `THIRD_PARTY_NOTICES.chromedriver` instead of the actual `chromedriver` executable.

## Solutions (Pick One)

### ✅ Solution 1: Use the Simple Version (RECOMMENDED)

The simplest and most reliable solution is to install ChromeDriver via Homebrew and use the simple version of the script.

#### Step 1: Install ChromeDriver via Homebrew
```bash
brew install chromedriver
```

#### Step 2: Remove quarantine (macOS security)
```bash
xattr -d com.apple.quarantine $(which chromedriver)
```

#### Step 3: Use the simple script
```bash
python3 espn_gallery_downloader_simple.py -n 10
```

---

### ✅ Solution 2: Use the Fixed Auto Version

I've updated the auto version to handle this issue. It should now work correctly.

```bash
python3 espn_gallery_downloader_auto.py -n 10
```

---

### ✅ Solution 3: Manual ChromeDriver Cleanup

If you want to clean up the incorrectly downloaded ChromeDriver:

#### Step 1: Remove the cached ChromeDriver
```bash
rm -rf ~/.wdm/drivers/chromedriver
```

#### Step 2: Try the auto version again
```bash
python3 espn_gallery_downloader_auto.py -n 10
```

---

### ✅ Solution 4: Manual ChromeDriver Download

Download ChromeDriver manually and tell the script where to find it.

#### Step 1: Download ChromeDriver for your system
- For macOS ARM64 (M1/M2/M3): https://googlechromelabs.github.io/chrome-for-testing/
- Choose the version that matches your Chrome browser

#### Step 2: Extract and move to system path
```bash
# Assuming you downloaded chromedriver-mac-arm64.zip
unzip chromedriver-mac-arm64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

#### Step 3: Use the simple version
```bash
python3 espn_gallery_downloader_simple.py -n 10
```

---

## Quick Test

After installing ChromeDriver, verify it works:

```bash
# Check if chromedriver is in PATH
which chromedriver

# Test chromedriver
chromedriver --version
```

Expected output:
```
ChromeDriver 142.0.7444.x (...)
```

---

## Recommended Workflow

For the best experience:

1. **Install ChromeDriver once:**
   ```bash
   brew install chromedriver
   xattr -d com.apple.quarantine $(which chromedriver)
   ```

2. **Use the simple version going forward:**
   ```bash
   python3 espn_gallery_downloader_simple.py -n 10
   ```

This avoids the webdriver-manager complexity and is more reliable.

---

## Script Comparison

| Script | ChromeDriver Method | Pros | Cons |
|--------|-------------------|------|------|
| `espn_gallery_downloader_simple.py` | Uses system ChromeDriver | ✅ Simple, reliable | ⚠️ Requires manual install |
| `espn_gallery_downloader_auto.py` | Auto-downloads via webdriver-manager | ✅ No manual install | ⚠️ Can have issues on ARM64 |
| `espn_gallery_downloader.py` | Expects ChromeDriver in PATH | ✅ Fast startup | ⚠️ Requires manual install |

---

## Still Having Issues?

### Error: "chromedriver cannot be opened because the developer cannot be verified"

**Solution:**
```bash
xattr -d com.apple.quarantine $(which chromedriver)
```

### Error: "chromedriver not found"

**Solution:**
```bash
# Install via homebrew
brew install chromedriver

# OR add to PATH manually
export PATH="/usr/local/bin:$PATH"
```

### Error: "ChromeDriver version mismatch"

**Solution:**
```bash
# Update ChromeDriver to match your Chrome version
brew upgrade chromedriver

# Check versions match
chromedriver --version
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

---

## Quick Start After Fix

Once ChromeDriver is working:

```bash
# Test with 2 albums first
python3 espn_gallery_downloader_simple.py -n 2

# If successful, run full download
python3 espn_gallery_downloader_simple.py -n 10
```

---

## Need More Help?

Run the test script to diagnose:
```bash
python3 test_setup.py
```

This will tell you exactly what's working and what needs to be fixed.

