.PHONY: help env up up-d down logs build ps health \
	backend-install backend-dev frontend-install frontend-dev frontend-build \
	clean

COMPOSE := docker compose
API_URL ?= http://localhost:8000

help:
	@echo "TimeJump AI — common commands"
	@echo ""
	@echo "  make env              Copy .env.example to .env (skip if .env exists)"
	@echo "  make up               Build and start all services (foreground)"
	@echo "  make up-d             Build and start all services (detached)"
	@echo "  make down             Stop and remove containers"
	@echo "  make logs             Follow compose logs"
	@echo "  make build            Rebuild images"
	@echo "  make ps               List running services"
	@echo "  make health           Curl API /health"
	@echo ""
	@echo "  make backend-install  Python venv + pip install (backend/)"
	@echo "  make backend-dev      Run FastAPI locally (requires infra up)"
	@echo "  make frontend-install npm install (frontend/)"
	@echo "  make frontend-dev     Run Next.js dev server"
	@echo "  make frontend-build   Production build (frontend/)"
	@echo ""
	@echo "  make clean            Remove local venv/node artifacts (not Docker volumes)"

env:
	@test -f .env || cp .env.example .env
	@echo ".env ready"

up: env
	$(COMPOSE) up --build

up-d: env
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

health:
	@curl -sf "$(API_URL)/health" | python3 -m json.tool || (echo "API not reachable at $(API_URL)"; exit 1)

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-dev:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

clean:
	rm -rf backend/.venv frontend/node_modules frontend/.next
	@find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
