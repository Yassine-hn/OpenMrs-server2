# Operations & Maintenance Runbook
**Stack IA Neurochirurgie — Serveur 2 (`Cerist-Neurochir`)**
*CHU Frantz Fanon, Blida*

---

## 1. Routine Health & Status Checks

### 1.1. Quick Health Check One-Liner
Execute the following command on Server 2:
```bash
docker compose ps && nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
```
Expected output:
- All 6 containers (`server2-clinical-assistant`, `server2-vllm`, `server2-monai`, `server2-ohif-ai-viewer`, `server2-stt-gateway`, `server2-stt-engine`) in status `Up (healthy)`.
- GPU memory used: ~12,500 MiB to 13,000 MiB out of 16,303 MiB.
- GPU temperature: < 65°C under normal ambient hospital server room conditions.

### 1.2. Microservice Endpoint Verification
```bash
# 1. Clinical Assistant Gateway
curl -s http://localhost:8000/health
# {"status":"healthy","service":"clinical-assistant","vllm_connected":true,"model":"medgemma-1.5-4b-it"}

# 2. MedGemma vLLM Engine
curl -s http://localhost:8001/v1/models | jq .data[0].id
# "medgemma-1.5-4b-it"

# 3. MONAI Label Server
curl -s http://localhost:8002/info | jq '{name, version, models}'
# {"name":"MONAILabel","version":"0.8.x","models":["segmentation"]}

# 4. OHIF-AI Web Workstation
curl -I -s http://localhost:1026/ | head -n 1
# HTTP/1.1 200 OK

# 5. STT Engine (Qwen3-ASR)
curl -s http://localhost:8004/health
# {"status":"ok"}
```

---

## 2. Container Lifecycle Management

### 2.1. Graceful Shutdown & Restart
```bash
cd "/home/cerist/new folder/OpenMrs-server2"

# Graceful stop
docker compose stop

# Start the stack (in background)
docker compose up -d

# Restart a specific service (e.g. after model or config modification)
docker compose restart clinical-assistant
```

### 2.2. Checking Live Logs
```bash
# Follow logs of the clinical assistant API
docker compose logs -f clinical-assistant

# Follow vLLM inference engine logs (tokens/sec, prompts)
docker compose logs -f vllm

# Follow MONAI Label segmentation queries
docker compose logs -f monai-server

# Follow STT transcription engine
docker compose logs -f stt-engine
```

---

## 3. Troubleshooting & Recovery Protocols

### Scenario A: GPU Out of Memory (CUDA OOM)
**Symptom**: vLLM or MONAI Label crashes or reports `torch.cuda.OutOfMemoryError`.
**Cause**: High concurrent requests or KV-cache overflow beyond the 16 GB boundary.
**Resolution**:
1. Check process holding VRAM:
   ```bash
   fuser -v /dev/nvidia*
   ```
2. Restart the specific model container:
   ```bash
   docker compose restart vllm
   ```
3. If OOM recurs, verify the memory fractions in `.env`:
   - `LLM_GPU_MEMORY_UTILIZATION=0.50` (Allocates max ~8.0 GB for MedGemma)
   - `STT_GPU_FRACTION=0.25` (Allocates max ~4.0 GB for Qwen3-ASR)
   - MONAI Label dynamically claims ~3.2 GB. Total reserved = 15.2 GB, leaving 1.1 GB safety buffer.

### Scenario B: OHIF-AI Cannot Load DICOM Studies from Server 1
**Symptom**: OHIF-AI displays blank study list or reports `DICOMweb connection timed out`.
**Resolution**:
1. Verify network connectivity from Server 2 to Server 1 Orthanc:
   ```bash
   curl -I http://10.0.211.249:8042/studies
   ```
2. If unreachable, verify Orthanc container on Server 1:
   ```bash
   ssh server1 "docker compose ps orthanc"
   ```
3. Test NGINX PACS reverse proxy on Server 2:
   ```bash
   curl -s http://localhost:1026/pacs/studies | jq .
   ```
   If this returns 502 Bad Gateway, restart `server2-ohif-ai-viewer`:
   ```bash
   docker compose restart ohif-ai-viewer
   ```

### Scenario C: Speech Transcription Fails or Returns Empty Text
**Symptom**: Doctor speaks into the microphone but the transcript box displays `Aucune parole détectée` or an error.
**Resolution**:
1. Check if audio input is valid 16 kHz WAV (must exceed 1,000 bytes):
   - In browser console, ensure Web Audio recorder downsamples to 16,000 Hz mono PCM.
2. Verify STT engine log on Server 2:
   ```bash
   docker compose logs --tail 30 stt-engine
   ```
3. Test STT engine directly with a synthetic audio sample or curl:
   ```bash
   curl -s http://localhost:8000/v1/transcribe -H "Content-Type: audio/wav" --data-binary @/tmp/test.wav
   ```

### Scenario D: Host Reboot / Power Interruption
**Behavior**: Upon system power restoration, Docker daemon starts automatically because `systemctl is-enabled docker` is set to `enabled`.
All 6 containers have `restart: unless-stopped` and will restore their running state within 180 seconds.
**Verification Checklist**:
1. Run `docker compose ps` &mdash; ensure all 6 services are up.
2. Wait 120s for vLLM weights to reload into GPU memory.
3. Test `curl http://localhost:8000/health` &mdash; verify `"vllm_connected": true`.

---

## 4. Maintenance & Log Rotation

All Docker services in `docker-compose.yml` are configured with log rotation limits:
```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```
Logs will never exceed 30 MB per container, preserving NVMe disk space on Server 2.

---

## 5. Security Architecture & Data Isolation

```
                ┌────────────────────────────────────────────────────────┐
                │             Zero Cloud Egress Guarantee                │
                │                                                        │
                │  - No external HuggingFace / OpenAI API calls          │
                │  - All weights stored on /home/cerist/models           │
                │  - Model inference isolated on RTX 5070 Ti             │
                │  - Strictly compliant with Algerian Law 18-07          │
                └────────────────────────────────────────────────────────┘
```
All patient identifiers, surgical transcriptions, and radiological scans remain exclusively on the hospital's private subnetwork `10.0.211.0/24`.
