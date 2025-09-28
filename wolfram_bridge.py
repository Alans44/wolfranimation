# wolfram_bridge.py
import json, os, shutil, subprocess

def compute_with_wolfram(expr: str, a: float, b: float):
    if os.getenv("USE_WOLFRAM", "0") != "1":
        return None
    if shutil.which("wolframscript") is None:
        return None
    try:
        proc = subprocess.run(
            ["wolframscript", "-file", "compute_volume.wls", expr, str(a), str(b)],
            check=True, capture_output=True, text=True
        )
        return json.loads(proc.stdout.strip() or "{}")
    except Exception:
        return None
