FROM python:3.12-slim

# Build-time identity (set by deploy workflow / operator script).
# Surfaced via /health (release_version + git_sha fields) so operators
# can verify which build is actually serving traffic. Default "unknown"
# is intentional — local dev builds without explicit --build-arg should
# still produce a runnable container, just with unidentified provenance.
ARG GIT_SHA=unknown
ARG RELEASE_VERSION=unknown

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SCP_GIT_SHA=${GIT_SHA} \
    SCP_RELEASE_VERSION=${RELEASE_VERSION}

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos '' scp

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

EXPOSE 3787

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3787/health')" || exit 1

USER scp

CMD ["standards-control-plane", "serve", "--host", "0.0.0.0", "--port", "3787"]
