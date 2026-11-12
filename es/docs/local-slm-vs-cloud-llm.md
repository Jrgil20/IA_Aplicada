# Guía Arquitectónica: SLMs Locales vs. LLMs Frontera en la Nube

> **Registro de decisión arquitectónica (ADR) y análisis de trade-offs.** Evalúa cuándo operar modelos locales pequeños (SLMs / 1.5B–30B) tiene sentido técnico y financiero frente al consumo de APIs de modelos frontera en la nube (Gemini, Claude, OpenAI), basándose en benchmarks empíricos y economía de hardware.

---

## 1. Resumen Ejecutivo y Realidad de la Arquitectura

Los modelos de frontera en la nube (como Gemini 1.5/2.0/3.8 Flash, Claude Sonnet o GPT-4o) se ejecutan sobre centros de datos masivos (pods de TPUs, infraestructura NVLink H100/B200) con cientos de miles de millones de parámetros activos, ventanas de contexto de millones de tokens y técnicas avanzadas de RLHF/RLAIF.

Un modelo local restringido a hardware de consumo o estaciones de trabajo de borde (8 GB–48 GB de VRAM, corriendo modelos cuantizados a 4 bits como Qwen-1.5B, 7B o 30B) **no puede competir en diseño arquitectónico general de software ni en razonamiento multiturno complejo**.

Intentar reemplazar modelos de frontera con modelos locales para desarrollo de software general es un antipatrón. Sin embargo, los SLMs locales poseen ventajas operativas determinantes en tres nichos específicos: **latencia sub-50ms**, **privacidad estricta air-gapped sin salida a internet (zero egress)** y **especialización de dominio vía fine-tuning (PEFT/LoRA)**.

---

## 2. Matriz de Comparativa Técnica

| Dimensión de Evaluación | LLMs Frontera en la Nube (ej. Gemini Flash, Claude) | SLMs / Modelos Locales (1.5B – 30B, Cuantizados Q4) |
| :--- | :--- | :--- |
| **Infraestructura de Cómputo** | Clusters masivos distribuidos de TPU/GPU | GPU única local / Memoria unificada (GB10, RTX 3090/4090, Apple Silicon) |
| **Escala Efectiva de Parámetros** | Cientos de miles de millones (arquitecturas MoE) | 1.5B a 32B densos/MoE |
| **Límite de Tokens de Salida** | 8.192 – 64.000+ tokens por turno | Habitualmente restringido a 2.048 – 5.120 tokens por slot (por memoria KV) |
| **Tiempo al Primer Token (TTFT)**| 150 ms – 600 ms (gobernado por latencia de red y colas) | **10 ms – 40 ms** (en bus PCIe / memoria unificada local) |
| **Calidad de Código General** | Alta cohesión estructural, diseño de clases OOP, robustez | Código plano o en un solo archivo; propenso a truncarse en tareas complejas |
| **Gasto de Capital en Hardware** | $0 inicial; pago por uso según consumo de tokens | $1.500 – $6.000+ USD en hardware con VRAM especializada |
| **Ciclo de Obsolescencia** | Actualizaciones continuas en la nube sin costo de mantenimiento | Pesos fijos al descargar; obsolescencia tecnológica en 3–6 meses |
| **Operación Offline / Air-Gapped** | Imposible (requiere conexión constante a internet) | **100% autónomo, cero dependencias externas** |
| **Costo a Escala Baja/Media** | Insignificante ($0.10 – $0.35 por millón de tokens) | Alto (depreciación de hardware, electricidad, mantenimiento) |
| **Costo a Escala Masiva** | Escala linealmente ($$$$ con miles de millones de tokens/mes) | **Costo fijo de hardware ($0 costo marginal por token)** |

---

## 3. Casos de Uso Válidos para SLMs Locales

Ejecutar modelos en local se justifica técnica y económicamente **únicamente** en los siguientes escenarios:

### 3.1. Autocompletado en Línea en Tiempo Real (Sub-50ms)
- **Problema:** Las llamadas a APIs en la nube sufren latencia de red (DNS + handshake TLS + saltos de red = 150–350 ms TTFT). Esto introduce un retraso perceptible al escribir código activamente.
- **Solución:** Un modelo de 1.5B–3B (ej. Qwen2.5-Coder-1.5B, DeepSeek-Coder-1.3B) corriendo sobre CPU/iGPU con `llama.cpp` entrega 30–70 tok/s con un TTFT < 30 ms.

### 3.2. Entornos Air-Gapped y Cumplimiento Normativo (Cero Fuga de Datos)
- **Problema:** Industrias reguladas (defensa, banca, salud bajo HIPAA/GDPR) prohíben por ley que código propietario cruce las fronteras de la red corporativa.
- **Solución:** Estaciones de trabajo desconectadas o servidores on-premises con pesos abiertos cuantizados y endpoints de inferencia locales auditables.

### 3.3. Fine-Tuning Específico con LoRA/QLoRA (Especialización en el Edge)
- **Problema:** Los modelos generales en la nube carecen de apego determinista a estándares internos muy estrictos (ej. linting AST propietario, DSLs internas o reglas de Clean Architecture).
- **Solución:** Entrenar un modelo liviano (1.5B o 7B) mediante adaptadores de bajo rango (LoRA) con datasets sintéticos curados (como se demostró en el proyecto de semestre *Edge Clean Copilot*). Un modelo de 1.5B ajustado puede superar a un modelo general de 70B en una tarea de transformación acotada y determinista.

---

## 4. Dimensionamiento de Hardware y Umbrales Económicos

### 4.1. Ecuación: Gasto de Capital vs. Presupuesto de Tokens
Para correr un modelo de 30B con 4 slots concurrentes a 32k de contexto se requieren **~24 GB a 32 GB de VRAM de alta velocidad**:

$$\text{Costo Total de Estación Local} \approx \$2.500 - \$4.500 \text{ USD}$$

A los precios actuales de APIs de frontera:
- Gemini 2.0/3.8 Flash: $\approx \$0.15 \text{ por 1.000.000 tokens}$
- $\$3.000 \text{ USD} = 20.000.000.000 \text{ tokens (20 mil millones de tokens)}$

> [!IMPORTANT]
> Un desarrollador típico consume entre 10 y 30 millones de tokens al año usando asistentes de código de forma intensiva. Una compra de \$3.000 en hardware equivale a **décadas de consumo de APIs en la nube**, tiempo durante el cual el hardware local se deprecia y queda obsoleto.

### 4.2. Matriz de Dimensionamiento de Hardware

| Perfil de Modelo | VRAM / RAM Unificada Requerida | Objetivo Mínimo de Hardware | Rol Arquitectónico Viable |
| :--- | :--- | :--- | :--- |
| **SLM Diminuto (1.5B – 3B Q4)** | 2 GB – 4 GB | Laptop comercial CPU, iGPU, Apple Silicon (8 GB) | Autocompletado de código, linting AST local |
| **SLM Mediano (7B – 8B Q4)** | 6 GB – 8 GB | GPU de entrada (RTX 3060/4060, Apple 16 GB) | Agente conversacional offline, resumen de commits |
| **SLM Pesado (14B – 32B Q4)** | 16 GB – 24 GB | RTX 3090 / 4090 (24 GB) o Apple Silicon (32 GB+) | Generación sintética batch local, evaluación offline |
| **MoE / Frontera (70B+ Q4)** | 48 GB – 128 GB | Doble RTX 3090/4090, NVIDIA DGX Spark, Mac Studio 128 GB | Staging corporativo on-prem, inferencia departamental |

---

## 5. Recomendación Arquitectónica: Patrón Híbrido por Capas

En lugar de elegir ciegamente entre la nube o local, la ingeniería de software moderna con IA adopta el **Patrón de Inversión por Capas**:

```
+-------------------------------------------------------------------------+
|                       Capa 1: Frontera Cloud (Cerebro)                  |
|                (Gemini Flash / Claude Sonnet / GPT-4o)                  |
|  - Arquitectura de sistemas y descomposición de especificaciones        |
|  - Refactorización multi-archivo en Clean Architecture                  |
|  - Orquestación de motores gráficos y audio procedural                   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                     Capa 2: SLMs en el Edge/Local (Brazos)              |
|               (Qwen2.5-Coder-1.5B / 7B sobre llama.cpp)                 |
|  - Autocompletado continuo por pulsación de tecla (< 40ms TTFT)         |
|  - Modo offline ante caídas de conexión WAN                             |
|  - Linting determinista de AST y generación de boilerplate repetitivo   |
+-------------------------------------------------------------------------+
```

### Regla de Oro para Arquitectos
- **No compres hardware dedicado únicamente para simular razonamiento general de la nube.**
- **Utilizá modelos de frontera en la nube para ideación, planeamiento, revisión arquitectónica y síntesis pesada.**
- **Desplegá SLMs locales especializados para ejecución determinista, offline, ultrarrápida y de alta frecuencia en el borde.**
