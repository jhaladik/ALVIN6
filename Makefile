# Makefile - Development Automation
.PHONY: help install dev test lint format clean docker-build docker-run

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:  ## Run development server
	export FLASK_ENV=development && python run.py

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=app --cov-report=html

lint:  ## Run linters
	flake8 app tests
	mypy app

format:  ## Format code
	black app tests
	isort app tests

clean:  ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

docker-build:  ## Build Docker image
	docker build -t storyforge-ai .

docker-run:  ## Run with Docker Compose
	docker-compose up -d

docker-stop:  ## Stop Docker containers
	docker-compose down

init-db:  ## Initialize database
	flask init-db-command

create-admin:  ## Create admin user
	flask create-admin-command

token-stats:  ## Show token usage statistics
	flask token-stats-command

backup-db:  ## Backup database
	mkdir -p backups
	pg_dump $(DATABASE_URL) > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

deploy-prod:  ## Deploy to production
	docker-compose --profile production up -d

logs:  ## Show application logs
	docker-compose logs -f web

monitor:  ## Show system status
	docker-compose ps
	docker stats --no-stream