from core.parser import parse_traceback
from core.classifier import classify
from core.sandbox import run_code
from core.explainer import explain
from core.verifier import verify

MAX_RETRIES = 1  # extra LLM attempts if the first fix fails verification


def run(code: str, error_text: str = "", client=None) -> dict:
    """Full pipeline: reproduce -> parse -> classify -> explain -> verify (+1 retry).

    Always returns a dict with a "status":
      ok | no_error | timeout | llm_error
    """
    # 1. Reproduce the error in the sandbox
    sandbox = run_code(code)
    if sandbox["timed_out"]:
        return {"status": "timeout", "message": "Your code ran longer than 5 seconds (infinite loop?)."}

    reproduced = not sandbox["ok"]
    if reproduced:
        parsed = parse_traceback(sandbox["stderr"])          # trust the real run first
    elif error_text.strip():
        parsed = parse_traceback(error_text)                  # fall back to the pasted traceback
    else:
        return {"status": "no_error", "message": "The code ran without errors, and no traceback was given."}

    # 2. Classify with our own rules
    classified = classify(parsed)

    base = {
        "reproduced": reproduced,
        "error_type": parsed.get("error_type"),
        "message": parsed.get("message"),
        "line": parsed.get("line"),
        "code_line": parsed.get("code_line"),
        "category": classified["category"],
        "label": classified["label"],
    }

    # 3. Explain, then 4. verify (with a retry if the fix fails)
    retry = None
    attempts = 0
    last = None
    for _ in range(MAX_RETRIES + 1):
        attempts += 1
        answer = explain(code, parsed, classified, retry=retry, client=client)
        if "error" in answer:
            return {**base, "status": "llm_error", "message": answer["error"], "attempts": attempts}

        check = verify(code, answer["fixed_code"])
        last = (answer, check)
        if check["verified"]:
            break
        failure = (check["result"] or {}).get("stderr") or check["reason"]
        retry = {"fixed_code": answer["fixed_code"], "error": failure}

    answer, check = last
    return {
        **base,
        "status": "ok",
        "meaning": answer["meaning"],
        "reason": answer["reason"],
        "fixed_code": answer["fixed_code"],
        "how_to_avoid": answer["how_to_avoid"],
        "verified": check["verified"],
        "verify_note": check["reason"],
        "attempts": attempts,
    }