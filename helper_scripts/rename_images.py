#!/usr/bin/env python3
"""
Script to rename all images in a folder sequentially from 0 to n-1.
Preserves the original file extension.
"""

import os
import sys
import argparse
from pathlib import Path


# Common image file extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.svg', '.ico', '.heic', '.heif'}


def get_image_files(folder_path):
    """Get all image files in the folder, sorted by name."""
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    image_files = []
    for file in sorted(folder.iterdir()):
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
            image_files.append(file)
    
    return image_files


def rename_images(folder_path, dry_run=False):
    """Rename all images in the folder sequentially from 0 to n-1."""
    image_files = get_image_files(folder_path)
    
    if not image_files:
        print(f"No image files found in: {folder_path}")
        return
    
    print(f"Found {len(image_files)} image file(s)")
    
    if dry_run:
        print("\n[DRY RUN] Would rename:")
    else:
        print("\nRenaming files:")
    
    # First, rename to temporary names to avoid conflicts
    temp_files = []
    for idx, img_file in enumerate(image_files):
        ext = img_file.suffix
        new_name = f"__temp_{idx}{ext}"
        temp_path = img_file.parent / new_name
        
        if not dry_run:
            img_file.rename(temp_path)
        temp_files.append((temp_path, ext))
        
        if dry_run:
            print(f"  {img_file.name} -> {new_name} (temp)")
    
    # Now rename from temp names to final names
    for idx, (temp_path, ext) in enumerate(temp_files):
        final_name = f"{idx}{ext}"
        final_path = temp_path.parent / final_name
        
        if not dry_run:
            temp_path.rename(final_path)
        
        if dry_run:
            print(f"  __temp_{idx}{ext} -> {final_name}")
        else:
            print(f"  -> {final_name}")
    
    if not dry_run:
        print(f"\nSuccessfully renamed {len(image_files)} image file(s)")


def main():
    parser = argparse.ArgumentParser(
        description='Rename all images in a folder sequentially from 0 to n-1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python rename_images.py /path/to/folder
  python rename_images.py /path/to/folder --dry-run
        '''
    )
    parser.add_argument('folder', help='Path to the folder containing images')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be renamed without actually renaming')
    
    args = parser.parse_args()
    
    try:
        rename_images(args.folder, dry_run=args.dry_run)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

