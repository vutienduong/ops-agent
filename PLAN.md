# PLAN - Roadmap 1 Implementation

Updated: 2026-03-12 (Asia/Ho_Chi_Minh)

## Goal

Implement the next roadmap step in `README.md`:
- Real observability integration (Prometheus + Loki) with safe fallback to sample data.

## Scope

1. Add Prometheus integration for metrics fetch.
2. Add Loki integration for log fetch.
3. Keep backward compatibility with local sample files.
4. Add tests for integration behavior (success parse + fallback).
5. Update docs and run full test suite.

## Progress

- [x] Define roadmap-1 scope and implementation approach.
- [x] Implement Prometheus metrics source.
- [x] Implement Loki logs source.
- [x] Wire new settings/env vars into app bootstrap.
- [x] Add integration tests for Prometheus/Loki behavior.
- [x] Update README with configuration examples.
- [x] Run test suite and verify pass.
- [x] Auto commit roadmap-1 changes.

## Implemented Artifacts

- `app/agent/monitoring.py`
  Added `source=prometheus` mode, Prometheus query support, and fallback to sample JSON.
- `app/agent/logs.py`
  Added `source=loki` mode, Loki query-range support, and fallback to sample logs.
- `app/settings.py` + `app/main.py`
  Added env-based wiring for `METRICS_SOURCE`, `LOGS_SOURCE`, `PROMETHEUS_URL`, `LOKI_URL`, `LOKI_QUERY`.
- `tests/test_observability_integration.py`
  Added coverage for Prometheus/Loki success and fallback cases.
- `README.md`
  Added observability source configuration and roadmap status update.
