# Guía de Referencia: NVIDIA DGX Spark

Guía técnica y operativa para el desarrollo, entrenamiento e inferencia en la estación de trabajo **NVIDIA DGX Spark**.

---

## 1. Arquitectura de Hardware

La NVIDIA DGX Spark es una estación de supercómputo de escritorio compacta ("AI desktop supercomputer") diseñada para prototipado, fine-tuning y despliegue local de modelos de lenguaje e inteligencia artificial.

| Componente | Especificación Técnica |
| :--- | :--- |
| **Superchip** | **NVIDIA GB10 (Grace Blackwell)** |
| **CPU** | 20 núcleos Arm (10 Performance + 10 Efficiency cores) |
| **GPU** | Arquitectura NVIDIA Blackwell |
| **Memoria del Sistema** | **128 GB LPDDR5x unificada y coherente** (espacio compartido CPU/GPU) |
| **Rendimiento AI** | ~1 PFLOPS (1.000 AI TOPS) |
| **Conectividad / Red** | NVIDIA ConnectX-7 (hasta 200 GbE para clustering multi-nodo) |
| **Factor de Forma** | Escritorio compacto (desktop workstation silencioso) |

> [!NOTE]
> La **memoria unificada coherente de 128 GB** permite cargar y entrenar modelos con huellas de memoria que exceden la VRAM de GPUs dedicadas convencionales de consumo, eliminando cuellos de botella de transferencia PCIe CPU-GPU.

---

## 2. Stack de Software y Sistema Operativo

La estación opera bajo **NVIDIA DGX OS** (distribución optimizada basada en Ubuntu Linux):

- **Drivers & Runtime:** Drivers NVIDIA propietarios preinstalados, CUDA Toolkit, cuDNN y TensorRT.
- **Contenedores:** **NVIDIA Container Toolkit** (`nvidia-docker`) preconfigurado de fábrica para imágenes de NVIDIA NGC.
- **Frameworks Soportados:** PyTorch (nativo CUDA/aarch64), Hugging Face (`transformers`, `peft`, `bitsandbytes`), `vLLM`, `Ollama`, `llama.cpp` y microservicios NVIDIA NIM.

---

## 3. Conexión y Flujo de Desarrollo Remoto

Para las sesiones de trabajo en el laboratorio de la UCAB, el acceso habitual se realiza vía red:

### 3.1 Conexión SSH
```bash
# Conexión remota por terminal
ssh <usuario>@<dgx-spark-ip>
```

### 3.2 Desarrollo con VS Code Remote
1. Instalar la extensión **Remote - SSH** en Visual Studio Code local.
2. Conectar a `Host dgx-spark` configurando `~/.ssh/config`.
3. Abrir la carpeta del repositorio directamente en el sistema de archivos de la DGX Spark.

### 3.3 Sincronización de Archivos
* **Git:** Clonar y pushear ramas intermedias al repositorio remoto.
* **Rsync:** Para transferir pesos o datasets locales:
```bash
rsync -avzP ./dataset.jsonl <usuario>@<dgx-spark-ip>:~/Develop/IA_Aplicada/data/
```

---

## 4. Comandos Esenciales en DGX OS

### 4.1 Monitoreo de Recursos
```bash
# Estado de GPU y memoria unificada
nvidia-smi

# Monitoreo en tiempo real cada segundo
watch -n 1 nvidia-smi

# Monitoreo de núcleos CPU Arm y memoria RAM del sistema
htop
```

### 4.2 Ejecución de Contenedores NGC
```bash
# Lanzar un contenedor interactivo de PyTorch con soporte GPU completo
docker run --gpus all --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -it --rm -v $(pwd):/workspace nvcr.io/nvidia/pytorch:latest
```

### 4.3 Servidor de Inferencia Local (`llama-server`)
```bash
# Levantar el teacher model (Qwen 30B GGUF) en la DGX Spark
llama-server \
  -m /modelos/qwen3-coder-30b.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 8192 \
  --n-gpu-layers 99
```

---

## 5. Metodología: "Staging en Frío, Ráfaga en Caliente"

Dado el presupuesto de cómputo limitado (sesiones de ~2 horas semanales en la DGX Spark):

1. **Pre-laboratorio (en laptop):**
   - Validar sintaxis de datasets JSONL.
   - Ejecutar pruebas sintéticas de 1 solo step en CPU para verificar que los scripts de entrenamiento no crasheen por dependencias o formato.
2. **En DGX Spark:**
   - Montar el entorno o levantar el contenedor pre-aprobado.
   - Lanzar la ráfaga de fine-tuning LoRA (20 a 40 minutos).
   - Fusionar adaptadores (`merge_and_unload`).
   - Cuantizar inmediatamente a formato GGUF (`Q4_K_M`, `Q5_K_M`).
3. **Post-laboratorio (en laptop):**
   - Descargar el binario `.gguf` cuantizado.
   - Evaluar métricas de rendimiento y adherencia arquitectónica en local sin consumir tiempo de la DGX Spark.

---

## 6. Recursos Oficiales y Playbooks

- **Documentación Central:** [NVIDIA DGX Spark User Guide](https://docs.nvidia.com/dgx/dgx-spark/)
- **Guía de Sistema Operativo:** [NVIDIA DGX OS Documentation](https://docs.nvidia.com/dgx/dgx-os-7-user-guide/introduction.html)
- **Playbooks de Cargas de Trabajo (GitHub):** [NVIDIA/dgx-spark-playbooks](https://github.com/NVIDIA/dgx-spark-playbooks)
- **Portal de Desarrolladores:** [NVIDIA Spark Developer Portal](https://build.nvidia.com/spark)
