# adapters/ai_client.py
import os, requests

class AIClient:
    def __init__(self):
        self.base  = os.getenv("AI_API_BASE")
        self.key   = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "meta/llama-3.3-70b-instruct")

        if not (self.base and self.key):
            raise RuntimeError("Missing AI_API_BASE or AI_API_KEY in .env")

        self.base = self.base.rstrip("/")

    def complete(self, prompt: str, system: str | None = None,
                 json_mode: bool = False, max_tokens: int = 2500) -> str:
        body = {
            "model": self.model,
            "messages": (
                [{"role": "system", "content": system}] if system else []
            ) + [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base}/chat/completions"
        r = requests.post(url, json=body, headers=headers, timeout=60)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"AI API error {r.status_code} at {url}\nRequest body: {body}\nResponse: {r.text}"
            ) from e

        data = r.json()
        return data["choices"][0]["message"]["content"]
