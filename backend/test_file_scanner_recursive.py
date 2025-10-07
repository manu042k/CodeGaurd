"""
Test FileScanner Recursive Scanning
Demonstrates that FileScanner recursively scans all subdirectories
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.utils.file_scanner import FileScanner


def test_recursive_scanning():
    """Test that FileScanner recursively scans subdirectories"""
    
    print("=" * 80)
    print("  FILE SCANNER RECURSIVE SCANNING TEST")
    print("=" * 80)
    
    # Test with the actual cloned repo in Docker
    repo_path = "/tmp/codeguard_clone_35qqvj8h/G-Ai-chatbot"
    
    if not Path(repo_path).exists():
        print(f"\n❌ Repository not found at: {repo_path}")
        print("\nPlease run this test inside Docker container where repo is cloned.")
        return
    
    print(f"\n📂 Scanning repository: {repo_path}")
    
    # Initialize scanner
    scanner = FileScanner()
    
    # Scan directory (this uses os.walk which is recursive)
    print("\n⏳ Scanning files recursively...")
    files = scanner.scan_directory(repo_path)
    
    print(f"\n✅ Found {len(files)} files total\n")
    
    # Group files by directory depth
    by_depth = {}
    for file_info in files:
        # Count the depth by number of slashes in relative path
        depth = file_info.relative_path.count(os.sep)
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(file_info)
    
    print("📊 Files by Directory Depth:")
    for depth in sorted(by_depth.keys()):
        count = len(by_depth[depth])
        indent = "  " * depth
        print(f"  Depth {depth}: {count} files")
        
        # Show first few files at this depth
        for file_info in by_depth[depth][:3]:
            print(f"    {indent}└─ {file_info.relative_path}")
    
    # Group by top-level directory
    print("\n📁 Files by Top-Level Directory:")
    by_dir = {}
    for file_info in files:
        top_dir = file_info.relative_path.split(os.sep)[0]
        if top_dir not in by_dir:
            by_dir[top_dir] = []
        by_dir[top_dir].append(file_info)
    
    for dir_name in sorted(by_dir.keys()):
        count = len(by_dir[dir_name])
        print(f"  {dir_name}/: {count} files")
        
        # Show file types in this directory
        extensions = {}
        for f in by_dir[dir_name]:
            ext = f.extension or "no_ext"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        ext_str = ", ".join([f"{ext}({count})" for ext, count in sorted(extensions.items())[:5]])
        print(f"    Types: {ext_str}")
    
    # Show deepest nested files
    print("\n🌳 Deepest Nested Files:")
    deepest_files = sorted(files, key=lambda f: f.relative_path.count(os.sep), reverse=True)[:10]
    for file_info in deepest_files:
        depth = file_info.relative_path.count(os.sep)
        print(f"  Depth {depth}: {file_info.relative_path}")
    
    # Verify recursive scanning worked
    print("\n✅ Verification:")
    max_depth = max(by_depth.keys())
    print(f"  • Maximum directory depth reached: {max_depth}")
    print(f"  • Total directories scanned: {len(by_dir)}")
    print(f"  • Total files found: {len(files)}")
    
    if max_depth > 2:
        print("\n🎉 SUCCESS: FileScanner is recursively scanning through subdirectories!")
    else:
        print("\n⚠️  Warning: Only shallow scanning detected")
    
    return files


if __name__ == "__main__":
    import os
    test_recursive_scanning()
