# CrewPlan Lite

Edukacyjny projekt rekrutacyjny: uproszczony system harmonogramowania ekip wykonujacych prace infrastrukturalne.

Projekt jest rozwijany etapami. Na starcie repo zawiera minimalny szkielet:

- `apps/api` - backend FastAPI
- `apps/web` - frontend Next.js z App Router
- `docker-compose.yml` - lokalny PostgreSQL

## Wymagania lokalne

- Python 3.12+
- Node.js 20+
- Docker Desktop albo zgodny Docker Engine

## Uruchomienie bazy danych

```bash
docker compose up -d postgres
```

Sprawdzenie statusu kontenera:

```bash
docker compose ps
```

## Backend

Pierwsze przygotowanie srodowiska:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Uruchomienie API:

```bash
cd apps/api
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Healthcheck:

```bash
curl http://localhost:8000/health
```

Oczekiwana odpowiedz:

```json
{"status":"ok","service":"crewplan-lite-api"}
```

Testy backendu:

```bash
cd apps/api
.venv\Scripts\Activate.ps1
pytest
```

## Frontend

Pierwsze przygotowanie zaleznosci:

```bash
cd apps/web
npm install
```

Uruchomienie aplikacji:

```bash
cd apps/web
npm run dev
```

Frontend bedzie dostepny pod adresem:

```text
http://localhost:3000
```

Sprawdzenie typow:

```bash
cd apps/web
npm run typecheck
```

## Zasady pracy

- Nie wykonujemy commitow automatycznie.
- Kazdy etap powinien byc maly, czytelny i zakonczony testami.
- Solver, model domenowy i migracje beda dodawane w kolejnych etapach.
