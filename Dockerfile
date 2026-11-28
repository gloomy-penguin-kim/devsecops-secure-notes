FROM python:3.13-slim AS build

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install certificates and patch libzstd1
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20250419+deb13u1 \
        libzstd1=1.5.7+dfsg-1+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 \
        --gid 1001 \
        --create-home appuser

# Copy installed dependencies
COPY --from=build /install /usr/local

# Remove unnecessary package manager
RUN python -m pip uninstall --yes pip

COPY --chown=1001:1001 app.py models.py ./

USER 1001:1001

EXPOSE 5000

CMD ["gunicorn", "--no-control-socket", "--bind", "0.0.0.0:5000", "app:create_app()"]