# Servir Modelos para Aplicaciones Reales

> **Guía operativa AI-first.** Cómo ejecutar un modelo detrás de una app real: elección de runtime, planificación de capacidad, topología, escalado y checklist de producción. Se apoya en lecciones registradas en este repo. No se afirman cifras de benchmark; medir en tu hardware. Relacionado: [Playbook: Preparación para Producción](./playbook/preparacion-para-produccion.md), [Selección de Modelos](./seleccion-de-modelos.md), [Escalado de Cargas de IA](./escalado-cargas-ia.md), [Caché de Prompts](./cache-de-prompts.md), [SLMs Locales vs. LLMs en la Nube](./local-slm-vs-cloud-llm.md).
>
> **Estado de verificación (2026-11-17):** flags y valores por defecto de `llama-server` leídos de `llama-server --help` en el build local `0.8.0-dev (build 11982)`. Datos de vLLM tomados de la documentación oficial de vLLM (estable). Los valores por defecto cambian entre builds: revisar siempre `--help` en el build que se despliega.

---

## 1. Elección de Runtime

| Runtime | Fortalezas | Límites | Elegir cuando |
|---------|------------|---------|---------------|
| `llama.cpp` `llama-server` | Cuantización GGUF, CPU/GPU/Apple Silicon, huella pequeña, slots paralelos con batching continuo, API HTTP estilo OpenAI, API keys y métricas Prometheus integradas | El throughput con mucha concurrencia es menor que el de servidores orientados a GPU | Borde, laptop, una sola GPU, pocos usuarios concurrentes (usado en este repo) |
| vLLM | Orientado a GPU, caché KV paginada (PagedAttention), batching continuo, caché de prefijos, servidor compatible con OpenAI; también carga GGUF | Requiere una GPU compatible; instalación más pesada; para cargar GGUF recomienda el tokenizador del modelo base | Muchos usuarios concurrentes en un servidor con GPU |
| Ollama | Instalación y gestión de modelos sencillas (construido sobre `llama.cpp`) | Menos control sobre los flags de servicio | Máquinas de desarrollo, prototipos |
| API hospedada | Sin hardware, modelos de frontera, capacidad elástica, caché y batching del lado del proveedor | Costo por token, los datos salen de tu frontera, rate limits | Razonamiento de frontera, carga en ráfagas o desconocida |

## 2. Flags de `llama-server` Importantes en Producción

| Flag | Valor por defecto (build 0.8.0-dev) | Por qué importa |
|------|-------------------------------------|-----------------|
| `--host` | `127.0.0.1` | Valor por defecto seguro; no cambiarlo a `0.0.0.0` sin autenticación y un gateway |
| `--port` | `9931` en este build (builds anteriores y los scripts del repo usan `8080`/`8085`) | Fijarlo explícitamente en los scripts |
| `-c, --ctx-size` | `0` = tomado del modelo | Presupuesto total de KV |
| `-np, --parallel` | `-1` = automático | Número de slots concurrentes |
| `-kvu, --kv-unified` | Activo cuando los slots son automáticos | Un único buffer KV compartido entre secuencias |
| `--kv-unified-per-slot N` | Sin definir | Limita el contexto por slot |
| `-cb, --cont-batching` | Habilitado | Batching continuo (dinámico) |
| `--cache-prompt` | Habilitado | Reutilización de KV del prefijo entre solicitudes |
| `--api-key` / `--api-key-file` | Ninguno | Exigir una clave en las solicitudes |
| `--metrics` | Deshabilitado | Endpoint de métricas compatible con Prometheus |
| `-ngl` | Depende del build | Capas descargadas a la GPU (`-ngl 0` = solo CPU, como se usó para los ≈12 tok/s medidos) |

## 3. Planificación de Capacidad

| Componente | Cómo dimensionar |
|------------|------------------|
| Memoria de pesos | Usar el tamaño real del archivo cuantizado (p. ej. el `.gguf`), no bits nominales × parámetros |
| Caché KV | `2 × layers × kv_heads × head_dim × bytes_per_value × context_tokens × concurrent_sequences` (valores de la config del modelo) |
| Sobrecarga | Dejar margen para activaciones, buffers del runtime, la caché de prompts (`--cache-ram`) y el SO |
| Contexto por usuario | Con una KV dividida (no unificada), contexto total ÷ slots |

### Ejemplo trabajado de KV (solo el método)

Para un modelo con 28 capas, 4 cabezas KV, dimensión de cabeza 128 y caché FP16 (2 bytes):

```
per token = 2 × 28 × 4 × 128 × 2 bytes = 57,344 bytes ≈ 56 KiB
4,096 tokens × 1 sequence ≈ 224 MiB
```

Leer los valores reales del `config.json` del modelo o de los metadatos GGUF antes de dimensionar; las cifras anteriores solo muestran la aritmética.

### Lección de este repo: los slots pueden dividir el contexto

Durante el Lab 4/6, `llama-server -c 4096` se ejecutó con 4 slots, así que cada conversación recibió **1024 tokens** y perdió contexto tras pocos turnos (ver `qlora/POST_MORTEM_FAILURE_ANALYSIS.md`). Ese build dividía el contexto en partes iguales entre los slots. El build local actual usa por defecto slots automáticos con un buffer KV unificado, que se comporta de otra manera. Regla válida en ambos casos: **conocer el número de slots y el contexto por slot**, fijar `-np` explícitamente y dimensionar `-c` para `slots × contexto necesario` (o usar `--kv-unified-per-slot`). Para un asistente de un solo usuario, `-np 1` da a una conversación la ventana completa.

### Lección: aislar instancias

Instancias concurrentes de `llama-server` en puertos distintos (p. ej. `8085` vs `8080`) mantienen separados los buffers de memoria y las colas de slots, así las corridas de evaluación no perturban el tráfico en vivo (ver `proyecto/docs/history/session-2026-10-22-burst-and-lessons.md`).

## 4. Topologías de Despliegue

| Topología | Descripción | Encaja en |
|-----------|-------------|-----------|
| Proceso embebido / local | La app lanza o consulta un servidor local en `127.0.0.1` | Herramientas de escritorio, CLI (p. ej. `clean-copilot`) |
| Servidor único | Un servidor de modelo; la app lo llama por HTTP | Equipo pequeño, herramienta interna |
| Réplicas + balanceador de carga | N servidores idénticos detrás de un balanceador | Más usuarios concurrentes de los que atiende un servidor |
| Pools separados | Servidores distintos por modelo (pequeño/rápido vs. grande) con un router | Cascada por costo ([Enrutamiento por Costo](./enrutamiento-por-costo.md)) |
| GPU remota por túnel | Servidor en el DGX Spark, accedido por túnel SSH | Cómputo en ráfagas; ver el skill `secure-ssh-tunnels` |
| Híbrida | Modelo local para trabajo privado o sencillo, API hospedada para el resto | Privacidad más calidad de frontera ([Playbook: Decisiones de Nivel de Modelo](./playbook/decisiones-de-nivel-de-modelo.md)) |

## 5. Patrones de Escalado

| Cuello de botella | Acción |
|-------------------|--------|
| Las solicitudes hacen cola | Más slots/réplicas, o un runtime con batching más potente (vLLM en GPU) |
| Los prompts largos dominan la latencia | Caché de prefijos ([Caché de Prompts](./cache-de-prompts.md)), prompts más cortos |
| Memoria agotada | Modelo más pequeño o cuantización, menos contexto, menos slots, caché de prompts más pequeña |
| El problema es la calidad, no la velocidad | Mejor modelo o mejores datos; más hardware no ayudará |
| Carga con picos | API hospedada para el desborde |

Medir primero: registrar time-to-first-token, tokens/s, profundidad de cola y tasa de error bajo una carga realista antes de escalar (`--metrics` expone las cifras del lado del servidor).

## 6. Checklist de Producción

| Área | Requisito |
|------|-----------|
| Red | Enlazar a `127.0.0.1` o a una interfaz privada; exponer solo mediante un gateway o un túnel |
| Autenticación | `--api-key` más un gateway. **Advertencia sobre vLLM:** su `--api-key` solo cubre los prefijos `/v1`, `/v2`, `/inference` y `/cohere`. Los demás endpoints quedan sin autenticar, incluidos `/invocations` (la misma inferencia que `/v1`), controles operativos como `/pause`, `/abort_requests` y `/update_weights`, y utilidades como `/metrics` y `/tokenize`. Nunca exponer vLLM directamente; poner delante un proxy inverso que permita solo los endpoints necesarios (documentación de seguridad de vLLM, consultada 2026-11-17) |
| Límites | Máximo de tokens, timeout de solicitud, tope de tamaño de entrada, rate limits |
| Salud | Endpoint de salud, política de reinicio, readiness antes de enrutar tráfico |
| Observabilidad | Latencia, tokens, errores, nivel de escalado; sin prompts sensibles en los logs |
| Seguridad | Tratar la salida del modelo como no confiable; defenderse de prompt injection (ver el skill `inference-security-hardening` y [Playbook: Hardening](./playbook/checklist-de-hardening.md)) |
| Artefactos | Fijar el hash del archivo del modelo y la versión del runtime; nunca commitear pesos |
| Rollback | Conservar el artefacto del modelo anterior y un cambio de vuelta en un solo paso |
