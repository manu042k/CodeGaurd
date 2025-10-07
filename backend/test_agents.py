"""
Test script for multi-agent code analysis system
Run this to verify the foundation components work correctly.
"""

import asyncio
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.security_agent import SecurityAgent
from app.utils.file_scanner import FileScanner
from app.parsers.language_detector import LanguageDetector


async def test_security_agent():
    """Test security agent with sample code"""
    print("\n" + "="*60)
    print("Testing Security Agent")
    print("="*60)
    
    # Sample vulnerable code
    vulnerable_code = """
import os

password = "hardcoded_password123"
api_key = "sk-1234567890abcdef"

def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchone()

def run_command(cmd):
    os.system("echo " + cmd)
    
def render_html(content):
    document.getElementById("output").innerHTML = content
"""
    
    agent = SecurityAgent()
    result = await agent.analyze(
        file_path="test_file.py",
        file_content=vulnerable_code,
        language="python"
    )
    
    print(f"\nAgent: {result.agent_name}")
    print(f"Score: {result.score}/10")
    print(f"Execution Time: {result.execution_time:.3f}s")
    print(f"\nIssues Found: {len(result.issues)}")
    print(f"  - Critical: {result.metrics['critical_issues']}")
    print(f"  - High: {result.metrics['high_issues']}")
    print(f"  - Medium: {result.metrics['medium_issues']}")
    print(f"  - Low: {result.metrics['low_issues']}")
    
    print("\nDetailed Issues:")
    for i, issue in enumerate(result.issues[:5], 1):  # Show first 5
        print(f"\n{i}. [{issue.severity.value.upper()}] {issue.title}")
        print(f"   Line {issue.line_number}: {issue.code_snippet}")
        print(f"   💡 {issue.suggestion}")
    
    if len(result.issues) > 5:
        print(f"\n... and {len(result.issues) - 5} more issues")


def test_file_scanner():
    """Test file scanner"""
    print("\n" + "="*60)
    print("Testing File Scanner")
    print("="*60)
    
    scanner = FileScanner()
    
    # Get current backend directory
    backend_dir = Path(__file__).parent.parent / "app"
    
    if backend_dir.exists():
        print(f"\nScanning directory: {backend_dir}")
        files = scanner.scan_directory(str(backend_dir))
        
        print(f"\nFiles found: {len(files)}")
        
        stats = scanner.get_statistics(files)
        print(f"Total size: {stats['total_size_mb']} MB")
        print(f"\nFile types:")
        for ext, count in sorted(stats['extensions'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext}: {count} files")
        
        print(f"\nSample files:")
        for file_info in files[:5]:
            print(f"  - {file_info.relative_path} ({file_info.size} bytes)")
    else:
        print(f"Directory not found: {backend_dir}")


def test_language_detector():
    """Test language detector"""
    print("\n" + "="*60)
    print("Testing Language Detector")
    print("="*60)
    
    test_files = [
        ("script.py", None),
        ("app.js", None),
        ("Component.tsx", None),
        ("Main.java", None),
        ("main.go", None),
        ("Dockerfile", None),
        ("test.sh", "#!/bin/bash\necho 'test'"),
    ]
    
    for filename, content in test_files:
        language = LanguageDetector.detect_language(filename, content)
        print(f"{filename:20} -> {language}")
    
    print(f"\nTotal supported languages: {len(LanguageDetector.get_all_supported_languages())}")
    print("Sample languages:", ", ".join(LanguageDetector.get_all_supported_languages()[:10]))


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 Multi-Agent Code Analysis System - Component Tests")
    print("="*60)
    
    try:
        # Test 1: Language Detector
        test_language_detector()
        
        # Test 2: File Scanner
        test_file_scanner()
        
        # Test 3: Security Agent
        await test_security_agent()
        
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
