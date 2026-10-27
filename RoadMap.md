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

**Next:** Proceed to Step 2: Auth & Base UI.


## Step 2: Auth & Base UI (1 day)

### Goal
Set up authentication (register/login/logout), make email the primary identifier conceptually, create base template with navbar, and add profile page at `/u/<username>/`.

> Note: Project uses `configs/` as project module and `main/` as app. Custom User model will be added as needed; for now follow the steps below.

### 2a) Update settings for auth & templates
- [ ] Add auth redirect settings to `configs/settings.py`

```python
# Auth
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
```

- [ ] Ensure `templates` are discoverable (APP_DIRS True is set). We'll create templates under `main/templates/`.

### 2b) Create custom User model with email as primary identifier (conceptually)
- [ ] In `main/models.py`, create a custom User extending `AbstractUser` and make email required/unique (or use email as login). Also add `bio` later if desired.

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.CharField(max_length=300, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_absolute_url(self):
        return reverse("profile", args=[self.username])

    def __str__(self):
        return self.email
```

- [ ] Point Django to custom user model in `configs/settings.py` (must be done before first migrations if starting fresh). Add:

```python
AUTH_USER_MODEL = "main.User"
```

> If you already ran migrations with default User, you'll need to reset DB/migrations for a clean start in dev. Only do this if acceptable.

### 2c) Create forms for registration
- [ ] Create/update `main/forms.py`

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "username", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
```

### 2d) Add URLs for auth, home, profile
- [ ] Update `configs/urls.py` to include `main.urls`

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
]
```

- [ ] Create `main/urls.py`

```python
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='main/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('u/<str:username>/', views.profile, name='profile'),
]
```

### 2e) Create views for register, home, profile
- [ ] Update `main/views.py`

```python
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterForm
from .models import User

def home(request):
    return render(request, 'main/home.html')

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')
    return render(request, 'main/registration/register.html', {'form': form})

def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    return render(request, 'main/profile.html', {'profile_user': profile_user})
```

### 2f) Create base template with navbar (login state, create post, search box)
- [ ] Create directories: `main/templates/`, `main/templates/main/`, `main/templates/main/registration/`, `main/templates/main/partials/`
- [ ] Create `main/templates/base.html`

```html
{% load static %}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Readit{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <nav class="navbar navbar-expand-lg bg-white border-bottom sticky-top">
      <div class="container">
        <a class="navbar-brand fw-bold text-danger" href="{% url 'home' %}">readit</a>
        <form class="d-flex flex-grow-1 mx-lg-4 my-2 my-lg-0" action="#" method="get">
          <input class="form-control" type="search" name="q" placeholder="Search" value="{{ request.GET.q }}">
        </form>
        <ul class="navbar-nav ms-auto flex-row gap-2 align-items-center">
          <li class="nav-item"><a class="nav-link" href="#">All</a></li>
          {% if user.is_authenticated %}
            <li class="nav-item"><a class="nav-link" href="#">+ Create post</a></li>
            <li class="nav-item"><a class="nav-link" href="{% url 'profile' user.username %}">u/{{ user.username }}</a></li>
            <li class="nav-item">
              <form method="post" action="{% url 'logout' %}">
                {% csrf_token %}
                <button class="btn btn-sm btn-outline-secondary">Logout</button>
              </form>
            </li>
          {% else %}
            <li class="nav-item"><a class="btn btn-sm btn-outline-danger" href="{% url 'login' %}">Log in</a></li>
            <li class="nav-item"><a class="btn btn-sm btn-danger" href="{% url 'register' %}">Sign up</a></li>
          {% endif %}
        </ul>
      </div>
    </nav>
    <main class="container py-4">
      {% for message in messages %}
        <div class="alert alert-{{ message.tags|default:'info' }}">{{ message }}</div>
      {% endfor %}
      {% block content %}{% endblock %}
    </main>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
  </body>
</html>
```

### 2g) Create auth templates and pages
- [ ] `main/templates/main/registration/login.html`

```html
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-4">
    <h4>Log in</h4>
    <form method="post" class="card card-body">
      {% csrf_token %}
      {{ form.as_p }}
      <input type="hidden" name="next" value="{{ request.GET.next }}">
      <button class="btn btn-danger">Log in</button>
    </form>
    <p class="mt-3 small">New here? <a href="{% url 'register' %}">Sign up</a></p>
  </div>
</div>
{% endblock %}
```

- [ ] `main/templates/main/registration/register.html`

```html
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-4">
    <h4>Sign up</h4>
    <form method="post" class="card card-body">
      {% csrf_token %}
      {{ form.as_p }}
      <button class="btn btn-danger">Create account</button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] `main/templates/main/home.html`

```html
{% extends "base.html" %}
{% block title %}Home · readit{% endblock %}
{% block content %}
<div class="row">
  <div class="col-lg-8">
    <h4 class="mb-3">Home</h4>
    <p class="text-muted">Welcome to Readit.</p>
  </div>
</div>
{% endblock %}
```

- [ ] `main/templates/main/profile.html`

```html
{% extends "base.html" %}
{% block title %}u/{{ profile_user.username }}{% endblock %}
{% block content %}
<div class="row">
  <div class="col-lg-8">
    <div class="card mb-3">
      <div class="card-body">
        <h3>u/{{ profile_user.username }}</h3>
        <div class="text-muted small">Joined {{ profile_user.date_joined|date:"M Y" }}</div>
        {% if profile_user.bio %}
          <p class="mt-2 mb-0">{{ profile_user.bio }}</p>
        {% endif %}
        <div class="mt-2 small text-muted">{{ profile_user.email }}</div>
      </div>
    </div>
    <h5>Posts</h5>
    <p class="text-muted">No posts yet.</p>
  </div>
</div>
{% endblock %}
```

### 2h) Migrate and test
- [ ] Create and apply migrations

```bash
python manage.py makemigrations main
python manage.py migrate
```

- [ ] Create superuser

```bash
python manage.py createsuperuser
```

- [ ] Run server and test flows

```bash
python manage.py runserver
```

### Verification
- [ ] Can register a new user (email + username + password)
- [ ] Can login/logout (logout uses POST form)
- [ ] Navbar shows correct state based on auth
- [ ] Profile page loads at `/u/<username>/`
- [ ] Email is used as USERNAME_FIELD and shown conceptually as primary identifier
- [ ] `python manage.py check` passes

**Next:** Proceed to Step 3: Communities (create, detail, join/leave).
