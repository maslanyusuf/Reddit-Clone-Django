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
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


# ==========================================
# 1. CUSTOM USER MODEL
# ==========================================

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        if not username:
            raise ValueError("The Username field is required") # Fixed typo here

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="Email", unique=True)
    username = models.CharField(verbose_name="Username", unique=True, max_length=150)
    first_name = models.CharField(verbose_name="First Name", max_length=256, blank=True)
    last_name = models.CharField(verbose_name="Last Name", max_length=256, blank=True)
    bio = models.CharField(verbose_name="Bio", max_length=512, blank=True)

    is_active = models.BooleanField(verbose_name="Active", default=True)
    is_staff = models.BooleanField(verbose_name="Staff", default=False)
    date_joined = models.DateTimeField(verbose_name="Date joined", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username","first_name","last_name"] # Added username so createsuperuser prompts for it

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_absolute_url(self):
        return reverse("profile", kwargs={"username": self.username})
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
from django.contrib.auth import authenticate
from .models import User

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=256, widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}))
    last_name = forms.CharField(required=True, max_length=256, widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}))
    email = forms.EmailField(required=True, max_length=256, widget=forms.EmailInput(attrs={"type": "email", "class": "form-control"}))
    username = forms.CharField(required=True, max_length=150, widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username", "password1", "password2")

    # ==========================================
    # FIELDS VALIDATIONS
    # ==========================================

    def clean_email(self):
        # Get the email, strip whitespace, and make it lowercase
        email = self.cleaned_data.get('email', '').strip().lower()

        # Check if email already exists in the database (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")

        return email

    def clean_username(self):
        # Get the username and strip whitespace
        username = self.cleaned_data.get('username', '').strip()

        # Check if username already exists in the database (case-insensitive)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")

        return username

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
    return render(request, 'home.html')

def register_view(request):
  form = RegisterForm()
  if request.method == "POST":
    form = RegisterForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('main:home')
  return render(request,"register.html",{"form":form})

def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    return render(request, 'profile.html', {'profile_user': profile_user})
```

### 2f) Create base template with navbar (login state, create post, search box)

- [ ] Create directories: `main/templates/`, `main/templates/main/`, `main/templates/main/registration/`, `main/templates/main/partials/`
- [ ] Create `main/templates/base.html`

```html
{% load static %}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{% block title %}Readit{% endblock %}</title>
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
    />
  </head>
  <body class="bg-light">
    <nav class="navbar navbar-expand-lg bg-white border-bottom sticky-top">
      <div class="container">
        <a class="navbar-brand fw-bold text-danger" href="{% url 'home' %}"
          >readit</a
        >
        <form
          class="d-flex flex-grow-1 mx-lg-4 my-2 my-lg-0"
          action="#"
          method="get"
        >
          <input
            class="form-control"
            type="search"
            name="q"
            placeholder="Search"
            value="{{ request.GET.q }}"
          />
        </form>
        <ul class="navbar-nav ms-auto flex-row gap-2 align-items-center">
          <li class="nav-item"><a class="nav-link" href="#">All</a></li>
          {% if user.is_authenticated %}
          <li class="nav-item">
            <a class="nav-link" href="#">+ Create post</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="{% url 'profile' user.username %}"
              >u/{{ user.username }}</a
            >
          </li>
          <li class="nav-item">
            <form method="post" action="{% url 'logout' %}">
              {% csrf_token %}
              <button class="btn btn-sm btn-outline-secondary">Logout</button>
            </form>
          </li>
          {% else %}
          <li class="nav-item">
            <a class="btn btn-sm btn-outline-danger" href="{% url 'login' %}"
              >Log in</a
            >
          </li>
          <li class="nav-item">
            <a class="btn btn-sm btn-danger" href="{% url 'register' %}"
              >Sign up</a
            >
          </li>
          {% endif %}
        </ul>
      </div>
    </nav>
    <main class="container py-4">
      {% for message in messages %}
      <div class="alert alert-{{ message.tags|default:'info' }}">
        {{ message }}
      </div>
      {% endfor %} {% block content %}{% endblock %}
    </main>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
  </body>
</html>
```

### 2g) Create auth templates and pages

- [ ] `main/templates/main/registration/login.html`

```html
{% extends "base.html" %} {% block content %}
<div class="row justify-content-center">
  <div class="col-md-4">
    <h4>Log in</h4>
    <form method="post" class="card card-body">
      {% csrf_token %} {{ form.as_p }}
      <input type="hidden" name="next" value="{{ request.GET.next }}" />
      <button class="btn btn-danger">Log in</button>
    </form>
    <p class="mt-3 small">
      New here? <a href="{% url 'register' %}">Sign up</a>
    </p>
  </div>
</div>
{% endblock %}
```

- [ ] `main/templates/main/registration/register.html`

```html
{% extends "base.html" %} {% block content %}
<div class="row justify-content-center">
  <div class="col-md-4">
    <h4>Sign up</h4>
    <form method="post" class="card card-body">
      {% csrf_token %} {{ form.as_p }}
      <button class="btn btn-danger">Create account</button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] `main/templates/main/home.html`

```html
{% extends "base.html" %} {% block title %}Home · readit{% endblock %} {% block
content %}
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
{% extends "base.html" %} {% block title %}u/{{ profile_user.username }}{%
endblock %} {% block content %}
<div class="row">
  <div class="col-lg-8">
    <div class="card mb-3">
      <div class="card-body">
        <h3>u/{{ profile_user.username }}</h3>
        <div class="text-muted small">
          Joined {{ profile_user.date_joined|date:"M Y" }}
        </div>
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
