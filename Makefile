# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29
.PHONY: help pip-tools sync requirements upgrade test init

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = docker-compose
run = $(dc) run --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py
pytest = $(run) test pytest $(ARGS)

build_version := $(shell git describe --tags --exact-match 2> /dev/null || git symbolic-ref -q --short HEAD)
build_revision := $(shell git rev-parse --short HEAD)
build_date := $(shell date --iso-8601=seconds)

init: clean build migrate           ## Init clean

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

sync: pip-tools                     ## Sync your local venv with expected state as defined in requirements.txt
	pip-sync requirements.txt requirements_dev.txt

pip_compile = pip-compile --allow-unsafe --strip-extras --resolver=backtracking --quiet
requirements: pip-tools             ## (Re)compile requirements.txt and requirements_dev.txt
	$(pip_compile) requirements.in
	$(pip_compile) requirements_dev.in

upgrade:                            ## Upgrade the requirements.txt files, adhering to the constraints in the requirements.in files.
	$(pip_compile) --upgrade requirements.in
	$(pip_compile) --upgrade requirements_dev.in

migrations:                         ## Make migrations
	$(manage) makemigrations $(ARGS)

migrate:                            ## Migrate
	$(manage) migrate
	# $(manage) python manage.py init_database 

urls:
	$(manage) show_urls

build: export BUILD_DATE=$(build_date)
build: export BUILD_REVISION=$(build_revision)
build: export BUILD_VERSION=$(build_version)
build:                              ## Build docker image
	$(dc) build

app:                                ## Run app
	$(run) --service-ports app

bash:                               ## Run the container and start bash
	$(run) dev bash

shell:	                            ## Run a Django shell
	$(manage) shell

dev: 	                            ## Run the development app (and run extra migrations first)
	$(run) --service-ports dev

test:                               ## Execute tests. Optionally use test= to define which specific test, i.e. test=app.tests.test_models
	$(manage) test $(test)

clean:                              ## Clean docker stuff
	$(dc) down -v --remove-orphans

env:                                ## Print current env
	$(run) dev env | sort

superuser:                          ## Create a superuser (user with admin rights)
	$(manage) createsuperuser

janitor:                            ## Run the janitor
	$(manage) janitor $(ARGS)

dumpdata:                           ## Create a json dump. Optionally use models= to define which tables (space seperated), i.e. models=app app2.model
	$(run) dev bash -c './manage.py dumpdata -a --indent 2 --format=json $(model)> dump.json'

fixtures = locations location_properties property_options location_data external_services location_external_services location_docs property_groups
loaddata:                           ## Load $fixtures. Multiple fixtures can be loaded (space seperated), i.e. fixtures=fixture1 fixture2; or a json file, i.e. fixtures=dump.json
	$(manage) loaddata $(fixtures)