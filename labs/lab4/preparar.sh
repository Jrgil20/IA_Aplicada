#!/usr/bin/env bash
# Deja la carpeta lista: ERP en su estado inicial y repositorio git para poder deshacer
set -e
cd "$(dirname "$0")"
rm -f erp/erp.db
if [ ! -d .git ]; then
  git init -q
  git add -A
  git -c user.name="workshop" -c user.email="workshop@example.com" commit -q -m "Estado inicial del lab 2"
fi
echo "Listo. Abre OpenCode con: opencode"
