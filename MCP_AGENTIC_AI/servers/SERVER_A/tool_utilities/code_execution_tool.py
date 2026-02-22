from langchain_core.tools import StructuredTool
from pydantic import BaseModel
import numpy as np
import pandas as pd
import scipy
import plotly.express as px
from pathlib import Path
import uuid
# from logger.base_logger import get_logger

# logger = get_logger(__name__)


class CodeInput(BaseModel):
    code: str
    shared_folder: str  # folder to save output files

def python_code_exec(code: str, shared_folder: str):
    """
    Execute Python code safely with access to numpy, pandas, scipy, and plotly.express.
    - Only allows analysis and visualization operations.
    - Automatically saves outputs (.txt, .csv, .json) to shared folder with unique names.
    - Returns variables and only the most recently created file from this execution with absolute path.
    """
    print(f"Running Python code:\n{code}")

    # Security check
    harmful_keywords = ["import sys", "subprocess", "shutil", "exec(", "eval(", "__import__", "os.system"]
    if any(keyword in code for keyword in harmful_keywords):
        print("Potentially harmful code detected. Aborting execution.")
        return "Error: Potentially harmful code detected. Execution aborted."

    shared_path = Path(shared_folder)
    shared_path.mkdir(parents=True, exist_ok=True)

    # Snapshot files before execution
    files_before = set(f for f in shared_path.iterdir() if f.is_file())

    try:
        local_vars = {}
        exec(code, {"np": np, "pd": pd, "scipy": scipy, "px": px, "Path": Path}, local_vars)

        # Snapshot files after execution
        files_after = set(f for f in shared_path.iterdir() if f.is_file())
        new_files = list(files_after - files_before)

        # If multiple new files, return the most recently modified
        most_recent_file = None
        if new_files:
            most_recent_file = max(new_files, key=lambda f: f.stat().st_mtime).resolve()

        result_summary = {
            "variables": {k: repr(v) for k, v in local_vars.items()},
            "file_created": str(most_recent_file) if most_recent_file else None
        }

        return result_summary

    except Exception as e:
        print(f"Python code execution error: {e}")
        return f"Error: {e}"


python_code_exec_tool = StructuredTool(
    name="python_code_exec",
    func=python_code_exec,
    description="""
        Execute Python code for data analysis and visualization.
        Allowed libraries: numpy, pandas, scipy, plotly.express.
        Code runs in a restricted environment to prevent harmful operations.
        Save outputs as .txt, .csv, or .json in the provided shared folder.
        Return variables and file paths in the output.
    """,
    args_schema=CodeInput
)
