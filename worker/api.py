import os
import secrets

from fastapi import FastAPI, Header, HTTPException
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from .observability import (
    RequestSummaryMiddleware,
    flush_observability,
    init_observability,
)
from .store import jobs, submit_job

runtime_enabled = init_observability()
app = FastAPI()

if runtime_enabled:
    app.add_middleware(RequestSummaryMiddleware)
    FastAPIInstrumentor.instrument_app(app)


class JobIn(BaseModel):
    org_id: str
    kind: str
    payload: dict
    callback_url: str | None = None


def authenticate_org(authorization: str | None) -> str:
    """Authenticate an organisation using its configured API key."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key",
        )

    api_key = authorization.removeprefix("Bearer ").strip()

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    matched_org = None

    for name, configured_key in os.environ.items():
        if not name.startswith("ORG_API_KEY_") or not configured_key:
            continue

        if secrets.compare_digest(api_key, configured_key):
            if matched_org is not None:
                raise HTTPException(
                    status_code=500,
                    detail="Ambiguous API key configuration",
                )

            matched_org = name.removeprefix("ORG_API_KEY_").lower()

    if matched_org is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return matched_org


@app.post("/jobs")
def create_job(
    body: JobIn,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None),
):
    org_id = authenticate_org(authorization)

    # Never allow a caller to create jobs for another organisation.
    if org_id != body.org_id:
        raise HTTPException(
            status_code=403,
            detail="API key does not belong to the requested organisation",
        )

    return submit_job(
        org_id,
        body.kind,
        body.payload,
        idempotency_key,
    ).__dict__


@app.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    authorization: str | None = Header(default=None),
):
    job = next((item for item in jobs if item.id == job_id), None)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    org_id = authenticate_org(authorization)

    # Prevent one organisation from accessing another organisation's jobs.
    if org_id != job.org_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    return job.__dict__


@app.on_event("shutdown")
def flush_runtime():
    flush_observability()