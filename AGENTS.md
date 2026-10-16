# Stock Picker Project — Agent Rules

Boilerplate (admin.py, view stubs, template glue, connector skeletons, Celery
task stubs) is delegated to a local LLM (Ollama qwen2.5-coder:14b) via a small
dispatch/collect wrapper so the architecture-critical algorithms stay under
tight authorial control. The rules below codify that delegation protocol.

## Local-LLM Delegation Rules (MANDATORY — DO NOT DEVIATE)

### Dispatch
- ALWAYS use the `dispatch.sh` wrapper. NEVER call `pipeline.py` directly.
- `dispatch.sh <task-id> [--file path]... "prompt"`
- It auto-uses setsid, auto-sizes ctx/gpu, writes to `/tmp/ai-jobs/<task-id>.out`
- Dispatch ALL independent leaf tasks in ONE bash call

### Collection
- `collect.sh <task-id>` — polls, waits 90s, returns output or "STILL RUNNING"
- Do NOT check output files manually before 90s
- Do NOT poll repeatedly — call `collect.sh` once, it handles the wait

### Sizing
- NEVER pass --num-ctx or --num-gpu — let auto-tuning work
- Default --num-predict is 800 (max 1500) — larger values drop to slow tier
- Keep prompts under ~250 lines of context input

### Failure handling
- If a job fails: write the file yourself immediately. Do NOT debug the pipeline.
- If output is garbled: fix inline with `edit`. Do NOT re-investigate.
- Zero debugging. The pipeline works. If something breaks, you broke it.

### Parallelism protocol
- Dispatch ALL independent leaf tasks at once
- While waiting (90s), write architecture-critical files yourself
- Call `collect.sh` once, apply outputs, move on
- NEVER idle waiting for the LLM — always be writing something yourself

### What to delegate to the LLM
- `admin.py` files, view stubs, template boilerplate, connector skeletons, Celery task stubs
- Well-specified leaf tasks under ~800 tokens output

### What to write yourself
- Signal engine, composite scoring, RAG retrieval, expert runner, autotrader logic
- Architecture-critical files with domain-specific algorithms
- Files where context exceeds ~250 lines

## Project conventions
- Django 5 + HTMX + Postgres + pgvector + Celery + Ollama
- Project root: `.`
- Dark theme templates, Chart.js for charts, Plotly for heatmaps
- All prices in `DecimalField(max_digits=16, decimal_places=6)`
- Celery tasks in `tasks.py` per app, autodiscovered
- Templates extend `base.html`