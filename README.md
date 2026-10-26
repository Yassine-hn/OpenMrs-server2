# OpenMrs-server2: Clinical AI Infrastructure Stack
**Service de Neurochirurgie — CHU Frantz Fanon, Blida**

This repository contains the local, on-premise AI inference stack supporting the Neurosurgery Department of CHU Frantz Fanon (Blida, Algeria). The stack delivers real-time clinical document generation, interactive radiological AI segmentation, and specialized voice dictation directly to the primary OpenMRS 3.x electronic medical record and Orthanc PACS hosted on Server 1.

---

## 1. Architectural Overview

```
                                  CHU Frantz Fanon Hospital LAN (10.0.211.0/24)
  ┌─────────────────────────────────────────────────────────┐         ┌──────────────────────────────────────────────────────────┐
  │         SERVER 1: PowerEdge T140 (10.0.211.249)         │         │        SERVER 2: Cerist-Neurochir (10.0.211.250)         │
  │                                                         │         │                                                          │
  │   ┌───────────────────┐       ┌─────────────────────┐   │         │   ┌────────────────────┐      ┌──────────────────────┐   │
  │   │  OpenMRS Backend  │       │    Orthanc PACS     │   │         │   │ Clinical Assistant │      │     vLLM MedGemma    │   │
  │   │   (MariaDB 10.11) │       │   (PostgreSQL 16)   │   │         │   │   FastAPI (:8000)  ├─────►│  4B FP8 Engine (:8001)│   │
  │   └─────────▲─────────┘       └──────────▲──────────┘   │         │   └─────────▲──────────┘      └──────────┬───────────┘   │
  │             │                            │              │         │             │                        │                   │
  │   ┌─────────┴─────────┐                  │              │         │             │                        ▼                   │
  │   │   NGINX Gateway   │                  │              │         │             │               ┌──────────────────┐         │
  │   │ (Auth Guard /80)  ├──────────────────┼──────────────┼─────────┼─────────────┤               │  NVIDIA RTX 5070 │         │
  │   └─────────▲─────────┘                  │              │         │             │               │   Ti (16GB VRAM) │         │
  │             │                            │              │         │   ┌─────────┴──────────┐    └────────▲─────────┘         │
  │   ┌─────────┴─────────┐                  │              │         │   │    STT Gateway     │             │                   │
  │   │   Single-Spa MFE  │                  │              │         │   │   FastAPI (:8003)  ├─────────────┤                   │
  │   │ esm-neuro-imaging │                  │              │         │   └─────────▲──────────┘             │                   │
  │   └───────────────────┘                  │              │         │             │                        │                   │
  │                                          │              │         │   ┌─────────┴──────────┐      ┌──────┴───────────────┐   │
  │                                          │              │         │   │   OHIF-AI Viewer   │      │   MONAI MedSAM2      │   │
  │                                          └──────────────┼─────────┼──►│  Station (:1026)   ├─────►│  Server (:8002)      │   │
  │                                                         │         │   └────────────────────┘      └──────────────────────┘   │
  └─────────────────────────────────────────────────────────┘         └──────────────────────────────────────────────────────────┘
```

---

## 2. Hardware & VRAM Allocation

All models run concurrently on a single **NVIDIA GeForce RTX 5070 Ti (16 GB GDDR7 VRAM)** under CUDA 12.8:

| Container Service | Base Engine | Model Name / Variant | Precision | Allocated VRAM | Active Ports | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `server2-vllm` | vLLM OpenAI | `medgemma-1.5-4b-it-variant-C` | FP8 Quantized | **~6.8 GB** | `127.0.0.1:8001` | Clinical narrative drafting & consultation Q&A |
| `server2-monai` | MONAI Label | `MedSAM2` (SAM 2.1 Video/3D) | FP16 | **~3.2 GB** | `0.0.0.0:8002` | Interactive 2D/3D tumor & lesion segmentation |
| `server2-stt-engine` | vLLM Audio | `Qwen/Qwen3-ASR-0.6B` | FP16 | **~2.7 GB** | `127.0.0.1:8004` | 16 kHz WAV medical speech-to-text |
| `server2-clinical-assistant` | FastAPI / Uvicorn | Internal Gateway | N/A | < 150 MB RAM | `0.0.0.0:8000` | Structured prompt assembly & sanitize pipeline |
| `server2-stt-gateway` | FastAPI / Uvicorn | Audio Pre-processor | N/A | < 120 MB RAM | `0.0.0.0:8003` | Audio decoding, lexicon biasing, silence gate |
| `server2-ohif-ai-viewer` | NGINX / React | OHIF Viewer v3.13 | N/A | < 80 MB RAM | `0.0.0.0:1026` | Web radiology segmentation workstation |
| **System Headroom** | CUDA Runtime | Dynamic KV-Cache Buffer | - | **~3.2 GB** | - | Handles burst token sequences up to 4,096 tokens |

---

## 3. Services Catalogue & Endpoints

### 3.1. Clinical Assistant API (`:8000`)
- **Health**: `GET /health` &mdash; Reports service status and vLLM connectivity.
- **Operative Report**: `POST /v1/draft/operative-report` &mdash; Generates a 4-section structured operative report from intra-operative parameters (approach, findings, Simpson grade, blood loss).
- **Discharge Letter**: `POST /v1/draft/discharge-letter` &mdash; Generates hospital discharge letter, post-op evolution, and outpatient instructions.
- **Consultation Note**: `POST /v1/draft/consultation` &mdash; Generates clinical examination notes from history and clinical findings.
- **Direct Transcription**: `POST /v1/transcribe?lang=fr` &mdash; Transcribes raw 16 kHz 16-bit mono WAV audio with neurosurgical vocabulary biasing.
- **Clinical Chat**: `POST /v1/chat` &mdash; Multi-turn clinical Q&A with patient context injection and automatic role deduplication.

### 3.2. OHIF-AI Radiology Station (`:1026`)
- Accessible directly or reverse-proxied via Server 1 under `/ohif-ai/`.
- Pre-configured with MONAI Label MedSAM2 plugin for prompt-based mask propagation (points, bounding boxes).
- Transparently proxies DICOMweb queries to Server 1 Orthanc via `/pacs/` (`http://10.0.211.249:8042/`).

### 3.3. STT Audio Pipeline (`:8003` / `:8004`)
- Specialized vocabulary lexicon loaded from [`config/stt/lexicon-neurochir.txt`](file:///home/myusername/Desktop/Cerist/new%20folder/OpenMrs-server2/config/stt/lexicon-neurochir.txt) (GCS, Karnofsky, méningiome, clivus, Simpson, DVP, laminectomie, etc.).
- Real-time speech transcription with average latency under 1.5s for 15s utterances.

---

## 4. Security & Algerian Law 18-07 Compliance

In accordance with Algerian Law 18-07 on the protection of personal data and medical privacy:
1. **100% On-Premises Execution**: Zero telemetry, zero external API calls, zero cloud egress. All inference occurs directly on Server 2's RTX 5070 Ti GPU.
2. **Strict Perimeter Isolation**: Server 2 AI endpoints only accept connections originating from the internal LAN (`10.0.211.x`).
3. **Session Authentication Gate**: The OpenMRS gateway on Server 1 enforces `auth_request /_auth_openmrs` on all `/api/clinical-assistant/`, `/api/stt/`, and `/ohif-ai/` requests. Unauthenticated requests are rejected immediately with HTTP 401.
4. **Human-in-the-Loop Safeguard**: MedGemma and Qwen3-ASR operate as consultative drafting aids only. No model has write access to OpenMRS or Orthanc. All medical documents must be reviewed, edited, and explicitly committed by an authenticated clinician holding the required OpenMRS privileges.

---

## 5. Operations & Quickstart

### Starting the Stack
```bash
cd "/home/cerist/new folder/OpenMrs-server2"
cp .env.example .env   # Customize paths if needed
docker compose up -d
```

### Verifying Service Health
```bash
# Check container status
docker compose ps

# Check GPU VRAM and temperature
nvidia-smi

# Check Clinical Assistant API health
curl -s http://localhost:8000/health | jq .

# Check vLLM MedGemma health
curl -s http://localhost:8001/health

# Check MONAI Label server info
curl -s http://localhost:8002/info | jq .
```

For detailed operational procedures, backup policies, and failure recovery protocols, consult the [Operations Runbook](docs/RUNBOOK-OPERATIONS.md).
