# Django template

Dit is een repo die als sjabloon kan dienen voor een op Docker gebasseerde Python/Django omgeving met een Microsoft SQL als database

# Demo
Na het klonen kan je de Docker images starten vanuit de makefile:
- Bepaal welke database nodig is
  > De standaard database van de template is postgresql, als de applicatie gebruik moet maken van mssql dan kan je de inhoud van de 'mssql_version' folder naar de root folder kopieren. Dit vervangt alle bestanden die postgresql opzetten met bestanden die mssql opzetten. 
- Configureer de enviroment bestanden
  > Verwijder de suffix '.example' van de environment bestanden die nodig zijn. Dit is altijd het 'app.env.example' bestand en '' of '' gebaseerd op welke database de applicatie gebruikt. 
- Hernoem het example project naar de naam van de applicatie
  > Vervang overal in de code de tekst 'example_project' met de naam van de applicatie, en hernoem ook alle 'example_project' folders.
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
