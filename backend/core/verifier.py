from core.sandbox import run_code


def verify(original_code: str, fixed_code: str, timeout: int = 5) -> dict:
    """Run the fixed code and check that it really works.

    verified is True only if the fix is a real change AND it runs without error.
    """
    if not fixed_code.strip():
        return {"verified": False, "reason": "empty fix", "result": None}
    if fixed_code.strip() == original_code.strip():
        return {"verified": False, "reason": "fix is identical to the original code", "result": None}

    result = run_code(fixed_code, timeout=timeout)
    if result["timed_out"]:
        return {"verified": False, "reason": "fixed code timed out", "result": result}
    if not result["ok"]:
        return {"verified": False, "reason": "fixed code still fails", "result": result}
    return {"verified": True, "reason": "fixed code runs without errors", "result": result}