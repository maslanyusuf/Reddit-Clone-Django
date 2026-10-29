from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login, logout,get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required

from .forms import CustomPasswordChangeForm, LoginForm, ProfileSettingsForm, RegisterForm

User = get_user_model()

def home_view(request):
  return render(request,'home.html')


def register_view(request):
  form = RegisterForm()
  if request.method == "POST":
    form = RegisterForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('main:home')
  return render(request,"register.html",{"form":form})

def login_view(request):
    # If the user is already logged in, redirect them to the home page
    if request.user.is_authenticated:
        return redirect('main:home') # Change 'home' to your actual home URL name

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Retrieve the authenticated user object we saved in the form
            user = form.cleaned_data['user']

            # Log the user in (creates the session)
            login(request, user)

            # Redirect to the page they were trying to visit, or default to home
            next_url = request.GET.get('next', 'main:home')
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    # 1. Flush the session and log the user out
    logout(request)

    # 2. Redirect to the login page or home page
    # (Change 'main:login' to whatever your actual login URL name is)
    return redirect('main:login')

@login_required
def profile_settings_view(request):
    """Handle profile settings form"""

    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            # Redirect to the user's new profile page (in case username changed)
            return redirect('main:profile_settings')
    else:
        form = ProfileSettingsForm(instance=request.user)

    return render(request, 'profile_settings.html', {'form': form})


@login_required
def password_change_view(request):
    """Handle password change form"""

    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            # Important: Update the session so the user isn't logged out after changing password
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('main:profile_settings')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'password_change.html', {'form': form})

def public_profile_view(request, username):
    # 1. Fetch the user.
    # We use __iexact to make the URL case-insensitive (e.g., /u/JohnDoe works even if DB has johndoe)
    profile_user = get_object_or_404(User, username__iexact=username)

    # 2. Calculate some profile statistics
    # post_count = profile_user.posts.count()
    # comment_count = profile_user.comments.count()

    # 3. Get the user's recent posts (limit to 5 for the MVP)
    # recent_posts = profile_user.posts.select_related('community').order_by('-created_at')[:5]

    # 4. Build the context
    # Note: We name it 'profile_user' instead of 'user' so it doesn't overwrite
    # Django's built-in 'request.user' context processor in the template.
    context = {
        'profile': profile_user,
        # 'post_count': post_count,
        # 'comment_count': comment_count,
        # 'recent_posts': recent_posts,
    }

    return render(request, "profile.html", context)
