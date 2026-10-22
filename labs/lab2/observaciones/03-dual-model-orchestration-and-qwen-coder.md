# Observation 03: Dual Model Deployment (Gemma 3 VLM & Qwen 3 Coder) and One-Click Orchestration

> **Context:** Deployment and orchestration of concurrent multimodal and code-generation models on NVIDIA DGX Spark (`spark-0fbc`, `192.168.6.35/26`), resolution of payload mismatches in `app.py`, and creation of a centralized startup script.

---

## 1. System Topology & Active Endpoints

```
+------------------------------------+          Network (192.168.6.0/26)      +-------------------------------------------------+
|             Client PC              | -------------------------------------> |           NVIDIA DGX Spark (GB10 GPU)           |
|         (192.168.6.44/26)          |   HTTP MJPEG Stream (port 8080)        |                (192.168.6.35/26)                |
|                                    |                                        |                                                 |
|  - Built-in / USB Webcam           |                                        |  - Flask app.py (port 8082)                     |
|  - stream_camera.py (port 8080)    |                                        |  - Gemma 3 4B VLM (port 8084, --mmproj)         |
|  - Browser UI: 192.168.6.35:8082   | <------------------------------------- |  - Qwen 3 Coder 30B (port 8080, code/text)      |
+------------------------------------+         Inference Results & Web UI     +-------------------------------------------------+
```

### Port Mapping & Resource Allocations

| Service | Host Interface | Port | Model / Binary | VRAM Allocated | Endpoint Path |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Local Webcam Streamer** | Client (`192.168.6.44`) | `8080` | `stream_camera.py` (Flask MJPEG) | N/A | `/video` |
| **Flask Web App** | Spark (`192.168.6.35`) | `8082` | `~/Documents/Reps/Clase4/app.py` | ~150 MB (Host RAM) | `/`, `/inference`, `/camera_status` |
| **Gemma 3 4B VLM** | Spark (`127.0.0.1`) | `8084` | `gemma-3-4b-it-Q8_0.gguf` + `mmproj` | **5,779 MiB** | `/v1/chat/completions` |
| **Qwen 3 Coder 30B** | Spark (`127.0.0.1`) | `8080` | `Qwen3-Coder-30B-A3B-Instruct...` | **17,342 MiB** | `/v1/chat/completions` |

---

## 2. Root Cause Analysis & Engineering Fixes

### Problem A: Image Payload Sent to Non-Multimodal Model
- **Symptom:** When sending an inference request to `qwen3-30b-coder`, `llama-server` on port 8080 crashed or returned:
  ```json
  {"error":{"code":500,"message":"image input is not supported - hint: if this is unexpected, you may need to provide the mmproj","type":"server_error"}}
  ```
- **Root Cause:** In `app.py`, `send_to_model` unconditionally converted webcam frames into Base64 JPEG buffers and injected them into the OpenAI `messages` payload as `image_url` whenever `8080` was in the URL. Since Qwen 3 Coder is a pure text/code LLM without vision weights, `llama-server` rejected the image token.
- **Solution:** Refactored `send_to_model` in `app.py` to identify whether the target endpoint is a multimodal model (`is_vlm = "8084" in model_url or "gemma" in model_url`). Only VLM endpoints receive the `image_url` payload block; pure code/text models receive clean user text prompts.

### Problem B: `/completion` vs `/v1/chat/completions` Schema Mismatch
- **Symptom:** `config.json` initially defined Qwen's URL as `http://127.0.0.1:8080/completion`. When `app.py` sent structured `{"messages": [...]}` dictionaries, `llama-server` returned:
  ```json
  {"error":{"code":400,"message":"[json.exception.out_of_range.403] key 'prompt' not found","type":"invalid_request_error"}}
  ```
- **Solution:** Updated `config.json` to route requests to the OpenAI-compatible `/v1/chat/completions` endpoint for both models, providing consistent chat-templated execution.

---

## 3. Centralized Orchestration Script (`iniciar_lab2.sh`)

A unified script was placed at `/home/ucab-spark1/Documents/Reps/iniciar_lab2.sh` (with symlink at `~/start_all.sh`):

1. **Automatic Network Alignment:** Checks current network interface assignments for client laptop and Spark (`192.168.6.x`), writing verified IPs to `config.json`.
2. **Deterministic GPU Offload:** Launches both models concurrently with `-ngl 99` and appropriate context buffers without port conflicts.
3. **Background Daemon Management:** Starts `app.py` in the background and reports live `/camera_status` and `nvidia-smi` memory metrics.

---

## 4. Empirical Performance Metrics

| Metric | Gemma 3 4B VLM | Qwen 3 Coder 30B | Combined Total |
| :--- | :--- | :--- | :--- |
| **GPU Memory Footprint** | 5.7 GB | 16.8 GB | **22.5 GB / 128 GB** |
| **Prompt Evaluation Speed** | ~480 tokens/s | ~167 tokens/s | N/A |
| **Generation Speed** | ~50 tokens/s | **87.85 tokens/s** | N/A |
| **End-to-End Latency** | **1.40 seconds** | **1.67 seconds** | Sub-2s responsive |
