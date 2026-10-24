import os
import threading
import time
from collections import defaultdict, deque
import uvicorn

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from core import pipeline

app = FastAPI(title="Explain My Error API")

# --- Basic protection: this endpoint runs code and spends LLM quota ---
RATE_LIMIT = 10          # requests
RATE_WINDOW = 60         # per this many seconds, per IP
MAX_CONCURRENT_RUNS = 3  # sandbox runs at the same time
_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()
_slots = threading.BoundedSemaphore(MAX_CONCURRENT_RUNS)


class ExplainRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=10_000)
    error: str = Field("", max_length=5_000)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")       # set by Render's proxy
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    with _hits_lock:
        q = _hits[ip]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too many requests, wait a minute and try again.")
        q.append(now)


@app.get("/health")
def health():
    """Hit this to wake the server up (Render's free tier sleeps when idle)."""
    return {"status": "ok"}


@app.post("/explain")
def explain_error(req: ExplainRequest, request: Request):
    # Plain `def` on purpose: FastAPI runs it in a thread pool, so the
    # blocking sandbox and LLM calls don't freeze the server.
    _check_rate_limit(_client_ip(request))

    if not _slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="Server is busy, try again in a few seconds.")
    try:
        return pipeline.run(req.code, req.error)
    finally:
        _slots.release()

if __name__ == "__main__":
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    uvicorn.run("main:app", port=8000, host="127.0.0.1", reload=reload_enabled)