# services/prompt_loader.py
import os

def load_prompt_file(prompt_dir: str | None, fname: str) -> str:
    """
    Try <prompt_dir>/<fname>. If not found, return "" (caller can fall back).
    """
    if prompt_dir:
        path = os.path.join(prompt_dir, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return ""
