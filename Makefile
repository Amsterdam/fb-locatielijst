# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2024.07.01
.PHONY: help pip-tools sync requirements upgrade test init check-env

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = docker compose
run = $(dc) run --remove-orphans --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py

init: clean build migrate loaddata  ## Init clean

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	pip-compile --upgrade --output-file requirements.txt --allow-unsafe requirements.in
	pip-compile --upgrade --output-file requirements_linting.txt --allow-unsafe requirements_linting.in
	pip-compile --upgrade --output-file requirements_dev.txt --allow-unsafe requirements_dev.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:                         ## Make migrations
	$(manage) makemigrations $(ARGS)

migrate:                            ## Migrate
	$(manage) migrate
	# $(manage) python manage.py init_database 

urls:
	$(manage) show_urls

build:                              ## Build docker image
	$(dc) build

app:                                ## Run app
	$(run) --service-ports app

bash:                               ## Run the container and start bash
	$(run) dev bash

shell:	                            ## Run a Django shell
	$(manage) shell

dev-https:                          ## Run the development app over SSL with runserver_plus
	$(run) --service-ports dev python manage.py runserver_plus 0.0.0.0:8000 --cert-file cert.crt --key-file cert.key

dev: migrate
	$(run) --service-ports dev

test: 								## Execute tests.
	$(run) test pytest $(ARGS)                     

clean:                              ## Clean docker stuff
	$(dc) down -v --remove-orphans

lintfix:                            ## Execute lint fixes
	$(run) linting black /app/src/$(APP) /app/tests/$(APP)
	$(run) linting autoflake /app/src --recursive --in-place --remove-unused-variables --remove-all-unused-imports --quiet
	$(run) linting isort /app/src/$(APP) /app/tests/$(APP)

lint:                               ## Execute lint checks
	$(run) linting black --diff /app/src/$(APP) /app/tests/$(APP)
	$(run) linting autoflake /app/src --check --recursive --quiet
	$(run) linting isort --diff --check /app/src/$(APP) /app/tests/$(APP)

superuser:                          ## Create a superuser (user with admin rights)
	$(manage) createsuperuser

janitor:                            ## Run the janitor
	$(manage) janitor $(ARGS)

dumpdata:                           ## Create a json dump. Optionally use models= to define which tables (space seperated), i.e. models=app app2.model
	$(run) dev bash -c './manage.py dumpdata -a --indent 2 --format=json $(model)> dump.json'

fixtures = locations location_properties property_options location_data external_services location_external_services location_docs property_groups
loaddata:                           ## Load $fixtures. Multiple fixtures can be loaded (space seperated), i.e. fixtures=fixture1 fixture2; or a json file, i.e. fixtures=dump.json
	$(manage) loaddata $(fixtures)

push:                               ## Push to container registry
	$(dc) push

check-env:                          ## Check if an .env file exists, otherwise create one.
	@if [ ! -f .env ]; then \
		echo "No .env file found. Creating an empty .env file..."; \
		touch .env; \
	fi
