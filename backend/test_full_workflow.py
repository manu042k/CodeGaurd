"""
Complete End-to-End Workflow Test
Tests the full integration of GitHub cloner + multi-agent coordinator
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.github_service import GitHubService
from app.services.repository_analysis_service import RepositoryAnalysisService
from app.coordinator import AnalysisConfig
from app.models.database import Repository


def print_header(title: str, char: str = "="):
    """Print formatted header"""
    print("\n" + char * 100)
    print(f"  {title}")
    print(char * 100)


def print_section(title: str):
    """Print section title"""
    print(f"\n{'─' * 100}")
    print(f"  {title}")
    print(f"{'─' * 100}")


def print_progress(progress: dict):
    """Progress callback to show real-time updates"""
    bar_length = 50
    filled = int(bar_length * progress['progress_percent'] / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    print(
        f"\r  ⏳ [{bar}] {progress['progress_percent']:.1f}% | "
        f"{progress['completed_files']}/{progress['total_files']} files | "
        f"Issues: {progress['total_issues']} | "
        f"Time: {progress['elapsed_time']:.1f}s",
        end='',
        flush=True
    )


async def test_full_workflow():
    """
    Test the complete workflow:
    1. Clone repository from GitHub
    2. Run multi-agent analysis
    3. Generate comprehensive report
    4. Cleanup
    """
    
    print_header("🚀 CODEGUARD FULL WORKFLOW TEST", "=")
    
    # Mock repository object (simulating database record)
    # In production, this would come from your database
    repository = type('Repository', (), {
        'id': 849259406,
        'name': 'G-Ai-chatbot',
        'full_name': 'manu042k/G-Ai-chatbot',
        'html_url': 'https://github.com/manu042k/G-Ai-chatbot',
        'clone_url': 'https://github.com/manu042k/G-Ai-chatbot.git',
        'language': 'TypeScript',
        'stargazers_count': 0,
        'forks_count': 0,
        'private': False,
    })()
    
    print_section("📋 TEST CONFIGURATION")
    print(f"  Repository: {repository.full_name}")
    print(f"  URL: {repository.html_url}")
    print(f"  Language: {repository.language}")
    print(f"  Public Repository: Yes")
    
    # Configure analysis
    # Using only rule-based agents for faster testing
    analysis_config = AnalysisConfig(
        max_concurrent_files=10,
        timeout_per_file=30,
        use_llm=False,  # Set to True to enable LLM-based analysis
        enabled_agents=["security", "dependency"],
    )
    
    print(f"  Enabled Agents: {', '.join(analysis_config.enabled_agents)}")
    print(f"  Max Concurrent Files: {analysis_config.max_concurrent_files}")
    print(f"  LLM Enabled: {analysis_config.use_llm}")
    
    # Create GitHub service with dummy token for public repos
    # Note: For public repos, we can use the clone_url directly without auth
    github_service = GitHubService(
        access_token="dummy_token_for_public_repos",  # Dummy token for testing
        db=None
    )
    
    # Create analysis service
    analysis_service = RepositoryAnalysisService(
        github_service=github_service,
        analysis_config=analysis_config,
    )
    
    # Add progress callback for real-time updates
    analysis_service.add_progress_callback(print_progress)
    
    # Run the complete workflow
    print_section("🔄 STARTING WORKFLOW")
    print("\n  Step 1: Cloning repository...")
    print("  Step 2: Scanning files...")
    print("  Step 3: Running security analysis...")
    print("  Step 4: Running dependency analysis...")
    print("  Step 5: Aggregating results...")
    print("  Step 6: Generating report...\n")
    
    try:
        report = await analysis_service.clone_and_analyze(
            repository=repository,
            shallow=True,  # Shallow clone for faster testing
            cleanup=True,  # Clean up after analysis
        )
        
        # Print newline after progress bar
        print("\n")
        
        if report["status"] == "failed":
            print_header("❌ WORKFLOW FAILED", "=")
            print(f"\n  Error: {report.get('error')}")
            return
        
        # Display results
        print_header("✅ WORKFLOW COMPLETED SUCCESSFULLY", "=")
        
        # Clone results
        print_section("📦 CLONE RESULTS")
        clone_info = report["clone"]
        print(f"  ✓ Clone Successful: {clone_info['success']}")
        print(f"  ✓ Duration: {clone_info['duration']:.2f}s")
        print(f"  ✓ Repository Size: {clone_info['size_mb']:.2f} MB")
        print(f"  ✓ Commit Count: {clone_info.get('commit_count', 'N/A')}")
        print(f"  ✓ Clone Type: {'Shallow' if clone_info['shallow'] else 'Full'}")
        
        # Analysis results
        print_section("🔍 ANALYSIS RESULTS")
        analysis = report["analysis"]
        summary = analysis["summary"]
        
        print(f"  Files Analyzed: {analysis['files_analyzed']}")
        print(f"  Total Issues Found: {analysis['total_issues']}")
        print(f"  Overall Score: {summary['overall_score']}/100")
        print(f"  Grade: {summary['grade']}")
        
        # Severity breakdown
        print("\n  Issues by Severity:")
        by_severity = summary["by_severity"]
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = by_severity.get(severity, 0)
            emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
                "info": "⚪"
            }.get(severity, "•")
            if count > 0:
                print(f"    {emoji} {severity.upper()}: {count}")
        
        # Category breakdown
        print("\n  Issues by Category:")
        by_category = summary["by_category"]
        for category, count in by_category.items():
            if count > 0:
                print(f"    • {category}: {count}")
        
        # Agent breakdown
        print("\n  Issues by Agent:")
        by_agent = summary["by_agent"]
        for agent, count in by_agent.items():
            if count > 0:
                print(f"    🤖 {agent}: {count}")
        
        # Timing information
        print_section("⏱️  PERFORMANCE METRICS")
        timing = report["timing"]
        print(f"  Total Duration: {timing['total_duration']:.2f}s")
        print(f"  Clone Duration: {timing['clone_duration']:.2f}s")
        print(f"  Analysis Duration: {timing['analysis_duration']:.2f}s")
        print(f"  Files/Second: {analysis['files_analyzed'] / timing['analysis_duration']:.2f}")
        
        # Show sample issues (top 5)
        if analysis['total_issues'] > 0:
            print_section("🔍 SAMPLE ISSUES (Top 5)")
            for i, issue in enumerate(analysis['issues'][:5], 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵",
                    "info": "⚪"
                }.get(issue['severity'], "•")
                
                print(f"\n  {i}. {severity_emoji} {issue['title']}")
                print(f"     Category: {issue['category']}")
                print(f"     File: {issue['file_path']}")
                if issue.get('line_number'):
                    print(f"     Line: {issue['line_number']}")
                print(f"     Agent: {issue['agent']}")
                
                # Show description (truncated)
                desc = issue['description']
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                print(f"     Description: {desc}")
        
        # Recommendations
        if analysis.get('recommendations'):
            print_section("💡 TOP RECOMMENDATIONS")
            for i, rec in enumerate(analysis['recommendations'][:3], 1):
                print(f"\n  {i}. {rec['title']}")
                print(f"     Priority: {rec.get('priority', 'medium').upper()}")
                desc = rec['description']
                if len(desc) > 120:
                    desc = desc[:117] + "..."
                print(f"     {desc}")
        
        # Save detailed report to file
        print_section("💾 SAVING DETAILED REPORT")
        report_file = Path("test_workflow_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  ✓ Detailed report saved to: {report_file.absolute()}")
        
        print_header("🎉 TEST COMPLETED SUCCESSFULLY", "=")
        print("\n  Summary:")
        print(f"    • Repository: {repository.full_name}")
        print(f"    • Files Analyzed: {analysis['files_analyzed']}")
        print(f"    • Issues Found: {analysis['total_issues']}")
        print(f"    • Score: {summary['overall_score']}/100 (Grade: {summary['grade']})")
        print(f"    • Total Time: {timing['total_duration']:.2f}s")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("  CodeGuard - Complete End-to-End Workflow Test")
    print("  Testing: GitHub Clone → Multi-Agent Analysis → Comprehensive Report")
    print("=" * 100 + "\n")
    
    asyncio.run(test_full_workflow())
