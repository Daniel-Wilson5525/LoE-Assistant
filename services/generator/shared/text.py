def ensure_heading(text: str, heading: str) -> str:
    if not text: return text
    stripped = text.lstrip()
    if not stripped.upper().startswith(heading):
        return f"{heading}\n{stripped}"
    return text

def bullet_block(values, prefix="- ") -> str:
    vals = [str(v).strip() for v in (values or []) if str(v).strip()]
    return "\n".join(f"{prefix}{v}" for v in vals) if vals else ""
