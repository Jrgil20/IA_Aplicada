# Caché de Prompts: Tipos, Cuándo Usarlos, Cifras y Trampas

> **Referencia AI-first.** "Caché" abarca tres mecanismos distintos con ahorros y riesgos diferentes. Parte del conjunto de ruteo por costo: [Enrutamiento por Costo](./enrutamiento-por-costo.md), [Casos de Uso](./casos-de-uso-ia-aplicada.md), [Escalado](./escalado-cargas-ia.md), [Playbook: Costos y Ahorros](./playbook/costos-y-ahorros.md).
>
> **Estado de verificación (2026-11-17):** las cifras de Anthropic provienen de la referencia de la API de Claude incluida en Claude Code (precios en caché del 2026-11-03); precios y multiplicadores confirmados contra la página oficial de precios el 2026-11-17. Los flags de `llama.cpp` se leyeron de `llama-server --help` en el build local `0.8.0-dev (build 11982)`. El comportamiento de vLLM proviene de la documentación oficial de vLLM. Los precios y valores por defecto cambian: volver a verificarlos antes de depender de ellos.

---

## 1. Tres Mecanismos

| Mecanismo | Qué se reutiliza | Dónde | ¿Se sigue llamando al modelo? |
|-----------|------------------|-------|-------------------------------|
| Caché de respuesta (exacta) | Respuesta completa de una solicitud idéntica | Tu aplicación | No |
| Caché semántica | Respuesta de una solicitud similar (coincidencia por embeddings) | Tu aplicación | No |
| Caché de prefijo de prompt / KV | Cómputo sobre un prefijo de prompt estable | API del proveedor, `llama.cpp`, vLLM | Sí (solo se procesa el sufijo nuevo) |

## 2. Cuándo Usar Cada Uno

| Mecanismo | Usar cuando | Evitar cuando |
|-----------|-------------|---------------|
| Caché de respuesta exacta | La misma entrada se repite y la respuesta es determinista y no depende del tiempo | La respuesta depende de datos cambiantes o del contexto del usuario |
| Caché semántica | Muchas FAQ parafraseadas | Una respuesta casi correcta es dañina (código, números, texto legal/de seguridad); un acierto erróneo devuelve una respuesta incorrecta con total seguridad |
| Caché de prefijo de prompt | Prefijo estático grande (system prompt, definiciones de herramientas, documentos) reutilizado entre llamadas | El prefijo cambia en cada llamada, el prompt está por debajo del tamaño mínimo, o las llamadas están más separadas que el TTL |

## 3. Caché de Prefijo en la API de Claude (verificado)

### 3.1 Mecánica

| Hecho | Detalle |
|-------|---------|
| Coincidencia | Prefijo exacto byte a byte. Cualquier cambio invalida todo lo que viene después |
| Orden de renderizado | `tools` → `system` → `messages`; colocar primero el contenido estable |
| Marcadores | `cache_control: {"type": "ephemeral"}` en un bloque, o caché automática a nivel superior de la solicitud |
| Puntos de corte | Máximo 4 por solicitud |
| TTL | 5 minutos por defecto; `"ttl": "1h"` para 1 hora. Una lectura de caché renueva el temporizador sin costo |
| Prefijo mínimo | Depende del modelo: 512 tokens en los modelos más nuevos (Opus 5.5, Sonnet 5.5, Haiku 5.5); 1024–4096 en los anteriores (p. ej. 4096 en Haiku 4.5). Los prefijos más cortos no se cachean, sin aviso |
| Alcance | Las cachés son por modelo: cambiar de modelo (por ejemplo en una cascada) no reutiliza la caché |

### 3.2 Economía

| Operación | Precio relativo a la entrada base |
|-----------|-----------------------------------|
| Escritura de caché, TTL de 5 minutos | 1.25× |
| Escritura de caché, TTL de 1 hora | 2× |
| Lectura de caché | ~0.1× (0.05× en Opus 5.5 y Sonnet 5.5; 0.025× en Fable 5.1/5.2) |
| Batch API | 50% de descuento en cada token, incluidas lecturas y escrituras de caché (los descuentos se acumulan) |

**Punto de equilibrio:** con un TTL de 5 minutos, dos solicitudes ya compensan (1.25 + 0.1 = 1.35× vs. 2× sin caché). Con un TTL de 1 hora se necesitan al menos tres (2 + 0.2 = 2.2× vs. 3×).

**Elegir el TTL:**

| Intervalo entre solicitudes que comparten el prefijo | TTL |
|------------------------------------------------------|-----|
| Menos de 5 minutos (tráfico continuo, bucles de agentes) | 5 minutos (cada solicitud lo renueva) |
| De 5 a 60 minutos (el usuario responde más tarde, tareas secundarias lentas) | 1 hora |
| Más de 60 minutos | La caché rara vez compensa; reconsiderar |

### 3.3 Verificar los Aciertos, No Suponerlos

| Campo de uso | Significado |
|--------------|-------------|
| `cache_creation_input_tokens` | Tokens escritos en esta solicitud (se pagó el recargo de escritura) |
| `cache_read_input_tokens` | Tokens servidos desde la caché (se pagó la tarifa de lectura) |
| `input_tokens` | Solo el resto no cacheado |

Tamaño total del prompt = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. Si `cache_read_input_tokens` se mantiene en cero entre solicitudes idénticas, hay un invalidador silencioso actuando.

### 3.4 Invalidadores Silenciosos

| Invalidador | Solución |
|-------------|----------|
| Timestamp o ID de solicitud en el system prompt | Moverlo después del último punto de corte |
| JSON sin ordenar o lista de herramientas construida en orden variable | Serializar de forma determinista |
| El conjunto de herramientas cambia entre llamadas | Mantener una lista de herramientas fija |
| Cambiar de modelo o la configuración de thinking/effort a mitad de la conversación | Mantenerlos estables por conversación |

## 4. Servicio Local

### 4.1 `llama.cpp` (`llama-server`, verificado en el build local 0.8.0-dev)

| Flag | Valor por defecto | Efecto |
|------|-------------------|--------|
| `--cache-prompt` | Habilitado | Reutiliza la caché KV de un prefijo de prompt coincidente entre solicitudes |
| `--cache-reuse N` | 0 (desactivado) | Tamaño mínimo de fragmento para reutilizar KV en caché mediante desplazamiento, cuando el prefijo no es idéntico |
| `-sps, --slot-prompt-similarity` | 0.10 | Cuánto debe parecerse un prompt al prompt de un slot para reutilizar ese slot |
| `-cram, --cache-ram N` | 8192 MiB | Límite superior de la caché de prompts mantenida en RAM |
| `--slot-save-path` | Deshabilitado | Persistir en disco las cachés KV de los slots |

Útil en hardware solo CPU, donde el procesamiento del prompt domina la latencia. Medir antes de documentar cualquier ganancia.

### 4.2 vLLM

vLLM implementa caché automática de prefijos mediante su caché KV paginada. Si está activa por defecto depende de la versión y del tipo de modelo (el motor registra en el log si la habilitó); revisar el log de arranque y la documentación de la versión en uso.

## 5. Dónde Encaja en la Cascada

```
consulta → compuerta de política → [caché exacta / semántica] → reglas → SLM local (caché de prefijo) → LLM en la nube (caché de prefijo)
```

Las cachés de respuesta están en el nivel 1 y evitan la inferencia por completo. Las cachés de prefijo están dentro de los niveles de modelo y abaratan cada llamada. Hay una tensión: como las cachés del proveedor son por modelo, una cascada multimodelo renuncia a reutilizar la caché entre niveles.

## 6. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Respuestas obsoletas | TTL e invalidación al cambiar la fuente |
| Falsos positivos semánticos | Umbral de similitud alto, validar con un conjunto etiquetado, excluir tareas de alto riesgo |
| Filtración entre usuarios | Acotar las claves de caché por usuario/tenant; nunca compartir cachés entre fronteras de privacidad |
| Pérdida de calidad oculta | Evaluar respuestas cacheadas vs. frescas con el benchmark |
| Regresión de costo silenciosa | Monitorear `cache_read_input_tokens` de forma continua, no solo durante la configuración |
