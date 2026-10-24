"""Test script to verify logger and pipeline functionality"""
import sys
import os

# Set the working directory to the project root
os.chdir('/Users/Lenovo/Desktop/error_hackathon/Fix_my_error')

# Add the project root to the Python path
sys.path.insert(0, '/Users/Lenovo/Desktop/error_hackathon/Fix_my_error')

# Test imports
print('Testing imports from project root...')

try:
    from utils.logger import get_logger
    logger = get_logger('test')
    logger.info('Logger import successful from project root')
    print('OK: utils.logger imported successfully')
except Exception as e:
    print('FAIL: Failed to import utils.logger: ' + str(e))

try:
    from backend.core.pipeline import run
    print('OK: backend.core.pipeline imported successfully')
except Exception as e:
    print('FAIL: Failed to import backend.core.pipeline: ' + str(e))

try:
    from backend.core import parser, classifier, explainer, sandbox, verifier
    print('OK: All backend.core modules imported successfully')
except Exception as e:
    print('FAIL: Failed to import backend.core modules: ' + str(e))

print('All tests completed!')