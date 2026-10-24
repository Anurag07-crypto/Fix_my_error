from core.parser import parse_traceback
from core.classifier import classify
from core.sandbox import run_code
from core.explainer import explain
from core.verifier import verify
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

MAX_RETRIES = 1  # extra LLM attempts if the first fix fails verification

logger = get_logger(__name__)


def run(code: str, error_text: str = "", client=None) -> dict:
    """Full pipeline: reproduce -> parse -> classify -> explain -> verify (+1 retry).

    Always returns a dict with a "status":
      ok | no_error | timeout | llm_error
    """
    logger.info("Starting pipeline run")
    logger.debug(f"Code length: {len(code)}, Error text provided: {bool(error_text)}")
    
    # 1. Reproduce the error in the sandbox
    logger.info("Running code in sandbox")
    sandbox = run_code(code)
    logger.debug(f"Sandbox result: ok={sandbox['ok']}, timed_out={sandbox['timed_out']}")
    
    if sandbox["timed_out"]:
        logger.warning("Code timed out in sandbox")
        return {"status": "timeout", "message": "Your code ran longer than 5 seconds (infinite loop?)."}

    reproduced = not sandbox["ok"]
    if reproduced:
        logger.info("Reproducing error - using stderr from sandbox run")
        parsed = parse_traceback(sandbox["stderr"])          # trust the real run first
    elif error_text.strip():
        logger.info("Using provided error text (not from sandbox run)")
        parsed = parse_traceback(error_text)                  # fall back to the pasted traceback
    else:
        logger.info("No error to process")
        return {"status": "no_error", "message": "The code ran without errors, and no traceback was given."}

    logger.info(f"Parsed traceback: {parsed.get('error_type')}: {parsed.get('message')[:50]}...")

    # 2. Classify with our own rules
    logger.info("Classifying error")
    classified = classify(parsed)
    logger.debug(f"Classified as: {classified['category']} - {classified['label']}")

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
    for i in range(MAX_RETRIES + 1):
        attempts += 1
        logger.info(f"Explanation attempt {attempts}")
        answer = explain(code, parsed, classified, retry=retry, client=client)
        
        if "error" in answer:
            logger.error(f"LLM error: {answer['error']}")
            return {**base, "status": "llm_error", "message": answer["error"], "attempts": attempts}

        logger.debug(f"Verification attempt {attempts}")
        check = verify(code, answer["fixed_code"])
        last = (answer, check)
        
        if check["verified"]:
            logger.info(f"Fix verified on attempt {attempts}")
            break
            
        failure = (check["result"] or {}).get("stderr") or check["reason"]
        logger.warning(f"Fix failed (attempt {attempts}): {failure[:100]}...")
        retry = {"fixed_code": answer["fixed_code"], "error": failure}

    answer, check = last
    result = {
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
    logger.info(f"Pipeline completed successfully (status: {result['status']}, attempts: {attempts})")
    return result