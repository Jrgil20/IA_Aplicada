# Checklist de Hardening para Funciones de IA

> **Checklist de seguridad.** Cubre las principales clases de fallo de funciones respaldadas por LLM. Para auditorías y detalles de implementación usar los skills `inference-security-hardening` (servidores de inferencia, inyección en VLM y agentes) y `secure-ssh-tunnels` (acceso remoto).

---

## 1. Amenazas y Controles

| Amenaza | Qué ocurre | Controles |
|---------|-----------|-----------|
| Prompt injection (directa) | El texto del usuario anula las instrucciones | Separar instrucciones de datos, restringir lo que el modelo puede hacer, validar salidas |
| Prompt injection (indirecta) | Documentos, páginas web o imágenes traen instrucciones ocultas | Tratar todo contenido recuperado como no confiable; sin herramientas privilegiadas sobre entrada no confiable |
| Fuga de datos | Secretos o datos de otros usuarios aparecen en respuestas | Mantener secretos fuera de los prompts; acotar la recuperación por usuario; acotar cachés por tenant |
| Manejo inseguro de salida | La salida se renderiza o ejecuta de forma insegura (HTML, shell, SQL) | Escapar al renderizar; nunca ejecutar la salida del modelo; consultas parametrizadas |
| Agencia excesiva | El agente realiza acciones dañinas | Herramientas de mínimo privilegio, aprobación humana para acciones riesgosas, límites de pasos |
| Denegación de billetera / servicio | El abuso infla el costo o agota la capacidad | Rate limits, topes de tokens y pasos, alertas de presupuesto |
| Endpoint de inferencia expuesto | Puerto del modelo abierto a cualquiera | Enlazar a interfaz privada, autenticar, solo túnel o gateway |
| Cadena de suministro | Modelos o paquetes maliciosos | Fijar versiones y hashes, fuentes confiables, escanear dependencias |
| Agotamiento de contexto | El dimensionamiento de slots o contexto trunca en silencio | Dimensionar contexto por usuario ([Servir Modelos](../servir-modelos-para-apps.md)) |

## 2. Reglas de Diseño

| Regla | Detalle |
|-------|---------|
| Asumir que el modelo puede ser manipulado | La seguridad no puede depender solo del prompt |
| Autorizar fuera del modelo | El código verifica permisos, no se le pregunta al modelo |
| Mínimo privilegio en herramientas | Solo lectura por defecto; credenciales acotadas |
| Validar en ambos sentidos | Revisar entradas antes de la llamada y salidas después |
| Fallar cerrado | Ante fallo del validador, rechazar o pasar a una persona; no adivinar |

## 3. Infraestructura

| Elemento | Requisito |
|----------|-----------|
| Red | Enlace privado; exponer vía gateway o túnel SSH |
| Autenticación | API key o autenticación en el gateway en cada endpoint. Verificar qué cubre realmente la clave del servidor: el `--api-key` de vLLM protege solo `/v1`, `/v2` e `/inference`, y deja abiertos endpoints como `/invocations` (documentación de vLLM, verificado 2026-11-17). `llama-server` se enlaza a `127.0.0.1` por defecto y admite `--api-key` |
| Secretos | Entorno o gestor de secretos; nunca en prompts, repos ni logs |
| Pesos y artefactos | Nunca commiteados; hash fijado |
| Logging | Sin prompts sensibles; límite de retención |
| Acceso a GPU remota | Solo túneles autorizados (ver el skill `secure-ssh-tunnels`) |

## 4. Probarlo

| Prueba | Ejemplo |
|--------|---------|
| Suite de inyección | Instrucciones ocultas en documentos e imágenes; se espera que se ignoren |
| Prueba de fuga | Pedir el system prompt y datos de otros usuarios |
| Seguridad de salida | Pasar al renderizador salidas con HTML/script/SQL |
| Prueba de abuso | Ráfaga de solicitudes; confirmar que se activan los límites |
| Prueba de frontera de herramientas | Intentar que el agente llame herramientas fuera de su alcance |

Repetir tras cada cambio de modelo, prompt o herramienta.

## 5. Checklist

- [ ] El endpoint es privado y autenticado.
- [ ] El contenido no confiable no puede disparar acciones privilegiadas.
- [ ] Las salidas se validan y escapan antes de usarse.
- [ ] Hay rate limits y topes de tokens/pasos.
- [ ] Secretos y datos sensibles quedan fuera de prompts y logs.
- [ ] Existen pruebas de inyección y fuga, y pasan.
- [ ] Versiones de modelo y dependencias fijadas.
