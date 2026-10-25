import time
import httpx
from typing import Dict, Any, Optional
from .config import settings
from .prompts import SYSTEM_PROMPT

class LLMClient:
    def __init__(self, base_url: str = settings.LLM_BASE_URL, model_name: str = settings.LLM_MODEL_NAME):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = settings.LLM_TIMEOUT_SECONDS

    async def generate_draft(self, user_prompt: str, system_prompt: str = SYSTEM_PROMPT, max_tokens: int = settings.LLM_MAX_TOKENS) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "top_p": 0.95,
        }
        
        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = data["choices"][0]["message"]["content"].strip()
        return {
            "content": content,
            "latency_ms": latency_ms,
            "model": self.model_name
        }

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url.replace('/v1', '')}/health")
                return resp.status_code == 200
        except Exception:
            return False

llm_client = LLMClient()
