import os

class Settings:
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://vllm:8000/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "medgemma-1.5-4b-it")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    OPENMRS_BASE_URL: str = os.getenv("OPENMRS_BASE_URL", "http://10.0.211.249")
    STT_ENGINE_URL: str = os.getenv("STT_ENGINE_URL", "http://stt-engine:8000/v1")
    STT_MODEL_NAME: str = os.getenv("STT_MODEL_NAME", "Qwen3-ASR-0.6B")

settings = Settings()
