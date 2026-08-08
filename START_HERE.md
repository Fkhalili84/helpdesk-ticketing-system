# Start Here

## 1. Verify prerequisites

```bash
git --version
python --version
node --version
npm --version
```

For current Vite releases, use a supported modern Node.js version.

## 2. Start backend

```bash
cd backend
python -m venv .venv
```

Activate the environment, then:

```bash
python -m pip install -r requirements.txt
python manage.py makemigrations users
python manage.py migrate
python manage.py runserver
```

Check:

```text
http://127.0.0.1:8000/api/health/
```

Expected JSON:

```json
{
  "status": "ok",
  "service": "helpdesk-api"
}
```

## 3. Start frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The page should show that the backend is online.

## 4. First Git commit

From repository root:

```bash
git init -b main
git add .
git status
git commit -m "chore: initialize full-stack helpdesk project"
```

## 5. Push to GitHub

Create an empty public repository named:

```text
helpdesk-ticketing-system
```

Do not initialize it with a README, .gitignore, or license because those files already exist locally.

Then:

```bash
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## 6. Next feature

Next implement the Ticket domain:

- TicketCategory
- Ticket
- TicketMessage

Do this in a separate commit or feature branch.
