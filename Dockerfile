# BUILD STAGE - Download dependencies from GitHub that require SSH access
FROM            python:3.7.9-alpine3.13 as build

RUN             apk update \
    && apk add --update --no-cache \
    git \
    openssh \
    postgresql-dev \
    musl-dev \
    libxslt-dev \
    python3-dev \
    libffi-dev \
    gcc \
    bash \
    curl-dev \
    rust \
    build-base \
    cargo \
    libcurl \
    && pip install --upgrade pip

ARG             SSH_PRIVATE_KEY
RUN             mkdir /root/.ssh/
RUN             echo "${SSH_PRIVATE_KEY}" > /root/.ssh/id_rsa
RUN             ssh-keyscan -H github.com >> /root/.ssh/known_hosts
RUN             chmod 600 /root/.ssh/id_rsa

COPY            requirements.txt /
WORKDIR         /pip-packages/

RUN             pip wheel -r /requirements.txt




# RUNTIME STAGE - Copy packages from build stage and install runtime dependencies
FROM            python:3.7.9-alpine3.13

RUN             apk update && \
    apk upgrade expat && \
    apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc \
    musl-dev \
    postgresql-dev \
    libxslt-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    make \
    python3-dev \
    build-base \
    curl-dev \
    libcurl
RUN             wget -q -O /usr/local/bin/berglas https://storage.googleapis.com/berglas/0.5.0/linux_amd64/berglas && \
    chmod +x /usr/local/bin/berglas

WORKDIR         /pip-packages/
COPY            --from=build /pip-packages/ /pip-packages/

RUN             rm -rf /pip-packages/src
RUN             pip install --no-deps --find-links=/pip-packages/ /pip-packages/*

EXPOSE          8000

COPY            . /app

WORKDIR         /app
