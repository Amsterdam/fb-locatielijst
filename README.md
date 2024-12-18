# Datafundament-fb

Dit is een repo vor de applicatie datafundament-fb.
Een applicatie voor het opslaan en inlezen van gegevens van het faciliteiten bureau over de locaties waar zij werkzaamheden doen.

# Development
Na het klonen kan je de Docker images starten vanuit de makefile:
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

# Authenticatie via Entra ID oauth
Het is mogelijk om op je lokale ontwikkelomgeving gebruik te maken van authenticatie via Entra ID.
- Configureer de oauth koppeling met Entra ID
  
  Maak een `.env` bestand aan en plaats daarin de volgende inhoud en vul de waardes aan uit de keyvault voor datafundament-o:
  ```
  OIDC_RP_CLIENT_ID = '<waarde uit oidc_rp_client_id in keyvault>'
  OIDC_RP_CLIENT_SECRET = '<waarde uit oidc_rp_client_secret in keyvault>'
  ```
- Zet in `.app.env` je ENVIRONMENT variabele op `development`.
  >Let op dit zal je tests breken. Om de tests weer te kunnen draaien moet je deze variabele weer terug op `local` zetten.   
