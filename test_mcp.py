import sys
import logging
from middleware.special_agent import CLIENT

logging.basicConfig(level=logging.INFO)

print("Connecting to UnrealMCP at localhost:8768...")

try:
    code = """
import unreal
unreal.log("UnrealMCP Server is ALIVE and successfully executing Python code!")
unreal.log_warning("This is a test warning to prove it works!")
print("Hello from Python standard output!")
"""
    result = CLIENT.execute_python(code)
    print("\n✅ MCP Server Response:")
    print("-------------------------")
    print(result)
    print("-------------------------\n")
    print("If you check your Unreal Engine Output Log, you should see the messages!")

except Exception as e:
    print(f"\n❌ Connection Failed: {e}")
    print("Make sure Unreal Engine is running and the UnrealMCP plugin is active.")
