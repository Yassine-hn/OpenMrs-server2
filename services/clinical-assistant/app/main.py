import logging
import time
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .llm_client import llm_client
from .prompts import (
    SYSTEM_PROMPT,
    build_consultation_prompt,
    build_discharge_prompt,
    build_operative_report_prompt,
)
from .schemas import (
    ChatRequest,
    ChatResponse,
    ConsultationRequest,
    DischargeLetterRequest,
    DraftResponse,
    OperativeReportRequest,
    TranscribeResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("clinical-assistant")

app = FastAPI(
    title="Neurosurgery Clinical Assistant API",
    version="1.0.0",
    description="Local AI clinical drafting and assistant service for CHU Frantz Fanon, Blida.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    vllm_ok = await llm_client.check_health()
    return {
        "status": "healthy" if vllm_ok else "degraded",
        "service": "clinical-assistant",
        "vllm_connected": vllm_ok,
        "model": settings.LLM_MODEL_NAME,
    }

@app.post("/v1/draft/operative-report", response_model=DraftResponse)
async def draft_operative_report(request: OperativeReportRequest):
    logger.info("Drafting operative report for intervention: %s", request.intervention)
    prompt = build_operative_report_prompt(request)
    try:
        res = await llm_client.generate_draft(prompt)
        return DraftResponse(
            document_type="Compte rendu opératoire",
            draft_text=res["content"],
            model_used=res["model"],
            latency_ms=round(res["latency_ms"], 2),
        )
    except Exception as e:
        logger.error("Error generating operative report: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

@app.post("/v1/draft/consultation", response_model=DraftResponse)
async def draft_consultation(request: ConsultationRequest):
    logger.info("Drafting consultation note for motif: %s", request.motif)
    prompt = build_consultation_prompt(request)
    try:
        res = await llm_client.generate_draft(prompt)
        return DraftResponse(
            document_type="Consultation de neurochirurgie",
            draft_text=res["content"],
            model_used=res["model"],
            latency_ms=round(res["latency_ms"], 2),
        )
    except Exception as e:
        logger.error("Error generating consultation draft: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

@app.post("/v1/draft/discharge-letter", response_model=DraftResponse)
async def draft_discharge_letter(request: DischargeLetterRequest):
    logger.info("Drafting discharge letter for diagnostic: %s", request.diagnostic_principal)
    prompt = build_discharge_prompt(request)
    try:
        res = await llm_client.generate_draft(prompt)
        return DraftResponse(
            document_type="Compte-rendu d'hospitalisation et lettre de sortie",
            draft_text=res["content"],
            model_used=res["model"],
            latency_ms=round(res["latency_ms"], 2),
        )
    except Exception as e:
        logger.error("Error generating discharge letter: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM Generation Error: {str(e)}")

@app.post("/v1/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    request: Request,
    lang: str = "fr",
    prompt: Optional[str] = None,
):
    audio_bytes = await request.body()
    if not audio_bytes or len(audio_bytes) < 1000:
        return TranscribeResponse(text="", duration_seconds=0.0, language=lang)

    bias_prompt = prompt or "Neurochirurgie, CHU Frantz Fanon Blida, GCS, Karnofsky, méningiome, hydrocéphalie, craniotomie, hématome sous-dural"

    try:
        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": ("utterance.wav", audio_bytes, "audio/wav")}
            data = {
                "model": settings.STT_MODEL_NAME,
                "language": lang,
                "prompt": bias_prompt,
            }
            resp = await client.post(f"{settings.STT_ENGINE_URL}/audio/transcriptions", files=files, data=data)
            resp.raise_for_status()
            res_json = resp.json()

        text = res_json.get("text", "").strip()
        duration = res_json.get("usage", {}).get("seconds", round(time.perf_counter() - start_time, 2))
        return TranscribeResponse(
            text=text,
            duration_seconds=float(duration) if duration else None,
            language=lang,
        )
    except Exception as e:
        logger.error("Error transcribing audio: %s", e)
        raise HTTPException(status_code=500, detail=f"STT Error: {str(e)}")

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_clinical_assistant(request: ChatRequest):
    logger.info("Received clinical chat request with %d messages", len(request.messages))
    try:
        full_system = SYSTEM_PROMPT
        if request.patient_context:
            full_system += f"\n\nContexte clinique du patient en cours :\n{request.patient_context}"

        sanitized_messages = [{"role": "system", "content": full_system}]
        last_role = "system"
        for m in request.messages:
            content = m.content.strip()
            if not content:
                continue
            if m.role == last_role and len(sanitized_messages) > 1:
                # Merge consecutive messages from same role
                sanitized_messages[-1]["content"] += "\n" + content
            elif m.role != last_role:
                sanitized_messages.append({"role": m.role, "content": content})
                last_role = m.role

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            payload = {
                "model": settings.LLM_MODEL_NAME,
                "messages": sanitized_messages,
                "max_tokens": 1024,
                "temperature": 0.3,
                "top_p": 0.95,
            }
            resp = await client.post(f"{settings.LLM_BASE_URL}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        content = data["choices"][0]["message"]["content"].strip()
        return ChatResponse(
            response=content,
            model=settings.LLM_MODEL_NAME,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        logger.error("Error in clinical chat: %s", e)
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")
