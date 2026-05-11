# scModels Hub

Single-Cell Resource Portal — a curated collection of foundation models, datasets, tutorials, papers, research teams, and frontiers in single-cell biology.

**Live**: [www.entropyspace.top](https://www.entropyspace.top)

## Features

- 🔍 **Resource Portal** — 10-category navigation hub (NCBI-style)
- 🧬 **Model Database** — 20+ fields per entry: paper links, GitHub, architecture, pretraining data, parameters
- ✍️ **Markdown Editor** — EasyMDE with drag-drop image upload + KaTeX math rendering
- 🏷️ **Tag & Category System** — Model type classification + many-to-many tags
- 📊 **Data Browser** — Resource links for datasets (CELLxGENE, Tahoe-100M, scBaseCount...), tutorials, consortia
- 🔒 **HTTPS** — Let's Encrypt auto-renewal + HSTS

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Django 6.0 + Gunicorn |
| Database | SQLite |
| Frontend | Django Templates + Cormorant Garamond / Inter fonts |
| Editor | EasyMDE (Markdown) + KaTeX (math) |
| Server | Nginx + Let's Encrypt |

## Quick Start

### Option 1: Docker

```bash
docker compose up -d
```

Then visit `http://localhost/`. Create admin:

```bash
docker compose exec web python manage.py createsuperuser
```

### Option 2: Manual (Ubuntu 24.04)

```bash
# Install system deps
sudo apt install -y python3.12-venv nginx sqlite3 certbot python3-certbot-nginx

# Clone & set up
git clone <repo-url> /var/www/scmodels
cd /var/www/scmodels
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Database
venv/bin/python manage.py migrate
venv/bin/python manage.py createsuperuser
venv/bin/python manage.py collectstatic --noinput

# Seed initial data (optional)
venv/bin/python seed_data.py
venv/bin/python seed_resources.py

# Systemd service
sudo cp docker/nginx.conf /etc/nginx/sites-enabled/scmodels
sudo ln -sf /etc/nginx/sites-enabled/scmodels /etc/nginx/sites-enabled/default
sudo cp scmodels.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now scmodels nginx

# HTTPS
sudo certbot --nginx -d www.your-domain.com
```

## Project Structure

```
scmodels/
├── config/                  # Django settings, URLs, WSGI
├── scmodels_app/            # Main app
│   ├── models.py            # ModelEntry, Tag
│   ├── models_resources.py  # ResourceCategory, Resource
│   ├── views.py             # Views + Markdown rendering
│   ├── upload.py            # Image upload API
│   ├── admin.py             # Admin customization
│   ├── templates/           # HTML templates
│   └── migrations/          # DB migrations
├── docker/                  # Docker support
│   ├── nginx.conf
│   └── entrypoint.sh
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── backup.sh                # Backup script
├── seed_data.py             # Seed model entries
└── seed_resources.py        # Seed resource categories
```

## Admin Panel

`/admin/` — manage models, resources, categories, and tags.

### Writing Articles

The Description field uses a full Markdown editor with:

- **Formatting**: headings, bold, italic, lists, quotes, tables, code blocks
- **Images**: drag & drop or paste to auto-upload (stored in `/media/uploads/`)
- **Math**: inline `$E=mc^2$` and display `$$\int_0^\infty$$` via KaTeX

### Uploading Category Backgrounds

Resource Categories → edit → upload `Background Image` — shows as hero background on the category detail page.

## Backup

```bash
./backup.sh                    # Saves to backup_YYYYMMDD_HHMMSS/
./backup.sh /path/to/dest      # Custom destination
```

Backup includes: SQLite DB, media files, nginx config, and JSON exports of all data.

## Migration Checklist

- [ ] Copy project files
- [ ] `pip install -r requirements.txt`
- [ ] `python manage.py migrate`
- [ ] Copy `db.sqlite3` and `mediafiles/`
- [ ] Run `python manage.py collectstatic --noinput`
- [ ] Configure nginx + HTTPS
- [ ] Set up systemd service (or use Docker)
