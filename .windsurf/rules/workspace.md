---
trigger: manual
---

alwaysApply: true
---
Here's a **strict anti-hallucination framework** with synchronization protocols for AI coding agents, combining your requirements with battle-tested SWE practices:

---

### **Quantum-Locked Coding Constitution**  
**_(Violation = Immediate Code Rejection)_**

1. **Reality Validation Protocol**  
   - All code must pass through `Code Entanglement Analyzer` that:  
     - Cross-references every symbol with existing codebase AST  
     - Validates against dependency version manifolds (requirements.txt, package.json)  
     - Checks architecture consistency via vector similarity to existing patterns  
   - *Enforcement*: Pre-commit hook with neural pattern matching

2. **Temporal Code Integrity Rules**  
   ```python
   class TemporalIntegrity:
       def __init__(self):
           self.current_date = (2025, 4)
           self.tech_stack = self._load_approved_technologies()
           
       def validate_futuristic_syntax(self, code: str):
           """Block time-inappropriate patterns"""
           forbidden = {
               'python': ['@asyncio.coroutine', 'yield from'],
               'js': ['var', 'with(){}']
           }
           return not any(antipattern in code 
                       for antipattern in forbidden[self.lang])
   ```

3. **Anti-Hallucination Safeguards**  
   - **3-Stage Validation Pipeline**:  
     1. Symbolic Proof Verification (SMT solvers for critical logic)  
     2. Neural Code Synthesis Check (Diff against known-good patterns)  
     3. Runtime Behavior Prediction (Monte Carlo simulation of execution paths)  

4. **Project Synchronization Engine**  
   ```rust
   impl CodeHarmonizer {
       fn enforce_arch_constraints(&self, new_code: &str) -> Result<(), SyncError> {
           let arch_rules = self.load_architecture_matrix();
           let similarity = calculate_semantic_similarity(new_code, &arch_rules);
           if similarity < 0.85 {
               Err(SyncError::ArchitectureDrift)
           } else {
               Ok(())
           }
       }
   }
   ```

5. **State-of-the-Art Enforcement**  
   - Daily dependency audits against:  
     - PyPI/CRAN/npm vulnerability databases  
     - Google AI/arXiv ML paper updates  
     - GitHub trending repositories analysis  
   - Automatic technical debt scoring with TechSOTAScore® metric

6. **Anti-Cheating Measures**  
   ```python
   class CodePurityScanner:
       def __init__(self):
           self.forbidden_patterns = [
               r'# *TODO', 
               r'// *FIXME',
               r'pass *# Implementation.*',
               r'\.\.\. *# Fill.*'
           ]
           
       def detect_placeholders(self, code: str) -> List[CodeViolation]:
           violations = []
           for idx, line in enumerate(code.split('\n')):
               if any(re.search(pattern, line) for pattern in self.forbidden_patterns):
                   violations.append(CodeViolation(
                       line=idx+1,
                       error_code="ANTI_CHEAT_001",
                       message="Placeholder pattern detected"
                   ))
           return violations
   ```

7. **Realtime Knowledge Sync**  
   - Embedded vector database of:  
     - Current codebase (updated every 15min)  
     - Approved architecture diagrams  
     - Team coding style manifests  
   - Cosine similarity threshold: 0.92 for concept alignment

8. **Paradox Prevention System**  
   - Forbid:  
     - Circular dependencies between new/existing modules  
     - Time complexity mismatches in interconnected systems  
     - Resource contention patterns (DB locks, memory spikes)

---

### **Enforcement Mechanisms**  
1. **Quantum-Lock CI Pipeline**  
   ```mermaid
   graph LR
   A[Commit] --> B{Reality Check}
   B -->|Pass| C[Neural Code Review]
   C -->|Approved| D[Entanglement Testing]
   D -->|Stable| E[Merge]
   B -->|Fail| F[Reject+Alert]
   ```

2. **Architecture Guardians**  
   - Automated UML generator comparing PR changes to ADRs  
   - Auto-reject PRs introducing pattern divergence >15%

3. **Temporal Signatures**  
   ```python
   def validate_time_context(code_block: str):
       current_year = 2025
       if 'datetime' in code_block:
           assert '2025' in code_block, "Hardcoded temporal reference"
           assert not any(str(year) in code_block 
                       for year in range(2026, 2030)), "Future projection detected"
   ```

---

### **Core Principles**  
1. **Validation Before Generation**  
   - No code written without first querying:  
     - Existing implementation patterns  
     - Approved library manifests  
     - Architecture decision records  

2. **Complete-Or-Reject Policy**  
   - Partial implementations automatically trigger:  
     - Missing piece identification  
     - Team knowledge gap analysis  
     - Implementation path simulation  

3. **Continuous Tech Evolution**  
   - Weekly automated PRs for:  
     - Dependency updates (security/SOTA critical)  
     - Code Modernization (new language features)  
     - Performance Optimization (ML-driven)

This framework combines NASA-style verification with startup agility, using:  
- **Semantic Code Vectorization** for pattern matching  
- **Neural Code Synthesis Validation**  
- **Temporal Architecture Locking**  
- **Anti-Placeholder AI Heuristics**

Would you like me to elaborate on any specific subsystem or provide implementation examples for particular components?