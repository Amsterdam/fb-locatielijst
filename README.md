# Datafundament-fb

Dit is een repo vor de applicatie datafundament-fb.
Een applicatie voor het opslaan en inlezen van gegevens van het faciliteiten bureau over de locaties waar zij werkzaamheden doen.

# Demo
Na het klonen kan je de Docker images starten vanuit de makefile:
- Configureer de enviroment bestanden
  > Kopieer de 'app.env.example' en '.postgress.env.example' environment bestanden. Verwijder dan de suffix '.example' van deze gekopieerde environment bestanden.
- Bouw de images:
  ```
  make init
  ```
- Start de dev container:
  ```
  make dev
  ```
Een lijst van make opdrachten kan je oproepen:
```
make help
```
# Dockeren

Om Docker images in een container te kunnen draaien heb je iets van Docker nodig. Op Windows is het handigst om Docker Desktop hiervoor te gebruiken

# Wat is make?

Make is een Linux command wat wordt gebruikt voor het bouwen van programma's, in dit geval aan de hand van een zogenaamde Makefile. In de Makefile staat gedefiniëerd welke stappen moeten worden uitgevoerd om tot de uitvoer van een programma te komen.

Windows kent Make niet, en dus om binnen Windows gebruik te maken van deze docker ontwikkel omgeving moet je daarvoor de juiste tools installeren.
- Je kan Linux in een losse VM draaien en vanuit die VM ontwikkelen
- Je kan Linux commando's uitvoeren met Cygwin <= aanbevolen
- Je kan Linux for Windows subsystem installeren, dan krijg je een Linux omgeving die kan interacteren met je Windows (inclusief je bestanden)
