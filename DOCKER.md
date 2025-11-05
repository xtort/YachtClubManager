# Docker Compose Configuration for Yacht Club Manager

This project is configured to run using Docker Compose with PostgreSQL.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Make sure Docker is running on your system

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp .env.docker.example .env.docker
   ```

2. **Edit `.env.docker` with your desired settings** (optional - defaults are provided)

3. **Build and start the containers:**
   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   - Django app: http://localhost:8000
   - PostgreSQL: localhost:5432

## Useful Commands

### Start containers
```bash
docker compose up
```

### Start containers in detached mode (background)
```bash
docker compose up -d
```

### Stop containers
```bash
docker compose down
```

### Stop containers and remove volumes (⚠️ deletes database data)
```bash
docker compose down -v
```

### View logs
```bash
docker compose logs -f web
docker compose logs -f db
```

### Execute Django management commands
```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py init_roles
docker compose exec web python manage.py migrate
```

### Access Django shell
```bash
docker compose exec web python manage.py shell
```

### Access PostgreSQL shell
```bash
docker compose exec db psql -U postgres -d YCM
```

### Rebuild containers after code changes
```bash
docker compose up --build
```

## Environment Variables

Create a `.env.docker` file (or copy from `.env.docker.example`) with the following variables:

- `SECRET_KEY`: Django secret key (generate a new one for production!)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `POSTGRES_DB`: Database name (default: YCM)
- `POSTGRES_USER`: Database user (default: postgres)
- `POSTGRES_PASSWORD`: Database password (default: postgres)
- `POSTGRES_SCHEMA`: Database schema (default: public)

## Volumes

The following volumes are created to persist data:
- `postgres_data`: PostgreSQL database data
- `static_volume`: Django static files
- `media_volume`: User-uploaded media files

## Database Migrations

Migrations run automatically when the container starts. If you need to run them manually:

```bash
docker compose exec web python manage.py migrate
```

## Initial Setup

After starting the containers for the first time:

1. Initialize roles:
   ```bash
   docker compose exec web python manage.py init_roles
   ```

2. Create a superuser:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## Troubleshooting

### Database connection issues
- Make sure the `db` service is healthy (check with `docker compose ps`)
- Verify environment variables in `.env.docker`
- **Password authentication errors**: If you get "password authentication failed":
  - Edit `.env.docker` and set `POSTGRES_PASSWORD` to match the password used when the volume was created
  - OR reset the database volume: `docker compose down -v` (⚠️ this deletes all data)
  - Then restart: `docker compose up -d`

### Static files not loading
- Check that `collectstatic` ran successfully in logs
- Verify static volume is mounted correctly

### Port already in use
- Change `DJANGO_PORT` in `.env.docker` or `docker-compose.yml`
- Change `POSTGRES_PORT` if 5432 is already in use

### Setting Database Password

To set or change the database password:

1. **Edit `.env.docker` file** and set:
   ```
   POSTGRES_PASSWORD=your_secure_password_here
   ```

2. **If the database volume already exists with a different password**, you have two options:

   **Option A: Use the existing password** (if you know it)
   - Set `POSTGRES_PASSWORD` in `.env.docker` to match the existing password
   
   **Option B: Reset the database** (⚠️ deletes all data)
   ```bash
   docker compose down -v
   docker compose up -d
   ```
   This removes the volume and creates a new one with the password from `.env.docker`

3. **Restart containers** to apply changes:
   ```bash
   docker compose restart
   ```

