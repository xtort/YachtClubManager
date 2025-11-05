# Makefile for Docker Compose commands

.PHONY: help build up down restart logs shell migrate createsuperuser init_roles clean

help:
	@echo "Available commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start containers"
	@echo "  make down           - Stop containers"
	@echo "  make restart        - Restart containers"
	@echo "  make logs           - View logs"
	@echo "  make shell           - Access Django shell"
	@echo "  make migrate         - Run migrations"
	@echo "  make createsuperuser - Create superuser"
	@echo "  make init_roles      - Initialize roles"
	@echo "  make clean           - Stop and remove volumes"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f web

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

init_roles:
	docker compose exec web python manage.py init_roles

clean:
	docker compose down -v

