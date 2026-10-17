# autter-demo-python-worker

A realistic broken Python background worker for testing [Autter](https://autter.dev) code review workflows.

This repository is part of the Autter Sandbox set. It models an async job-processing service with a FastAPI control API, an internal queue, retries, job status, webhook callbacks, idempotency keys, file processing, and mock LLM tasks. The code intentionally includes reliability, tenant-isolation, retry, file-safety, and prompt-handling issues.

## What this worker includes

- Python 3.11+
- FastAPI control routes
- Internal queue abstraction
- Pydantic request models
- Job submission and status lookup
- Worker processing loop
- File and LLM task mocks
- Pytest tests with expected-failure markers
- Challenge files with copy-paste AI editor prompts
- GitHub issue templates copied from the challenge files

## Quick start

```bash
git clone https://github.com/Autter-dev/autter-demo-python-worker.git
cd autter-demo-python-worker
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
cp -n .env.example .env
uvicorn --env-file .env worker.api:app --reload
```

The control API runs on `http://127.0.0.1:8000` by default.

## Autter Runtime

The FastAPI service exports OpenTelemetry traces, delta HTTP metrics, process
RSS, and request summaries to
`https://otlp.autter.dev`. Copy `.env.example` to `.env` if you do not already
have a local `.env`, then set
`AUTTER_RUNTIME_KEY` to a Runtime **server ingest key** in the local
environment; never commit the key. The service leaves telemetry disabled when
the variable is missing. Deployments should also set `GIT_SHA` to the full
deployed commit SHA and `DEPLOYMENT_ENVIRONMENT` to a stable environment name.

The worker emits always-sampled spans and operation summaries for processed
jobs; successful HTTP traces use the OpenTelemetry 1% default sampler. The `llm`
job kind is currently a local mock and does not make an external model call, so
it does not produce LLM-provider telemetry. There is no database, outbound
HTTP client, browser app, or external queue integration in this project.

Errors and request summaries appear after instrumented traffic reaches the
service; usage metrics are exported on a 60-second interval. See
[`worker/observability.py`](./worker/observability.py) for the local
instrumentation setup.

Example job submission:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: demo-1" \
  -d '{"org_id":"org_a","kind":"llm","payload":{"text":"summarize this"}}'
```

## Demo flow with Autter

1. Fork this repository or create a working branch.
2. Go to [autter.dev](https://autter.dev) and sign in.
3. Connect GitHub to Autter if it is not connected already.
4. Add this repository to the Autter installation or select it from the Autter dashboard.
5. Pick one challenge from the table below.
6. Open the matching file in `/challenges`.
7. Copy the "Suggested AI Editor Prompt" into Cursor, Claude Code, Copilot, Windsurf, or another AI code editor.
8. Let the editor implement a small fix and add or update tests.
9. Push the branch and open a pull request.
10. Let Autter review the PR, then address the findings it raises.

Good first demos are "Missing idempotency on job submission" and "File processing accepts unsafe paths" because they show Autter reviewing reliability and security issues in backend worker code.

## How the sandbox is designed

This repo is intentionally imperfect. Do not fix every issue on `main`. Each challenge is meant to create one focused PR.

Some tests use expected-failure markers. They document known broken behavior while keeping the baseline suite runnable for demo setup. When solving a challenge, convert or replace the relevant expected-failure coverage with passing regression tests.

## Challenges

| Challenge                                                                                                                    | Difficulty | Category      | Expected Autter review angle             |
| ---------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------- | ---------------------------------------- |
| [Retry logic reprocesses successful jobs](./challenges/retry-logic-reprocesses-successful-jobs.md)                           | High       | Reliability   | idempotency and state transition risk    |
| [Missing idempotency on job submission](./challenges/missing-idempotency-on-job-submission.md)                               | Medium     | Reliability   | duplicate side effects                   |
| [Webhook callback lacks signature verification](./challenges/webhook-callback-lacks-signature-verification.md)               | High       | Security      | SSRF-style risk and trust boundary issue |
| [Failed jobs lose original error context](./challenges/failed-jobs-lose-original-error-context.md)                           | Medium     | Observability | observability regression                 |
| [Worker processes jobs from wrong organization](./challenges/worker-processes-jobs-from-wrong-organization.md)               | High       | Authorization | tenant isolation bug                     |
| [File processing accepts unsafe paths](./challenges/file-processing-accepts-unsafe-paths.md)                                 | Medium     | Security      | path traversal risk                      |
| [Queue visibility timeout causes double processing](./challenges/queue-visibility-timeout-causes-double-processing.md)       | High       | Reliability   | concurrency risk                         |
| [LLM task prompt builder allows instruction injection](./challenges/llm-task-prompt-builder-allows-instruction-injection.md) | Medium     | AI safety     | prompt injection risk                    |

## Recommended PR description

```markdown
## What changed

- Fixed the selected challenge
- Added or updated regression coverage

## Why

- The previous implementation allowed the broken behavior described in `/challenges/...`

## Validation

- pytest

## Risks

- Note any behavior that Autter should review carefully
```

## Learn more

Visit [autter.dev](https://autter.dev) to learn more about Autter and connect this repository as a review demo.
