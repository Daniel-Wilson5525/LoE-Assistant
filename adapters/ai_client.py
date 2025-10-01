# adapters/ai_client.py
from __future__ import annotations

import os
import json
import re
import requests


# --- helpers ---------------------------------------------------------------

_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE | re.MULTILINE)
_JSON_STR_RE   = re.compile(r'"(?:\\.|[^"\\])*"')  # match a JSON string literal (rough but effective)


def _strip_code_fences(text: str) -> str:
    if not isinstance(text, str):
        return text
    return _CODE_FENCE_RE.sub("", text)


def _maybe_extract_json(text: str) -> str:
    """
    Best-effort: return a JSON object string.
    - Strip code fences if present
    - If whole text parses, return it
    - Else try to extract the last {...} blob
    """
    if not text:
        return text
    text = _strip_code_fences(text).strip()

    # fast path
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # extract last {...} block (greedy)
    m = re.search(r"\{(?:.|\n|\r)*\}\s*$", text)
    if m:
        candidate = m.group(0)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    return text  # give back original for further handling


def _escape_ctrl_in_json_strings(text: str) -> str:
    """
    Escape raw control characters inside JSON string literals so json.loads won't choke.
    Only modifies the contents of quoted strings. Does NOT blanket-escape backslashes.
    """
    if not isinstance(text, str):
        return text

    def _fix(m: re.Match) -> str:
        s = m.group(0)  # includes quotes
        inner = s[1:-1]
        # Replace actual control characters with escaped sequences
        inner = inner.replace("\r", r"\r").replace("\n", r"\n").replace("\t", r"\t")
        return f'"{inner}"'

    return _JSON_STR_RE.sub(_fix, text)


# --- client ----------------------------------------------------------------

class AIClient:
    """
    Minimal OpenAI-compatible chat completions client with:
      - Litellm/NIM compatibility (auto-drop unsupported params)
      - JSON enforcement/repair
      - Control-character sanitation
    """

    def __init__(self):
        self.base  = os.getenv("AI_API_BASE")
        self.key   = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "meta/llama-3.3-70b-instruct")

        if not (self.base and self.key):
            raise RuntimeError("Missing AI_API_BASE or AI_API_KEY in .env")

        self.base = self.base.rstrip("/")

    # --- HTTP ---

    def _post(self, body: dict) -> str:
        url = f"{self.base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        r = requests.post(url, json=body, headers=headers, timeout=60)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"AI API error {r.status_code} at {url}\nRequest body: {body}\nResponse: {r.text}"
            ) from e

        data = r.json()
        # defensive: some providers nest differently, but this is standard
        return data["choices"][0]["message"]["content"]

    # --- public API ---

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        json_mode: bool = False,
        max_tokens: int = 2500,
    ) -> str:
        """
        Return the model's message content as a STRING.
        If json_mode=True, guarantees a valid JSON string is returned.
        """
        base_msgs = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]

        body_base = {
            "model": self.model,
            "messages": base_msgs,
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }

        # First attempt: try JSON-enforcement flags (some backends accept them)
        body_try = dict(body_base)
        if json_mode:
            body_try.update({
                "response_format": {"type": "json_object"},  # OpenAI/OpenRouter-style
                "format": "json",                             # some vendors accept this alias
                "tool_choice": "none",                        # can trigger rejections; we'll drop if needed
            })

        # Call #1
        try:
            out = self._post(body_try)
        except RuntimeError as e:
            msg = str(e)
            # Your Litellm/NIM proxy rejects some params -> retry clean
            if ("UnsupportedParamsError" in msg) or ("does not support parameters" in msg):
                out = self._post(body_base)  # drop response_format / tool_choice / format
            else:
                raise

        if not json_mode:
            return out

        # Enforce JSON: clean, sanitize, parse
        cleaned = _maybe_extract_json(out)
        cleaned = _escape_ctrl_in_json_strings(cleaned)
        try:
            json.loads(cleaned)
            return cleaned
        except Exception:
            # One-shot repair: ask model to re-emit as strict JSON
            repair_body = {
                "model": self.model,
                "messages": base_msgs + [{
                    "role": "user",
                    "content": (
                        "Convert your previous answer to ONE valid JSON object with exactly these keys: "
                        "\"summary\" (string), \"tasks\" (string), \"open_questions\" (array of strings). "
                        "Return MINIFIED JSON (single line). Escape all newlines/tabs in strings as \\n and \\t. "
                        "No prose, no code fences, no markdown outside JSON."
                    ),
                }],
                "max_tokens": max_tokens,
                "temperature": 0.0,
            }
            repaired = self._post(repair_body)
            repaired = _maybe_extract_json(repaired)
            repaired = _escape_ctrl_in_json_strings(repaired)
            # Final guard (raise with helpful message if still invalid)
            json.loads(repaired)
            return repaired
