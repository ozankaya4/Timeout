FROM python:3.12-slim

# The label lets the deploy prune only this project's old images on the shared VM.
LABEL project=timeout

ENV PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=false \
    DATA_DIRECTORY=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN SECRET_KEY=collectstatic-build-step-only python manage.py collectstatic --noinput

# A new named volume inherits this ownership, so the app can run unprivileged.
RUN useradd --uid 1000 --create-home app \
    && mkdir -p /data/media \
    && chown -R app:app /data
USER app

CMD ["sh", "docker-entrypoint.sh"]
