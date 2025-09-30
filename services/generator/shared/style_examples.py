import os
EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "examples"))

def load_style_examples(service: str) -> str:
    try:
        s = (service or "").lower()
        path = os.path.join(EXAMPLES_DIR, "wireless_install.md")
        if any(k in s for k in ["relocation", "move", "migrat", "decom", "re-rack"]):
            path = os.path.join(EXAMPLES_DIR, "device_relocation.md")
        elif any(k in s for k in ["switch", "router", "l3", "l2"]):
            path = os.path.join(EXAMPLES_DIR, "switch_install.md")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
