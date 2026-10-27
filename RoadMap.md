# Reddit Clone RoadMap

> Follow this step by step. Complete each step fully before moving to the next. Add checkmarks as you go.

## Step 1: Setup env in development and production

### Goal
Prepare environment variables for dev (local) and prod (deployment), isolate dependencies, and load them safely in Django.

### 1a) Create and update `.gitignore`
- [ ] Create/update `.gitignore` in repo root

```gitignore
# Virtual env
.venv/
venv/
env/

# Environment variables
.env
.env.local
.env.*.local

# Django
__pycache__/
*.py[cod]
*.sqlite3
db.sqlite3
/staticfiles/
/media/

# OS/IDE
.DS_Store
.idea/
.vscode/
```

### 1b) Setup Python virtual environment (Development)
- [ ] Create venv
- [ ] Activate venv
- [ ] Install dependencies

```bash
# Create venv
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows - cmd)
# .venv\Scripts\activate.bat

# Activate (Windows - PowerShell)
# .venv\Scripts\Activate.ps1
```

```bash
# Upgrade pip and install packages
pip install --upgrade pip
pip install django python-decouple
# (add others later: markdown, bleach, gunicorn, whitenoise, psycopg[binary] etc.)
pip freeze > requirements.txt
```

### 1c) Create `.env` for Development
- [ ] Create `.env` in repo root (never commit this)

```env
# Development
DEBUG=True
SECRET_KEY=dev-change-this-to-a-random-secure-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# (optional) CSRF/TRUSTED for local
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

> Generate a secure key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 1d) Create `.env.example` for Production/Onboarding
- [ ] Create `.env.example` (safe to commit) with placeholders

```env
# Production/Example
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@host:port/dbname

CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 1e) Configure Django to load env vars (`config/settings.py`)
- [ ] Add imports at top of `config/settings.py`
- [ ] Replace hardcoded values with env vars

```python
from pathlib import Path
from decouple import config, Csv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
```

```python
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
```

### 1f) Setup for Production
- [ ] Add production dependencies to `requirements.txt`

```bash
pip install gunicorn whitenoise psycopg[binary]
pip freeze > requirements.txt
```

- [ ] Update `config/settings.py` for production basics

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # add for static files
    ...
]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security (only enable in prod via env)
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### Verification
- [ ] `.env` is in `.gitignore` and not committed
- [ ] `.env.example` is committed
- [ ] `python manage.py check` passes with env loaded
- [ ] App runs with `python manage.py runserver` using dev env

**Next:** When ready, ask to proceed to next step (e.g. "continue roadmap to step 2: Project structure & custom User model").
