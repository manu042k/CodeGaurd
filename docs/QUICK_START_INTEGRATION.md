# 🚀 CodeGuard Integration - Quick Start Guide

## Overview

CodeGuard integrates GitHub repository cloning with multi-agent code analysis to provide comprehensive security and quality reports.

---

## 🎯 Quick Start (5 Minutes)

### 1. Start the Services

```bash
cd /Users/manu042k/Documents/CodeGaurd
docker-compose up -d
```

### 2. Test the Integration

```bash
# Run the workflow test
docker-compose exec backend python test_workflow_simple.py
```

### 3. Use the API

```bash
curl -X POST http://localhost:8000/api/v1/repository-analysis/analyze \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": 123456,
    "shallow_clone": true,
    "use_llm": false,
    "enabled_agents": ["security", "dependency"]
  }'
```

---

## 📡 API Endpoints

### POST /api/v1/repository-analysis/analyze

Clone and analyze a GitHub repository.

**Request:**

```json
{
  "repository_id": 123456,
  "shallow_clone": true,
  "use_llm": false,
  "enabled_agents": ["security", "dependency"]
}
```

**Response:**

```json
{
  "status": "success",
  "repository": {
    "name": "repo-name",
    "full_name": "user/repo-name",
    "url": "https://github.com/user/repo-name"
  },
  "clone": {
    "success": true,
    "duration": 2.5,
    "size_mb": 15.3
  },
  "analysis": {
    "files_analyzed": 47,
    "total_issues": 5,
    "summary": {
      "overall_score": 85,
      "grade": "B+",
      "by_severity": {
        "high": 2,
        "medium": 3
      }
    }
  }
}
```

---

## 🔧 Configuration

### Enable/Disable Agents

```python
{
  "enabled_agents": [
    "security",         # Security vulnerabilities
    "dependency",       # Dependency analysis
    "code_quality",     # Code quality issues
    "performance",      # Performance problems
    "best_practices"    # Best practice violations
  ]
}
```

### Clone Options

```python
{
  "shallow_clone": true,   # Faster, less history
  "shallow_clone": false   # Full history
}
```

### LLM Analysis

```python
{
  "use_llm": true    # Enable AI-powered analysis
}
```

---

## 🧪 Testing

### Run All Tests

```bash
# Integration test
docker-compose exec backend python test_integration.py

# Simplified workflow test
docker-compose exec backend python test_workflow_simple.py

# Coordinator test
docker-compose exec backend python test_coordinator.py

# Agent tests
docker-compose exec backend python test_all_agents.py
```

---

## 📊 Understanding Results

### Overall Score

- **90-100**: A+ (Excellent)
- **80-89**: A (Very Good)
- **70-79**: B (Good)
- **60-69**: C (Fair)
- **50-59**: D (Poor)
- **0-49**: F (Critical Issues)

### Issue Severity

- 🔴 **Critical**: Immediate action required
- 🟠 **High**: Should be fixed soon
- 🟡 **Medium**: Should be addressed
- 🔵 **Low**: Consider fixing
- ⚪ **Info**: Informational

---

## 🛠️ Common Tasks

### Analyze a Public Repository

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/repository-analysis/analyze",
    json={
        "repository_id": 123456,
        "shallow_clone": True,
        "enabled_agents": ["security", "dependency"]
    }
)

report = response.json()
```

### Analyze with Progress Tracking

```python
from app.services.repository_analysis_service import RepositoryAnalysisService

def on_progress(progress):
    print(f"{progress['progress_percent']:.1f}% complete")

service = RepositoryAnalysisService(github_service, config)
service.add_progress_callback(on_progress)
report = await service.clone_and_analyze(repo)
```

### Custom Analysis Configuration

```python
from app.coordinator import AnalysisConfig

config = AnalysisConfig(
    max_concurrent_files=20,      # More parallelism
    timeout_per_file=60,           # Longer timeout
    use_llm=True,                  # Enable AI
    enabled_agents=["security", "dependency", "code_quality"]
)
```

---

## 🐛 Troubleshooting

### Issue: Clone Fails with Authentication Error

**Solution:** Check GitHub token permissions

```bash
# Test token
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user
```

### Issue: Analysis Times Out

**Solution:** Increase timeout or reduce concurrency

```python
AnalysisConfig(
    max_concurrent_files=5,    # Reduce from 10
    timeout_per_file=60        # Increase from 30
)
```

### Issue: Out of Disk Space

**Solution:** Cleanup is automatic, but you can manually clean:

```bash
# Remove temp directories
docker-compose exec backend find /tmp -name "codeguard_*" -type d -exec rm -rf {} +
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── agents/              # Security, Dependency, etc.
│   ├── coordinator/         # Analysis orchestration
│   ├── services/
│   │   ├── github_service.py           # GitHub cloning
│   │   └── repository_analysis_service.py  # Integration
│   ├── routers/
│   │   └── repository_analysis.py      # API endpoints
│   └── utils/
│       └── file_scanner.py             # Recursive scanning
└── test_workflow_simple.py             # Integration test
```

---

## 🔐 Security Considerations

1. **GitHub Tokens**: Store securely, use minimal permissions
2. **Public Repos**: Can be cloned without authentication
3. **Private Repos**: Require valid access token
4. **Temp Files**: Automatically cleaned up after analysis
5. **Rate Limits**: GitHub API has rate limits, consider caching

---

## 📈 Performance Tips

1. **Use Shallow Clones**: 5-10x faster for large repos
2. **Limit Agents**: Only enable agents you need
3. **Increase Concurrency**: For powerful servers
4. **Cache Results**: Store analysis results in database
5. **Incremental Analysis**: Only analyze changed files (future)

---

## 🎯 Next Steps

1. **Frontend Integration**: Build UI for repository analysis
2. **Database Storage**: Persist analysis results
3. **Webhooks**: Trigger analysis on git push
4. **Scheduled Scans**: Regular repository scanning
5. **Advanced Agents**: Add more analysis capabilities

---

## 📚 Additional Resources

- **INTEGRATION_SUMMARY.md** - Detailed integration docs
- **LLM_HYBRID_ARCHITECTURE.md** - Agent architecture
- **COORDINATOR_IMPLEMENTATION_COMPLETE.md** - Coordinator details
- **API Documentation** - OpenAPI docs at `/docs`

---

## 💬 Support

Need help? Check:

1. Test files for examples
2. Documentation in `/docs`
3. API documentation at http://localhost:8000/docs
4. Source code comments

---

_Quick Start Guide - Last Updated: October 6, 2025_
