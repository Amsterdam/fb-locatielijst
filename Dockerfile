ARG PYTHON_VERSION=3.13

# Builder
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED 1

RUN set -eux && \
    python -m ensurepip --upgrade && \
    apt-get update && apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app/install

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


FROM python:${PYTHON_VERSION}-slim-bookworm AS app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED 1

RUN set -eux && \
    python -m ensurepip --upgrade && \
    apt-get update && apt-get install -y \
        libgeos3.11.1 \
        gdal-bin && \
    useradd --user-group --system appuser && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin

WORKDIR /app/deploy
COPY deploy .

WORKDIR /app/src
COPY src .

ARG SECRET_KEY=not-used
ARG OIDC_RP_CLIENT_ID=not-used
ARG OIDC_RP_CLIENT_SECRET=not-used
RUN python manage.py collectstatic --no-input
RUN chmod +x /app/deploy/docker-run.sh

USER appuser

CMD ["/app/deploy/docker-run.sh"]

# devserver
FROM app AS dev

USER root
WORKDIR /app/install

COPY requirements_dev.txt requirements_dev.txt

RUN pip install --no-cache-dir -r requirements_dev.txt

WORKDIR /app/src
USER appuser

ENV HOME /tmp
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# tests
FROM dev AS tests

WORKDIR /app
#COPY tests tests
COPY pyproject.toml pyproject.toml

USER appuser

ENV COVERAGE_FILE=/tmp/.coverage
ENV PYTHONPATH=/src

CMD ["pytest"]

# linting
FROM python:${PYTHON_VERSION}-alpine AS linting

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements_linting.txt