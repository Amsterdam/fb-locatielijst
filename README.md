# FB-Locatielijst

Dit is een repo vor de applicatie FB-Locatielijst.
Een applicatie voor het opslaan en inlezen van gegevens van het faciliteiten bureau over de locaties waar zij werkzaamheden doen.

# Development
Na het klonen kan je de Docker images starten vanuit de makefile:
- Maak de benodigde requirements.txt, requirements_dev.txt en requirements_linting aan:
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

# Authenticatie via Entra ID oauth
Het is mogelijk om op je lokale ontwikkelomgeving gebruik te maken van authenticatie via Entra ID.
- Configureer de oauth koppeling met Entra ID
  
  Maak een `.env` bestand aan, als deze nog niet bestaat, en plaats daarin de volgende inhoud en vul de waardes aan uit de keyvault voor datafundament-o:
  ```
  OIDC_RP_CLIENT_ID = '<waarde uit oidc_rp_client_id in keyvault>'
  OIDC_RP_CLIENT_SECRET = '<waarde uit oidc_rp_client_secret in keyvault>'
  ```
  >Dit .env bestand is opgenomen in de .gitignore, want deze inhoud moet uiteraard nooit in de repo komen.
- Zet in `.app.env` je ENVIRONMENT variabele op `development`.
  >Let op dit zal je tests breken. Om de tests weer te kunnen draaien moet je deze variabele weer terug op `local` zetten.   
