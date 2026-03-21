# AI Course Generator — MVP

Autonomous platform that fetches AI/ML research daily from ArXiv and generates structured mini-courses using Claude.

## Project Structure

```
evolution/
├── backend/               # FastAPI Python backend
│   ├── main.py            # App entrypoint + lifespan
│   ├── database.py        # SQLAlchemy setup
│   ├── models/            # DB models
│   │   └── course.py
│   ├── routers/           # API routes
│   │   └── courses.py
│   ├── pipeline/          # Core automation
│   │   ├── fetcher.py     # ArXiv content ingestion
│   │   ├── generator.py   # Claude course generation
│   │   └── scheduler.py   # Daily cron scheduler
│   ├── requirements.txt
│   └── .env.example
└── frontend/              # Next.js 15 frontend
    └── src/
        ├── app/
        │   ├── page.tsx           # Course list + domain filter
        │   ├── courses/[id]/      # Course detail
        │   └── domains/           # Browse by domain
        ├── components/
        │   └── CourseCard.tsx
        └── lib/
            └── api.ts             # API client + types
```

## Setup

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY and DATABASE_URL

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# Edit .env.local if backend runs on a different port

npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/courses | List all courses (filter by ?domain=) |
| GET | /api/courses/:id | Get course detail with modules |
| GET | /api/courses/domains | List available domains |
| POST | /api/trigger?domain=machine_learning | Manually trigger pipeline |

## How It Works

1. **Scheduler** fires daily at 08:00 UTC
2. **Fetcher** pulls latest papers from ArXiv by domain
3. **Generator** sends each paper to Claude → structured course JSON
4. **Database** stores course (deduplicates by source URL)
5. **Frontend** displays courses via Next.js server components

## Manual Pipeline Trigger

```bash
curl -X POST "http://localhost:8000/api/trigger?domain=machine_learning&max_results=3"
```

## Domains

- `machine_learning`
- `computer_vision`
- `nlp`
- `robotics`
- `ai_general`
