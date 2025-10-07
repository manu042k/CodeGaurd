# 🎯 Quick Reference - Multi-Agent Code Analysis System

## 📁 Directory Structure

```
CodeGaurd/backend/app/
│
├── agents/                          # ✅ Analysis Agents
│   ├── __init__.py
│   ├── base_agent.py               # ✅ Base class (262 lines)
│   ├── security_agent.py           # ✅ Security checks (465 lines)
│   ├── dependency_agent.py         # 🔄 Next to build
│   ├── code_quality_agent.py       # ⏳ Pending
│   ├── performance_agent.py        # ⏳ Pending
│   ├── best_practices_agent.py     # ⏳ Pending
│   ├── test_coverage_agent.py      # ⏳ Pending
│   ├── code_style_agent.py         # ⏳ Pending
│   └── documentation_agent.py      # ⏳ Pending
│
├── coordinator/                     # ⏳ Analysis Orchestration
│   ├── __init__.py
│   ├── analysis_coordinator.py     # Runs all agents in parallel
│   └── result_aggregator.py        # Combines & prioritizes results
│
├── parsers/                         # ✅ Code Parsing
│   ├── __init__.py
│   └── language_detector.py        # ✅ 48 languages (265 lines)
│
├── utils/                           # ✅ Utilities
│   ├── __init__.py
│   ├── file_scanner.py             # ✅ Directory scanning (325 lines)
│   └── report_generator.py         # ⏳ HTML/JSON/PDF reports
│
└── config/                          # ✅ Configuration
    ├── __init__.py                  # ✅ ConfigManager (113 lines)
    ├── agent_config.yaml            # ✅ Agent settings
    └── rules.yaml                   # ✅ 100+ analysis rules
```

---

## 🔧 Core Classes

### BaseAgent (Abstract)

```python
from app.agents.base_agent import BaseAgent, Issue, Severity

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "MyAgent"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_languages(self) -> List[str]:
        return ["python", "javascript"]

    async def analyze(self, file_path, file_content, language, **kwargs):
        issues = []
        # ... your analysis logic ...
        return self._create_result(file_path, issues)
```

### Issue (Dataclass)

```python
issue = Issue(
    title="SQL Injection Vulnerability",
    description="Query uses string concatenation",
    severity=Severity.CRITICAL,  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    file_path="app/models.py",
    line_number=42,
    code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
    suggestion="Use parameterized queries",
    rule_id="SQL_INJECTION"
)
```

### AgentResult (Dataclass)

```python
result = AgentResult(
    agent_name="SecurityAgent",
    file_path="app/models.py",
    issues=[issue1, issue2],
    metrics={"total_issues": 2, "critical": 1},
    score=7.5,
    execution_time=0.123
)
```

---

## 🛠️ Utility Classes

### FileScanner

```python
from app.utils.file_scanner import FileScanner

scanner = FileScanner(
    exclude_patterns=["node_modules/**", "*.pyc"],
    max_file_size=10*1024*1024  # 10 MB
)

files = scanner.scan_directory("/path/to/repo")

for file in files:
    print(f"{file.relative_path} - {file.size} bytes")
```

### LanguageDetector

```python
from app.parsers.language_detector import LanguageDetector

language = LanguageDetector.detect_language("script.py")  # "python"
language = LanguageDetector.detect_language("app.tsx")    # "typescript"

# With content (for shebang detection)
content = "#!/usr/bin/env python3\nprint('hello')"
language = LanguageDetector.detect_language("script", content)  # "python"
```

### ConfigManager

```python
from app.config import get_config_manager

config = get_config_manager()

# Get agent config
agent_cfg = config.get_agent_config("security")
print(agent_cfg["enabled"])  # True

# Get rules
rules = config.get_rules_for_agent("security")
print(rules["sql_injection"])
```

---

## 📊 Completed Features

### ✅ Security Agent

Detects 10+ vulnerability types:

- SQL Injection
- XSS (Cross-Site Scripting)
- Hardcoded Secrets (passwords, API keys)
- Weak Cryptography (MD5, SHA1)
- Command Injection
- Path Traversal
- Insecure Deserialization
- Dangerous Functions (eval, exec)
- Python-specific issues
- JavaScript-specific issues

**Usage:**

```python
import asyncio
from app.agents.security_agent import SecurityAgent

async def analyze_code():
    agent = SecurityAgent()
    result = await agent.analyze(
        file_path="app.py",
        file_content=open("app.py").read(),
        language="python"
    )

    print(f"Score: {result.score}/10")
    print(f"Issues: {len(result.issues)}")

    for issue in result.issues:
        print(f"\n[{issue.severity.value}] {issue.title}")
        print(f"  Line {issue.line_number}: {issue.code_snippet}")
        print(f"  💡 {issue.suggestion}")

asyncio.run(analyze_code())
```

---

## 🎯 Agent Priority List

| Agent          | Priority | Status  | Estimated Time |
| -------------- | -------- | ------- | -------------- |
| Security       | Critical | ✅ Done | -              |
| Dependency     | Critical | 🔄 Next | 4-6h           |
| Code Quality   | High     | ⏳      | 4-6h           |
| Performance    | High     | ⏳      | 4-6h           |
| Best Practices | Medium   | ⏳      | 3-4h           |
| Test Coverage  | Medium   | ⏳      | 3-4h           |
| Code Style     | Low      | ⏳      | 2-3h           |
| Documentation  | Low      | ⏳      | 2-3h           |

---

## 🧪 Testing

### Run Component Tests

```bash
cd /Users/manu042k/Documents/CodeGaurd/backend
python3 test_agents.py
```

### Expected Output

```
✅ Language Detector: 48 languages supported
✅ Security Agent: 3/3 vulnerabilities detected
✅ All tests completed successfully!
```

---

## 📝 Configuration Files

### agent_config.yaml

```yaml
global:
  max_file_size_mb: 10
  timeout_seconds: 60
  parallel_execution: true

security:
  enabled: true
  severity_threshold: "low"
  rules: [sql_injection, xss_vulnerability, ...]

code_quality:
  enabled: true
  max_complexity: 10
  max_function_length: 50
```

### rules.yaml

```yaml
security_rules:
  sql_injection:
    severity: "critical"
    patterns:
      - "execute\\(.*?%.*?\\)"
      - "SELECT.*?\\+.*?FROM"
    languages: ["python", "java", "php"]
```

---

## 🚀 Common Commands

```bash
# Test everything
python3 test_agents.py

# Test specific agent
python3 -c "
import asyncio
from app.agents.security_agent import SecurityAgent

async def test():
    agent = SecurityAgent()
    result = await agent.analyze(
        'test.py',
        'password = \"secret123\"',
        'python'
    )
    print(result.to_dict())

asyncio.run(test())
"

# Scan a directory
python3 -c "
from app.utils.file_scanner import FileScanner
scanner = FileScanner()
files = scanner.scan_directory('.')
print(f'Found {len(files)} files')
"

# Detect language
python3 -c "
from app.parsers.language_detector import LanguageDetector
print(LanguageDetector.detect_language('app.tsx'))
"
```

---

## 🐛 Troubleshooting

### Import Errors

```bash
# Make sure you're in the backend directory
cd /Users/manu042k/Documents/CodeGaurd/backend

# Add to PYTHONPATH if needed
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Missing Dependencies

```bash
pip3 install -r requirements.txt
```

### Config File Not Found

```python
from pathlib import Path
config_dir = Path(__file__).parent / "app" / "config"
print(f"Looking for config in: {config_dir}")
```

---

## 📚 Resources

### Documentation Files

- `COMPLETE_ROADMAP.md` - Full implementation plan
- `AGENTS_IMPLEMENTATION_PLAN.md` - Detailed phase breakdown
- `AGENTS_PROGRESS.md` - Current progress tracking
- `AGENTS_SUMMARY.md` - What we've built so far

### Key Files to Reference

- `base_agent.py` - Template for new agents
- `security_agent.py` - Complete agent example
- `rules.yaml` - Pattern examples
- `test_agents.py` - Testing examples

---

## 💡 Tips

### Adding a New Agent

1. Create `agents/my_agent.py`
2. Extend `BaseAgent`
3. Implement `name`, `version`, `supported_languages`
4. Implement `async def analyze()`
5. Add rules to `rules.yaml`
6. Add config to `agent_config.yaml`
7. Test with sample code

### Adding New Rules

Edit `config/rules.yaml`:

```yaml
security_rules:
  my_new_rule:
    severity: "high"
    patterns:
      - "dangerous_pattern"
    languages: ["python"]
```

### Adjusting Scoring

Edit in `BaseAgent.calculate_score()`:

```python
severity_weights = {
    Severity.CRITICAL: 2.0,   # Adjust these
    Severity.HIGH: 1.5,
    Severity.MEDIUM: 1.0,
    Severity.LOW: 0.5,
}
```

---

## 🎓 Best Practices

1. **Always use async/await** for agents (enables parallel execution)
2. **Return AgentResult, don't raise exceptions** (errors go in result.error)
3. **Provide actionable suggestions** for every issue
4. **Use config files** for rules (avoid hardcoding patterns)
5. **Test with real code** samples from actual projects
6. **Log progress** for long-running operations
7. **Handle all file types gracefully** (skip unsupported languages)

---

## 📊 Current Statistics

```
✅ Completed: 1,700+ lines of production code
✅ Agents: 1/8 complete (Security)
✅ Languages: 48 supported
✅ Rules: 100+ defined
✅ Tests: All passing ✓
✅ Progress: ~20% overall
```

---

## 🚀 What's Next?

**Immediate Next Steps:**

1. Build Dependency Agent (checks for CVEs, outdated packages)
2. Build Code Quality Agent (complexity, code smells)
3. Build Coordination Layer (runs all agents in parallel)
4. Add API endpoints
5. Create frontend dashboard

**Choose your path:**

- A) Continue with Dependency Agent
- B) Build all agents first, then coordinator
- C) Build coordinator with just Security Agent
- D) Jump to API integration

---

**Ready to continue? Let me know which agent to build next!** 🎯
