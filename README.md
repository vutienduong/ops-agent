# Ops Agent Lab

FastAPI application that simulates an autonomous IT infrastructure agent:

- monitor metrics
- diagnose anomalies from metrics + logs
- plan actions
- execute automation scripts
- verify incident resolution

## Architecture

- `planner` agent: builds action plan from anomalies
- `executor` agent: runs allowed shell automations
- `verifier` agent: validates post-execution metrics

Workflow is implemented with LangGraph in:
`app/agent/workflow.py`

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open API docs at:
`http://127.0.0.1:8000/docs`

## Run Example

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"incident":"Disk usage > 90%"}'
```

## Optional LLM RCA

Set `OPENAI_API_KEY` to enable LLM-assisted diagnosis. If not set,
the app uses deterministic rule-based diagnosis.

```bash
export OPENAI_API_KEY=your_key_here
```

## Tests

```bash
pytest -q
```
