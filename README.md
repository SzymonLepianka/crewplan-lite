# CrewPlan Lite

CrewPlan Lite to edukacyjny projekt rekrutacyjny pokazujący uproszczony system harmonogramowania ekip wykonujących prace infrastrukturalne.

## Cel projektu

Celem projektu jest nauka budowania czytelnego modularnego monolitu z backendem API, frontendem webowym, relacyjną bazą danych i solverem optymalizacyjnym. MVP ma docelowo pozwalać zobaczyć przykładowy projekt, zadania, ekipy, wymagane kwalifikacje, zależności oraz wynik optymalizacji harmonogramu.

## Technologie

Backend:

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- OR-Tools CP-SAT
- pytest

Frontend:

- Next.js
- React
- TypeScript
- App Router

Infrastruktura:

- Docker
- Docker Compose

## Struktura repozytorium

```text
apps/
  api/
    alembic/
    app/
      main.py
      db/
      modules/
    tests/
    Dockerfile
    requirements.txt
  web/
    app/
    components/
    lib/
    Dockerfile
    package.json
    tsconfig.json
docker-compose.yml
README.md
AGENTS.md
```

## Uruchomienie

Cały aktualny szkielet aplikacji jest uruchamiany przez Docker Compose.

```bash
docker compose up --build
```

Po starcie usług:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Jeżeli któryś port jest zajęty, można go nadpisać zmienną środowiskową. Przykład dla PowerShell:

```powershell
$env:API_PORT = "8010"
$env:WEB_PORT = "3010"
docker compose up --build
```

W takim wariancie backend będzie dostępny pod adresem `http://localhost:8010`, a frontend pod adresem `http://localhost:3010`.

Sprawdzenie statusu kontenerów:

```bash
docker compose ps
```

Uruchomienie migracji bazy danych:

```bash
docker compose run --rm api alembic upgrade head
```

Dodanie przykładowych danych demo:

```bash
docker compose run --rm api python -m app.seed.demo_data
```

Zatrzymanie środowiska:

```bash
docker compose down
```

Usunięcie danych lokalnej bazy:

```bash
docker compose down -v
```

## Endpointy i funkcjonalności

Aktualnie dostępne są:

```text
GET /health
GET /api/projects
GET /api/projects/{project_id}
GET /api/projects/{project_id}/planning-data
POST /api/projects/{project_id}/schedule-runs
GET /api/projects/{project_id}/schedule-runs/latest
GET /api/projects/{project_id}/schedule-runs/{run_id}
```

Oczekiwana odpowiedź z `/health`:

```json
{"status":"ok","service":"crewplan-lite-api"}
```

Frontend pokazuje dane projektu demo, listę zadań, listę ekip, kwalifikacje, zależności, metryki wyniku solvera oraz zapisany harmonogram. Przycisk `Uruchom optymalizację` wywołuje backendowy solver i odświeża wynik na ekranie.

Endpoint `/api/projects/{project_id}/planning-data` zwraca dane wejściowe do późniejszego solvera: projekt, zadania, kwalifikacje, ekipy, dostępności, zależności i aktywne blokady planistyczne.

Endpoint `POST /api/projects/{project_id}/schedule-runs` uruchamia solver synchronicznie i zapisuje wynik w tabelach `schedule_runs` oraz `task_assignments`.

## Testy

Testy backendu można uruchomić w kontenerze API:

```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.seed.demo_data
docker compose run --rm api pytest
```

Sprawdzenie typów frontendu:

```bash
docker compose run --rm web npm run typecheck
```

Build frontendu:

```bash
docker compose run --rm web npm run build
```

## Aktualny stan implementacji

Zaimplementowane są etapy 1, 2, 3, 4, 5 i 6:

- szkielet backendu FastAPI,
- endpoint `GET /health`,
- test backendu dla healthchecka,
- szkielet frontendu Next.js App Router,
- uruchamianie PostgreSQL, API i frontendu przez Docker Compose,
- konfiguracja SQLAlchemy,
- migracje Alembic,
- schemat bazy danych dla domeny planowania,
- seed przykładowego projektu demo,
- endpointy odczytu projektu i danych planistycznych,
- czysta warstwa solvera CP-SAT dla harmonogramowania zadań,
- endpoint uruchamiający solver i zapisujący wynik harmonogramu,
- frontend MVP pokazujący dane projektu i harmonogram oraz uruchamiający optymalizację.

Obsługa ręcznych blokad planistycznych będzie dodawana w późniejszym etapie.
