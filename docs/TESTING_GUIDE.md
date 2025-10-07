# Quick Test Guide: Full Analysis Flow

## 🎯 Objective

Test that the complete analysis flow works: UI → Clone → Agents → LLM → Report

---

## ✅ Prerequisites

1. **Backend Running**

   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend Running**

   ```bash
   cd frontend
   npm run dev
   ```

3. **Environment Variables Set**

   ```bash
   # Backend (.env)
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   DATABASE_URL=postgresql://...
   SECRET_KEY=your_secret_key

   # Frontend (.env.local)
   NEXTAUTH_SECRET=your_secret
   GITHUB_ID=your_client_id
   GITHUB_SECRET=your_client_secret
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Logged in with GitHub**

---

## 🧪 Test Procedure

### Step 1: Navigate to Projects

```
1. Open http://localhost:3000
2. Login with GitHub
3. Go to Projects page
```

### Step 2: Run Analysis

```
1. Find any project in the list
2. Click "Run Analysis" button
3. Observe the notifications
```

### Step 3: Watch Console Logs

#### Frontend Console (Browser DevTools)

Look for these logs:

```
🚀 Starting multi-agent analysis for: <project-name>
📦 Repository ID: <repo-id>
🔗 GitHub URL: https://github.com/<user>/<repo>
📋 Flow: Clone repo → Run agents → LLM analysis → Generate report
✅ Analysis completed for: <project-name>
📊 Overall Score: XX/100
🔍 Agents Run: 5
```

#### Backend Console (Terminal)

Look for these logs:

```
INFO: Starting clone and analysis for <user>/<repo>
INFO: Cloning repository <user>/<repo>...
INFO: Clone completed in X.XXs (XX.XX MB, XXX commits)
INFO: Starting analysis of <user>/<repo>...
INFO: Analysis completed in X.XXs (XX issues found)
INFO: Complete analysis: XX files, XX issues, score: XX/100
INFO: Cleaning up cloned repository
```

### Step 4: Verify Results

```
1. You should be automatically redirected to /reports/{id}
2. Report should show:
   ✓ Overall score
   ✓ Results from 5 agents
   ✓ Issues categorized by severity
   ✓ Recommendations
```

---

## 📋 Success Indicators

### ✅ Frontend Indicators

1. **Notifications Appear**:

   - "🚀 Starting analysis for {project}..."
   - "🔄 Cloning repository and preparing analysis..."
   - "✅ Analysis completed! Viewing report..."

2. **Console Shows Flow**:

   - Starting message with project name
   - Repository ID and URL
   - Flow description
   - Completion with score
   - Agent count

3. **Status Changes**:
   - Project status → "analyzing"
   - Button text → "Analyzing..."
   - After completion → Redirect to report

### ✅ Backend Indicators

1. **Cloning Happens**:

   - Log: "Cloning repository..."
   - Log: "Clone completed in X.XXs"
   - Temporary directory created in /tmp

2. **Agents Run**:

   - Log: "Starting analysis of..."
   - Each agent logs start/completion
   - Parallel execution visible in timestamps

3. **LLM Calls (if enabled)**:

   - Look for LLM provider logs
   - API calls to OpenAI/Anthropic/etc.
   - Token usage logged

4. **Cleanup Occurs**:
   - Log: "Cleaning up cloned repository"
   - /tmp directory removed

### ✅ Report Page

1. **Data Present**:

   - Overall score (0-100)
   - 5 agent sections
   - Issues with file paths and line numbers
   - Severity badges (critical, high, medium, low)

2. **Agent Results**:
   - SecurityAgent findings
   - DependencyAgent findings
   - CodeQualityAgent findings
   - PerformanceAgent findings
   - BestPracticesAgent findings

---

## 🐛 Troubleshooting

### Issue: "Repository not found"

**Solution**: Make sure project has `github_repo_id` set. Check database:

```sql
SELECT id, name, github_repo_id FROM repositories;
```

### Issue: "Clone failed"

**Solution**:

- Check GitHub token is valid
- Verify network connectivity
- Check repository permissions
- Try with a public repository first

### Issue: "No agents run"

**Solution**:

- Check `enabled_agents` array in request
- Verify agent files exist in backend
- Check for import errors in backend logs

### Issue: "LLM not working"

**Solution**:

- Verify `use_llm: true` in request
- Check LLM API keys in environment
- Look for LLM provider errors in logs
- Try with `use_llm: false` first

### Issue: "Cleanup failed"

**Solution**:

- Check file permissions on /tmp
- Verify shutil import works
- Should be just a warning, not fatal

### Issue: "Frontend shows old data"

**Solution**:

- Clear browser cache
- Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- Check Network tab in DevTools
- Verify API response in Network tab

---

## 🔍 Detailed Verification

### 1. Check API Request

Open DevTools → Network tab → Filter XHR:

**Request to**: `POST /api/repository-analysis/analyze`

**Payload**:

```json
{
  "repository_id": 123,
  "shallow_clone": true,
  "use_llm": true,
  "enabled_agents": [
    "security",
    "dependency",
    "code_quality",
    "performance",
    "best_practices"
  ]
}
```

**Response** (should be):

```json
{
  "status": "success",
  "message": "Successfully analyzed user/repo",
  "report": {
    "repository": {...},
    "clone": {
      "success": true,
      "duration": 2.34,
      "size_mb": 15.6,
      "commit_count": 342
    },
    "analysis": {
      "files_analyzed": 87,
      "total_issues": 23,
      "summary": {
        "overall_score": 78,
        ...
      },
      "agents": {
        "security": {...},
        "dependency": {...},
        "code_quality": {...},
        "performance": {...},
        "best_practices": {...}
      }
    }
  }
}
```

### 2. Check File System

During analysis, verify clone exists:

```bash
# In another terminal
ls /tmp/codeguard_clone_*
```

After analysis, verify cleanup:

```bash
# Should return nothing
ls /tmp/codeguard_clone_*
```

### 3. Check Database

Verify analysis record (if saved):

```sql
SELECT * FROM analyses ORDER BY created_at DESC LIMIT 1;
```

### 4. Check Agent Outputs

Each agent should produce:

```json
{
  "agent_name": "security",
  "status": "completed",
  "score": 85,
  "summary": "Found 5 security issues",
  "findings": [
    {
      "type": "security",
      "severity": "high",
      "title": "Potential SQL Injection",
      "file_path": "app/queries.py",
      "line_number": 42,
      ...
    }
  ]
}
```

---

## 📊 Expected Timeline

For a typical repository (~100 files, ~10K LOC):

1. **Clone**: 2-5 seconds
2. **Security Agent**: 1-3 seconds
3. **Dependency Agent**: 0.5-2 seconds
4. **Code Quality Agent**: 2-5 seconds
5. **Performance Agent**: 1-3 seconds
6. **Best Practices Agent**: 1-3 seconds
7. **Aggregation**: < 1 second
8. **Cleanup**: < 1 second

**Total**: ~10-25 seconds

With LLM enabled, add:

- **LLM calls per agent**: 2-5 seconds each
- **Total with LLM**: 20-50 seconds

---

## 🎯 Test Matrix

| Test Case                      | Expected Result                   |
| ------------------------------ | --------------------------------- |
| Small public repo (< 10 files) | ✅ Completes in < 10s             |
| Medium repo (50-100 files)     | ✅ Completes in < 30s             |
| Large repo (> 500 files)       | ✅ Completes but may take 1-2 min |
| Private repo                   | ✅ Works with valid token         |
| Invalid repo ID                | ❌ Returns 404 error              |
| Network failure                | ❌ Returns clone error            |
| LLM enabled                    | ✅ Shows LLM insights             |
| LLM disabled                   | ✅ Shows rule-based only          |
| All agents enabled             | ✅ 5 agent results                |
| Subset of agents               | ✅ Only selected agents run       |

---

## 🚀 Quick Test Script

```bash
# Test backend endpoint directly
curl -X POST http://localhost:8000/api/repository-analysis/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "repository_id": 1,
    "shallow_clone": true,
    "use_llm": false,
    "enabled_agents": ["security", "dependency"]
  }'
```

Expected output:

```json
{
  "status": "success",
  "message": "Successfully analyzed ...",
  "report": {...}
}
```

---

## 📝 Test Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend is running on port 3000
- [ ] Logged in with GitHub
- [ ] At least one project exists
- [ ] Click "Run Analysis" button
- [ ] See "Starting analysis" notification
- [ ] Backend logs show clone activity
- [ ] Backend logs show agent execution
- [ ] Backend logs show cleanup
- [ ] Frontend redirects to report page
- [ ] Report shows all agent results
- [ ] Overall score is calculated
- [ ] Issues are displayed with details
- [ ] Can navigate back to projects

---

## ✅ Success!

If all the above works, the complete analysis flow is functioning correctly! 🎉

**The system is now**:

- ✅ Cloning repositories
- ✅ Running multi-agent analysis
- ✅ Calling LLMs (when enabled)
- ✅ Generating comprehensive reports
- ✅ Cleaning up automatically

---

## 📚 Next Steps

1. **Test with Different Repos**: Try various languages and sizes
2. **Enable LLM**: Test with `use_llm: true`
3. **Custom Agents**: Add agent configurations
4. **Export Reports**: Test report export features
5. **CI/CD Integration**: Set up automated scans

---

## 🆘 Need Help?

- Check [docs/ANALYSIS_FLOW.md](./ANALYSIS_FLOW.md) for detailed flow
- Review [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)
- Examine backend logs for errors
- Check frontend console for API issues
- Verify environment variables are set correctly
