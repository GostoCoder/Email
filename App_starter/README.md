# App Starter (Hub-Almadia compliant)

Starter template aligning with the documented standards: FastAPI backend, React/Vite frontend, Supabase connectivity, secure Docker packaging, and Traefik-ready routing.

## What you get
- Backend FastAPI with health + sample apps feature, CORS, env-based settings, Supabase client
- Frontend React/Vite consuming the backend with Supabase fallback, ready for Bootstrap styling
- Docker multi-stage builds (non-root), security options, healthchecks
- Traefik labels for the frontend service and shared `hub_almadia_network`

## Quick start
```bash
# From workspace root
docker network create hub_almadia_network || true
cd App_starter

# Build & run
docker-compose up -d --build

# Logs
docker-compose logs -f backend frontend
```

## Domains & hosts
Add to `/etc/hosts`:
```
127.0.0.1   app-starter.reception.local
```

## Environment
- Single env template: `.env.example` at repo root. Copy to `.env` and fill Supabase keys + Vite values.

## Next steps
- Replace sample feature data with real logic
- Wire Supabase using the provided settings placeholders
- Add tests (pytest / Vitest) and CI as needed
