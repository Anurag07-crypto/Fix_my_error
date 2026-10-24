import re

# File "x.py", line 3, in <module>
FRAME_RE = re.compile(r'^\s*File "(?P<file>.+?)", line (?P<line>\d+)(?:, in (?P<func>.+))?\s*$')
# KeyError: 'age'   |   ValueError   |   requests.exceptions.HTTPError: 404
ERROR_RE = re.compile(r'^(?P<type>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt|Iteration))(?::\s*(?P<msg>.*))?$')
# Python 3.11+ marker lines made only of ^ and ~
MARKER_RE = re.compile(r'^\s*[\^~]+\s*$')
CHAIN_MARKERS = (
    "During handling of the above exception",
    "The above exception was the direct cause",
)


def _last_block(tb: str) -> list[str]:
    """If exceptions are chained, keep only the final traceback."""
    lines = tb.strip().splitlines()
    start = 0
    for i, line in enumerate(lines):
        if any(m in line for m in CHAIN_MARKERS):
            start = i + 1
    return lines[start:]


def parse_traceback(tb: str) -> dict:
    """Extract error type, message and the failing frame from a Python traceback."""
    result = {
        "error_type": None,
        "message": "",
        "file": None,
        "line": None,
        "function": None,
        "code_line": None,
        "frames": [],
        "valid": False,
    }
    if not tb or not tb.strip():
        return result

    lines = _last_block(tb)

    # 1. Collect frames (File ... line ... [in ...]) plus the code line under each
    frames = []
    for i, line in enumerate(lines):
        m = FRAME_RE.match(line)
        if not m:
            continue
        code = None
        if i + 1 < len(lines):
            nxt = lines[i + 1]
            if not FRAME_RE.match(nxt) and not MARKER_RE.match(nxt) and nxt.strip():
                code = nxt.strip()
        frames.append({
            "file": m.group("file"),
            "line": int(m.group("line")),
            "function": m.group("func"),
            "code_line": code,
        })

    # 2. Find the final "ErrorType: message" line (search from the bottom)
    for line in reversed(lines):
        s = line.strip()
        if not s or MARKER_RE.match(s):
            continue
        m = ERROR_RE.match(s)
        if m:
            result["error_type"] = m.group("type").split(".")[-1]
            result["message"] = (m.group("msg") or "").strip()
            break

    result["frames"] = frames
    if frames:
        last = frames[-1]  # the frame where the error was raised
        result.update(
            file=last["file"],
            line=last["line"],
            function=last["function"],
            code_line=last["code_line"],
        )

    result["valid"] = result["error_type"] is not None
    return result