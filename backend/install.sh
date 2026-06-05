#!/bin/bash
# install.sh — Corre UNA SOLA VEZ para configurar el proyecto desde cero

echo "── Instalando dependencias del backend ──"
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo "── Instalando dependencias del frontend ──"
cd frontend
npm install
cd ..

echo "✓ Instalación completa. Ahora corrés ./start.sh para levantar el entorno."
