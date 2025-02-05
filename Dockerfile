FROM python:3.12.4-slim-bookworm AS app

  # build variables.
  ENV DEBIAN_FRONTEND=noninteractive

  # install PostgreSQL requirements.
  RUN apt-get update \
  && apt-get -y install libpq-dev gcc

  WORKDIR /app/src/datafundament_fb
  COPY requirements.txt requirements.txt
  COPY . /app/src/

  RUN pip install --upgrade pip
  RUN pip install -r requirements.txt

  # copy deployment files
  COPY deploy /app/deploy
  # RUN chmod +x /app/deploy/wait-for-it.sh
  # RUN chmod +x /app/deploy/db/entrypoint.sh
  # RUN chmod +x /app/deploy/db/setup-database.sh
  
  # copy runtime files
  COPY runtime /app/runtime
  RUN chmod +x /app/runtime/app/docker-run.sh

  COPY runtime/app/docker-run.sh /app/deploy/docker-run.sh 
  RUN chmod +x /app/deploy/docker-run.sh

  ENTRYPOINT ["/app/runtime/app/docker-run.sh"]

  # TODO tijdens het draaien van collectstatic moet de env ENVIRONMENT gegeven zijn
  # anders kan settings\init.py niet de juiste settings laden;
  # behalve met een work-around waarbij een default settings wordt gezet
  # dit werkt niet in combinatie met args: - NODE_ENV = development in docker-compose.yml:
  # ARG NODE_ENV
  # ENV ENVIRONMENT $NODE_ENV
  RUN python manage.py collectstatic --no-input


# stage 2, dev
FROM app AS dev

  USER root
  ADD requirements_dev.txt requirements_dev.txt
  RUN pip install -r requirements_dev.txt

  USER ITforCare

  # Any process that requires to write in the home dir
  # we write to /tmp since we have no home dir
  ENV HOME=/tmp


# stage 3, test
FROM dev AS test

  USER ITforCare

  ENV AUDIT_LOG_ENABLED=false
  ENV COVERAGE_FILE=/tmp/.coverage
  ENV PYTHONPATH=/app/src

  CMD ["pytest"]


FROM postgres AS postgres
  COPY deploy/db/setup.sql /docker-entrypoint-initdb.d/
