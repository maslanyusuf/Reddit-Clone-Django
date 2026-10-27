# Reddit Clone MVP — Django Roadmap & Blueprint

A complete plan for building a Reddit-style MVP with **Django**, using:

- `config/` → the Django **project** (settings, root urls, wsgi/asgi only)
- `main/` → the **single app** (models, views, forms, urls, templates, static, tests)

---

## 1. MVP Scope

**In scope (MVP)**

| Area        | Features                                                |
| ----------- | ------------------------------------------------------- |
| Auth        | Register, login, logout, user profile page              |
| Communities | Create community, join/leave, community page            |
| Posts       | Text posts and link posts, edit, delete                 |
| Comments    | Threaded (nested) comments, delete                      |
| Voting      | Upvote/downvote posts and comments (toggle)             |
| Feeds       | Home (joined communities), All, sort by Hot / New / Top |
| Misc        | Search, pagination, Django admin for moderation         |

**Out of scope (post-MVP)**: image uploads, notifications, private messages, awards, real-time updates, mod tools beyond admin, API/DRF, email verification.

---

## 2. Tech Stack

- Python 3.11+, Django 5.x
- SQLite for development (switch to PostgreSQL for production)
- Bootstrap 5 via CDN (no build step)
- Vanilla JS `fetch` for voting (no framework needed)
- `markdown` + `bleach` (optional) to render safe markdown in posts/comments

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install django markdown bleach
django-admin startproject config .
python manage.py startapp main
```

---

## 3. Project Structure

```
reddit_clone/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── main/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── utils.py                  # hot ranking, vote logic, comment tree
    ├── tests.py
    ├── templatetags/
    │   ├── __init__.py
    │   └── main_extras.py        # markdown filter
    ├── static/main/
    │   ├── css/style.css
    │   └── js/vote.js
    └── templates/
        ├── base.html
        └── main/
            ├── home.html
            ├── community_detail.html
            ├── community_form.html
            ├── post_detail.html
            ├── post_form.html
            ├── profile.html
            ├── search.html
            ├── partials/
            │   ├── post_card.html
            │   ├── comment.html
            │   ├── pagination.html
            │   └── sort_tabs.html
            └── registration/
                ├── login.html
                └── register.html
```

> Tip: put `registration/` templates under `templates/registration/` if you want Django's built-in `LoginView` to find them by default. This guide sets `template_name` explicitly instead.

---

## 4. Roadmap (Phases)

### Phase 0 — Setup (½ day)

- [ ] Create venv, project `config`, app `main`
- [ ] Add `main` to `INSTALLED_APPS`
- [ ] Create **custom User model before the first migration**
- [ ] Configure templates, static, auth redirects
- [ ] Git init + `.gitignore`

### Phase 1 — Auth & Base UI (1 day)

- [ ] Register / login / logout
- [ ] `base.html` with navbar (login state, create post, search box)
- [ ] Profile page (`/u/<username>/`)

### Phase 2 — Communities (1 day)

- [ ] `Community` and `Membership` models
- [ ] Create community, community detail page
- [ ] Join / leave (POST)

### Phase 3 — Posts (1–2 days)

- [ ] `Post` model (text or link)
- [ ] Submit to community, post detail, edit, delete
- [ ] Reusable `post_card.html`

### Phase 4 — Voting (1 day)

- [ ] `PostVote` model with unique constraint
- [ ] Toggle vote logic in a transaction
- [ ] JS fetch → update score and arrow state without reload

### Phase 5 — Comments (1–2 days)

- [ ] `Comment` model with `parent` self-FK
- [ ] Build comment tree in Python (avoids N+1 queries)
- [ ] Recursive template include, reply form, delete
- [ ] `CommentVote`

### Phase 6 — Feeds, Sorting, Search (1 day)

- [ ] Home (joined communities) and All
- [ ] Hot / New / Top sorting, pagination
- [ ] Search posts and communities

### Phase 7 — Polish & Safety (1 day)

- [ ] Permissions (only author can edit/delete)
- [ ] Markdown rendering with sanitization
- [ ] Admin configuration, 404/403 pages
- [ ] Tests for models, voting, permissions

### Phase 8 — Deploy (½–1 day)

- [ ] Environment variables, `DEBUG=False`, `ALLOWED_HOSTS`
- [ ] PostgreSQL, `collectstatic`, gunicorn + whitenoise

---

## 5. Database Design

### 5.1 Tables Overview

| Table (model) | Purpose                              |
| ------------- | ------------------------------------ |
| `User`        | Custom user extending `AbstractUser` |
| `Community`   | A subreddit-like space               |
| `Membership`  | User ↔ Community (join / role)       |
| `Post`        | Text or link submission              |
| `PostVote`    | One vote per user per post           |
| `Comment`     | Threaded comments                    |
| `CommentVote` | One vote per user per comment        |

### 5.2 Relationships

```
User 1───* Post            (author)
User 1───* Comment         (author)
User *───* Community       (through Membership)
Community 1───* Post
Post 1───* Comment
Comment 1───* Comment      (parent → replies)
User *───* Post            (through PostVote)
User *───* Comment         (through CommentVote)
```

### 5.3 Columns

**User** (extends `AbstractUser`)

| Field         | Type                                     | Notes    |
| ------------- | ---------------------------------------- | -------- |
| bio           | CharField(300)                           | optional |
| _(inherited)_ | username, email, password, date_joined … |          |

**Community**

| Field       | Type          | Notes                                                 |
| ----------- | ------------- | ----------------------------------------------------- |
| name        | CharField(21) | unique (case-insensitive), letters/numbers/underscore |
| description | TextField     | optional                                              |
| creator     | FK User       | SET_NULL                                              |
| created_at  | DateTime      | auto                                                  |

**Membership**

| Field     | Type         | Notes                    |
| --------- | ------------ | ------------------------ |
| user      | FK User      |                          |
| community | FK Community |                          |
| role      | CharField    | `member` / `moderator`   |
| joined_at | DateTime     | auto                     |
|           |              | unique (user, community) |

**Post**

| Field                   | Type                 | Notes                |
| ----------------------- | -------------------- | -------------------- |
| community               | FK Community         | CASCADE              |
| author                  | FK User              | SET_NULL             |
| title                   | CharField(300)       |                      |
| body                    | TextField            | optional (text post) |
| url                     | URLField             | optional (link post) |
| score                   | IntegerField         | cached sum of votes  |
| comment_count           | PositiveIntegerField | cached               |
| hot_rank                | FloatField           | indexed              |
| created_at / updated_at | DateTime             |                      |

**PostVote / CommentVote**

| Field          | Type              | Notes                       |
| -------------- | ----------------- | --------------------------- |
| user           | FK User           |                             |
| post / comment | FK                |                             |
| value          | SmallIntegerField | `+1` or `-1`                |
|                |                   | unique (user, post/comment) |

**Comment**

| Field      | Type         | Notes                           |
| ---------- | ------------ | ------------------------------- |
| post       | FK Post      |                                 |
| parent     | FK self      | null for top-level              |
| author     | FK User      | SET_NULL                        |
| body       | TextField    |                                 |
| score      | IntegerField | cached                          |
| is_deleted | Boolean      | soft delete keeps thread intact |
| created_at | DateTime     |                                 |

---

## 6. Configuration (`config/`)

### 6.1 `config/settings.py` (important parts)

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
]

AUTH_USER_MODEL = "main.User"          # must be set BEFORE first migrate

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],                    # app templates are found via APP_DIRS
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### 6.2 `config/urls.py`

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
]
```

---

## 7. Models (`main/models.py`)

```python
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse

from .utils import calculate_hot


class User(AbstractUser):
    bio = models.CharField(max_length=300, blank=True)

    def get_absolute_url(self):
        return reverse("profile", args=[self.username])


class Community(models.Model):
    name = models.CharField(
        max_length=21,
        validators=[RegexValidator(r"^[A-Za-z0-9_]+$", "Letters, numbers and underscores only.")],
    )
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_communities"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Membership", related_name="communities"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "communities"
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_community_name_ci"),
        ]

    def __str__(self):
        return f"c/{self.name}"

    def get_absolute_url(self):
        return reverse("community_detail", args=[self.name])


class Membership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        MODERATOR = "moderator", "Moderator"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "community"], name="unique_membership"),
        ]


class Post(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="posts"
    )
    title = models.CharField(max_length=300)
    body = models.TextField(blank=True)
    url = models.URLField(blank=True)
    score = models.IntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    hot_rank = models.FloatField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        if not self.body and not self.url:
            raise ValidationError("A post needs either text or a link.")

    @property
    def is_link(self):
        return bool(self.url)

    def get_absolute_url(self):
        return reverse("post_detail", args=[self.pk])

    def refresh_rank(self):
        self.hot_rank = calculate_hot(self.score, self.created_at)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="comments"
    )
    body = models.TextField()
    score = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment {self.pk} on {self.post_id}"


class BaseVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=[(1, "Up"), (-1, "Down")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class PostVote(BaseVote):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="votes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_post_vote")]


class CommentVote(BaseVote):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="votes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "comment"], name="unique_comment_vote")]
```

Run:

```bash
python manage.py makemigrations main
python manage.py migrate
python manage.py createsuperuser
```

---

## 8. Utilities (`main/utils.py`)

```python
from math import log10

from django.db import transaction
from django.db.models import Sum

EPOCH = 1134028003  # reddit's reference timestamp


def calculate_hot(score, created_at):
    """Reddit-style hot ranking: log of score + time bonus."""
    order = log10(max(abs(score), 1))
    sign = 1 if score > 0 else -1 if score < 0 else 0
    seconds = created_at.timestamp() - EPOCH
    return round(sign * order + seconds / 45000, 7)


@transaction.atomic
def apply_vote(vote_model, obj, user, value, fk_name):
    """
    Toggle logic:
      - same vote again  -> remove vote
      - opposite vote    -> switch
      - no vote          -> create
    Returns (new_score, user_vote) where user_vote is 1, -1 or 0.
    """
    lookup = {"user": user, fk_name: obj}
    existing = vote_model.objects.filter(**lookup).first()

    if existing and existing.value == value:
        existing.delete()
        user_vote = 0
    elif existing:
        existing.value = value
        existing.save(update_fields=["value"])
        user_vote = value
    else:
        vote_model.objects.create(value=value, **lookup)
        user_vote = value

    total = vote_model.objects.filter(**{fk_name: obj}).aggregate(s=Sum("value"))["s"] or 0
    obj.score = total
    if hasattr(obj, "refresh_rank"):
        obj.refresh_rank()
        obj.save(update_fields=["score", "hot_rank"])
    else:
        obj.save(update_fields=["score"])
    return total, user_vote


def build_comment_tree(comments):
    """Takes a flat queryset/list, returns top-level comments with .children lists."""
    by_id = {c.id: c for c in comments}
    for c in comments:
        c.children = []
    roots = []
    for c in comments:
        if c.parent_id and c.parent_id in by_id:
            by_id[c.parent_id].children.append(c)
        else:
            roots.append(c)
    return roots
```

---

## 9. Forms (`main/forms.py`)

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Community, Post, User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Community.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("This community name is taken.")
        return name


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "body", "url")
        widgets = {"body": forms.Textarea(attrs={"rows": 8})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "What are your thoughts?"})}
```

---

## 10. URLs (`main/urls.py`)

```python
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # feeds
    path("", views.HomeView.as_view(), name="home"),
    path("all/", views.AllView.as_view(), name="all"),
    path("search/", views.search, name="search"),

    # auth
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="main/registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # communities
    path("c/create/", views.community_create, name="community_create"),
    path("c/<str:name>/", views.community_detail, name="community_detail"),
    path("c/<str:name>/join/", views.community_toggle_join, name="community_join"),
    path("c/<str:name>/submit/", views.post_create, name="post_create"),

    # posts
    path("post/<int:pk>/", views.post_detail, name="post_detail"),
    path("post/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("post/<int:pk>/delete/", views.post_delete, name="post_delete"),
    path("post/<int:pk>/vote/", views.post_vote, name="post_vote"),
    path("post/<int:pk>/comment/", views.comment_create, name="comment_create"),

    # comments
    path("comment/<int:pk>/vote/", views.comment_vote, name="comment_vote"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),

    # profile
    path("u/<str:username>/", views.profile, name="profile"),
]
```

> Django 5 requires `LogoutView` to be called with **POST**. Use a small form with CSRF token in the navbar (see `base.html`).

---

## 11. Views (`main/views.py`)

```python
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .forms import CommentForm, CommunityForm, PostForm, RegisterForm
from .models import (
    Comment, CommentVote, Community, Membership, Post, PostVote, User,
)
from .utils import apply_vote, build_comment_tree

PAGE_SIZE = 20
SORTS = {
    "hot": "-hot_rank",
    "new": "-created_at",
    "top": "-score",
}


# ---------- helpers ----------
def paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))


def attach_user_votes(request, page_obj):
    """Adds .user_vote (1, -1, 0) to every post on the page in one query."""
    posts = list(page_obj.object_list)
    if request.user.is_authenticated and posts:
        votes = PostVote.objects.filter(user=request.user, post__in=posts)
        vote_map = {v.post_id: v.value for v in votes}
    else:
        vote_map = {}
    for p in posts:
        p.user_vote = vote_map.get(p.id, 0)
    page_obj.object_list = posts
    return page_obj


def sorted_posts(request, queryset):
    sort = request.GET.get("sort", "hot")
    if sort not in SORTS:
        sort = "hot"
    qs = queryset.select_related("author", "community").order_by(SORTS[sort])
    return qs, sort


# ---------- feeds ----------
class AllView(TemplateView):
    template_name = "main/home.html"
    title = "All"

    def get_queryset(self):
        return Post.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs, sort = sorted_posts(self.request, self.get_queryset())
        ctx["page_obj"] = attach_user_votes(self.request, paginate(self.request, qs))
        ctx["sort"] = sort
        ctx["title"] = self.title
        return ctx


class HomeView(AllView):
    title = "Home"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            joined = Membership.objects.filter(user=user).values("community_id")
            qs = Post.objects.filter(community_id__in=joined)
            if qs.exists():
                return qs
        return Post.objects.all()   # fallback for guests / no memberships


def search(request):
    q = request.GET.get("q", "").strip()
    posts, communities = Post.objects.none(), Community.objects.none()
    if q:
        posts = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q)).select_related("author", "community")[:50]
        communities = Community.objects.filter(Q(name__icontains=q) | Q(description__icontains=q))[:20]
    return render(request, "main/search.html", {"q": q, "posts": posts, "communities": communities})


# ---------- auth ----------
def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(request, "main/registration/register.html", {"form": form})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = profile_user.posts.select_related("community")
    comments = profile_user.comments.filter(is_deleted=False).select_related("post")[:20]
    return render(request, "main/profile.html", {
        "profile_user": profile_user,
        "page_obj": attach_user_votes(request, paginate(request, posts)),
        "comments": comments,
    })


# ---------- communities ----------
@login_required
def community_create(request):
    form = CommunityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        community = form.save(commit=False)
        community.creator = request.user
        community.save()
        Membership.objects.create(user=request.user, community=community, role=Membership.Role.MODERATOR)
        return redirect(community)
    return render(request, "main/community_form.html", {"form": form})


def community_detail(request, name):
    community = get_object_or_404(Community, name__iexact=name)
    qs, sort = sorted_posts(request, community.posts.all())
    is_member = (
        request.user.is_authenticated
        and Membership.objects.filter(user=request.user, community=community).exists()
    )
    return render(request, "main/community_detail.html", {
        "community": community,
        "page_obj": attach_user_votes(request, paginate(request, qs)),
        "sort": sort,
        "is_member": is_member,
        "member_count": community.membership_set.count(),
    })


@login_required
@require_POST
def community_toggle_join(request, name):
    community = get_object_or_404(Community, name__iexact=name)
    membership = Membership.objects.filter(user=request.user, community=community)
    if membership.exists():
        membership.delete()
    else:
        Membership.objects.create(user=request.user, community=community)
    return redirect(community)


# ---------- posts ----------
@login_required
def post_create(request, name):
    community = get_object_or_404(Community, name__iexact=name)
    form = PostForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.community = community
        post.author = request.user
        post.refresh_rank()  # created_at not set yet -> save first, then rank
        post.save()
        post.refresh_rank()
        post.save(update_fields=["hot_rank"])
        return redirect(post)
    return render(request, "main/post_form.html", {"form": form, "community": community})


def post_detail(request, pk):
    post = get_object_or_404(Post.objects.select_related("author", "community"), pk=pk)
    comments = list(post.comments.select_related("author"))
    tree = build_comment_tree(comments)

    post.user_vote = 0
    comment_votes = {}
    if request.user.is_authenticated:
        v = PostVote.objects.filter(user=request.user, post=post).first()
        post.user_vote = v.value if v else 0
        comment_votes = dict(
            CommentVote.objects.filter(user=request.user, comment__post=post).values_list("comment_id", "value")
        )
    for c in comments:
        c.user_vote = comment_votes.get(c.id, 0)

    return render(request, "main/post_detail.html", {
        "post": post,
        "comments": tree,
        "comment_form": CommentForm(),
    })


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden()
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(post)
    return render(request, "main/post_form.html", {"form": form, "community": post.community, "editing": True})


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    community = post.community
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect(community)


@login_required
@require_POST
def post_vote(request, pk):
    post = get_object_or_404(Post, pk=pk)
    value = 1 if request.POST.get("value") == "1" else -1
    score, user_vote = apply_vote(PostVote, post, request.user, value, "post")
    return JsonResponse({"score": score, "user_vote": user_vote})


# ---------- comments ----------
@login_required
@require_POST
def comment_create(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        parent_id = request.POST.get("parent")
        if parent_id:
            comment.parent = get_object_or_404(Comment, pk=parent_id, post=post)
        comment.save()
        post.comment_count = post.comments.count()
        post.save(update_fields=["comment_count"])
    return redirect(post)


@login_required
@require_POST
def comment_vote(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    value = 1 if request.POST.get("value") == "1" else -1
    score, user_vote = apply_vote(CommentVote, comment, request.user, value, "comment")
    return JsonResponse({"score": score, "user_vote": user_vote})


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    comment.is_deleted = True
    comment.body = "[deleted]"
    comment.save(update_fields=["is_deleted", "body"])
    return redirect(comment.post)
```

> Note in `post_create`: `created_at` is set by `auto_now_add` during `save()`, so rank is computed **after** the first save. You can remove the first `refresh_rank()` call — it is harmless but redundant.

---

## 12. Template Tags (`main/templatetags/main_extras.py`)

```python
import bleach
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "ul", "ol", "li", "blockquote",
    "code", "pre", "a", "h1", "h2", "h3", "hr",
]
ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}


@register.filter
def render_markdown(text):
    html = md.markdown(text or "", extensions=["fenced_code", "nl2br"])
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    clean = bleach.linkify(clean)
    return mark_safe(clean)
```

Create an empty `main/templatetags/__init__.py` too.

---

## 13. Templates

### 13.1 `main/templates/base.html`

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
    <link href="{% static 'main/css/style.css' %}" rel="stylesheet" />
  </head>
  <body class="bg-light">
    <nav class="navbar navbar-expand-lg bg-white border-bottom sticky-top">
      <div class="container">
        <a class="navbar-brand fw-bold text-danger" href="{% url 'home' %}"
          >readit</a
        >

        <form
          class="d-flex flex-grow-1 mx-lg-4 my-2 my-lg-0"
          action="{% url 'search' %}"
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
          <li class="nav-item">
            <a class="nav-link" href="{% url 'all' %}">All</a>
          </li>
          {% if user.is_authenticated %}
          <li class="nav-item">
            <a class="nav-link" href="{% url 'community_create' %}"
              >+ Community</a
            >
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

    <script>
      window.IS_AUTH = {{ user.is_authenticated|yesno:"true,false" }}; window.LOGIN_URL = "{% url 'login' %}";
    </script>
    <script src="{% static 'main/js/vote.js' %}"></script>
    {% block extra_js %}{% endblock %}
  </body>
</html>
```

### 13.2 `partials/post_card.html`

```html
<div class="card mb-2 post-card" data-post-id="{{ post.id }}">
  <div class="d-flex">
    <div
      class="vote-col text-center p-2 bg-body-tertiary"
      data-vote-url="{% url 'post_vote' post.id %}"
    >
      <button
        class="btn btn-sm vote-btn up {% if post.user_vote == 1 %}active{% endif %}"
        data-value="1"
      >
        ▲
      </button>
      <div class="score fw-bold">{{ post.score }}</div>
      <button
        class="btn btn-sm vote-btn down {% if post.user_vote == -1 %}active{% endif %}"
        data-value="-1"
      >
        ▼
      </button>
    </div>
    <div class="card-body py-2">
      <div class="small text-muted">
        <a
          href="{{ post.community.get_absolute_url }}"
          class="fw-semibold text-decoration-none"
          >c/{{ post.community.name }}</a
        >
        · Posted by {% if post.author %}<a
          href="{{ post.author.get_absolute_url }}"
          >u/{{ post.author.username }}</a
        >{% else %}[deleted]{% endif %} · {{ post.created_at|timesince }} ago
      </div>
      <h5 class="mb-1">
        <a
          href="{{ post.get_absolute_url }}"
          class="text-decoration-none text-dark"
          >{{ post.title }}</a
        >
      </h5>
      {% if post.is_link %}
      <a
        href="{{ post.url }}"
        target="_blank"
        rel="noopener noreferrer nofollow"
        class="small"
        >{{ post.url|truncatechars:60 }} ↗</a
      >
      {% elif post.body %}
      <p class="mb-1 text-muted small">{{ post.body|truncatewords:35 }}</p>
      {% endif %}
      <a
        href="{{ post.get_absolute_url }}"
        class="small text-muted text-decoration-none"
        >💬 {{ post.comment_count }} comments</a
      >
    </div>
  </div>
</div>
```

### 13.3 `partials/sort_tabs.html`

```html
<ul class="nav nav-pills mb-3">
  {% for key, label in sort_options %}{% endfor %}
  <li class="nav-item">
    <a class="nav-link {% if sort == 'hot' %}active{% endif %}" href="?sort=hot"
      >🔥 Hot</a
    >
  </li>
  <li class="nav-item">
    <a class="nav-link {% if sort == 'new' %}active{% endif %}" href="?sort=new"
      >🆕 New</a
    >
  </li>
  <li class="nav-item">
    <a class="nav-link {% if sort == 'top' %}active{% endif %}" href="?sort=top"
      >🏆 Top</a
    >
  </li>
</ul>
```

(Delete the empty `{% for %}` line — it is a leftover placeholder; the three static links are enough.)

### 13.4 `partials/pagination.html`

```html
{% if page_obj.has_other_pages %}
<nav class="mt-3">
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
    <li class="page-item">
      <a
        class="page-link"
        href="?sort={{ sort }}&page={{ page_obj.previous_page_number }}"
        >Previous</a
      >
    </li>
    {% endif %}
    <li class="page-item disabled">
      <span class="page-link"
        >{{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span
      >
    </li>
    {% if page_obj.has_next %}
    <li class="page-item">
      <a
        class="page-link"
        href="?sort={{ sort }}&page={{ page_obj.next_page_number }}"
        >Next</a
      >
    </li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

### 13.5 `main/home.html` (used by Home and All)

```html
{% extends "base.html" %} {% block title %}{{ title }} · readit{% endblock %} {%
block content %}
<div class="row">
  <div class="col-lg-8">
    <h4 class="mb-3">{{ title }}</h4>
    {% include "main/partials/sort_tabs.html" %} {% for post in page_obj %} {%
    include "main/partials/post_card.html" %} {% empty %}
    <div class="alert alert-secondary">
      No posts yet. Join or create a community to get started.
    </div>
    {% endfor %} {% include "main/partials/pagination.html" %}
  </div>
  <div class="col-lg-4">
    <div class="card">
      <div class="card-body">
        <h6>Welcome</h6>
        <p class="small text-muted">
          Your personal front page. Join communities to fill it up.
        </p>
        {% if user.is_authenticated %}
        <a class="btn btn-danger w-100" href="{% url 'community_create' %}"
          >Create community</a
        >
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### 13.6 `main/community_detail.html`

```html
{% extends "base.html" %} {% block title %}c/{{ community.name }}{% endblock %}
{% block content %}
<div class="card mb-3">
  <div class="card-body d-flex justify-content-between align-items-center">
    <div>
      <h3 class="mb-0">c/{{ community.name }}</h3>
      <div class="text-muted small">{{ member_count }} members</div>
      <p class="mb-0 mt-2">{{ community.description }}</p>
    </div>
    <div class="d-flex gap-2">
      {% if user.is_authenticated %}
      <form method="post" action="{% url 'community_join' community.name %}">
        {% csrf_token %}
        <button
          class="btn {% if is_member %}btn-outline-secondary{% else %}btn-danger{% endif %}"
        >
          {% if is_member %}Joined ✓{% else %}Join{% endif %}
        </button>
      </form>
      <a
        class="btn btn-outline-danger"
        href="{% url 'post_create' community.name %}"
        >Create post</a
      >
      {% endif %}
    </div>
  </div>
</div>

{% include "main/partials/sort_tabs.html" %} {% for post in page_obj %} {%
include "main/partials/post_card.html" %} {% empty %}
<div class="alert alert-secondary">
  Nothing here yet — be the first to post.
</div>
{% endfor %} {% include "main/partials/pagination.html" %} {% endblock %}
```

### 13.7 `main/community_form.html`

```html
{% extends "base.html" %} {% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <h4>Create a community</h4>
    <form method="post" class="card card-body">
      {% csrf_token %} {{ form.as_p }}
      <button class="btn btn-danger">Create</button>
    </form>
  </div>
</div>
{% endblock %}
```

### 13.8 `main/post_form.html`

```html
{% extends "base.html" %} {% block content %}
<div class="row justify-content-center">
  <div class="col-md-8">
    <h4>
      {% if editing %}Edit post{% else %}Post to c/{{ community.name }}{% endif
      %}
    </h4>
    <form method="post" class="card card-body">
      {% csrf_token %} {{ form.non_field_errors }} {{ form.as_p }}
      <p class="small text-muted">
        Fill in text, a link, or both. Markdown is supported in text.
      </p>
      <button class="btn btn-danger">
        {% if editing %}Save{% else %}Post{% endif %}
      </button>
    </form>
  </div>
</div>
{% endblock %}
```

### 13.9 `main/post_detail.html`

```html
{% extends "base.html" %} {% load main_extras %} {% block title %}{{ post.title
}}{% endblock %} {% block content %}
<div class="row">
  <div class="col-lg-8">
    {% include "main/partials/post_card.html" %} {% if post.body %}
    <div class="card mb-3">
      <div class="card-body markdown">{{ post.body|render_markdown }}</div>
    </div>
    {% endif %} {% if user == post.author or user.is_staff %}
    <div class="mb-3 d-flex gap-2">
      {% if user == post.author %}<a
        href="{% url 'post_edit' post.id %}"
        class="btn btn-sm btn-outline-secondary"
        >Edit</a
      >{% endif %}
      <form
        method="post"
        action="{% url 'post_delete' post.id %}"
        onsubmit="return confirm('Delete this post?')"
      >
        {% csrf_token %}
        <button class="btn btn-sm btn-outline-danger">Delete</button>
      </form>
    </div>
    {% endif %} {% if user.is_authenticated %}
    <form
      method="post"
      action="{% url 'comment_create' post.id %}"
      class="mb-4"
    >
      {% csrf_token %} {{ comment_form.body }}
      <button class="btn btn-danger btn-sm mt-2">Comment</button>
    </form>
    {% else %}
    <p>
      <a href="{% url 'login' %}?next={{ request.path }}">Log in</a> to comment.
    </p>
    {% endif %}

    <h6>{{ post.comment_count }} comments</h6>
    {% for comment in comments %} {% include "main/partials/comment.html" with
    comment=comment depth=0 %} {% empty %}
    <p class="text-muted">No comments yet.</p>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

### 13.10 `partials/comment.html` (recursive)

```html
{% load main_extras %}
<div class="comment border-start ps-3 mt-3" id="comment-{{ comment.id }}">
  <div class="small text-muted">
    {% if comment.author and not comment.is_deleted %}
    <a href="{{ comment.author.get_absolute_url }}"
      >u/{{ comment.author.username }}</a
    >
    {% else %}[deleted]{% endif %} · {{ comment.created_at|timesince }} ago
  </div>

  <div class="my-1 markdown">
    {% if comment.is_deleted %}<em class="text-muted">[deleted]</em>{% else %}{{
    comment.body|render_markdown }}{% endif %}
  </div>

  <div
    class="d-flex align-items-center gap-2 small vote-col-inline"
    data-vote-url="{% url 'comment_vote' comment.id %}"
  >
    <button
      class="btn btn-sm vote-btn up {% if comment.user_vote == 1 %}active{% endif %}"
      data-value="1"
    >
      ▲
    </button>
    <span class="score fw-bold">{{ comment.score }}</span>
    <button
      class="btn btn-sm vote-btn down {% if comment.user_vote == -1 %}active{% endif %}"
      data-value="-1"
    >
      ▼
    </button>

    {% if user.is_authenticated and not comment.is_deleted %}
    <a
      class="text-muted"
      data-bs-toggle="collapse"
      href="#reply-{{ comment.id }}"
      role="button"
      >Reply</a
    >
    {% if user == comment.author or user.is_staff %}
    <form
      method="post"
      action="{% url 'comment_delete' comment.id %}"
      class="d-inline"
    >
      {% csrf_token %}
      <button class="btn btn-link btn-sm text-danger p-0">Delete</button>
    </form>
    {% endif %} {% endif %}
  </div>

  {% if user.is_authenticated %}
  <div class="collapse mt-2" id="reply-{{ comment.id }}">
    <form method="post" action="{% url 'comment_create' post.id %}">
      {% csrf_token %}
      <input type="hidden" name="parent" value="{{ comment.id }}" />
      <textarea name="body" rows="2" class="form-control" required></textarea>
      <button class="btn btn-danger btn-sm mt-1">Reply</button>
    </form>
  </div>
  {% endif %} {% if depth < 8 %} {% for child in comment.children %} {% include
  "main/partials/comment.html" with comment=child depth=depth|add:1 %} {% endfor
  %} {% endif %}
</div>
```

For Bootstrap's collapse (reply form), add the Bootstrap JS bundle before `</body>` in `base.html`:

```html
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```

### 13.11 `main/profile.html`

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
      </div>
    </div>

    <h5>Posts</h5>
    {% for post in page_obj %} {% include "main/partials/post_card.html" %} {%
    empty %}
    <p class="text-muted">No posts.</p>
    {% endfor %}

    <h5 class="mt-4">Recent comments</h5>
    {% for c in comments %}
    <div class="card mb-2">
      <div class="card-body py-2 small">
        On <a href="{{ c.post.get_absolute_url }}">{{ c.post.title }}</a>: {{
        c.body|truncatechars:150 }}
      </div>
    </div>
    {% empty %}
    <p class="text-muted">No comments.</p>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

### 13.12 `main/search.html`

```html
{% extends "base.html" %} {% block content %}
<h4>Results for “{{ q }}”</h4>

<h6 class="mt-4">Communities</h6>
{% for c in communities %}
<div>
  <a href="{{ c.get_absolute_url }}">c/{{ c.name }}</a>
  <span class="text-muted small">{{ c.description|truncatechars:80 }}</span>
</div>
{% empty %}
<p class="text-muted">None found.</p>
{% endfor %}

<h6 class="mt-4">Posts</h6>
{% for post in posts %} {% include "main/partials/post_card.html" %} {% empty %}
<p class="text-muted">None found.</p>
{% endfor %} {% endblock %}
```

### 13.13 Auth templates

`main/registration/login.html`

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

`main/registration/register.html`

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

---

## 14. Static Files

### `main/static/main/css/style.css`

```css
.vote-col {
  width: 52px;
}
.vote-btn {
  line-height: 1;
  padding: 0 0.35rem;
  color: #878a8c;
}
.vote-btn.up.active {
  color: #ff4500;
}
.vote-btn.down.active {
  color: #7193ff;
}
.post-card:hover {
  border-color: #999;
}
.markdown pre {
  background: #f6f7f8;
  padding: 0.75rem;
  border-radius: 0.375rem;
}
.markdown p:last-child {
  margin-bottom: 0;
}
```

### `main/static/main/js/vote.js`

```javascript
function getCookie(name) {
  const match = document.cookie.match(
    new RegExp("(^|;\\s*)" + name + "=([^;]*)"),
  );
  return match ? decodeURIComponent(match[2]) : null;
}

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".vote-btn");
  if (!btn) return;

  if (!window.IS_AUTH) {
    window.location.href =
      window.LOGIN_URL +
      "?next=" +
      encodeURIComponent(window.location.pathname);
    return;
  }

  const wrapper = btn.closest("[data-vote-url]");
  const body = new URLSearchParams({ value: btn.dataset.value });

  const res = await fetch(wrapper.dataset.voteUrl, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
  if (!res.ok) return;

  const data = await res.json();
  wrapper.querySelector(".score").textContent = data.score;
  wrapper.querySelector(".up").classList.toggle("active", data.user_vote === 1);
  wrapper
    .querySelector(".down")
    .classList.toggle("active", data.user_vote === -1);
});
```

> The CSRF cookie is only set when a page renders a `{% csrf_token %}`. If a visitor lands on a page without any form, add `@method_decorator(ensure_csrf_cookie)` to that view, or keep the logout form in the navbar (it renders a token for logged-in users).

---

## 15. Admin (`main/admin.py`)

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Comment, CommentVote, Community, Membership, Post, PostVote, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Profile", {"fields": ("bio",)}),)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "creator", "created_at")
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "author", "score", "created_at")
    list_filter = ("community",)
    search_fields = ("title", "body")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "score", "is_deleted", "created_at")


admin.site.register(Membership)
admin.site.register(PostVote)
admin.site.register(CommentVote)
```

---

## 16. Tests (`main/tests.py`)

```python
from django.test import TestCase
from django.urls import reverse

from .models import Community, Post, PostVote, User
from .utils import apply_vote


class VoteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass12345")
        self.community = Community.objects.create(name="python", creator=self.user)
        self.post = Post.objects.create(community=self.community, author=self.user, title="Hi", body="x")

    def test_toggle_vote(self):
        score, v = apply_vote(PostVote, self.post, self.user, 1, "post")
        self.assertEqual((score, v), (1, 1))
        score, v = apply_vote(PostVote, self.post, self.user, 1, "post")   # same again -> remove
        self.assertEqual((score, v), (0, 0))
        score, v = apply_vote(PostVote, self.post, self.user, -1, "post")
        self.assertEqual((score, v), (-1, -1))

    def test_only_author_can_edit(self):
        other = User.objects.create_user("bob", password="pass12345")
        self.client.force_login(other)
        res = self.client.get(reverse("post_edit", args=[self.post.pk]))
        self.assertEqual(res.status_code, 403)

    def test_post_requires_body_or_url(self):
        from django.core.exceptions import ValidationError
        p = Post(community=self.community, author=self.user, title="Empty")
        with self.assertRaises(ValidationError):
            p.full_clean()
```

Run: `python manage.py test`

---

## 17. Build Order Checklist (quick version)

1. `startproject config .` → `startapp main` → add to `INSTALLED_APPS`
2. Write `User` model + `AUTH_USER_MODEL` → first `makemigrations` / `migrate`
3. Add the rest of the models → migrate → register in admin
4. `base.html` + auth views/templates
5. Communities (create, detail, join)
6. Posts (create, detail, edit, delete) + `post_card.html`
7. Voting (`utils.apply_vote`, JSON view, `vote.js`)
8. Comments (tree builder, recursive template)
9. Feeds, sorting, pagination, search
10. Markdown filter, permissions, tests
11. Deploy settings

---

## 18. Common Pitfalls

- **Custom user model must be set before the first migration.** If you already migrated, delete `db.sqlite3` and migration files and start again (fine during MVP).
- **N+1 queries**: always `select_related("author", "community")` for feeds and fetch comments in a single query, then build the tree in Python.
- **Voting must be POST + CSRF**; never use GET for state changes.
- **Never render user content with `|safe`** — only through the sanitizing `render_markdown` filter.
- **Cached counters** (`score`, `comment_count`) can drift; recompute with `Sum`/`count()` (as this code does) instead of `+= 1`.
- **Logout requires POST** in Django 5.

---

## 19. After the MVP — Next Features

| Priority | Feature                          | Hint                                                 |
| -------- | -------------------------------- | ---------------------------------------------------- |
| High     | Image upload for posts           | `ImageField`, Pillow, `MEDIA_ROOT`                   |
| High     | Saved posts                      | new `SavedPost` model                                |
| Medium   | Moderator tools                  | use `Membership.role`, remove posts in community     |
| Medium   | Notifications for replies        | `Notification` model + signal on comment create      |
| Medium   | Infinite scroll / HTMX           | replace pagination with `hx-get`                     |
| Medium   | REST API                         | Django REST Framework serializers on the same models |
| Low      | Real-time comment updates        | Django Channels                                      |
| Low      | Rate limiting, spam control      | `django-ratelimit`                                   |
| Low      | Time-windowed Top (day/week/all) | filter on `created_at` before ordering by `score`    |

---

Happy building! 🚀
