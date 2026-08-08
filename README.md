# Helpdesk Ticketing System

A full-stack helpdesk ticketing system built with Django REST Framework and React.

## Goal

Build a portfolio-ready project that demonstrates:

- REST API design
- Custom users and roles
- Authentication and authorization
- Ticket workflow and business rules
- Filtering, search, ordering, and pagination
- Automated tests
- PostgreSQL
- Docker
- OpenAPI / Swagger
- GitHub Actions CI

## Roles

- **Customer** — creates tickets, sees own tickets, sends replies
- **Support Agent** — sees support queue, assigns tickets, replies, changes ticket status
- **Admin** — manages the system through Django Admin

## Repository structure

```text
helpdesk-ticketing-system/
├── backend/
├── frontend/
├── ROADMAP.md
├── README.md
└── .gitignore
```

## Current milestone

**Milestone 0 — Project bootstrap**

- [x] Django project scaffold
- [x] Custom User model with roles
- [x] DRF health endpoint
- [x] React/Vite scaffold
- [x] Frontend-to-backend development proxy
- [ ] Ticket domain models
- [ ] Authentication
- [ ] Permissions

## Run backend

From the repository root:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then:

```bash
python -m pip install -r requirements.txt
python manage.py makemigrations users
python manage.py migrate
python manage.py runserver
```

Backend health endpoint:

```text
http://127.0.0.1:8000/api/health/
```

## Run frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

The Vite development server proxies `/api/*` requests to Django on port 8000.

## Development workflow

Use small, meaningful commits. Suggested early history:

```text
chore: initialize full-stack monorepo
feat(users): add custom user roles
feat(api): add backend health endpoint
feat(ui): connect React app to backend health endpoint
feat(tickets): add ticket domain models
feat(auth): add authentication endpoints
feat(authz): add role-based permissions
```

As features grow, use GitHub Issues and feature branches rather than committing everything directly as one large change.
