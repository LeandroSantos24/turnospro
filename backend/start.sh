#!/bin/bash
# start.sh — Levanta el entorno de desarrollo completo

echo "── Levantando base de datos y Redis ──"
docker-compose up -d

echo "── Iniciando backend (FastAPI) ──"
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
cd ..

echo "── Iniciando frontend (Next.js) ──"
cd frontend
npm run dev &
cd ..

echo ""
echo "✓ TurnosPro corriendo en:"
echo "   Frontend  → http://localhost:3000"
echo "   Backend   → http://localhost:8000"
echo "   API Docs  → http://localhost:8000/docs"
