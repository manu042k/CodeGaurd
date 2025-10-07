"""
Simplified Workflow Test - Direct Clone and Analysis
Tests coordinator + cloner without GitHub API dependency
"""

import asyncio
import sys
import json
import tempfile
import shutil
from pathlib import Path
import git

sys.path.insert(0, str(Path(__file__).parent))

from app.coordinator import AnalysisCoordinator, AnalysisConfig


def print_header(title: str, char: str = "="):
    """Print formatted header"""
    print("\n" + char * 100)
    print(f"  {title}")
    print(char * 100)


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


async def test_workflow():
    """
    Test complete workflow with direct git cloning
    """
    
    print_header("🚀 CODEGUARD SIMPLIFIED WORKFLOW TEST", "=")
    
    # Repository to test
    repo_url = "https://github.com/manu042k/G-Ai-chatbot.git"
    repo_name = "G-Ai-chatbot"
    
    print(f"\n  Repository: {repo_url}")
    print(f"  Test Type: Public Repository (No Authentication)")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="codeguard_test_")
    clone_path = Path(temp_dir) / repo_name
    
    print(f"  Clone Path: {clone_path}")
    
    try:
        # Step 1: Clone repository
        print_header("📥 STEP 1: CLONING REPOSITORY")
        print(f"\n  Cloning {repo_url}...")
        print(f"  Using shallow clone (depth=1) for speed...\n")
        
        import time
        clone_start = time.time()
        
        # Perform shallow clone
        git.Repo.clone_from(
            repo_url,
            str(clone_path),
            depth=1,
            single_branch=True
        )
        
        clone_duration = time.time() - clone_start
        
        # Calculate size
        total_size = 0
        for item in clone_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
        size_mb = total_size / (1024 * 1024)
        
        print(f"  ✓ Clone completed successfully!")
        print(f"  ✓ Duration: {clone_duration:.2f}s")
        print(f"  ✓ Size: {size_mb:.2f} MB")
        
        # Step 2: Configure analysis
        print_header("⚙️  STEP 2: CONFIGURING ANALYSIS")
        
        config = AnalysisConfig(
            max_concurrent_files=10,
            timeout_per_file=30,
            use_llm=False,
            enabled_agents=["security", "dependency"],
        )
        
        print(f"  Enabled Agents: {', '.join(config.enabled_agents)}")
        print(f"  Max Concurrent Files: {config.max_concurrent_files}")
        print(f"  LLM Enabled: {config.use_llm}")
        
        # Step 3: Run analysis
        print_header("🔍 STEP 3: RUNNING MULTI-AGENT ANALYSIS")
        
        coordinator = AnalysisCoordinator(config=config)
        coordinator.add_progress_callback(print_progress)
        
        print("\n  Starting analysis...\n")
        
        analysis_start = time.time()
        report = await coordinator.analyze_repository(str(clone_path))
        analysis_duration = time.time() - analysis_start
        
        print("\n")  # New line after progress bar
        
        # Step 4: Display results
        print_header("✅ STEP 4: ANALYSIS RESULTS")
        
        summary = report["summary"]
        
        print(f"\n  📊 Summary:")
        print(f"  Files Analyzed: {report['files_analyzed']}")
        print(f"  Total Issues: {report['total_issues']}")
        print(f"  Overall Score: {summary['overall_score']}/100")
        print(f"  Grade: {summary['grade']}")
        print(f"  Analysis Duration: {analysis_duration:.2f}s")
        
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
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"    • {category}: {count}")
        
        # Agent breakdown
        print("\n  Issues by Agent:")
        by_agent = summary["by_agent"]
        for agent, count in by_agent.items():
            if count > 0:
                print(f"    🤖 {agent}: {count}")
        
        # Show top 5 issues
        if report.get('total_issues', 0) > 0 and report.get('issues'):
            print_header("🔍 TOP ISSUES FOUND")
            
            for i, issue in enumerate(report['issues'][:5], 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵",
                    "info": "⚪"
                }.get(issue['severity'], "•")
                
                print(f"\n  {i}. {severity_emoji} {issue['title']}")
                print(f"     File: {issue['file_path']}")
                if issue.get('line_number'):
                    print(f"     Line: {issue['line_number']}")
                print(f"     Severity: {issue['severity'].upper()}")
                print(f"     Category: {issue['category']}")
                print(f"     Agent: {issue['agent']}")
                
                desc = issue['description']
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                print(f"     Description: {desc}")
        
        # Show recommendations
        if report.get('recommendations'):
            print_header("💡 RECOMMENDATIONS")
            
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"\n  {i}. {rec['title']}")
                print(f"     Priority: {rec.get('priority', 'medium').upper()}")
                desc = rec['description']
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                print(f"     {desc}")
        
        # Performance metrics
        print_header("⏱️  PERFORMANCE METRICS")
        print(f"\n  Clone Duration: {clone_duration:.2f}s")
        print(f"  Analysis Duration: {analysis_duration:.2f}s")
        print(f"  Total Duration: {clone_duration + analysis_duration:.2f}s")
        print(f"  Files/Second: {report['files_analyzed'] / analysis_duration:.2f}")
        
        # Save report
        print_header("💾 SAVING REPORT")
        report_file = Path("test_workflow_report.json")
        
        complete_report = {
            "repository": {
                "url": repo_url,
                "name": repo_name,
            },
            "clone": {
                "duration": clone_duration,
                "size_mb": size_mb,
            },
            "analysis": report,
            "timing": {
                "clone": clone_duration,
                "analysis": analysis_duration,
                "total": clone_duration + analysis_duration,
            }
        }
        
        with open(report_file, "w") as f:
            json.dump(complete_report, f, indent=2, default=str)
        
        print(f"  ✓ Report saved to: {report_file.absolute()}")
        
        # Final summary
        print_header("🎉 TEST COMPLETED SUCCESSFULLY", "=")
        print(f"\n  Summary:")
        print(f"    • Repository: {repo_name}")
        print(f"    • Files Analyzed: {report['files_analyzed']}")
        print(f"    • Issues Found: {report['total_issues']}")
        print(f"    • Score: {summary['overall_score']}/100 (Grade: {summary['grade']})")
        print(f"    • Total Time: {clone_duration + analysis_duration:.2f}s")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print_header("🧹 CLEANUP")
        print(f"  Removing temporary directory: {temp_dir}")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"  ✓ Cleanup complete")
        except Exception as e:
            print(f"  ⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("  CodeGuard - Simplified Workflow Test")
    print("  Testing: Direct Git Clone → Multi-Agent Analysis → Report")
    print("=" * 100)
    
    asyncio.run(test_workflow())
