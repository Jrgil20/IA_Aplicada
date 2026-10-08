#!/usr/bin/env python3
"""
Interactive Multimodal Webcam Client for Gemma 3 on DGX Spark.

Captures frames from a local webcam, encodes them as JPEG Base64, and sends
them to an Ollama instance running on an NVIDIA DGX Spark workstation.

Usage:
    python3 webcam_vlm.py --host http://<SPARK_IP>:11434 --model gemma3:4b
"""

import argparse
import base64
import json
import sys
import time
from typing import Optional, Tuple

try:
    import cv2
except ImportError:
    sys.exit("Error: opencv-python is required. Install via: pip install opencv-python")

try:
    import requests
except ImportError:
    requests = None
    import urllib.request
    import urllib.error


class VLMClient:
    """Client for dispatching multimodal prompts to Ollama."""

    def __init__(self, host: str, model: str, timeout: int = 30):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.endpoint = f"{self.host}/api/chat"

    def query_image(self, prompt: str, image_b64: str) -> Tuple[Optional[str], float]:
        """
        Send image and text prompt to Ollama.
        Returns a tuple of (response_text, latency_seconds).
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }
            ],
            "stream": False,
        }

        start_time = time.time()
        try:
            if requests:
                res = requests.post(self.endpoint, json=payload, timeout=self.timeout)
                res.raise_for_status()
                data = res.json()
            else:
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    self.endpoint,
                    data=req_data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

            latency = time.time() - start_time
            content = data.get("message", {}).get("content", "").strip()
            return content, latency
        except Exception as err:
            latency = time.time() - start_time
            print(f"\n[Error querying VLM]: {err}")
            return None, latency


def encode_frame_to_base64(frame, max_width: int = 640, quality: int = 80) -> str:
    """Resize and encode an OpenCV BGR frame to JPEG base64 string."""
    height, width = frame.shape[:2]
    if width > max_width:
        scale = max_width / float(width)
        new_height = int(height * scale)
        frame = cv2.resize(frame, (max_width, new_height), interpolation=cv2.INTER_AREA)

    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buffer = cv2.imencode(".jpg", frame, encode_params)
    if not success:
        raise ValueError("Failed to encode frame to JPEG")

    return base64.b64encode(buffer).decode("utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive Webcam Client for Gemma 3 VLM"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://localhost:11434",
        help="Ollama host endpoint (e.g. http://192.168.1.50:11434)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemma3:4b",
        help="Model name (e.g. gemma3:4b, gemma3:12b, gemma3:27b)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera device index (default: 0)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Describe detalladamente lo que ves en esta imagen en español.",
        help="Initial prompt for visual analysis",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=640,
        help="Maximum width to resize frame before sending (default: 640)",
    )

    args = parser.parse_args()

    client = VLMClient(host=args.host, model=args.model)
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        sys.exit(f"Error: Unable to open camera device index {args.camera}")

    print("\n" + "=" * 60)
    print("  Interacción con Gemma 3 VLM — DGX Spark")
    print(f"  Servidor : {args.host}")
    print(f"  Modelo   : {args.model}")
    print(f"  Prompt   : {args.prompt}")
    print("=" * 60)
    print("Controles:")
    print("  [ESPACIO] : Capturar y analizar frame")
    print("  [P]       : Cambiar el texto del prompt")
    print("  [A]       : Alternar modo automático (cada 4 seg)")
    print("  [Q / ESC] : Salir")
    print("=" * 60 + "\n")

    current_prompt = args.prompt
    last_response = "Presiona [ESPACIO] para capturar."
    last_latency = 0.0
    auto_mode = False
    last_auto_time = 0.0
    is_processing = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Fallo al capturar frame de la webcam.")
                break

            current_time = time.time()

            # Automatic sampling check
            if auto_mode and not is_processing and (current_time - last_auto_time >= 4.0):
                is_processing = True
                print("\n[Auto] Capturando frame...")
                b64_img = encode_frame_to_base64(frame, max_width=args.max_width)
                resp, latency = client.query_image(current_prompt, b64_img)
                last_latency = latency
                last_auto_time = time.time()
                is_processing = False

                if resp:
                    last_response = resp
                    print(f"\n[Gemma 3 ({latency:.2f}s)]:\n{resp}\n")

            # Draw status on the frame
            display_frame = frame.copy()
            status_text = f"Modo: {'AUTO (4s)' if auto_mode else 'MANUAL'} | Modelo: {args.model}"
            cv2.putText(
                display_frame,
                status_text,
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            if last_latency > 0:
                perf_text = f"Latencia: {last_latency:.2f}s"
                cv2.putText(
                    display_frame,
                    perf_text,
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )

            cv2.imshow("VLM Webcam Interaction (DGX Spark)", display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):  # 'q' or ESC
                break
            elif key == ord(" "):  # Spacebar snapshot
                print(f"\n[Captura iniciada] Enviando frame con prompt: '{current_prompt}'...")
                b64_img = encode_frame_to_base64(frame, max_width=args.max_width)
                resp, latency = client.query_image(current_prompt, b64_img)
                last_latency = latency
                if resp:
                    last_response = resp
                    print(f"\n[Gemma 3 ({latency:.2f}s)]:\n{resp}\n")
                else:
                    print("\n[Error]: No se recibió respuesta del modelo.")
            elif key == ord("p"):  # Change prompt
                new_prompt = input("\nIngresa el nuevo prompt para el VLM: ").strip()
                if new_prompt:
                    current_prompt = new_prompt
                    print(f"Prompt actualizado a: '{current_prompt}'")
            elif key == ord("a"):  # Toggle auto mode
                auto_mode = not auto_mode
                print(f"Modo automático {'ACTIVADO' if auto_mode else 'DESACTIVADO'}.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\nSesión finalizada.")


if __name__ == "__main__":
    main()
