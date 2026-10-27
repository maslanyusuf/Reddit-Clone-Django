from .views import home_view
from django.urls import path

app_name = "main"

urlpatterns = [
    path("",view=home_view,name="home")
]
