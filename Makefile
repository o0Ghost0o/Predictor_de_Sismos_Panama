SHELL := /bin/zsh
ROOT := $(shell pwd)

.PHONY: install api worker web up down status logs live tasks-logs

install: ## deps Python (uv) + web (bun)
	uv sync
	cd web && bun install

redis: ## asegura Redis local
	@redis-cli ping >/dev/null 2>&1 || (brew services start redis && sleep 3 && redis-cli ping)

api: redis ## FastAPI :8001
	@pkill -f "uvicorn src.serve.app" 2>/dev/null; sleep 1; true
	cd $(ROOT) && nohup uv run uvicorn src.serve.app:app --port 8001 > server8001.log 2>&1 &
	@echo "API :8001"

worker: redis ## Dramatiq (todas las colas)
	@pkill -f "dramatiq src.tasks" 2>/dev/null; sleep 1; true
	cd $(ROOT) && OMP_NUM_THREADS=1 nohup uv run dramatiq src.tasks.actors --processes 1 --threads 4 > dramatiq.log 2>&1 &
	@echo "worker dramatiq"

web: ## Nuxt :3001
	@pkill -f "nuxt dev" 2>/dev/null; sleep 1; true
	cd $(ROOT)/web && nohup bun run dev --port 3001 > nuxt.log 2>&1 &
	@echo "web :3001"

up: api worker web live ## sistema completo + loops
	@echo "OK: api :8001 | web :3001 | worker"

live: ## arranca loops USGS 5min + IGC/RSS 60s
	@sleep 6 && curl -s -X POST localhost:8001/tasks/live-start | head -c 120; echo

down: ## apaga todo
	@pkill -f "uvicorn src.serve.app" 2>/dev/null; pkill -f "dramatiq src.tasks" 2>/dev/null; pkill -f "nuxt dev" 2>/dev/null; true
	@echo "apagado"

status: ## salud de todo
	@printf "api: "; curl -s -m 3 -o /dev/null -w "%{http_code}\n" localhost:8001/health || true
	@printf "web: "; curl -s -m 3 -o /dev/null -w "%{http_code}\n" -L localhost:3001/ || true
	@printf "redis: "; redis-cli ping 2>&1
	@printf "worker: "; ps aux | grep -c "[d]ramatiq src"
	@printf "ingesta: "; curl -s -m 5 localhost:8001/ingesta 2>/dev/null | head -c 160; echo

logs: ## cola de logs principales
	@tail -5 server8001.log; echo ---; tail -3 dramatiq.log | cut -c1-140
