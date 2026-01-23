import runpy
import sys
import os

if __name__ == "__main__":
    # Ensure the current directory is in sys.path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
        
    # Run the module as a script, equivalent to `python -m umamusume_prompt.mcp.server`
    runpy.run_module("umamusume_prompt.mcp.server", run_name="__main__", alter_sys=True)
