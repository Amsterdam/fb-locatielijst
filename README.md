# Datafundament-fb

Dit is een repo vor de applicatie datafundament-fb.
Een applicatie voor het opslaan en inlezen van gegevens van het faciliteiten bureau over de locaties waar zij werkzaamheden doen.

# Demo
Na het klonen kan je de Docker images starten vanuit de makefile:
- Configureer de environment bestanden
  > Verwijder de suffix '.example' van beide env bestanden die nodig zijn zodat je de volgende bestanden overhoudt: `.app.env` en `.db.env`
- Maak de benodigde requirements.txt en requirements_dev.txt aan:
  ```
  make requirements
  ```
  > Let op: als je geen venv hebt gestart dan wordt je lokale Python installatie gebruikt voor het installeren van pip-tools en het maken van requirements.
- Bouw de images:
  ```
  make init
  ```
- Laad voorbeeld dat:
  ```
  make loaddata
  ```
- Maak een superuser aan:
  ```
  make superuser
  ```
- Start de development container:
  ```
  make dev
  ```