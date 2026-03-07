### Ý tưởng

Build **AI agent quản lý IT infrastructure nhỏ**.

Agent có thể:

- đọc log
- phát hiện anomaly
- suggest action
- chạy automation

Ví dụ workflow:

```
Prometheus metrics
      ↓
LLM Agent
      ↓
Root cause analysis
      ↓
Trigger automation
```

Tech stack:

```
FastAPI
LangGraph / CrewAI
OpenAI / Claude
Prometheus API
Grafana logs
```

Features:

```
Agent: "Server CPU spike"

1 analyze metrics
2 read logs
3 propose root cause
4 run fix script
```

Skill học được:

- agent architecture
- tool calling
- automation loop

---

Goal: simulate managed service provider automation.

Agent loop:

```
monitor
diagnose
plan
execute
verify
```

Example case:

```
Disk usage > 90%
```

Agent actions:

```
check logs
identify large files
cleanup
verify
```

Architecture:

```
planner agent
executor agent
verification agent
```

Tools:

```
shell commands
metrics API
log analysis
```

Outcome:

```
Autonomous infrastructure agent
```

---

## Architecture Diagram

```
              +-------------+
              | Monitoring  |
              | (metrics)   |
              +-------------+
                     |
                     v
               +-----------+
               | LLM Agent |
               +-----------+
                     |
      +--------------+--------------+
      |                             |
      v                             v
Planner Agent                Tool Executor
      |                             |
      v                             v
Plan actions                Run automation
      |                             |
      +-------------+---------------+
                    v
               Verifier Agent
                    |
                    v
              Incident resolved
```