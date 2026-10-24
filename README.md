# Explain My Error

> **Copilot fixes your error. Explain My Error proves the fix works and helps you stop repeating the mistake.**

Explain My Error is a learning-focused Python debugging assistant. Paste a Python script and, optionally, its traceback. The app runs the script to reproduce an error, extracts and classifies the traceback, asks an LLM for a plain-English explanation and complete corrected script, then runs the suggested fix before reporting whether it passed.

## The problem

Beginners often copy a traceback into an AI assistant, paste in the suggested fix, and move on. That workflow can fail in three ways:

- **The fix is never checked.** An AI can sound confident and still be wrong.
- **The cause is easy to forget.** The error goes away, but the same mistake can happen again.
- **The diagnosis may be a guess.** An assistant that only sees pasted text may miss what actually happened in the code.

## What Explain My Error does

1. Reproduces the error by running the submitted code, when possible.
2. Parses the traceback and classifies the error with project rules.
3. Uses Groq to explain the cause in plain English and suggest a complete corrected script.
4. Runs the suggested script and reports whether it completed successfully. If verification fails, it can ask for one revised fix.
5. Tracks error categories during the current Streamlit session, so users can see recurring patterns.

You can also provide a traceback when the error depends on an input, file, or environment that cannot be reproduced by running the snippet on the backend.

## Why it’s different

| Typical AI assistant | Explain My Error |
| --- | --- |
| Reads pasted text and guesses what happened | **Runs the code** and uses the reproduced traceback when available |
| Leaves parsing, diagnosis, and explanation entirely to the LLM | **Parses and classifies** the error with project code; the LLM focuses on explaining and suggesting a fix |
| Says “here’s a fix” without checking it | **Runs the suggested fix** and reports the verification result |
| Forgets recurring errors between prompts | Shows **mistake patterns during the current app session** |
| Fixes the error without helping the user learn | Explains **what happened, why, and how to avoid it next time** |

## How it works

```text
Streamlit UI
    │  POST /explain
    ▼
FastAPI backend
    ├── Run submitted code and capture output / traceback
    ├── Parse traceback and classify the error
    ├── Ask Groq for an explanation and corrected script
    ├── Run the corrected script to verify it
    └── Retry once if verification fails
```

The parser and classifier provide structured facts—such as the exception type, message, line, and category—to the explanation step. The UI displays the result and keeps a session-local history of successful analyses.

## Tech stack

- **Frontend:** Streamlit
- **Backend:** FastAPI and Uvicorn
- **Traceback analysis:** Python parser and rule-based classifier
- **Explanation generation:** Groq API
- **Verification:** Python subprocess execution

## Project structure

```text
Fix_my_error/
├── backend/
│   ├── core/
│   │   ├── classifier.py    # Maps exceptions to helpful categories
│   │   ├── explainer.py     # Builds Groq request and validates its response
│   │   ├── parser.py        # Extracts useful facts from tracebacks
│   │   ├── pipeline.py      # Coordinates reproduction, explanation, verification
│   │   ├── sandbox.py       # Runs code in a temporary subprocess
│   │   └── verifier.py      # Checks that suggested code runs
│   ├── main.py              # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit application
│   └── requirements.txt
├── samples/                 # Small scripts that demonstrate common errors
├── utils/
│   └── logger.py
├── logs/                    # Runtime log output
└── README.md
```

## Getting started

### Requirements

- Python 3.11 or newer
- A Groq API key

### 1. Create and activate a virtual environment

From the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, use the environment's interpreter directly as shown in the next steps, or follow your organization's PowerShell policy.

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt -r frontend/requirements.txt
```

### 3. Configure the Groq API key

Copy the example file and add your key:

```powershell
Copy-Item backend\.env.example backend\.env
```

Then edit `backend/.env`:

```dotenv
GROQ_API_KEY=your_groq_api_key
# Optional; defaults to openai/gpt-oss-20b in the application
GROQ_MODEL=openai/gpt-oss-20b
```

Keep `backend/.env` private. It is excluded from Git. Do not put real API keys in source files, screenshots, or code submitted to the app.

### 4. Start the backend

From the project root:

```powershell
python backend/main.py
```

The API listens at `http://localhost:8000`. Check that it is running:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### 5. Start the frontend

Open a second terminal at the project root, activate the same virtual environment, and run:

```powershell
streamlit run frontend/app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). The frontend uses `http://localhost:8000` by default. To point it at a different backend, set `BACKEND_URL` before starting Streamlit:

```powershell
$env:BACKEND_URL = "http://localhost:8000"
streamlit run frontend/app.py
```

### Streamlit Community Cloud demo

The hosted frontend may go to sleep after around 12 hours of inactivity. Before a demo or submission, open the Streamlit Community Cloud app shortly beforehand and wait for it to finish waking up. If the backend is hosted separately and also sleeps, its first request may take longer while that service starts; the backend health endpoint can be opened to wake it:

```text
https://<your-backend-host>/health
```

Wait for the `{"status":"ok"}` response, then try an example in the frontend before presenting.

## API

### `GET /health`

Returns a small health response:

```json
{"status":"ok"}
```

### `POST /explain`

Request body:

```json
{
  "code": "user = {\"name\": \"Anu\"}\nprint(user[\"age\"])",
  "error": ""
}
```

`code` is required and must contain 1–10,000 characters. `error` is an optional traceback, up to 5,000 characters. The response includes a `status`; on a successful analysis it also includes the detected error, explanation, suggested code, and verification information.

The API applies an in-memory rate limit of 10 requests per IP per minute and allows up to three concurrent analysis requests per process. These limits reset when the server restarts and are not shared across multiple server instances.

## Example errors

The Streamlit app includes examples for `KeyError`, `IndexError`, `NameError`, `TypeError`, and `ZeroDivisionError`. Equivalent standalone scripts are available in `samples/`.

## Important safety and privacy notes

**Do not expose this app publicly as-is or use it to run code from untrusted users.** Submitted Python is executed by a subprocess on the machine hosting the backend. The subprocess has a timeout and uses a temporary working directory, but it is **not an operating-system security sandbox**: code may still access the host's filesystem or network with the backend process's permissions. Resource limits are applied only on POSIX systems.

When an analysis needs an LLM explanation, submitted code and traceback facts are sent to the configured Groq API. Do not submit credentials, private data, or code you are not permitted to share with that provider.

## Current limitations

- Verification confirms that the suggested script runs without an error in the backend's environment; it does not prove the program is logically correct or behaves as intended.
- Code that depends on local files, external services, particular inputs, or packages may not reproduce on the backend. A pasted traceback can help explain such errors, but verification may remain incomplete.
- Mistake history is stored only in Streamlit session state and is not a persistent user profile.
- The backend's rate and concurrency controls are process-local and intended as basic safeguards, not production-grade abuse protection.