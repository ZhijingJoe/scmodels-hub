#!/bin/bash
# Backup scModels Hub — database + media files + nginx config
set -e

BACKUP_DIR="${1:-./backup_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$BACKUP_DIR"

cd /var/www/scmodels

echo "=== Backing up to $BACKUP_DIR ==="

# Database
cp db.sqlite3 "$BACKUP_DIR/"

# Media files (user uploads)
if [ -d mediafiles ]; then
    cp -r mediafiles "$BACKUP_DIR/"
fi

# Nginx config
cp /etc/nginx/sites-enabled/default "$BACKUP_DIR/nginx-default.conf" 2>/dev/null || true

# Systemd service
cp /etc/systemd/system/scmodels.service "$BACKUP_DIR/" 2>/dev/null || true

# Export categories + resources as JSON
venv/bin/python manage.py dumpdata scmodels_app.ResourceCategory scmodels_app.Resource --indent 2 > "$BACKUP_DIR/resources.json" 2>/dev/null || true

# Export models + tags
venv/bin/python manage.py dumpdata scmodels_app.ModelEntry scmodels_app.Tag --indent 2 > "$BACKUP_DIR/models.json" 2>/dev/null || true

echo "=== Backup complete: $BACKUP_DIR ==="
ls -lh "$BACKUP_DIR/"
