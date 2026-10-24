"""Test script to verify logger and pipeline functionality"""
import sys
sys.path.insert(0, '.')

# Test logger
from utils.logger import get_logger
logger = get_logger('test_script')
logger.info("Logger test successful")

# Test imports
print("Testing imports...")

try:
    from utils.logger import get_logger
    print("OK: utils.logger imported successfully")
except ImportError as e:
    print(f"FAIL: Failed to import utils.logger: {e}")

try:
    from backend.core.pipeline import run
    print("OK: backend.core.pipeline imported successfully")
except ImportError as e:
    print(f"FAIL: Failed to import backend.core.pipeline: {e}")

try:
    from backend.core import parser, classifier, explainer, sandbox, verifier
    print("OK: All backend.core modules imported successfully")
except ImportError as e:
    print(f"FAIL: Failed to import backend.core modules: {e}")

print("\nAll tests completed!")