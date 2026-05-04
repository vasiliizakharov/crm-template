# CRM Template — FastAPI + Vue 3 + PostgreSQL

Generic CRM template for small businesses. Containerized, deployable in one command.

## Features

- **Customers** — base of clients, contacts, tags, history
- **Orders / Tasks** — lifecycle (new → in_progress → done → archived), status history
- **Inventory** — products catalog, stock levels, in/out operations
- **Finance** — income/expense tied to orders, simple balance reports
- **Roles** — Admin / Manager / Worker (RBAC)
- **REST API** — OpenAPI auto-docs at /docs
- **Frontend** — Vue 3 + Tailwind, mobile-ready
- **Observability** — `/metrics` Prometheus endpoint

## Quick start

```bash
git clone https://github.com/vasiliizakharov/crm-template.git
cd crm-template
cp .env.example .env
docker compose up -d
```

Open:
- App: http://localhost:8000
- API docs: http://localhost:8000/docs
- Default login (override in .env): admin / changeme-please

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI 0.115+, SQLAlchemy 2.0, Alembic |
| DB | PostgreSQL 16 |
| Frontend | Vue 3 + Vite + Tailwind |
| Auth | JWT cookies + Argon2 hashes |
| Deploy | Docker Compose |

## License

MIT
