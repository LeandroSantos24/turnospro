#!/bin/bash
# start.sh — Levantar el entorno de desarrollo completo
# Correr desde la RAÍZ del proyecto: ~/Escritorio/turnospro/

RAIZ="$(cd "$(dirname "$0")" && pwd)"

echo "── Levantando base de datos y Redis ──"
docker-compose -f "$RAIZ/docker-compose.yml" up -d

echo "── Iniciando backend (FastAPI) ──"
cd "$RAIZ/backend"
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "── Iniciando frontend (Next.js) ──"
cd "$RAIZ/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ TurnosPro corriendo en:"
echo "   Frontend  → http://localhost:3000"
echo "   Backend   → http://localhost:8000"
echo "   API Docs  → http://localhost:8000/docs"
echo ""
echo "Para detener todo: kill $BACKEND_PID $FRONTEND_PID"