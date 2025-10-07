"""
Test Analysis on Cloned Repository in Docker
Analyzes a real GitHub repository using the multi-agent coordinator
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.coordinator import AnalysisCoordinator, AnalysisConfig


def print_header(title: str):
    """Print a nice header"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def print_progress(progress_data: dict):
    """Progress callback"""
    completed = progress_data['completed_files']
    total = progress_data['total_files']
    percent = progress_data['progress_percent']
    issues = progress_data['total_issues']
    elapsed = progress_data['elapsed_time']
    
    # Calculate files per second
    fps = completed / elapsed if elapsed > 0 else 0
    
    print(
        f"⏳ Progress: {completed}/{total} files ({percent:.1f}%) | "
        f"Issues: {issues} | Elapsed: {elapsed:.1f}s | Speed: {fps:.2f} files/s"
    )


async def analyze_docker_repo():
    """Analyze the repository in Docker container"""
    
    # Path to the cloned repository in Docker
    repo_path = "/tmp/codeguard_clone_35qqvj8h/G-Ai-chatbot"
    
    print_header("🐳 DOCKER REPOSITORY ANALYSIS")
    print(f"\n📂 Repository: {repo_path}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if path exists
    if not Path(repo_path).exists():
        print(f"\n❌ Error: Repository path does not exist: {repo_path}")
        print("\nAvailable paths in /tmp:")
        import os
        if Path("/tmp").exists():
            for item in os.listdir("/tmp"):
                print(f"  - /tmp/{item}")
        return None
    
    # Show repository structure
    print("\n📊 Repository Structure:")
    try:
        for item in Path(repo_path).iterdir():
            if item.is_dir():
                file_count = len(list(item.rglob("*"))) if item.name != ".git" else 0
                print(f"  📁 {item.name}/ ({file_count} items)")
            else:
                print(f"  📄 {item.name}")
    except Exception as e:
        print(f"  ⚠️ Could not read structure: {e}")
    
    # Configure coordinator
    print("\n⚙️ Configuring Analysis Coordinator...")
    config = AnalysisConfig(
        max_concurrent_files=10,  # Analyze 10 files in parallel
        timeout_per_file=30,      # 30 seconds timeout per file
        use_llm=False,            # Disable LLM for faster testing
        enabled_agents=[
            "security",
            "dependency",
        ],
    )
    
    coordinator = AnalysisCoordinator(config=config)
    
    # Show loaded agents
    agents = coordinator.get_agent_info()
    print(f"\n🤖 Loaded {len(agents)} Agents:")
    for agent in agents:
        print(f"  • {agent['name']}: {agent['description']}")
        print(f"    Languages: {', '.join(agent['supported_languages'][:5])}...")
    
    # Add progress callback
    coordinator.add_progress_callback(print_progress)
    
    # Start analysis
    print_header("🔍 STARTING REPOSITORY ANALYSIS")
    print("\n⏳ Scanning and analyzing files...\n")
    
    try:
        report = await coordinator.analyze_repository(repo_path)
        
        print_header("✅ ANALYSIS COMPLETE")
        
        # Summary
        summary = report['summary']
        print(f"\n📊 Analysis Summary:")
        print(f"  Files Analyzed: {report['files_analyzed']}")
        print(f"  Total Issues: {report['total_issues']}")
        print(f"  Duration: {report['duration']:.2f} seconds")
        print(f"  Overall Score: {summary['overall_score']}/100 (Grade: {summary['grade']})")
        
        # Issues by severity
        print(f"\n🔴 Issues by Severity:")
        by_severity = summary.get('by_severity', {})
        severities = ['critical', 'high', 'medium', 'low', 'info']
        for severity in severities:
            count = by_severity.get(severity, 0)
            if count > 0:
                emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "📝", "info": "ℹ️"}
                print(f"  {emoji.get(severity, '•')} {severity.upper()}: {count}")
        
        # Issues by category
        print(f"\n📂 Issues by Category:")
        by_category = summary.get('by_category', {})
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {category}: {count}")
        
        # Agent statistics
        print(f"\n🤖 Agent Performance:")
        by_agent = summary.get('by_agent', {})
        for agent_name, stats in by_agent.items():
            files = stats.get('files', 0)
            issues = stats.get('issues', 0)
            print(f"  • {agent_name}: {issues} issues from {files} files")
        
        # Top problematic files
        top_files = summary.get('top_problematic_files', [])
        if top_files:
            print(f"\n🔥 Top 10 Problematic Files:")
            for idx, file_info in enumerate(top_files[:10], 1):
                file_name = file_info['file']
                issue_count = file_info['issues']
                print(f"  {idx}. {file_name}: {issue_count} issues")
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:5]:
                print(f"  • {rec}")
        
        # Sample issues
        print(f"\n🔍 Sample Issues (First 10):")
        for idx, issue in enumerate(report['issues'][:10], 1):
            severity_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "📝",
                "info": "ℹ️"
            }
            emoji = severity_emoji.get(issue['severity'], '•')
            
            file_path = issue['file_path']
            line_num = issue.get('line_number', '?')
            title = issue['title']
            
            print(f"\n  {idx}. {emoji} [{issue['severity'].upper()}] {title}")
            print(f"     File: {file_path}:{line_num}")
            print(f"     Rule: {issue['rule_id']}")
            if issue.get('code_snippet'):
                snippet = issue['code_snippet'][:80]
                print(f"     Code: {snippet}...")
        
        # Issues by file breakdown
        print(f"\n📁 Issues by File (Top 10):")
        issues_by_file = report.get('issues_by_file', {})
        sorted_files = sorted(
            issues_by_file.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for file_path, issues in sorted_files[:10]:
            print(f"\n  📄 {file_path} ({len(issues)} issues)")
            
            # Group by severity
            by_sev = {}
            for issue in issues:
                sev = issue['severity']
                by_sev[sev] = by_sev.get(sev, 0) + 1
            
            sev_str = ", ".join([f"{sev}: {count}" for sev, count in by_sev.items()])
            print(f"     {sev_str}")
            
            # Show first 3 issues
            for issue in issues[:3]:
                line = issue.get('line_number', '?')
                print(f"     • Line {line}: {issue['title'][:60]}...")
        
        # Save full report
        output_file = "/tmp/codeguard_analysis_report.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Full report saved to: {output_file}")
        except Exception as e:
            print(f"\n⚠️ Could not save report: {e}")
        
        print_header("🎉 ANALYSIS SUCCESSFULLY COMPLETED")
        
        return report
        
    except Exception as e:
        print_header("❌ ANALYSIS FAILED")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function"""
    print("\n" + "=" * 100)
    print("  🐳 DOCKER REPOSITORY ANALYSIS TEST")
    print("  Testing multi-agent analysis on real cloned repository")
    print("=" * 100)
    
    report = await analyze_docker_repo()
    
    if report:
        print("\n✅ Test completed successfully!")
        print(f"\n📊 Final Stats:")
        print(f"  Total Issues Found: {report['total_issues']}")
        print(f"  Files Analyzed: {report['files_analyzed']}")
        print(f"  Analysis Duration: {report['duration']:.2f}s")
        print(f"  Overall Score: {report['summary']['overall_score']}/100")
        print(f"  Grade: {report['summary']['grade']}")
        
        # Exit code based on critical issues
        critical_count = report['summary'].get('by_severity', {}).get('critical', 0)
        if critical_count > 0:
            print(f"\n🚨 Warning: {critical_count} critical issues found!")
            sys.exit(1)
        else:
            sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
