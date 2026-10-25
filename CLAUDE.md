# CLAUDE.md — OpenMrs-server2

AI and GPU-accelerated microservices supporting the **OpenMRS O3 + Orthanc PACS** deployment for the **Neurosurgery Department, CHU Frantz Fanon, Blida**.

## Scope & Status

The project architecture comprises two servers:
- **Server 1 (`server-PowerEdge-T140`, LAN IP: `10.0.211.249`)**: Core EMR + Orthanc PACS + OHIF Viewer v3 + Neurosurgery Clinical Content (Repo: `OpenMrs-EMR`). Status: COMPLETED & PRODUCTION-READY.
- **Server 2 (`Cerist-Neurochir`, LAN IP: `10.0.211.250`, Public IP: `193.194.91.237:2022`)**: GPU server hosting AI imaging tools (OHIF-AI / segmentation), medical dictation (Whisper STT), and local LLM clinical assistant.

### Server 2 Services (Current Phase):
1. **Clinical LLM Assistant**: Local inference (e.g. vLLM or Ollama with Mistral / Llama 3) for drafting consultation notes, operative reports, and discharge summaries from structured form data.
2. **Medical Dictation**: Speech-to-text service (e.g. `faster-whisper`) for clinical dictation into text fields.
3. **AI Imaging & Segmentation (OHIF-AI)**: Medical imaging backend (e.g. MONAI Label / TotalSegmentator) connected with Server 1 Orthanc via DICOMweb, saving DICOM SEG back to PACS.

---

## Persistent Rules & Principles

1. **Private Documentation Rule:**
   - Any plan for a phase or subtask must live in `docs/` and be named `PLAN-*.md` (strictly git-ignored as private documentation).
2. **Git Workflow & Commits:**
   - The user personally performs git commits and pushes. Do not run `git commit` or `git push` directly without explicit request.
   - Work on the `main` branch in this repository.
3. **Pin Container Images by Multi-Arch Digest:**
   - Pin every image by digest in `docker-compose.yml` (`tag@sha256:...`). Never use mutable tags (`latest`, `main`).
4. **Secrets Management:**
   - Secrets and internal tokens live strictly in `.env` (git-ignored). No credentials committed to source.
5. **Data Privacy (Algerian Law 18-07):**
   - All AI inference and patient data stay strictly within the local hospital network. No external cloud API calls for clinical data or audio.
6. **Verification & Audit:**
   - Record actions, commands, and tests in `WORK-LOG.md` (git-ignored).
   - Never claim something works without demonstrating it with actual command output.
