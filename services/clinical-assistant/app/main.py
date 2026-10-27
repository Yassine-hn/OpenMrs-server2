import logging
import re
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
    ActionProposal,
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

def extract_action_proposal(user_prompt: str) -> Optional[ActionProposal]:
    p = user_prompt.strip()
    if not p:
        return None

    # 1. Update patient address intent
    addr_patterns = [
        r"(?:modifie[rz]?|change[rz]?|mets? à jour|mettre à jour|actualise[rz]?|nouvelle)\s+(?:l['’\s]?adresse|adresse)(?:\s+du\s+patient)?\s*(?::|à|en|\=)\s*(.+)",
        r"(?:adresse|habite|demeure)\s*(?::|à|\=)\s*(.+)",
    ]
    for pat in addr_patterns:
        m = re.search(pat, p, re.IGNORECASE)
        if m:
            raw_addr = m.group(1).strip().rstrip(".")
            parts = [x.strip() for x in re.split(r"[,–-]", raw_addr) if x.strip()]
            address1 = parts[0] if len(parts) >= 2 else raw_addr
            city = parts[1] if len(parts) >= 2 else "Blida"
            return ActionProposal(
                action_type="update_patient_address",
                action_label="Mettre à jour l'adresse du patient",
                parameters={
                    "address1": address1,
                    "cityVillage": city,
                    "full_address": raw_addr,
                },
                preview_text=f"Nouvelle adresse : {address1} ({city})",
            )

    # 2. Add clinical diagnosis intent
    diag_patterns = [
        r"(?:ajoute[rz]?|enregistre[rz]?|noter?|poser?)\s+(?:le\s+|un\s+)?diagnostic(?:\s+de|\s+d['’\s]|\s*:)?\s*(.+)",
        r"(?:diagnostic\s*(?:retenu|principal|post-op|posé)?\s*:\s*)(.+)",
    ]
    for pat in diag_patterns:
        m = re.search(pat, p, re.IGNORECASE)
        if m:
            diag_text = m.group(1).strip().rstrip(".")
            return ActionProposal(
                action_type="add_clinical_diagnosis",
                action_label="Ajouter un diagnostic au dossier",
                parameters={
                    "diagnosis": diag_text,
                    "status": "ACTIVE",
                },
                preview_text=f"Diagnostic : {diag_text} (Statut: Actif)",
            )

    # 3. Record clinical note / observation intent
    note_patterns = [
        r"(?:enregistre[rz]?|ajoute[rz]?|consigne[rz]?|écris|écrire|créer?)\s+(?:une\s+)?(?:note|observation|remarque)(?:\s+clinique|\s+de\s+consultation|\s+d['’\s]évolution)?\s*(?::|\-|\=)\s*(.+)",
        r"(?:observation\s*(?:clinique)?\s*:\s*)(.+)",
    ]
    for pat in note_patterns:
        m = re.search(pat, p, re.IGNORECASE)
        if m:
            note_text = m.group(1).strip()
            return ActionProposal(
                action_type="record_clinical_note",
                action_label="Enregistrer une note de consultation",
                parameters={
                    "note": note_text,
                    "encounter_type": "1f331153-e484-554a-9184-1d45a2399166",
                    "location": "795d1d96-f5fb-4966-bea0-753525a24d71",
                },
                preview_text=f"Note clinique : « {note_text} »",
            )

    return None

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_clinical_assistant(request: ChatRequest):
    logger.info("Received clinical chat request with %d messages", len(request.messages))
    try:
        last_user_prompt = ""
        for m in reversed(request.messages):
            if m.role == "user" and m.content.strip():
                last_user_prompt = m.content.strip()
                break

        action_proposal = extract_action_proposal(last_user_prompt)

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
                "presence_penalty": 0.1,
                "frequency_penalty": 0.2,
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
            action=action_proposal,
        )
    except Exception as e:
        logger.error("Error in clinical chat: %s", e)
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")
