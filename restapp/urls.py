from django.urls import path
from .views import user_login, dummy_home, user_logout, message, download_file

urlpatterns = [
    path('', user_login, name='login'),
    path('home', dummy_home, name='home'),
    path('logout', user_logout, name='logout'),
    path('message', message, name='message'),
    path('download/<str:filename>/', download_file, name='download_file'),
]
