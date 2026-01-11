.PHONY: help install dev test lint format clean build docker-build docker-run docs run venv check all check-all commit-changes release

# Force use of bash shell (required for make to work properly with line continuations)
SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

# Use venv Python if available, otherwise fall back to system python
PYTHON := $(shell [ -d venv ] && echo venv/bin/python3 || echo python3)
PIP := $(shell [ -d venv ] && echo venv/bin/pip || echo pip)
PYTEST := $(shell [ -d venv ] && echo venv/bin/pytest || echo pytest)
RUFF := $(shell [ -d venv ] && echo venv/bin/ruff || echo ruff)
BLACK := $(shell [ -d venv ] && echo venv/bin/black || echo black)
MYPY := $(shell [ -d venv ] && echo venv/bin/mypy || echo mypy)

help:
	@echo "High-Command - Helldivers 2 MCP Server"
	@echo ""
	@echo "Available targets:"
	@echo "  venv           Create virtual environment"
	@echo "  install        Install dependencies"
	@echo "  dev            Install development dependencies"
	@echo "  run            Run the MCP server (HTTP mode)"
	@echo "  run-stdio      Run the MCP server (stdio mode)"
	@echo "  test           Run tests with coverage"
	@echo "  test-fast      Run tests without coverage"
	@echo "  lint           Run linters (ruff, mypy)"
	@echo "  format         Format code with black and ruff"
	@echo "  build          Build Python package (creates dist/)"
	@echo "  clean          Remove build artifacts and cache files"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-login   Login to Harbor registry (requires HARBOR_USERNAME and HARBOR_PASSWORD)"
	@echo "  docker-push    Build and push image to Harbor registry"
	@echo "  docker-pull    Pull image from Harbor registry"
	@echo "  docker-run     Run Docker container"
	@echo "  docs           Build documentation"
	@echo "  docs-serve     Serve documentation locally"
	@echo "  check          Run linters and tests"
	@echo "  check-all      Format, lint, and test (quality gate)"
	@echo "  commit-changes Git add, commit, and status"
	@echo "  release        Format, lint, test, and prepare release"
	@echo "  help           Show this help message"

venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip setuptools wheel

install: venv
	$(PIP) install -e .

dev: install
	$(PIP) install -e ".[dev]"

run:
	MCP_TRANSPORT=http $(PYTHON) -m highcommand.server

run-stdio:
	$(PYTHON) -m highcommand.server

test:
	$(PYTEST)

test-fast:
	$(PYTEST) --no-cov -q

lint:
	$(RUFF) check .
	$(MYPY) highcommand --ignore-missing-imports

format:
	$(BLACK) highcommand tests
	$(RUFF) check --fix .

build: clean
	pip install --upgrade pip build
	python -m build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .pytest_cache .mypy_cache htmlcov .ruff_cache

HARBOR_REGISTRY := harbor.dataknife.net
APP_NAME := high-command-mcp
HARBOR_IMAGE := $(HARBOR_REGISTRY)/library/$(APP_NAME)
IMAGE_TAG ?= latest

docker-login:
	@echo "Logging into Harbor registry..."
	@if [ -z "$$HARBOR_USERNAME" ] || [ -z "$$HARBOR_PASSWORD" ]; then \
		echo "Error: HARBOR_USERNAME and HARBOR_PASSWORD must be set"; \
		exit 1; \
	fi
	@echo "$$HARBOR_PASSWORD" | docker login $(HARBOR_REGISTRY) \
		-u "$$HARBOR_USERNAME" \
		--password-stdin

docker-build:
	docker build -t high-command:latest .
	docker tag high-command:latest $(HARBOR_IMAGE):$(IMAGE_TAG)

docker-push: docker-build docker-login
	docker push $(HARBOR_IMAGE):$(IMAGE_TAG)

docker-pull:
	docker pull $(HARBOR_IMAGE):$(IMAGE_TAG)
	docker tag $(HARBOR_IMAGE):$(IMAGE_TAG) high-command:latest

docker-run: docker-build
	docker run -it --rm high-command:latest

docs:
	cd docs && make html

docs-serve: docs
	@echo "Serving docs at http://localhost:8000"
	$(PYTHON) -m http.server 8000 -d docs/_build/html

check: lint test

all: clean install lint test

# Multi-step targets

check-all: format lint test
	@echo "✅ All checks passed!"

commit-changes:
	@echo "Adding changes..."
	git add -A
	@echo "Enter commit message: " && read msg; \
	git commit -m "$$msg"
	@echo ""
	@echo "Git status:"
	git status

release: clean check-all
	@echo ""
	@echo "✅ Release ready!"
	@echo "Run: git push"
