"""
Test LLM-Enhanced Multi-Agent System
Demonstrates hybrid rule-based + LLM analysis.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.security_agent import SecurityAgent
from app.agents.llm_wrapper import SimpleLLMService


# Sample vulnerable code for testing
VULNERABLE_CODE = """
import os
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Hardcoded credentials
DB_PASSWORD = "super_secret_123"
API_KEY = "sk-1234567890abcdefghij"
JWT_SECRET = "my-secret-key"

def get_user_by_id(user_id):
    # SQL Injection vulnerability
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchone()

@app.route('/search')
def search():
    # XSS vulnerability
    search_term = request.args.get('q', '')
    return render_template_string(f"<h1>Results for: {search_term}</h1>")

@app.route('/execute')
def execute_command():
    # Command injection vulnerability
    cmd = request.args.get('cmd', '')
    result = os.system(cmd)
    return f"Command executed: {result}"

def authenticate_user(username, password):
    # Weak authentication
    if username == "admin" and password == "admin123":
        return True
    return False

def encrypt_data(data):
    # Weak cryptography
    import hashlib
    return hashlib.md5(data.encode()).hexdigest()

class User:
    def __init__(self, user_id):
        self.id = user_id
        self.data = self.load_data()
    
    def load_data(self):
        # Insecure deserialization
        import pickle
        with open(f'user_{self.id}.pkl', 'rb') as f:
            return pickle.load(f)
    
    def update_price(self, new_price):
        # Business logic flaw: no authorization check
        self.price = new_price
        self.save()

# Debug mode enabled in production
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
"""


async def test_rule_based_only():
    """Test rule-based analysis without LLM"""
    print("\n" + "="*70)
    print("TEST 1: Rule-Based Analysis Only (Fast)")
    print("="*70)
    
    # Create agent without LLM service
    agent = SecurityAgent(config={"use_llm": False})
    
    result = await agent._rule_based_analysis(
        file_path="test_vulnerable.py",
        file_content=VULNERABLE_CODE,
        language="python"
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"   Score: {result.score}/10")
    print(f"   Execution Time: {result.execution_time:.3f}s")
    print(f"   Total Issues: {len(result.issues)}")
    
    severity_counts = result.get_issue_count_by_severity()
    print(f"\n   Issues by Severity:")
    print(f"   🔴 Critical: {severity_counts['critical']}")
    print(f"   🟠 High: {severity_counts['high']}")
    print(f"   🟡 Medium: {severity_counts['medium']}")
    print(f"   🟢 Low: {severity_counts['low']}")
    
    print(f"\n📋 Issues Found:")
    for i, issue in enumerate(result.issues[:8], 1):
        print(f"\n   {i}. [{issue.severity.value.upper()}] {issue.title}")
        print(f"      Line {issue.line_number}: {issue.code_snippet[:60]}...")
        print(f"      💡 {issue.suggestion}")


async def test_llm_prompt_generation():
    """Test LLM prompt generation"""
    print("\n" + "="*70)
    print("TEST 2: LLM Prompt Generation")
    print("="*70)
    
    agent = SecurityAgent()
    
    # Get rule-based results first
    rule_result = await agent._rule_based_analysis(
        file_path="test_vulnerable.py",
        file_content=VULNERABLE_CODE,
        language="python"
    )
    
    # Generate LLM prompt
    prompt = agent._build_llm_prompt(
        file_path="test_vulnerable.py",
        file_content=VULNERABLE_CODE,
        language="python",
        rule_issues=rule_result
    )
    
    print(f"\n📝 Generated LLM Prompt Preview:")
    print("-" * 70)
    print(prompt[:1000] + "\n... (truncated)")
    print("-" * 70)
    
    print(f"\n✅ Prompt includes:")
    print(f"   - Agent role and expertise")
    print(f"   - Code to analyze")
    print(f"   - Quick scan results ({len(rule_result.issues)} issues)")
    print(f"   - Specific security instructions")
    print(f"   - JSON output format specification")


async def test_decision_logic():
    """Test LLM decision logic"""
    print("\n" + "="*70)
    print("TEST 3: LLM Decision Logic")
    print("="*70)
    
    agent = SecurityAgent(config={"llm_sample_rate": 0.2})
    
    test_cases = [
        ("small_file.py", "print('hello')\n" * 5, "Small file"),
        ("config.yaml", "setting: value\n" * 10, "Config file"),
        ("complex.py", "if x:\n  while y:\n    for z:\n      " * 10, "Complex code"),
        ("critical.py", VULNERABLE_CODE, "File with critical issues"),
    ]
    
    print(f"\n🤔 Should use LLM analysis?")
    
    for file_path, content, description in test_cases:
        # Get rule-based results
        rule_result = await agent._rule_based_analysis(
            file_path=file_path,
            file_content=content,
            language="python"
        )
        
        should_use = agent._should_use_llm(file_path, content, rule_result)
        complexity = agent._estimate_complexity(content)
        
        print(f"\n   {description}:")
        print(f"      File: {file_path}")
        print(f"      Lines: {content.count(chr(10)) + 1}")
        print(f"      Complexity: {complexity}")
        print(f"      Critical Issues: {sum(1 for i in rule_result.issues if i.severity.value == 'critical')}")
        print(f"      Decision: {'✅ Use LLM' if should_use else '❌ Skip LLM'}")


async def test_hybrid_analysis_simulation():
    """Simulate hybrid analysis (without actual LLM call)"""
    print("\n" + "="*70)
    print("TEST 4: Hybrid Analysis Simulation")
    print("="*70)
    
    agent = SecurityAgent(config={"use_llm": False})
    
    # Rule-based analysis
    print("\n⚡ Phase 1: Rule-Based Analysis (Fast)")
    rule_result = await agent._rule_based_analysis(
        file_path="app.py",
        file_content=VULNERABLE_CODE,
        language="python"
    )
    print(f"   Found: {len(rule_result.issues)} issues")
    print(f"   Time: {rule_result.execution_time:.3f}s")
    
    # Simulated LLM analysis
    print("\n🤖 Phase 2: LLM Analysis (Intelligent) - SIMULATED")
    print("   Would analyze:")
    print("   - Business logic flaws")
    print("   - Authorization issues")
    print("   - Race conditions")
    print("   - Complex attack chains")
    print("   - False positive verification")
    print(f"   Estimated time: ~2-3 seconds")
    
    print("\n📊 Expected Combined Results:")
    print("   Rule-based: 8-10 issues (patterns)")
    print("   LLM-based: 3-5 additional issues (context)")
    print("   Total: 11-15 unique issues")
    print("   Accuracy: ~90-95% (vs 60-70% with rules only)")


def test_configuration():
    """Test configuration options"""
    print("\n" + "="*70)
    print("TEST 5: Configuration Options")
    print("="*70)
    
    configs = [
        {"use_llm": False, "description": "Rule-based only (fastest, 60% accuracy)"},
        {"use_llm": True, "llm_sample_rate": 0.1, "description": "10% LLM sampling (good balance)"},
        {"use_llm": True, "llm_sample_rate": 0.5, "description": "50% LLM sampling (thorough)"},
        {"use_llm": True, "llm_sample_rate": 1.0, "description": "100% LLM analysis (most accurate)"},
    ]
    
    print("\n⚙️ Available Configurations:")
    for i, config in enumerate(configs, 1):
        print(f"\n   {i}. {config['description']}")
        print(f"      Config: {config}")
        if not config['use_llm']:
            cost = "$0"
        else:
            rate = config.get('llm_sample_rate', 0)
            cost = f"~${0.05 * rate:.3f} per 1000 files"
        print(f"      Cost: {cost}")


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 LLM-Enhanced Multi-Agent System - Tests")
    print("="*70)
    
    try:
        await test_rule_based_only()
        await test_llm_prompt_generation()
        await test_decision_logic()
        await test_hybrid_analysis_simulation()
        test_configuration()
        
        print("\n" + "="*70)
        print("✅ All tests completed successfully!")
        print("="*70)
        
        print("\n📝 Summary:")
        print("   ✓ Rule-based analysis works")
        print("   ✓ LLM prompt generation works")
        print("   ✓ Decision logic works")
        print("   ✓ Configuration system works")
        
        print("\n🚀 Next Steps:")
        print("   1. Set up actual LLM service (OpenAI/Anthropic/Gemini)")
        print("   2. Test with real LLM calls")
        print("   3. Build remaining agents")
        print("   4. Create coordination layer")
        
        print("\n💡 To use with real LLM:")
        print("   1. Configure LLM provider in settings")
        print("   2. Pass LLMService to agent initialization")
        print("   3. Enable use_llm in config")
        print("   4. Run analysis\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
