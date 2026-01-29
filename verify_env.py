import os
import sys

print("--- ENV CHECK ---")
print(f"DEFAULT_PROVIDER: {os.environ.get('DEFAULT_PROVIDER')}")
print(f"CWD: {os.getcwd()}")
try:
    import middleware.routes.api
    print(f"API MODULE FILE: {middleware.routes.api.__file__}")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
print("-----------------")
