# TurnosPro

SaaS de gestión de turnos, CRM y automatización por WhatsApp.

## Stack
- Frontend: Next.js 15 + React + Tailwind CSS
- Backend: FastAPI + Python 3.13
- Base de datos: PostgreSQL 16
- Cache: Redis + Celery
- Mensajería: WhatsApp Cloud API

## Estructura
turnospro/
├── frontend/   Next.js — landing page y panel admin
├── backend/    FastAPI — API REST
├── docker/     Configuraciones Docker
└── docs/       Documentación

## Levantar entorno local
docker-compose up -d

## Estado
En desarrollo activo


# 1. Levantar la base de datos y Redis
cd ~/Escritorio/turnospro
docker-compose up -d

# 2. Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal nueva)
cd backend
source venv/bin/activate
cd ../frontend
npm run dev