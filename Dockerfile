# Chester's · imagen para el servidor (spec 008).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Los estáticos se generan al construir; la clave de este paso no se usa en ejecución.
RUN DJANGO_DEBUG=0 DJANGO_SECRET_KEY=solo-para-collectstatic python manage.py collectstatic --noinput \
    && useradd --uid 1000 --no-create-home chesters \
    && mkdir -p /datos && chown chesters /datos
USER chesters

EXPOSE 8000
# migrate en cada arranque: es rápido con SQLite y deja la base al día tras cada despliegue.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn chesters_site.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 60 --max-requests 500 --max-requests-jitter 50 --access-logfile -"]
