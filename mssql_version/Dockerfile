FROM python:3.11-slim-buster as app

  # build variables.
  ENV DEBIAN_FRONTEND noninteractive

  # install Microsoft SQL Server requirements.
  ENV ACCEPT_EULA=Y
  RUN apt-get update -y && apt-get update \
    && apt-get install -y --no-install-recommends curl gcc g++ gnupg unixodbc-dev

  # Add SQL Server ODBC Driver 17 for Ubuntu 18.04
  RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends --allow-unauthenticated msodbcsql17 mssql-tools \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile \
    && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc

  WORKDIR /app/src/example_project
  COPY requirements.txt requirements.txt
  COPY . /app/src/

  RUN pip install --upgrade pip
  RUN pip install -r requirements.txt
  # TODO tijdens het draaien van collectstatic moet de env ENVIRONMENT gegeven zijn
  # anders kan settings\init.py niet de juiste settings laden;
  # behalve met een work-around waarbij een default settings wordt gezet
  # dit werkt niet in combinatie met args: - NODE_ENV = development in docker-compose.yml:
  # ARG NODE_ENV
  # ENV ENVIRONMENT $NODE_ENV
  RUN python manage.py collectstatic --no-input

  # Build metadata
  ENV BUILD_DATE=$BUILD_DATE
  ENV BUILD_REVISION=$BUILD_REVISION
  ENV BUILD_VERSION=$BUILD_VERSION

  # CMD ["/app/deploy/docker-run.sh"]

# stage 2, dev
FROM app as dev

  USER root
  ADD requirements_dev.txt requirements_dev.txt
  RUN pip install -r requirements_dev.txt

  USER ITforCare

  # Any process that requires to write in the home dir
  # we write to /tmp since we have no home dir
  ENV HOME /tmp


# stage 3, test
FROM dev as test

  USER ITforCare

  ENV AUDIT_LOG_ENABLED=false
  ENV COVERAGE_FILE=/tmp/.coverage
  ENV PYTHONPATH=/app/src

  CMD ["pytest"]


FROM mcr.microsoft.com/mssql/server:2022-latest as mssql

  USER root

  # Create app directory
  RUN mkdir -p /usr/src/app
  WORKDIR /usr/src/app

  # Copy initialization scripts
  COPY deploy/db/. /usr/src/app

  # Grant permissions for the run-initialization script to be executable
  RUN chmod +x /usr/src/app/setup-database.sh

  # Expose port 1433 in case accesing from other container
  EXPOSE 1433

  # Run Microsoft SQl Server and initialization script (at the same time)
  # Note: If you want to start MsSQL only (without initialization script) you can comment bellow line out, CMD entry from base image will be taken
  CMD /bin/bash ./entrypoint.sh