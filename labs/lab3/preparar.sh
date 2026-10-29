#!/usr/bin/env bash
# Ejecutar una vez dentro de esta carpeta, en el Spark: bash preparar.sh
# Convierte la carpeta en un repositorio git (OpenCode lo necesita para /undo)
# y deja .env y secretos/ fuera de ese repositorio.
set -e
cp gitignore-del-kit .gitignore
git init -q
git add -A
git -c user.name="workshop" -c user.email="workshop@example.invalid" commit -qm "Kit inicial del workshop"
echo "Listo: carpeta preparada para OpenCode."
