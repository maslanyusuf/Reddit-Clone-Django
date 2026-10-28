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


## Reference (Existing Implementation)

This section captures the current working state of the codebase for easy recreation/reference.

### Settings (`configs/settings.py`)
```python
"""
Django settings for configs project.
"""
from pathlib import Path
from decouple import config, Csv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'configs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'configs.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = "main.User"
```

### URLs (`configs/urls.py`)
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
]
```

### Custom User Model (`main/models.py`)
```python
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        if not username:
            raise ValueError("The Username field is required")

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
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

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

### Forms (`main/forms.py`)
```python
from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=256, widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}))
    last_name = forms.CharField(required=True, max_length=256, widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}))
    email = forms.EmailField(required=True, max_length=256, widget=forms.EmailInput(attrs={"type": "email", "class": "form-control"}))
    username = forms.CharField(required=True, max_length=150, widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username


class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        max_length=256,
        widget=forms.EmailInput(attrs={"type": "email", "class": "form-control", "placeholder": "Email Address"})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"type": "password", "class": "form-control", "placeholder": "Password"})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            cleaned_data['user'] = user
        return cleaned_data


class ProfileSettingsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=256, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=256, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    bio = forms.CharField(max_length=512, required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about yourself...', 'rows': 3}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'bio']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
```

### Views (`main/views.py`)
```python
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required

from .forms import CustomPasswordChangeForm, LoginForm, ProfileSettingsForm, RegisterForm

User = get_user_model()


def home_view(request):
    return render(request, 'home.html')


def register_view(request):
    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main:home')
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            next_url = request.GET.get('next', 'main:home')
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('main:login')


@login_required
def profile_settings_view(request):
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('main:profile', username=request.user.username)
    else:
        form = ProfileSettingsForm(instance=request.user)
    return render(request, 'profile_settings.html', {'form': form})


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('main:profile_settings')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'password_change.html', {'form': form})


def public_profile_view(request, username):
    profile_user = get_object_or_404(User, username__iexact=username)
    context = {
        'profile': profile_user,
    }
    return render(request, "profile.html", context)
```

### URLs (`main/urls.py`)
```python
from django.urls import path
from .views import home_view, login_view, register_view, logout_view, public_profile_view, profile_settings_view, password_change_view

app_name = "main"

urlpatterns = [
    path("", view=home_view, name="home"),
    path("login/", view=login_view, name="login"),
    path("register/", view=register_view, name="register"),
    path('logout/', logout_view, name='logout'),
    path('settings/', profile_settings_view, name='profile_settings'),
    path('settings/password/', password_change_view, name='password_change'),
    path('u/<str:username>/', public_profile_view, name='profile'),
]
```

### Templates
**`templates/base.html`**
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Reddit-Clone -{% block title %}{% endblock %}</title>
  </head>
  <body>
    {% include './partials/_header.html' %}
    {% block content %}{% endblock %}
    {% include './partials/_footer.html' %}
  </body>
</html>
```

**`templates/home.html`**
```html
{% extends './base.html' %}
{% block content %}
  <h1>Home Page</h1>
{% endblock %}
```

**`templates/login.html`**
```html
<h1>Login</h1>
{% if form.non_field_errors %}
  <div style="color: red; margin-bottom: 15px; border: 1px solid red; padding: 10px; background-color: #ffe6e6;">
    {% for error in form.non_field_errors %}
      <p style="margin: 0;">{{ error }}</p>
    {% endfor %}
  </div>
{% endif %}
<form method="post" action="{% url 'main:login' %}">
  {% csrf_token %}
  <div style="margin-bottom: 10px;">
    <label for="{{ form.email.id_for_label }}">{{ form.email.label }}</label><br />
    {{ form.email }}
    {% if form.email.errors %}
      <div style="color: red;">{{ form.email.errors }}</div>
    {% endif %}
  </div>
  <div style="margin-bottom: 15px;">
    <label for="{{ form.password.id_for_label }}">{{ form.password.label }}</label><br />
    {{ form.password }}
    {% if form.password.errors %}
      <div style="color: red;">{{ form.password.errors }}</div>
    {% endif %}
  </div>
  <button type="submit" class="btn btn-primary">Login</button>
</form>
<p>Don't have an account? <a href="{% url 'main:register' %}">Register here</a></p>
```

**`templates/register.html`**
```html
<h1>Register Page</h1>
{% if form.non_field_errors %}
  <div style="color: red; margin-bottom: 15px; border: 1px solid red; padding: 10px;">
    {% for error in form.non_field_errors %}
      <p>{{ error }}</p>
    {% endfor %}
  </div>
{% endif %}
<form action="{% url 'main:register' %}" method="post" novalidate>
  {% csrf_token %}
  <div style="margin-bottom: 10px;">
    <label for="{{ form.first_name.id_for_label }}">{{ form.first_name.label }}</label><br />
    {{ form.first_name }}
    {% if form.first_name.errors %}<div style="color: red;">{{ form.first_name.errors }}</div>{% endif %}
  </div>
  <div style="margin-bottom: 10px;">
    <label for="{{ form.last_name.id_for_label }}">{{ form.last_name.label }}</label><br />
    {{ form.last_name }}
    {% if form.last_name.errors %}<div style="color: red;">{{ form.last_name.errors }}</div>{% endif %}
  </div>
  <div style="margin-bottom: 10px;">
    <label for="{{ form.email.id_for_label }}">{{ form.email.label }}</label><br />
    {{ form.email }}
    {% if form.email.errors %}<div style="color: red;">{{ form.email.errors }}</div>{% endif %}
  </div>
  <div style="margin-bottom: 10px;">
    <label for="{{ form.username.id_for_label }}">{{ form.username.label }}</label><br />
    {{ form.username }}
    {% if form.username.errors %}<div style="color: red;">{{ form.username.errors }}</div>{% endif %}
  </div>
  <div style="margin-bottom: 10px;">
    <label for="{{ form.password1.id_for_label }}">{{ form.password1.label }}</label><br />
    {{ form.password1 }}
    {% if form.password1.errors %}<div style="color: red;">{{ form.password1.errors }}</div>{% endif %}
    {% if form.password1.help_text %}<small style="color: gray; display: block; margin-top: 5px;">{{ form.password1.help_text|safe }}</small>{% endif %}
  </div>
  <div style="margin-bottom: 15px;">
    <label for="{{ form.password2.id_for_label }}">{{ form.password2.label }}</label><br />
    {{ form.password2 }}
    {% if form.password2.errors %}<div style="color: red;">{{ form.password2.errors }}</div>{% endif %}
  </div>
  <button type="submit">Create Account</button>
</form>
<div>
  <p>Already have Account</p>
  <a href="{% url 'main:login' %}">Login</a>
</div>
```

**`templates/profile.html`**
```html
<h1>Profile</h1>
<p>{{ profile.username }}</p>
```

**`templates/partials/_header.html`**
```html
<header>Header</header>
```

**`templates/partials/_footer.html`**
```html
<footer>Footer</footer>
```

