# sdnd-dev

[Japanese README (README.md)](README.md)

An autonomous software improvement framework powered by multi-agent AI.
Sister project of [sdnd-theater](https://github.com/piperendervt-glitch/sdnd-theater).

## Features

- Three-agent architecture: Architect / Implementer / Reviewer
- Safety Constitution as an automatic guardrail
- AST-based + test-case-based benchmarks (51 tasks)
- RSI (Recursive Self-Improvement) cycle support
- HumanEval-style tasks for code generation evaluation

## Requirements

- Python 3.x (conda recommended)
- Ollama (qwen2.5:3b)
- sdnd-theater (linked via `pip install -e`)

## Quick Start

```bash
# 1. Install sdnd-theater
pip install -e ../sdnd-theater

# 2. Start Ollama
ollama serve

# 3. Run a development session
python sdnd_dev/dev_session.py --task "Write a script that reads a CSV and aggregates data"

# 4. Run benchmarks
python -m benchmarks.run_benchmark --all

# 5. Run RSI cycles
python -m benchmarks.rsi_benchmark --cycles 5
```

## Benchmark Results (as of March 2026)

### Overall Scores

| Metric | Value |
|--------|-------|
| Total tasks | 51 (35 refactoring + 8 HumanEval + 8 HumanEval-Pure) |
| Average improvement | +0.73 (from 0.20 baseline) |
| Perfect score rate | 38/51 (74.5%) |
| Model | qwen2.5:3b (3B parameters) |

### HumanEval (Code Generation)

Evaluated on 16 HumanEval easy-to-medium problems.

| Evaluation mode | Tasks | pass@1 |
|-----------------|-------|--------|
| With examples (T36-T43) | 8 | 100% (8/8 perfect) |
| Without examples / pure (T44-T51) | 8 | 87.5% (7/8 perfect) |
| **Total** | **16** | **93.8% (15/16 perfect)** |

**Note:** 87.5% pass@1 without any examples is notably high for a 3B model. Typical 3B models score 20-40% on HumanEval pass@1.

#### HumanEval-Pure Breakdown (no examples)

| ID | Task | Score | Tests passed |
|----|------|-------|-------------|
| T44 | Bracket matching | 1.00 | 6/6 |
| T45 | Roman numeral to integer | 1.00 | 6/6 |
| T46 | Maximum subarray sum | 1.00 | 5/5 |
| T47 | Merge sorted lists | 1.00 | 5/5 |
| T48 | Matrix transpose | 1.00 | 4/4 |
| T49 | String compression | 0.36 | 1/5 |
| T50 | Primality test | 1.00 | 6/6 |
| T51 | Word frequency count | 1.00 | 5/5 |

T49 failure: The model ignores the "always append count even if 1" rule. A known 3B model limitation.

### Reproducible Results (Pure Execution)

HumanEval-Pure (no examples) results are publicly available.

- Tasks: 8
- pass@1: 87.5% (7/8 perfect)
- Model: qwen2.5:3b (no Claude Code involvement)
- Report: [proofs/human-eval-pure-results.md](proofs/human-eval-pure-results.md)
- Raw logs: [proofs/human-eval-pure-logs/](proofs/human-eval-pure-logs/)

To reproduce:
```bash
git clone https://github.com/piperendervt-glitch/sdnd-dev.git
cd sdnd-dev
pip install -e ../sdnd-theater  # requires ollama
ollama run qwen2.5:3b
python -m benchmarks.run_benchmark --task 44 45 46 47 48 49 50 51
```

### Score Progression (5 Generations)

| Generation | Description | Avg score |
|------------|-------------|-----------|
| Gen1 | Phase 0.5 baseline | 0.67 |
| Gen2 | Scoring accuracy improvement | 0.71 |
| Gen3 | Task-specific prompt tuning | 0.86 |
| Gen4 | Unified AST-based evaluation | 0.81 |
| Gen5 | Task 4 variance mitigation | 0.85 |

### Per-Task Scores (51 Tasks)

#### Core Tasks (T1-T25)

| ID | Task | After | Improvement |
|----|------|-------|-------------|
| T1 | Add docstrings | 1.00 | +0.80 |
| T2 | Bug fix | 0.86 | +0.66 |
| T3 | Loop optimization | 1.00 | +0.80 |
| T4 | Variable renaming | 1.00 | +0.80 |
| T5 | Error handling | 0.86 | +0.66 |
| T6 | PEP 8 compliance | 0.85 | +0.65 |
| T7 | Type hints | 1.00 | +0.80 |
| T8 | Function length limit | 1.00 | +0.80 |
| T9 | Security vulnerability fix | 0.60 | +0.40 |
| T10 | Unit test generation | 1.00 | +0.80 |
| T11 | JSON log formatting | 1.00 | +0.80 |
| T12 | Dynamic log level | 0.55 | +0.35 |
| T13 | Import cleanup | 0.35 | +0.15 |
| T14 | Config string parser | 0.80 | +0.60 |
| T15 | Class to functions | 1.00 | +0.80 |
| T16 | Ternary operator | 1.00 | +0.80 |
| T17 | argparse adoption | 1.00 | +0.80 |
| T18 | try-except with defaults | 1.00 | +0.80 |
| T19 | Generator conversion | 1.00 | +0.80 |
| T20 | Decorator extraction | 1.00 | +0.80 |
| T21 | Dict comprehension | 1.00 | +0.80 |
| T22 | Guard clause (early return) | 1.00 | +0.80 |
| T23 | Property decorator | 0.80 | +0.60 |
| T24 | Log format customization | 1.00 | +0.80 |
| T25 | enumerate conversion | 1.00 | +0.80 |

#### Theater / RP Tasks (T26-T28) -- 100% perfect

| ID | Task | After | Improvement |
|----|------|-------|-------------|
| T26 | Scenario template generator | 1.00 | +0.80 |
| T27 | Character config parser | 1.00 | +0.80 |
| T28 | Dialogue formatter | 1.00 | +0.80 |

#### Practical / Everyday Tasks (T29-T32)

| ID | Task | After | Improvement |
|----|------|-------|-------------|
| T29 | CSV to dict conversion | 1.00 | +0.80 |
| T30 | Date format unification | 1.00 | +0.80 |
| T31 | Retry decorator | 0.80 | +0.60 |
| T32 | Validation function | 1.00 | +0.80 |

#### Creativity / Human-like Tasks (T33-T35)

| ID | Task | After | Improvement |
|----|------|-------|-------------|
| T33 | Error message improvement | 1.00 | +0.80 |
| T34 | Greeting generator | 0.85 | +0.65 |
| T35 | Help text improvement | 0.65 | +0.45 |

#### HumanEval with Examples (T36-T43)

| ID | Task | After | Improvement |
|----|------|-------|-------------|
| T36 | Two Sum | 1.00 | +0.80 |
| T37 | FizzBuzz | 1.00 | +0.80 |
| T38 | Palindrome check | 1.00 | +0.80 |
| T39 | Fibonacci | 1.00 | +0.80 |
| T40 | List flattening | 1.00 | +0.80 |
| T41 | Vowel count | 1.00 | +0.80 |
| T42 | Deduplicate (order-preserving) | 1.00 | +0.80 |
| T43 | Greatest common divisor | 1.00 | +0.80 |

#### HumanEval-Pure / No Examples (T44-T51)

| ID | Task | After | Improvement |
|----|------|-------|-------------|
| T44 | Bracket matching | 1.00 | +0.80 |
| T45 | Roman numeral to integer | 1.00 | +0.80 |
| T46 | Maximum subarray sum | 1.00 | +0.80 |
| T47 | Merge sorted lists | 1.00 | +0.80 |
| T48 | Matrix transpose | 1.00 | +0.80 |
| T49 | String compression | 0.36 | +0.16 |
| T50 | Primality test | 1.00 | +0.80 |
| T51 | Word frequency count | 1.00 | +0.80 |

| | | | |
|----|------|-------|-------------|
| **Average** | **51 tasks** | | **+0.73** |

### Continuous Cycle Stability

Confirmed flat stability over 10+ consecutive cycles.

```
10-cycle run (35 tasks): avg +0.68 (range +0.57 to +0.72)
 8-cycle run (15 tasks): avg +0.66
```

- No performance degradation over 18+ cycles
- Agent personality (Koma) remains consistent throughout

## Key Design Decisions

- **Lightweight Safety Constitution:** 98% reduction in injected constitution text for 3B model compatibility
- **Approval UI + human delegation:** Reviewer defers ambiguous decisions to the human operator
- **Task-type hints:** Category-specific system prompt optimization (10 categories)
- **Dual HumanEval tracks:** Both with-examples and without-examples tracks to measure raw implementation ability

## Honest Assessment

- Maintaining +0.73 average across 51 tasks with a 3B model is **uncommon** for a solo project.
- Compared to enterprise/lab-scale RSI systems (70B+ models, hundreds to thousands of tasks), this project is smaller in task scale, model scale, and cycle count.
- Unique strength: A "human-aligned" design (voluntary confirmation requests + approval UI) pursuing the direction of **"AI that builds trust."**

## Directory Structure

```
sdnd-dev/
├── sdnd_dev/                      # Main module
│   ├── __init__.py
│   ├── agents.py                  # Multi-agent setup (Architect/Implementer/Reviewer)
│   ├── constitution.md            # Safety Constitution (Markdown source)
│   ├── dev_session.py             # Development session entry point
│   └── sandbox.py                 # Code execution sandbox
├── core/                          # Core functionality
│   ├── __init__.py
│   └── safety_constitution.py     # Safety Constitution (programmatic injection)
├── benchmarks/                    # Benchmarks
│   ├── __init__.py
│   ├── minimal_benchmark.py       # Task definitions + AST-based scoring (51 tasks)
│   ├── run_benchmark.py           # Benchmark runner (--repeat support)
│   └── rsi_benchmark.py           # RSI cycle runner + proofs output
├── proofs/                        # RSI cycle evidence (auto-generated)
│   └── genN_TIMESTAMP/
│       ├── scores.json            # Per-task scores
│       ├── prompts_used.txt       # System prompts used
│       ├── constitution_log.txt   # Safety Constitution compliance check
│       ├── summary.md             # Before/after comparison
│       └── generated_code/        # Generated code per task
├── sessions/                      # Session logs (gitignored)
│   ├── dev_sessions/
│   ├── benchmark_logs/
│   ├── rsi_logs/
│   └── sandbox_work/
├── task_pool.json                 # Task pool definitions (51 tasks)
├── .gitignore
├── .env.example
└── README.md
```

## Dependencies

- **sdnd-theater**: Provides the LLM backend (OllamaBackend)
- Future plan: Extract OllamaBackend into a standalone package (sdnd-llm)

## Agent Personality: "Koma"

All agents share a common personality called "Koma" -- a slightly clumsy but earnest AI.
Inspired by Tachikoma/Fuchikoma from Ghost in the Shell, though this is an original character, not a derivative.

Traits:
- When uncertain, honestly says: "I'm not quite sure about this... could you check?"
- After a mistake, recovers with: "I'm sorry... I'll do better next time."
- The Safety Constitution is non-negotiable.

## Koma Team Achievements

- Average improvement of +0.73 across 51 tasks
- 38/51 perfect scores (HumanEval pass@1 = 93.8%)
- Theater/RP tasks: 100% perfect score rate
- 18+ continuous cycles with flat stability confirmed
- Koma's voice: "I'm a bit worried about this part... could you take a look?"

## License

MIT
