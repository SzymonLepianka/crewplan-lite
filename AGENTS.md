# Instrukcje dla agentów programistycznych

Ten plik zawiera zasady pracy dla Codexa lub innego agenta programistycznego pracującego w repozytorium CrewPlan Lite.

## Zasady ogólne

- Nie wykonuj żadnych commitów.
- Nie uruchamiaj `git commit`, `git push`, `git rebase`, `git reset` ani `git checkout`.
- Nie twórz branchy.
- Wszystkie commity wykonuje właściciel repozytorium.
- Pracuj małymi etapami.
- Nie implementuj kilku etapów jednocześnie.
- Nie przechodź do następnego etapu bez wyraźnego polecenia użytkownika.
- Nie ukrywaj problemów i nie stosuj tymczasowych obejść bez ich opisania.
- Preferuj prostą i czytelną architekturę zamiast nadmiernego komplikowania.

## Komunikacja przed etapem

Przed rozpoczęciem każdego etapu wyjaśnij:

- jaki problem rozwiązujemy,
- jakie decyzje techniczne podejmujemy,
- jakie pliki będą zmieniane,
- czego użytkownik powinien się nauczyć.

## Komunikacja po etapie

Po zakończeniu każdego etapu zatrzymaj się i podaj:

- listę zmienionych plików,
- polecenia do uruchomienia aplikacji i testów,
- oczekiwany wynik,
- najważniejsze elementy kodu, które użytkownik powinien sam przeczytać,
- proponowany komunikat commita.

## Ograniczenia technologiczne

- Nie dodawaj technologii niewymienionych w planie bez wcześniejszego uzasadnienia i zgody użytkownika.
- Nie używaj Redis, Celery, Kubernetes, mikroserwisów ani systemu logowania w pierwszej wersji.
- Kod powinien mieć typowanie, testy i czytelne nazwy domenowe.
- Cała logika solvera ma znajdować się w backendzie Python.
- Next.js ma pełnić rolę frontendu i klienta API.

## Zakres MVP

MVP ma pozwalać użytkownikowi zobaczyć przykładowy projekt, jego zadania i dostępne ekipy, uruchomić optymalizację oraz zobaczyć wygenerowany harmonogram.

Podstawowe encje domenowe:

- `Project`
- `Task`
- `TaskDependency`
- `Skill`
- `Crew`
- `CrewSkill`
- `CrewAvailability`
- `ScheduleRun`
- `TaskAssignment`
- `PlanningLock`

Solver ma podejmować dwie główne decyzje:

- kiedy rozpoczyna się zadanie,
- która ekipa wykonuje zadanie.

Twarde ograniczenia solvera:

- każde zadanie ma dokładnie jedną ekipę,
- ekipa musi mieć wszystkie wymagane kwalifikacje,
- jedna ekipa nie może wykonywać dwóch zadań jednocześnie,
- zależności między zadaniami muszą być zachowane,
- zadanie nie może rozpocząć się przed dostępnością ekipy,
- ręcznie zablokowane przypisania muszą być respektowane.

Funkcja celu:

- minimalizacja sumy opóźnień,
- minimalizacja czasu zakończenia całego projektu.
