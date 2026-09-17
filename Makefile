PYTHON ?= python
API_DIR := services/api-gateway
IDENTITY_DIR := services/identity
CITY_CORE_DIR := services/city-core
service ?= identity
SERVICE_DIR := services/$(service)

.PHONY: setup dev infra-up infra-down logs test lint format migrate migration downgrade build health bootstrap-admin check

# Lint + test everything that doesn't need Docker running (web + all three
# Python services). Same as `scripts/check.sh` / `scripts/check.ps1` for
# people without `make`.
check: lint test

setup:
	npm install
	cd $(API_DIR) && $(PYTHON) -m pip install -e ".[dev]"
	cd $(IDENTITY_DIR) && $(PYTHON) -m pip install -e ".[dev]"
	cd $(CITY_CORE_DIR) && $(PYTHON) -m pip install -e ".[dev]"

dev:
	docker compose --profile apps up --build

infra-up:
	docker compose up -d

infra-down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	npm run test:web
	cd $(API_DIR) && $(PYTHON) -m pytest
	cd $(IDENTITY_DIR) && $(PYTHON) -m pytest
	cd $(CITY_CORE_DIR) && $(PYTHON) -m pytest

lint:
	npm run lint:web
	npm run typecheck:web
	cd $(API_DIR) && $(PYTHON) -m ruff check .
	cd $(IDENTITY_DIR) && $(PYTHON) -m ruff check .
	cd $(CITY_CORE_DIR) && $(PYTHON) -m ruff check .

format:
	cd $(API_DIR) && $(PYTHON) -m ruff format .
	cd $(IDENTITY_DIR) && $(PYTHON) -m ruff format .
	cd $(CITY_CORE_DIR) && $(PYTHON) -m ruff format .

# Applies to one service at a time: `make migrate service=api-gateway`.
# Defaults to identity, since that's where schema changes happen most often.
migrate:
	cd $(SERVICE_DIR) && $(PYTHON) -m alembic upgrade head

migration:
	cd $(SERVICE_DIR) && $(PYTHON) -m alembic revision --autogenerate -m "$(message)"

downgrade:
	cd $(SERVICE_DIR) && $(PYTHON) -m alembic downgrade -1

build:
	npm run build:web
	docker compose --profile apps build

health:
	curl --fail http://localhost:8000/health
	curl --fail http://localhost:8000/ready
	curl --fail http://localhost:8001/health
	curl --fail http://localhost:8002/health

# Creates the first SUPER_ADMIN account from SUPERADMIN_EMAIL/SUPERADMIN_PASSWORD
# in .env. Idempotent; safe to re-run. See services/identity/README.md.
bootstrap-admin:
	cd $(IDENTITY_DIR) && $(PYTHON) -m scripts.bootstrap_admin
