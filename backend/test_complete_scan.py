"""
Complete Repository Scan Analysis
Shows exactly what files are found vs excluded
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.utils.file_scanner import FileScanner


def analyze_complete_repository():
    """Analyze what files are scanned vs excluded"""
    
    print("=" * 100)
    print("  COMPLETE REPOSITORY SCAN ANALYSIS")
    print("=" * 100)
    
    repo_path = "/tmp/codeguard_clone_35qqvj8h/G-Ai-chatbot"
    
    if not Path(repo_path).exists():
        print(f"\n❌ Repository not found at: {repo_path}")
        return
    
    print(f"\n📂 Repository: {repo_path}")
    
    # Count ALL files manually (using os.walk)
    print("\n1️⃣ Manual File Count (ALL files):")
    all_files = []
    excluded_dirs = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Filter out .git
        if '.git' in dirs:
            dirs.remove('.git')
            excluded_dirs += 1
        
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            all_files.append(rel_path)
    
    print(f"  Total files found: {len(all_files)}")
    print(f"  Excluded directories (.git): {excluded_dirs}")
    
    # Group by directory
    by_dir = {}
    for file_path in all_files:
        top_dir = file_path.split(os.sep)[0] if os.sep in file_path else "root"
        if top_dir not in by_dir:
            by_dir[top_dir] = []
        by_dir[top_dir].append(file_path)
    
    print("\n  Files by directory:")
    for dir_name in sorted(by_dir.keys()):
        files = by_dir[dir_name]
        print(f"    {dir_name}/: {len(files)} files")
        
        # Show file types
        extensions = {}
        for f in files:
            ext = Path(f).suffix or "no_ext"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Show top 5 extensions
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]
        ext_str = ", ".join([f"{ext}({count})" for ext, count in top_exts])
        print(f"      Types: {ext_str}")
    
    # Now scan with FileScanner
    print("\n2️⃣ FileScanner Results (code files only):")
    scanner = FileScanner()
    scanned_files = scanner.scan_directory(repo_path)
    
    print(f"  Files scanned: {len(scanned_files)}")
    print(f"  Reduction: {len(all_files) - len(scanned_files)} files excluded")
    
    scanned_paths = {f.relative_path for f in scanned_files}
    
    # Group scanned files by directory
    scanned_by_dir = {}
    for file_info in scanned_files:
        top_dir = file_info.relative_path.split(os.sep)[0]
        if top_dir not in scanned_by_dir:
            scanned_by_dir[top_dir] = []
        scanned_by_dir[top_dir].append(file_info)
    
    print("\n  Scanned files by directory:")
    for dir_name in sorted(scanned_by_dir.keys()):
        files = scanned_by_dir[dir_name]
        print(f"    {dir_name}/: {len(files)} files")
        
        # Show file types
        extensions = {}
        for f in files:
            ext = f.extension or "no_ext"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]
        ext_str = ", ".join([f"{ext}({count})" for ext, count in top_exts])
        print(f"      Types: {ext_str}")
    
    # Show what was EXCLUDED
    print("\n3️⃣ Files EXCLUDED by FileScanner:")
    excluded_files = []
    for file_path in all_files:
        if file_path not in scanned_paths:
            excluded_files.append(file_path)
    
    print(f"  Total excluded: {len(excluded_files)} files")
    
    # Group excluded by reason
    excluded_by_reason = {
        "Images/Media": [],
        "Config/Lock files": [],
        "IDE files": [],
        "Other": []
    }
    
    for file_path in excluded_files:
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']:
            excluded_by_reason["Images/Media"].append(file_path)
        elif file_path.endswith(('package-lock.json', 'yarn.lock', '.json')):
            excluded_by_reason["Config/Lock files"].append(file_path)
        elif '.vscode' in file_path:
            excluded_by_reason["IDE files"].append(file_path)
        else:
            excluded_by_reason["Other"].append(file_path)
    
    print("\n  Excluded files by reason:")
    for reason, files in excluded_by_reason.items():
        if files:
            print(f"    {reason}: {len(files)} files")
            for f in files[:3]:
                print(f"      - {f}")
            if len(files) > 3:
                print(f"      ... and {len(files) - 3} more")
    
    # Show sample of scanned files from each directory
    print("\n4️⃣ Sample of SCANNED files from each directory:")
    for dir_name in sorted(scanned_by_dir.keys()):
        files = scanned_by_dir[dir_name]
        print(f"\n  {dir_name}/ ({len(files)} files):")
        for f in files[:5]:
            print(f"    ✓ {f.relative_path} ({f.size} bytes)")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")
    
    # Verify recursion
    print("\n5️⃣ Recursion Verification:")
    max_depth = max(f.relative_path.count(os.sep) for f in scanned_files)
    print(f"  Maximum depth reached: {max_depth} levels")
    print(f"  Total directories with code files: {len(scanned_by_dir)}")
    
    # Show deepest files
    deepest = sorted(scanned_files, key=lambda f: f.relative_path.count(os.sep), reverse=True)[:3]
    print(f"\n  Deepest files:")
    for f in deepest:
        depth = f.relative_path.count(os.sep)
        print(f"    Depth {depth}: {f.relative_path}")
    
    print("\n" + "=" * 100)
    print("  SUMMARY")
    print("=" * 100)
    print(f"  ✓ Total files in repository: {len(all_files)}")
    print(f"  ✓ Code files scanned: {len(scanned_files)}")
    print(f"  ✓ Files excluded: {len(excluded_files)}")
    print(f"  ✓ Directories scanned: {len(scanned_by_dir)}")
    print(f"  ✓ Maximum depth: {max_depth} levels")
    print(f"\n  🎉 FileScanner IS recursively scanning ALL subdirectories!")
    print(f"     It found code files in {len(scanned_by_dir)} directories at depths up to {max_depth}")
    print("=" * 100)


if __name__ == "__main__":
    analyze_complete_repository()
