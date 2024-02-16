# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29
.PHONY: help pip-tools install requirements update test init

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

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	## The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	## https://stackoverflow.com/questions/58843905
	pip-compile --upgrade --output-file requirements.txt --allow-unsafe requirements.in --resolver=backtracking
	pip-compile --upgrade --output-file requirements_dev.txt --allow-unsafe requirements_dev.in --resolver=backtracking

upgrade: requirements install       ## Run 'requirements' and 'install' targets

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

shell:
	$(manage) shell

dev: 						        ## Run the development app (and run extra migrations first)
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

fixtures = locations location_properties property_options location_data external_services location_external_services location_docs
loaddata:                           ## Load $fixtures. Multiple fixtures can be loaded (space seperated), i.e. fixtures=fixture1 fixture2; or a json file, i.e. fixtures=dump.json
	$(manage) loaddata $(fixtures)

trivy:                              ## Detect image vulnerabilities
	$(dc) build --no-cache app
	## trivy image --ignore-unfixed ## registry URL
