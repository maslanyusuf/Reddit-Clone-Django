from django.urls import path
from .views import home_view,login_view,register_view,logout_view,public_profile_view,profile_settings_view,password_change_view
app_name = "main"

urlpatterns = [
    path("",view=home_view,name="home"),
    path("login/",view=login_view,name="login"),
    path("register/",view=register_view,name="register"),
    path('logout/', logout_view, name='logout'),
    path('settings/', profile_settings_view, name='profile_settings'),
    path('settings/password/', password_change_view, name='password_change'),
    # The 'u/' prefix is standard for Reddit-like user profiles (e.g., reddit.com/u/username)
    path('u/<str:username>/', public_profile_view, name='profile'),
]
