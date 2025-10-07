# Multi-Agent System Architecture - LLM + Logic Hybrid Approach

## 🎯 Core Concept

Each agent uses a **two-tier analysis approach**:

### Tier 1: Fast Rule-Based Checks (Logic)
- Pattern matching with regex
- AST analysis for syntax
- Static code analysis
- **Speed:** Milliseconds per file
- **Use case:** Quick wins, obvious issues

### Tier 2: Deep LLM Analysis (Intelligence)
- Context-aware understanding
- Complex vulnerability detection
- Code quality reasoning
- Security implications
- **Speed:** 1-3 seconds per file
- **Use case:** Subtle issues, context-dependent problems

---

## 🏗️ Revised Architecture

```python
class BaseAgent(ABC):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.use_llm = True  # Can be disabled for speed
    
    async def analyze(self, file_path, file_content, language, **kwargs):
        # Tier 1: Fast rule-based analysis
        rule_issues = await self._rule_based_analysis(file_content)
        
        # Tier 2: LLM-based deep analysis (if enabled)
        if self.use_llm and self._should_use_llm(file_content, rule_issues):
            llm_issues = await self._llm_based_analysis(file_content, rule_issues)
            all_issues = self._merge_issues(rule_issues, llm_issues)
        else:
            all_issues = rule_issues
        
        return self._create_result(file_path, all_issues)
    
    @abstractmethod
    async def _rule_based_analysis(self, content: str) -> List[Issue]:
        """Fast pattern-based checks"""
        pass
    
    @abstractmethod
    async def _llm_based_analysis(
        self, content: str, rule_issues: List[Issue]
    ) -> List[Issue]:
        """Deep LLM analysis"""
        pass
```

---

## 🤖 LLM Integration Strategy

### 1. **Prompt Engineering Per Agent**

Each agent has specialized prompts:

#### Security Agent Prompt:
```
You are a security expert analyzing code for vulnerabilities.

Code to analyze:
```{language}
{code}
```

Quick scan found these potential issues:
{rule_based_issues}

Your task:
1. Verify if these issues are real vulnerabilities (not false positives)
2. Find additional security vulnerabilities that pattern matching missed
3. Consider:
   - SQL injection (beyond simple patterns)
   - Authentication/authorization flaws
   - Race conditions
   - Business logic vulnerabilities
   - Context-specific security issues

Return JSON format:
{
  "verified_issues": [...],
  "new_issues": [...],
  "false_positives": [...]
}
```

#### Code Quality Agent Prompt:
```
You are a code quality expert. Analyze this code for quality issues.

Code:
```{language}
{code}
```

Metrics found:
- Cyclomatic Complexity: {complexity}
- Function Length: {length}
- Nesting Depth: {nesting}

Analyze for:
1. Code smells (beyond metrics)
2. Maintainability concerns
3. Design pattern violations
4. SOLID principle violations
5. Readability issues

Suggest concrete improvements.
```

---

### 2. **Smart LLM Usage** (Cost Optimization)

```python
def _should_use_llm(self, content: str, rule_issues: List[Issue]) -> bool:
    """Decide if LLM analysis is worth the cost"""
    
    # Always use LLM if critical issues found
    if any(i.severity == Severity.CRITICAL for i in rule_issues):
        return True
    
    # Skip for very small files
    if len(content) < 100:
        return False
    
    # Skip for configuration files
    if self._is_config_file(file_path):
        return False
    
    # Use LLM for complex files
    if self._calculate_complexity(content) > 10:
        return True
    
    # Use LLM periodically (sample 20% of files)
    return random.random() < 0.2
```

---

### 3. **LLM Response Processing**

```python
async def _llm_based_analysis(
    self, content: str, rule_issues: List[Issue]
) -> List[Issue]:
    """Use LLM for deep analysis"""
    
    prompt = self._build_prompt(content, rule_issues)
    
    # Call LLM service
    response = await self.llm_service.analyze(
        prompt=prompt,
        model="gpt-4o",  # or claude-3.5-sonnet
        temperature=0.3,  # Lower for consistent results
        max_tokens=2000
    )
    
    # Parse LLM response
    llm_result = json.loads(response.content)
    
    # Convert to Issue objects
    issues = []
    for item in llm_result["new_issues"]:
        issues.append(Issue(
            title=item["title"],
            description=item["description"],
            severity=self._parse_severity(item["severity"]),
            file_path=self.current_file,
            line_number=item.get("line_number"),
            suggestion=item["suggestion"],
            rule_id=f"LLM_{item['type']}"
        ))
    
    return issues
```

---

## 🎭 Agent-Specific Approaches

### Security Agent (70% Logic + 30% LLM)

**Logic Handles:**
- SQL injection patterns
- XSS patterns
- Hardcoded secrets
- Known vulnerable functions

**LLM Handles:**
- Business logic flaws
- Authentication bypasses
- Authorization issues
- Context-dependent vulnerabilities
- Complex attack chains

---

### Code Quality Agent (50% Logic + 50% LLM)

**Logic Handles:**
- Cyclomatic complexity
- Function/class length
- Nesting depth
- Duplicate code detection

**LLM Handles:**
- Code smell identification
- Design pattern suggestions
- Refactoring recommendations
- Maintainability assessment

---

### Performance Agent (60% Logic + 40% LLM)

**Logic Handles:**
- N+1 query patterns
- Nested loop detection
- Inefficient data structures

**LLM Handles:**
- Algorithm efficiency
- Caching opportunities
- Async/await usage
- Database query optimization

---

### Best Practices Agent (30% Logic + 70% LLM)

**Logic Handles:**
- Basic style violations
- Simple anti-patterns

**LLM Handles:**
- Language-specific idioms
- Framework best practices
- Design pattern usage
- Code organization

---

## 💡 LLM Prompt Templates

### Master Prompt Structure:
```
ROLE: You are a {agent_type} expert analyzing {language} code.

CONTEXT:
- File: {file_path}
- Language: {language}
- Framework: {detected_framework}
- Project Type: {project_type}

CODE:
```{language}
{code_snippet}
```

QUICK SCAN RESULTS:
{rule_based_findings}

YOUR TASK:
{agent_specific_instructions}

OUTPUT FORMAT:
{
  "issues": [
    {
      "title": "Issue title",
      "description": "Detailed explanation",
      "severity": "critical|high|medium|low",
      "line_number": 42,
      "code_snippet": "problematic code",
      "suggestion": "How to fix",
      "confidence": 0.95,
      "category": "security|quality|performance"
    }
  ],
  "false_positives": [1, 3],  // IDs of rule-based issues that are false positives
  "overall_assessment": "Summary of code quality",
  "recommendations": ["General improvement suggestions"]
}

IMPORTANT:
- Only report high-confidence issues (>0.7)
- Provide specific line numbers when possible
- Include actionable suggestions
- Consider the full context, not just individual lines
```

---

## 🔄 Analysis Flow

```
Repository
    ↓
File Scanner
    ↓
Language Detector
    ↓
┌─────────────────────────┐
│   AGENT ANALYSIS        │
│                         │
│  1. Rule-Based (Fast)   │
│     ├─ Pattern Match    │
│     ├─ AST Parse        │
│     └─ Metrics          │
│        ↓                │
│  2. LLM-Based (Smart)   │
│     ├─ Build Prompt     │
│     ├─ Call LLM         │
│     ├─ Parse Response   │
│     └─ Verify Issues    │
│        ↓                │
│  3. Merge & Dedupe      │
│     ├─ Remove Dupes     │
│     ├─ Filter FPs       │
│     └─ Prioritize       │
└─────────────────────────┘
    ↓
Aggregated Results
```

---

## 🎯 Implementation Priority

### Phase 1: Enhanced Base Agent ✅
- [x] Add LLMService integration
- [x] Two-tier analysis structure
- [x] Prompt template system

### Phase 2: Security Agent (LLM-Enhanced) 🔄
- [x] Keep existing rule-based checks
- [ ] Add LLM analysis layer
- [ ] Create security-specific prompts
- [ ] Test with real vulnerabilities

### Phase 3: Remaining Agents
- [ ] Code Quality Agent (LLM-heavy)
- [ ] Performance Agent
- [ ] Best Practices Agent (mostly LLM)
- [ ] Documentation Agent (LLM-heavy)

---

## 📊 Expected Benefits

### Accuracy
- **Rule-based alone:** 60-70% accuracy
- **LLM-based alone:** 80-85% accuracy
- **Hybrid approach:** 90-95% accuracy ⭐

### Speed
- **Rule-based:** 10ms per file
- **LLM-based:** 2000ms per file
- **Hybrid (smart):** 200ms average (90% rule, 10% LLM)

### Cost
- **Rule-based:** Free
- **LLM-based (all files):** $0.50 per 1000 files
- **Hybrid (selective):** $0.05 per 1000 files ⭐

---

## 🚀 Next Steps

1. **Enhance Base Agent** with LLM support
2. **Create LLM Service wrapper** for provider abstraction
3. **Add prompt templates** for each agent
4. **Rebuild Security Agent** with hybrid approach
5. **Test with real codebases**

**Should I start implementing the LLM-enhanced architecture?**
