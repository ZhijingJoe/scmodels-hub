FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    sqlite3 \
    certbot \
    python3-certbot-nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p mediafiles staticfiles \
    && python manage.py collectstatic --noinput

# Nginx config
COPY docker/nginx.conf /etc/nginx/sites-enabled/default
RUN rm -f /etc/nginx/sites-enabled/*.bak /etc/nginx/sites-available/default

EXPOSE 80 443

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
