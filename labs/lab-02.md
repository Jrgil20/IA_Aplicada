# Lab 02: Interactive Multimodal VLM with Webcam (DGX Spark)

> **Status:** Ready for Lab Session Execution  
> **Target System:** NVIDIA DGX Spark (`ucab-spark2`, 128 GB Unified Memory, GB10 architecture)  
> **Models under Test:** `gemma3:4b`, `gemma3:12b`, `gemma3:27b` (multimodal vision-language models)  
> **Serving Engine:** Ollama (`0.0.0.0:11434`) with `/api/chat` and OpenAI-compatible `/v1/chat/completions`  
> **Client Runtime:** Local workstation / laptop with webcam (OpenCV + Python)

---

## 1. Objectives

- [ ] Verify multimodal models deployed on DGX Spark via Ollama (`gemma3:4b`, `gemma3:12b`, `gemma3:27b`).
- [ ] Ensure Ollama network binding listens on `0.0.0.0:11434` to accept remote HTTP connections from the client PC.
- [ ] Validate remote network accessibility from the student PC using `curl` pre-flight checks.
- [ ] Implement/execute the interactive webcam client script ([`webcam_vlm.py`](file:///home/jr_g/Develop/IA_Aplicada/labs/lab2/webcam_vlm.py)).
- [ ] Test on-demand visual questioning (Snapshot Mode: capture frame via `SPACE`, send prompt to Gemma 3).
- [ ] Measure end-to-end multimodal inference latency (frame encoding, network transport, prefill, generation) across model scales (`4b` vs `12b` vs `27b`).
- [ ] Analyze failure modes, hallucinations, and spatial reasoning limitations on live physical objects.

---

## 2. Architecture & Topology

```
+------------------------------------+          Network (HTTP)          +--------------------------------------+
|             Client PC              | -------------------------------> |           NVIDIA DGX Spark           |
|                                    |   POST /api/chat (JSON + Base64) |                                      |
|  - USB / Built-in Webcam           |                                  |  - GB10 Superchip (128 GB Unified)   |
|  - OpenCV Frame Capture            | <------------------------------- |  - Ollama Service (port 11434)       |
|  - Frame Encoder (JPEG -> Base64)  |         Stream / Response        |  - Model: gemma3:4b / 12b / 27b      |
|  - Interactive CLI / Preview Window|                                  |                                      |
+------------------------------------+                                  +--------------------------------------+
```

### Key Technical Considerations
1. **Network Binding:** By default, Ollama binds to `127.0.0.1`. When running on the Spark for remote client access, it must be launched with `OLLAMA_HOST=0.0.0.0:11434`.
2. **Inference Latency vs. Frame Rate:** VLMs cannot sustain 30 FPS real-time video streaming. The pipeline uses **on-demand snapshot triggering** or throttled sampling to avoid queuing bottlenecks in GPU memory.
3. **Payload Optimization:** Video frames are resized (e.g., 640x480 or 768x768) and compressed as JPEG before base64 transmission to minimize network serialization overhead.

---

## 3. Step-by-Step Execution Plan

### Step 1: Spark Server Preparation (via SSH / PuTTY)
Check running models and start Ollama bound to all interfaces if not already running:
```bash
# Check available Gemma 3 models
ollama list | grep gemma3

# If Ollama is not listening on 0.0.0.0, run with explicit host:
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Step 2: Client Pre-flight Verification (from Client PC)
Verify remote connectivity from the client machine before launching the video capture:
```bash
# Replace <SPARK_IP> with the actual DGX Spark IP address
curl http://<SPARK_IP>:11434/api/tags
```

### Step 3: Client Workspace & Execution
Install client prerequisites and launch the webcam interaction client:
```bash
pip install opencv-python requests
python3 webcam_vlm.py --host http://<SPARK_IP>:11434 --model gemma3:4b
```

### Step 4: Live Multimodal Evaluation
1. Point the camera at objects, handwritten notes, or diagrams.
2. Press `SPACE` to capture a frame and send an analytical prompt (e.g., "Describe what you see", "Transcribe the text in the image", "Identify any potential safety hazard").
3. Switch models (`gemma3:12b` or `gemma3:27b`) to evaluate differences in reasoning depth, hallucination rate, and response latency.

---

## 4. Execution Log & Metrics

*(To be recorded during the live lab session)*

| Model | Memory Footprint | First Token Latency | Generation Speed | Visual Accuracy Score (1-5) |
| :--- | :--- | :--- | :--- | :--- |
| **Gemma 3 4B** | ~4–6 GB | | | |
| **Gemma 3 12B** | ~9–12 GB | | | |
| **Gemma 3 27B** | ~18–24 GB | | | |

---

## 5. Deliverables & Lab Criteria

- **Execution guide:** [labs/lab2/README.md](file:///home/jr_g/Develop/IA_Aplicada/labs/lab2/README.md)
- **Client code:** [labs/lab2/webcam_vlm.py](file:///home/jr_g/Develop/IA_Aplicada/labs/lab2/webcam_vlm.py)
- **Observations and metrics report:** Recorded latency numbers, token counts, and qualitative findings on vision tasks.
