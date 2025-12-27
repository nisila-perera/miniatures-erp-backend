# Miniatures.lk ERP System - Backend

FastAPI backend for the Miniatures.lk ERP System. This repository contains the complete backend application with PostgreSQL database, RESTful API, and business logic.

## Features

- **Order Management**: Multi-source order tracking with status workflow
- **Product & Inventory**: Product catalog with category management, raw material tracking
- **Customer Management**: Customer database with order history
- **Financial Management**: Payment processing, commission tracking, expense management
- **Invoicing**: Customizable invoice templates with PDF generation
- **Reporting & Analytics**: Sales reports, profit & loss statements, material usage
- **WooCommerce Integration**: Synchronize products, customers, and orders

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Containerization | Docker, Docker Compose |
| Reverse Proxy | Nginx |
| Email | SMTP |

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- Git installed

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd miniatures-erp-backend
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment**
   ```bash
   make dev
   # Or: docker compose up -d
   ```

4. **Run database migrations**
   ```bash
   make migrate
   # Or: docker compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Commands

```bash
make dev          # Start development environment
make prod         # Start production environment
make down         # Stop all containers
make logs-dev     # View development logs
make migrate      # Run database migrations
make test         # Run backend tests
make shell        # Open shell in backend container
make shell-db     # Open PostgreSQL shell
make health       # Check services health
```

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+
- PostgreSQL 15+

### Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env - set DATABASE_URL to your local PostgreSQL
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   # Or: ./run_backend.sh
   ```

## Project Structure

```
miniatures-erp-backend/
├── app/
│   ├── api/               # API route handlers
│   ├── core/              # Core configuration
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Data access layer
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── main.py            # FastAPI application
├── alembic/               # Database migrations
├── docker/nginx/          # Nginx configuration (production)
├── tests/                 # Test suite
├── docker-compose.yml     # Development Docker Compose
├── docker-compose.prod.yml # Production Docker Compose
├── Dockerfile             # Multi-stage Docker build
├── Makefile               # Convenience commands
├── alembic.ini            # Alembic configuration
├── pytest.ini             # Pytest configuration
└── requirements.txt       # Python dependencies
```

## Database Migrations

```bash
# Apply all pending migrations
make migrate

# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker compose exec backend alembic downgrade -1

# View migration history
docker compose exec backend alembic history
```

## Testing

```bash
# Run all tests
make test

# Run property-based tests only
make test-property

# Local testing
pytest -v
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## Production Deployment

1. **Configure production environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values (strong passwords!)
   ```

2. **Build and start production**
   ```bash
   make prod
   ```

3. **Run migrations**
   ```bash
   make migrate-prod
   ```

## Environment Variables

See `.env.example` for all available configuration options.

### Required Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database username |
| `POSTGRES_PASSWORD` | Database password |
| `WOOCOMMERCE_URL` | WooCommerce site URL |
| `WOOCOMMERCE_CONSUMER_KEY` | WooCommerce API key |
| `WOOCOMMERCE_CONSUMER_SECRET` | WooCommerce API secret |
| `SMTP_*` | Email configuration |

## License

Proprietary - All rights reserved

## Support

For support, contact: support@miniatures.lk
