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
    app/
      main.py
    tests/
    Dockerfile
    requirements.txt
  web/
    app/
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
docker compose up --build
```

W takim wariancie backend będzie dostępny pod adresem `http://localhost:8010`.

Sprawdzenie statusu kontenerów:

```bash
docker compose ps
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

Aktualnie dostępny jest podstawowy healthcheck API:

```text
GET /health
```

Oczekiwana odpowiedź:

```json
{"status":"ok","service":"crewplan-lite-api"}
```

Frontend pokazuje stronę startową CrewPlan Lite oraz aktualny status pierwszego etapu implementacji.

## Testy

Testy backendu można uruchomić w kontenerze API:

```bash
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

Zaimplementowany jest etap 1:

- szkielet backendu FastAPI,
- endpoint `GET /health`,
- test backendu dla healthchecka,
- szkielet frontendu Next.js App Router,
- uruchamianie PostgreSQL, API i frontendu przez Docker Compose.

Model domenowy, migracje Alembic, seed danych demo, endpointy planistyczne i solver CP-SAT będą dodawane w kolejnych etapach.
