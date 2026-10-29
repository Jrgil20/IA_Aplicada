# Lab 2 · Conectar el agente a un sistema

La misma empresa de compras del workshop 1, dos semanas después. Ahora los datos viven en un ERP, y el agente se conecta a él con un servidor MCP.

Igual que en el workshop 1: no hay pasos guiados, cada problema dice qué hay que entregar y qué condición tiene que cumplir, y el equipo decide cómo llegar ahí. Discutan entre los tres antes de escribirle al agente.

## Antes de empezar

1. Entra al Spark de tu equipo por SSH.
2. Copia esta carpeta en tu usuario y entra en ella.
3. Ejecuta `bash preparar.sh`.
4. Abre OpenCode con `opencode`.

## Cómo se entrega

Igual que en el workshop 1: cada problema termina en una página HTML en `salidas/` que un jefe pueda abrir y usar en una reunión sin que nadie se la explique, y que se abra sin internet.

## Los problemas

| # | Problema |
| --- | --- |
| 6 | [El ERP entra a la conversación](problemas/6-el-erp-entra-a-la-conversacion.md) |
| 7 | [Reclamos con firma](problemas/7-reclamos-con-firma.md), para quien termine el 6 |

## Qué hay en la carpeta

- `erp/`: el ERP de compras como servidor MCP, con sus datos. Lee `erp/README.md`.
- `AGENTS.md` y `CLAUDE.md`: las reglas del proyecto.
- `opencode.json`: la configuración de OpenCode del proyecto, vacía.

Todos los datos son ficticios.
