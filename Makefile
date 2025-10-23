# Makefile for AI-Driven Legal Document Automation System
# Development, Testing, and Deployment Commands

.PHONY: help install install-dev test test-unit test-integration test-e2e test-security test-performance lint format clean build docs docker-build docker-up docker-down docker-logs security-scan coverage-report

# Default target
help:
	@echo "AI-Driven Legal Document Automation System - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  setup          Initial project setup"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests"
	@echo "  test-e2e       Run end-to-end tests"
	@echo "  test-security  Run security tests"
	@echo "  test-performance Run performance tests"
	@echo "  coverage-report Generate test coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code"
	@echo "  security-scan  Run security vulnerability scan"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build all Docker images"
	@echo "  docker-up      Start all services"
	@echo "  docker-down    Stop all services"
	@echo "  docker-logs    Show service logs"
	@echo "  docker-test    Run tests in Docker containers"
	@echo ""
	@echo "Development:"
	@echo "  dev            Start development environment"
	@echo "  shell          Start interactive shell"
	@echo "  clean          Clean temporary files"
	@echo "  build          Build project for production"
	@echo "  docs           Generate documentation"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate     Run database migrations"
	@echo "  db-seed        Seed database with test data"
	@echo "  db-reset       Reset database"

# Setup & Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-test.txt
	pre-commit install

setup:
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && make install-dev
	cp .env.example .env
	@echo "Setup complete! Don't forget to configure .env file"

# Testing Commands
test:
	pytest tests/ -v --cov=services --cov=shared --cov-report=html --cov-report=term

test-unit:
	pytest tests/ -v -m "unit" --cov=services --cov=shared

test-integration:
	pytest tests/ -v -m "integration" --cov=services --cov=shared

test-e2e:
	pytest tests/ -v -m "e2e" --cov=services --cov=shared

test-security:
	pytest tests/ -v -m "security" --cov=services --cov=shared
	bandit -r services/ shared/

test-performance:
	pytest tests/ -v -m "performance" --benchmark-only
	locust -f tests/performance/locustfile.py --headless -u 10 -r 2 -t 60s --host=http://localhost:8000

coverage-report:
	pytest tests/ --cov=services --cov=shared --cov-report=html --cov-report=xml --cov-fail-under=80
	@echo "Coverage report generated in htmlcov/"

# Code Quality
lint:
	flake8 services/ shared/ tests/
	mypy services/ shared/
	black --check services/ shared/ tests/
	isort --check-only services/ shared/ tests/

format:
	black services/ shared/ tests/
	isort services/ shared/ tests/

security-scan:
	bandit -r services/ shared/ -f json -o security-report.json
	safety check --json --output safety-report.json
	semgrep --config=auto services/ shared/

# Docker Commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	sleep 10
	@echo "Services started. Use 'make docker-logs' to view logs."

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-exec:
	docker-compose exec $(service) bash

# Database Commands
db-migrate:
	docker-compose exec postgres alembic upgrade head

db-seed:
	docker-compose exec postgres python scripts/seed_database.py

db-reset:
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	make db-migrate
	make db-seed

# Development Commands
dev:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
	@echo "Development environment started"
	@echo "Validation Engine: http://localhost:8003"
	@echo "Google Drive Service: http://localhost:8004"
	@echo "Audit Service: http://localhost:8005"
	@echo "Web Dashboard: http://localhost:3000"

shell:
	docker-compose exec validation-engine bash

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf reports/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

build:
	python -m build
	@echo "Build complete. Check dist/ directory."

docs:
	cd docs && make html
	@echo "Documentation generated in docs/_build/html/"

# Production Deployment
deploy-staging:
	@echo "Deploying to staging environment..."
	# Add staging deployment commands here

deploy-production:
	@echo "Deploying to production environment..."
	# Add production deployment commands here

# Health Checks
health-check:
	@echo "Checking service health..."
	curl -f http://localhost:8003/health || echo "Validation Engine: DOWN"
	curl -f http://localhost:8004/health || echo "Google Drive Service: DOWN"
	curl -f http://localhost:8005/health || echo "Audit Service: DOWN"
	curl -f http://localhost:3000/health || echo "Web Dashboard: DOWN"

# Load Testing
load-test:
	locust -f tests/performance/locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 300s

# Backup and Recovery
backup-db:
	docker-compose exec postgres pg_dump -U postgres legal_automation > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@echo "Usage: make restore-db BACKUP_FILE=backup_file.sql"
	docker-compose exec -T postgres psql -U postgres legal_automation < $(BACKUP_FILE)

# Log Analysis
analyze-logs:
	docker-compose logs --tail=1000 > logs_$(shell date +%Y%m%d_%H%M%S).log
	@echo "Logs saved to logs_$(shell date +%Y%m%d_%H%M%S).log"

# Compliance and Auditing
compliance-check:
	python scripts/compliance_check.py
	@echo "Compliance check complete. See compliance_report.json"

audit-logs:
	python scripts/extract_audit_logs.py --days 30
	@echo "Audit logs extracted to audit_logs_$(shell date +%Y%m%d_%H%M%S).json"

# Quick Start for New Developers
quickstart: setup install-dev docker-up
	@echo "Quickstart complete!"
	@echo "1. Configure your .env file with API keys"
	@echo "2. Run 'make db-migrate' to setup database"
	@echo "3. Run 'make test' to verify everything works"
	@echo "4. Visit http://localhost:3000 for the web dashboard"

# CI/CD Pipeline Commands
ci-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down --volumes

ci-build:
	docker-compose -f docker-compose.ci.yml build
	docker-compose -f docker-compose.ci.yml push

# Monitoring and Observability
metrics:
	curl http://localhost:8003/metrics
	curl http://localhost:8004/metrics
	curl http://localhost:8005/metrics

# Security Operations
security-scan-production:
	bandit -r services/ shared/ -f json -o production-security-scan.json
	safety check --json --output production-safety-report.json
	@echo "Production security scan complete"

# Environment Management
env-dev:
	cp .env.example .env.dev
	@echo "Development environment file created. Configure .env.dev"

env-prod:
	cp .env.example .env.prod
	@echo "Production environment file created. Configure .env.prod with production values"

# Data Management
export-test-data:
	python scripts/export_test_data.py
	@echo "Test data exported to test_data_export_$(shell date +%Y%m%d_%H%M%S).json"

import-test-data:
	@echo "Usage: make import-test-data DATA_FILE=test_data_export.json"
	python scripts/import_test_data.py $(DATA_FILE)