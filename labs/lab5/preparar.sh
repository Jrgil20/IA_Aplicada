#!/usr/bin/env bash
# Deja la carpeta lista: repositorio git para poder deshacer y comprobación del modelo local
set -e
cd "$(dirname "$0")"
if [ ! -d .git ]; then
  git init -q
  git add -A
  git -c user.name="workshop" -c user.email="workshop@example.com" commit -q -m "Estado inicial del lab 3"
fi
if curl -sf http://127.0.0.1:8080/health >/dev/null; then
  echo "El modelo local responde en http://127.0.0.1:8080."
else
  echo "Aviso: el modelo local no responde en http://127.0.0.1:8080. Avisa al facilitador."
fi
echo "Listo. Abre OpenCode con: opencode"
